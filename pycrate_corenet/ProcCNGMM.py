# -*- coding: UTF-8 -*-
#/**
# * Software Name : pycrate
# * Version : 0.2
# *
# * Copyright 2017. Benoit Michau. ANSSI.
# *
# * This program is free software; you can redistribute it and/or
# * modify it under the terms of the GNU General Public License
# * as published by the Free Software Foundation; either version 2
# * of the License, or (at your option) any later version.
# * 
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# * 
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# * 02110-1301, USA.
# *
# *--------------------------------------------------------
# * File Name : pycrate_corenet/ProcCNGMM.py
# * Created : 2017-07-19
# * Authors : Benoit Michau 
# *--------------------------------------------------------
#*/

from .utils       import *
from .ProcProto   import *
from .ProcCNRanap import *


TESTING = False

#------------------------------------------------------------------------------#
# NAS GPRS Mobility Management signalling procedures
# TS 24.008, version d90
# Core Network side
#------------------------------------------------------------------------------#

class GMMSigProc(NASSigProc):
    """GPRS Mobility Management signalling procedure handler
    
    instance attributes:
        - Name : procedure name
        - GMM  : reference to the UEGMMd instance running this procedure
        - Iu   : reference to the IuPSd instance connecting the UE
        - Cont : 2-tuple of CN-initiated NAS message(s) and UE-initiated NAS 
                 message(s)
        - Timer: timer in sec. for this procedure
        - Encod: custom NAS message encoders with fixed values
        - Decod: custom NAS message decoders with transform functions
    """
    
    # tacking all exchanged NAS message within the procedure
    TRACK_PDU = True
    
    # potential timer
    Timer        = None
    TimerDefault = 4
    
    if TESTING:
        def __init__(self, encod=None):
            self._prepare(encod)
            self._log('DBG', 'instantiating procedure')
        
        def _log(self, logtype, msg):
            log('[TESTING] [%s] [GMMSigProc] [%s] %s' % (logtype, self.Name, msg))
    
    else:
        def __init__(self, gmmd, encod=None, gmm_preempt=False):
            self._prepare(encod)
            self.GMM = gmmd
            self.Iu  = gmmd.Iu
            self.UE  = gmmd.UE
            self._gmm_preempt = gmm_preempt
            if gmm_preempt:
                self.GMM.ready.clear()
            self._log('DBG', 'instantiating procedure')
        
        def _log(self, logtype, msg):
            self.GMM._log(logtype, '[%s] %s' % (self.Name, msg))
    
    def output(self):
        self._log('ERR', 'output() not implemented')
        return []
    
    def process(self, pdu):
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'UL', pdu) )
        self.UEInfo = {}
        self.decode_msg(pdu, self.UEInfo)
        #
        self._log('ERR', 'process() not implemented')
        return []
    
    def postprocess(self, Proc=None):
        self._log('ERR', 'postprocess() not implemented')
        return []
    
    def abort(self):
        # abort this procedure, and all procedures started within this one
        ind = self.GMM.Proc.index(self)
        if ind >= 0:
            for p in self.GMM.Proc[ind+1:]:
                p.abort()
            del self.GMM.Proc[ind:]
        if self._gmm_preempt:
            # release the GMM stack
            self.GMM.ready.set()
        self._log('INF', 'aborting')
    
    def rm_from_gmm_stack(self):
        # remove the procedure from the GMM stack of procedures
        if self.GMM.Proc[-1] == self:
            del self.GMM.Proc[-1]
        if self._gmm_preempt:
            # release the GMM stack
            self.GMM.ready.set()
    
    def init_timer(self):
        if self.Timer is not None:
            self.TimerValue = getattr(self.GMM, self.Timer, self.TimerDefault)
            self.TimerStart = time()
            self.TimerStop  = self.TimerStart + self.TimerValue
    
    def get_timer(self):
        if self.Timer is None:
            return None
        else:
            return getattr(self.GMM, self.Timer)
    
    def gmm_preempt(self):
        self._gmm_preempt = True
        self.GMM.ready.clear()
    
    #--------------------------------------------------------------------------#
    # common helpers
    #--------------------------------------------------------------------------#
    
    def _collect_cap(self):
        if not hasattr(self, 'Cap') or not hasattr(self, 'UEInfo'):
            return
        for Cap in self.Cap:
            if Cap in self.UEInfo:
                self.UE.Cap[Cap] = self.UEInfo[Cap]
    
    def _chk_imsi(self):
        # arriving here means the UE's IMSI was unknown at first
        Server, imsi = self.UE.Server, self.UE.IMSI
        if not Server.is_imsi_allowed(imsi):
            self.errcause = self.GMM.IDENT_IMSI_NOT_ALLOWED
            return False
        else:
            # update the PTMSI table
            Server.PTMSI[self.UE.PTMSI] = imsi
            #
            if imsi in Server.UE:
                # in the meantime, IMSI was obtained from the CS domain connection
                if self.UE != Server.UE[imsi]:
                    # there is 2 distincts Iu contexts, that need to be merged
                    ue = Server.UE[imsi]
                    if not ue.merge_ps_handler(self.Iu):
                        # unable to merge to the existing profile
                        self._log('WNG', 'profile for IMSI %s already exists, '\
                                  'need to reject for reconnection' % imsi)
                        # reject so that it will reconnect
                        # and get the already existing profile
                        self.errcause = self.GMM.ATT_IMSI_PROV_REJECT
                        return False
                    else:
                        return True
                else:
                    return True
            else:
                Server.UE[imsi] = self.UE
                # update the Server UE's tables
                if imsi in Server.ConfigUE:
                    # update UE's config with it's dedicated config
                    self.UE.set_config( Server.ConfigUE[imsi] )
                elif '*' in Server.ConfigUE:
                    self.UE.set_config( Server.ConfigUE['*'] )
                return True
    
    def _ret_req_imsi(self):
        NasProc = self.GMM.init_proc(GMMIdentification)
        NasProc.set_msg(8, 21, IDType=NAS.IDTYPE_IMSI)
        return NasProc.output()
    
    def _ret_req_imeisv(self):
        NasProc = self.GMM.init_proc(GMMIdentification)
        NasProc.set_msg(8, 21, IDType=NAS.IDTYPE_IMEISV)
        return NasProc.output()
    
    def _ret_auth(self):
        NasProc = self.GMM.init_proc(GMMAuthenticationCiphering)
        return NasProc.output()
    
    def _ret_smc(self, cksn=None, newkey=False):
        # initialize a RANAP SMC procedure
        RanapProc = self.Iu.init_ranap_proc(RANAPSecurityModeControl,
                                            **self.Iu.get_smc_ies(cksn, newkey))
        if RanapProc:
            # and set a callback to self in it
            RanapProc._cb = self
            return [RanapProc]
        else:
            return []


#------------------------------------------------------------------------------#
# GMM procedures: TS 24.008, section 4.7
#------------------------------------------------------------------------------#

class GMMAttach(GMMSigProc):
    """GPRS attach: TS 24.008, section 4.7.3
    
    UE-initiated
    
    CN messages:
        GMMAttachAccept (PD 8, Type 2), IEs:
        - Type1V    : ForceStdby
        - Type1V    : AttachResult
        - Type2     : PeriodicRAUpdateTimer
        - Type1V    : RadioPrioForTOM8
        - Type1V    : RadioPrioForSMS
        - Type3V    : RAI
        - Type3TV   : PTMSISign (T: 25)
        - Type3TV   : NegoREADYTimer (T: 23)
        - Type4TLV  : AllocPTMSI (T: 24)
        - Type4TLV  : MSIdent (T: 35)
        - Type3TV   : GMMCause (T: 37)
        - Type4TLV  : T3302 (T: 42)
        - Type2     : CellNotif (T: 140)
        - Type4TLV  : EquivPLMNList (T: 74)
        - Type1TV   : NetFeatSupp (T: 10)
        - Type4TLV  : T3319 (T: 55)
        - Type4TLV  : T3323 (T: 56)
        - Type4TLV  : T3312Ext (T: 57)
        - Type4TLV  : AddNetFeatSupp (T: 102)
        - Type4TLV  : T3324 (T: 106)
        - Type4TLV  : ExtDRXParam (T: 110)
        - Type1TV   : UPIntegrityInd (T: 12)
        - Type4TLV  : ReplayedMSNetCap (T: 49)
        - Type4TLV  : ReplayedMSRACap (T: 51)
        
        GMMAttachReject (PD 8, Type 4), IEs:
        - Type2     : GMMCause
        - Type4TLV  : T3302 (T: 42)
        - Type4TLV  : T3346 (T: 58)
    
    UE messages:
        GMMAttachRequest (PD 8, Type 1), IEs:
        - Type4LV   : MSNetCap
        - Type1V    : CKSN
        - Type1V    : AttachType
        - Type3V    : DRXParam
        - Type4LV   : ID
        - Type3V    : OldRAI
        - Type4LV   : MSRACap
        - Type3TV   : OldPTMSISign (T: 25)
        - Type3TV   : ReqREADYTimer (T: 23)
        - Type1TV   : TMSIStatus (T: 9)
        - Type4TLV  : PSLCSCap (T: 51)
        - Type4TLV  : MSCm2 (T: 17)
        - Type4TLV  : MSCm3 (T: 32)
        - Type4TLV  : SuppCodecs (T: 64)
        - Type4TLV  : UENetCap (T: 88)
        - Type4TLV  : AddID (T: 26)
        - Type4TLV  : AddRAI (T: 27)
        - Type4TLV  : VoiceDomPref (T: 93)
        - Type1TV   : DeviceProp (T: 13)
        - Type1TV   : PTMSIType (T: 14)
        - Type1TV   : MSNetFeatSupp (T: 12)
        - Type4TLV  : OldLAI (T: 20)
        - Type1TV   : AddUpdateType (T: 15)
        - Type4TLV  : TMSIBasedNRICont (T: 16)
        - Type4TLV  : T3324 (T: 106)
        - Type4TLV  : T3312Ext (T: 57)
        - Type4TLV  : ExtDRXParam (T: 110)
        
        GMMAttachComplete (PD 8, Type 3), IEs:
        - Type4TLV  : InterRATHOInfo (T: 39)
        - Type4TLV  : EUTRANInterRATHOInfo (T: 43)
    """
    
    Cont = (
        (TS24008_GMM.GMMAttachAccept, TS24008_GMM.GMMAttachReject),
        (TS24008_GMM.GMMAttachRequest, TS24008_GMM.GMMAttachComplete)
        )
    
    Cap = ('MSNetCap', 'DRXParam', 'MSRACap', 'PSLCSCap', 'MSCm2', 'MSCm3', 
           'SuppCodecs', 'UENetCap', 'VoiceDomPref', 'DeviceProp', 'MSNetFeatSupp',
           'ExtDRXParam')
    
    Decod = {
        (8, 1) : {
            'CKSN'          : lambda x: x.get_val(),
            'ID'            : lambda x: x[1].decode(),
            'OldRAI'        : lambda x: x.decode(),
            'ReqREADYTimer' : lambda x: {'Unit': x[1]['Unit'].get_val(), 'Value': x[1]['Value'].get_val()},
            }
        }
    
    def process(self, pdu):
        # preempt the GMM stack
        self.gmm_preempt()
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'UL', pdu) )
        #
        if pdu._name == 'GMMAttachRequest':
            # AttachRequest
            self.errcause, self.UEInfo = None, {}
            self.decode_msg(pdu, self.UEInfo)
            return self._process_req()
        else:
            # AttachComplete
            self.errcause, self.CompInfo = None, {}
            self.decode_msg(pdu, self.CompInfo)
            if self.ptmsi_realloc >= 0:
                self.UE.set_ptmsi(self.ptmsi_realloc)
                self._log('INF', 'new P-TMSI set, 0x%.8x' % self.ptmsi_realloc)
            return self._end()
    
    def _process_req(self):
        #
        if self.UEInfo['ID'][0] == NAS.IDTYPE_TMSI and self.UE.PTMSI is None:
            self.UE.PTMSI = self.UEInfo['ID'][1]
        #
        att_type = self.UEInfo['AttachType']['Type']
        self.att_type = att_type.get_val()
        self._log('INF', 'request type %i (%s), old RAI %s.%.4x.%.2x'\
                  % (att_type(), att_type._dic[self.att_type],
                     self.UEInfo['OldRAI'][0], self.UEInfo['OldRAI'][1], self.UEInfo['OldRAI'][2]))
        # collect capabilities
        self._collect_cap()
        #
        if self.UE.IMEISV is None and self.GMM.IDENT_IMEISV_REQ:
            self._req_imeisv = True
        else:
            self._req_imeisv = False
        #
        # check for emergency attach
        if self.att_type == 4:
            if self.GMM.ATT_EMERG:
                self.errcause = self.GMM.ATT_EMERG
                return self.output()
            else:
                # jump directly to the attach accept
                self.EMM.set_sec_ctx_emerg()
                # emergency ctx has always ksi 0
                return self.output()
        #
        # check local ID
        if self.UE.IMSI is None:
            # UEd was created based on a PTMSI provided at the RRC layer
            # -> we need to get its IMSI before continuing
            # we remove it from the Server's provisory dict of UE
            try:
                del self.UE.Server._UEpre[self.UE.PTMSI]
            except:
                pass
            #
            if self.UEInfo['ID'][0] == 1:
                # IMSI is provided at the NAS layer
                self.UE.set_ident_from_ue(*self.UEInfo['ID'], dom='PS')
                if not self._chk_imsi():
                    # IMSI not allowed
                    return self.output()
            else:
                # need to request the IMSI, prepare an id request procedure
                return self._ret_req_imsi()
        #
        if self.Iu.require_auth(self, cksn=self.UEInfo['CKSN']):
            return self._ret_auth()
        #
        if self.Iu.require_smc(self):
            # if we are here, there was no auth procedure,
            # hence the cksn submitted by the UE is valid
            return self._ret_smc(self.UEInfo['CKSN'], False)
        #
        if self._req_imeisv:
            return self._ret_req_imeisv()
        #
        # otherwise, go directly to postprocess
        return self.postprocess()
    
    def postprocess(self, Proc=None):
        if isinstance(Proc, GMMIdentification):
            if Proc.IDType == NAS.IDTYPE_IMSI:
                # got the UE's IMSI, check if it's allowed
                if self.UE.IMSI is None:
                    # UE did actually not responded with its IMSI, this is bad !
                    # error 96: invalid mandatory info
                    self.errcause = 96
                    return self.output()
                elif not self._chk_imsi():
                    return self.output()
                elif self.Iu.require_auth(self):
                    return self._ret_auth()
                elif self.Iu.require_smc(self):
                    # if we are here, there was no auth procedure,
                    # hence the cksn submitted by the UE is valid
                    return self._ret_smc(self.UEInfo['CKSN'], False)
                elif self._req_imeisv:
                    return self._ret_req_imeisv()
            elif Proc.IDType == NAS.IDTYPE_IMEISV:
                # got the UE's IMEISV, check if it is allowed
                if self.UE.IMEISV is None or \
                not self.UE.Server.is_imeisv_allowed(self.UE.IMEISV):
                    self.errcause = self.GMM.IDENT_IMEI_NOT_ALLOWED
                    return self.output()
        #
        elif isinstance(Proc, GMMAuthenticationCiphering):
            if self.Iu.require_smc(self):
                # if we are here, the valid cksn is the one established during
                # the auth procedure
                return self._ret_smc(Proc.cksn, True)
            elif self._req_imeisv:
                return self._ret_req_imeisv()
        #
        elif isinstance(Proc, RANAPSecurityModeControl):
            if not Proc.success:
                self.abort()
                return []
            # self.Iu.SEC['CKSN'] has been taken into use at the RRC layer
            elif self._req_imeisv:
                return self._ret_req_imeisv()
        #
        elif Proc == self:
            # something bad happened with one of the GMM common procedure
            pass
        #
        elif Proc is not None:
            self._err = Proc
            assert()
        #
        return self.output()
    
    def output(self):
        if self.att_type == 3 and self.GMM.ATT_IMSI:
            # IMSI attach not supported
            self.errcause = self.GMM.ATT_IMSI
        #
        if self.errcause:
            # prepare AttachReject IE
            if self.errcause == self.GMM.ATT_IMSI_PROV_REJECT:
                self.set_msg(8, 4, GMMCause=self.errcause, T3346=self.GMM.ATT_T3346)
            else:
                self.set_msg(8, 4, GMMCause=self.errcause)
            self.encode_msg(8, 4)
            self.ptmsi_realloc = -1
            self._log('INF', 'reject, %r' % self._nas_tx['GMMCause'])
        else:
            # prepare AttachAccept IEs
            IEs = {'ForceStdby'            : {'Value': self.GMM.ATT_FSTDBY},
                   'AttachResult'          : {'FollowOnProc': self.UEInfo['AttachType']['FollowOnReq'].get_val(),
                                              'Result': self.att_type},
                   'PeriodicRAUpdateTimer' : self.GMM.ATT_RAU_TIMER,
                   'RadioPrioForTOM8'      : {'Value': self.GMM.ATT_PRIO_TOM8},
                   'RadioPrioForSMS'       : {'Value': self.GMM.ATT_PRIO_SMS},
                   'RAI'                   : {'PLMN': self.UE.PLMN, 'LAC': self.UE.LAC, 'RAC': self.UE.RAC}
                   }
            #
            # READY timer negotiation
            if 'ReqREADYTimer' in self.UEInfo:
                if self.GMM.ATT_READY_TIMER is None:
                    IEs['NegoREADYTimer'] = self.UEInfo['ReqREADYTimer']
                else:
                    IEs['NegoREADYTimer'] = self.GMM.ATT_READY_TIMER
            # in case we want to realloc a PTMSI, we start a PTMSIRealloc,
            # but don't forward its output
            if self.GMM.ATT_PTMSI_REALLOC:
                NasProc = self.GMM.init_proc(GMMPTMSIReallocation)
                NasProc.output(embedded=True)
                IEs['AllocPTMSI'] = {'type': NAS.IDTYPE_TMSI, 'ident': NasProc.ptmsi}
                self.ptmsi_realloc = NasProc.ptmsi
            else:
                self.ptmsi_realloc = -1
            #
            if self.GMM.ATT_T3302 is not None:
                IEs['T3302'] = self.GMM.ATT_T3302
            if self.Iu.Config['EquivPLMNList'] is not None:
                IEs['EquivPLMNList'] = self.Iu.Config['EquivPLMNList']
            if self.GMM.ATT_NETFEAT_SUPP is not None:
                IEs['NetFeatSupp'] = self.GMM.ATT_NETFEAT_SUPP
            #
            if isinstance(self.Iu.Config['EmergNumList'], bytes_types):
                IEs['EmergNumList'] = self.Iu.Config['EmergNumList']
            elif self.Iu.Config['EmergNumList'] is not None:
                IEs['EmergNumList'] = [{'ServiceCat': uint_to_bitlist(cat), 'Num': num} for \
                                       (cat, num) in self.Iu.Config['EmergNumList']]
            #
            if self.GMM.ATT_MSINF_REQ is not None:
                IE['ReqMSInfo'] = self.GMM.ATT_MSINF_REQ
            if self.GMM.ATT_T3312_EXT is not None:
                IEs['T3312Ext'] = self.GMM.ATT_T3312_EXT
            if self.GMM.ATT_ADDNETFEAT_SUPP is not None:
                IEs['AddNetFeatSupp'] = self.GMM.ATT_ADDNETFEAT_SUPP
            #
            if 'ExtDRXParam' in self.UEInfo:
                if self.GMM.ATT_EXTDRX is None:
                    IEs['ExtDRXParam'] = self.UEInfo['ExtDRXParam']
                else:
                    IEs['ExtDRXParam'] = self.GMM.ATT_EXTDRX
            #
            # encode the msg with all its IEs
            self.set_msg(8, 2, **IEs)
            self.encode_msg(8, 2)
        #
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'DL', self._nas_tx) )
        ret = self.Iu.ret_ranap_dt(self._nas_tx)
        if self.ptmsi_realloc < 0:
            ret.extend( self._end() )
        else:
            # use the timer of the GMMPTMSIRealloc
            # and wait for a GMMAttachComplete to end the procedure
            self.Timer = NasProc.Timer
            self.init_timer()
        # send Attach reject / accept
        return ret
    
    def _end(self):
        ret = []
        if self.GMM.ATT_IUREL and \
        (self.errcause or not self.UEInfo['AttachType']['FollowOnReq'].get_val()):
            # trigger an IuRelease with Cause NAS normal-release (83)
            RanapProcRel = self.Iu.init_ranap_proc(RANAPIuRelease, Cause=('nAS', 83))
            if RanapProcRel:
                ret.append(RanapProcRel)
        self.rm_from_gmm_stack()
        return ret


class GMMDetachUE(GMMSigProc):
    """MS-initiated GPRS detach: TS 24.008, section 4.7.4.1
    
    UE-initiated
    
    CN message:
        GMMDetachAcceptMO (PD 8, Type 6), IEs:
        - Type1V    : spare
        - Type1V    : ForceStdby
    
    UE message:
        GMMDetachRequestMO (PD 8, Type 5), IEs:
        - Type1V    : spare
        - Type1V    : DetachTypeMO
        - Type4TLV  : AllocPTMSI (T: 24)
        - Type4TLV  : PTMSISign (T: 25)
    """
    
    Cont = (
        (TS24008_GMM.GMMDetachAcceptMO, ),
        (TS24008_GMM.GMMDetachRequestMO, )
        )
    
    def _detach(self):
        # set GMM state
        self.GMM.state = 'INACTIVE'
        self._log('INF', 'detaching')
        #
        # we only consider GPRS detach here
        self.rm_from_gmm_stack()
        # abort all ongoing PS procedures
        self.Iu.clear_nas_proc()
    
    def process(self, pdu):
        # preempt the GMM stack
        self.gmm_preempt()
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'UL', pdu) )
        self.UEInfo = {}
        self.decode_msg(pdu, self.UEInfo)
        if self.UEInfo['DetachTypeMO']['PowerOff'].get_val():
            # if UE is to power-off, procedure ends here
            ret = self.output(poff=True)
        else:
            ret = self.output()
        self._detach()
        return ret
    
    def output(self, poff=False):
        # prepare a stack of RANAP procedure(s)
        if not poff:
            # set a RANAP direct transfer to transport the DetachAccept
            self.set_msg(8, 6, ForceStdby={'Value': self.GMM.DET_FSTDBY})
            self.encode_msg(8, 6)
            if self.TRACK_PDU:
                self._pdu.append( (time(), 'DL', self._nas_tx) )
            RanapTxProc = self.Iu.ret_ranap_dt(self._nas_tx)
        # set an Iu release with Cause NAS normal-release (83)
        RanapProcRel = self.Iu.init_ranap_proc(RANAPIuRelease, Cause=('nAS', 83))
        if RanapProcRel:
            RanapTxProc.append( RanapProcRel )
        return RanapTxProc


class GMMDetachCN(GMMSigProc):
    """Network-initiated GPRS detach: TS 24.008, section 4.7.4.2
    
    CN-initiated
    
    CN message:
        GMMDetachRequestMT (PD 8, Type 5), IEs:
        - Type1V    : ForceStdby
        - Type1V    : DetachTypeMT
        - Type3TV   : GMMCause (T: 37)
    
    UE message:
        GMMDetachAcceptMT (PD 8, Type 6), IEs:
          None
    """
    
    Cont = (
        (TS24008_GMM.GMMDetachRequestMT, ),
        (TS24008_GMM.GMMDetachAcceptMT, )
        )
    
    Timer = 'T3322'
    
    def output(self):
        self.encode_msg(8, 5)
        # log the NAS msg
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'DL', self._nas_tx) )
        #
        self._log('INF', 'request type %r' % self._nas_tx['DetachTypeMT']['Type'])
        self.init_timer()
        # send it over RANAP
        return self.Iu.ret_ranap_dt(self._nas_tx)
    
    def process(self, pdu):
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'UL', pdu) )
        self.UEInfo = {}
        #
        self._log('INF', 'accepted')
        self.rm_from_gmm_stack()
        return []


class GMMRoutingAreaUpdating(GMMSigProc):
    """Routing area updating: TS 24.008, section 4.7.5
    
    UE-initiated
    
    CN-messages:
        GMMRoutingAreaUpdateAccept (PD 8, Type 9), IEs:
        - Type1V    : ForceStdby
        - Type1V    : UpdateResult
        - Type2     : PeriodicRAUpdateTimer
        - Type3V    : RAI
        - Type3TV   : PTMSISign (T: 25)
        - Type4TLV  : AllocPTMSI (T: 24)
        - Type4TLV  : MSIdent (T: 35)
        - Type4TLV  : RcvNPDUNumList (T: 38)
        - Type3TV   : NegoREADYTimer (T: 23)
        - Type3TV   : GMMCause (T: 37)
        - Type4TLV  : T3302 (T: 42)
        - Type2     : CellNotif (T: 140)
        - Type4TLV  : EquivPLMNList (T: 74)
        - Type4TLV  : PDPCtxtStat (T: 50)
        - Type1TV   : NetFeatSupp (T: 10)
        - Type4TLV  : EmergNumList (T: 52)
        - Type4TLV  : MBMSCtxtStat (T: 53)
        - Type1TV   : ReqMSInfo (T: 10)
        - Type4TLV  : T3319 (T: 55)
        - Type4TLV  : T3323 (T: 56)
        - Type4TLV  : T3312Ext (T: 57)
        - Type4TLV  : AddNetFeatSupp (T: 102)
        - Type4TLV  : T3324 (T: 106)
        - Type4TLV  : ExtDRXParam (T: 110)
        - Type1TV   : UPIntegrityInd (T: 12)
        - Type4TLV  : ReplayedMSNetCap (T: 49)
        - Type4TLV  : ReplayedMSRACap (T: 51)
        
        GMMRoutingAreaUpdateReject (PD 8, Type 11), IEs:
        - Type2     : GMMCause
        - Type1V    : spare
        - Type1V    : ForceStdby
        - Type4TLV  : T3302 (T: 42)
        - Type4TLV  : T3346 (T: 58)
    
    UE messages:
        GMMRoutingAreaUpdateRequest (PD 8, Type 8), IEs:
        - Type1V    : CKSN
        - Type1V    : UpdateType
        - Type3V    : OldRAI
        - Type4LV   : MSRACap
        - Type3TV   : OldPTMSISign (T: 25)
        - Type3TV   : ReqREADYTimer (T: 23)
        - Type3TV   : DRXParam (T: 39)
        - Type1TV   : TMSIStatus (T: 9)
        - Type4TLV  : PTMSI (T: 24)
        - Type4TLV  : MSNetCap (T: 49)
        - Type4TLV  : PDPCtxtStat (T: 50)
        - Type4TLV  : PSLCSCap (T: 51)
        - Type4TLV  : MBMSCtxtStat (T: 53)
        - Type4TLV  : UENetCap (T: 88)
        - Type4TLV  : AddID (T: 26)
        - Type4TLV  : AddRAI (T: 27)
        - Type4TLV  : MSCm2 (T: 17)
        - Type4TLV  : MSCm3 (T: 32)
        - Type4TLV  : SuppCodecs (T: 64)
        - Type4TLV  : VoiceDomPref (T: 93)
        - Type1TV   : PTMSIType (T: 14)
        - Type1TV   : DeviceProp (T: 13)
        - Type1TV   : MSNetFeatSupp (T: 12)
        - Type4TLV  : OldLAI (T: 20)
        - Type1TV   : AddUpdateType (T: 15)
        - Type4TLV  : TMSIBasedNRICont (T: 16)
        - Type4TLV  : T3324 (T: 106)
        - Type4TLV  : T3312Ext (T: 57)
        - Type4TLV  : ExtDRXParam (T: 110)
        
        GMMRoutingAreaUpdateComplete (PD 8, Type 10), IEs:
        - Type4TLV  : RcvNPDUNumList (T: 38)
        - Type4TLV  : InterRATHOInfo (T: 39)
        - Type4TLV  : EUTRANInterRATHOInfo (T: 43)
    """
    
    Cont = (
        (TS24008_GMM.GMMRoutingAreaUpdateAccept, TS24008_GMM.GMMRoutingAreaUpdateReject),
        (TS24008_GMM.GMMRoutingAreaUpdateRequest, TS24008_GMM.GMMRoutingAreaUpdateComplete)
        )
    
    Cap = ('MSRACap', 'DRXParam', 'MSNetCap', 'PSLCSCap', 'UENetCap', 'MSCm2', 
           'MSCm3', 'SuppCodecs', 'VoiceDomPref', 'DeviceProp', 'MSNetFeatSupp',
           'ExtDRXParam') 
    
    Decod = {
        (8, 8) : {
            'CKSN'          : lambda x: x.get_val(),
            'OldRAI'        : lambda x: (x['PLMN'].decode(), x['LAC'].get_val(), x['RAC'].get_val()),
            'ReqREADYTimer' : lambda x: {'Unit': x[1]['Unit'].get_val(), 'Value': x[1]['Value'].get_val()},
            }
        }
    
    def process(self, pdu):
        # preempt the GMM stack
        self.gmm_preempt()
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'UL', pdu) )
        #
        if pdu['Type'].get_val() == 8:
            # RoutingAreaUpdateRequest
            self.errcause, self.UEInfo = None, {}
            self.decode_msg(pdu, self.UEInfo)
            return self._process_req()
        else:
            # RoutingAreaUpdateComplete
            self.errcause, self.CompInfo = None, {}
            self.decode_msg(pdu, self.CompInfo)
            if self.ptmsi_realloc >= 0:
                self.UE.set_ptmsi(self.ptmsi_realloc)
                self._log('INF', 'new P-TMSI set, 0x%.8x' % self.ptmsi_realloc)
            return self._end()
    
    def _process_req(self):
        #
        if 'PTMSI' in self.UEInfo and \
        self.UEInfo['PTMSI'][0] == NAS.IDTYPE_TMSI and self.UE.PTMSI is None:
            self.UE.PTMSI = self.UEInfo['PTMSI'][1]
        #
        rau_type = self.UEInfo['UpdateType']['Value']
        self._log('INF', 'request type %i (%s) from, old RAI %s.%.4x.%.2x'\
                  % (rau_type(), rau_type._dic[rau_type()],
                     self.UEInfo['OldRAI'][0], self.UEInfo['OldRAI'][1], self.UEInfo['OldRAI'][2]))
        # collect capabilities
        self._collect_cap()
        #
        # check local ID
        if self.UE.IMSI is None:
            # UEd was created based on a PTMSI provided at the RRC layer
            # -> we need to get its IMSI before continuing
            # we remove it from the Server's provisory dict of UE
            try:
                del self.UE.Server._UEpre[self.UE.PTMSI]
            except:
                pass
            # need to request the IMSI, prepare an id request procedure
            return self._ret_req_imsi()
        #
        if self.Iu.require_auth(self, cksn=self.UEInfo['CKSN']):
            return self._ret_auth()
        #
        if self.Iu.require_smc(self):
            # if we are here, there was no auth procedure,
            # hence the cksn submitted by the UE is valid
            return self._ret_smc(self.UEInfo['CKSN'], False)
        #
        # otherwise, go directly to postprocess
        return self.postprocess()
    
    def postprocess(self, Proc=None):
        if isinstance(Proc, GMMIdentification):
            # got the UE's IMSI, check if it's allowed
            if self.UE.IMSI is None:
                # UE did actually not responded with its IMSI, this is bad !
                # error 96: invalid mandatory info
                self.errcause = 96
                return self.output()
            elif not self._chk_imsi():
                return self.output()
            elif self.Iu.require_auth(self):
                return self._ret_auth()
            elif self.Iu.require_smc(self):
                # if we are here, there was no auth procedure,
                # hence the cksn submitted by the UE is valid
                return self._ret_smc(self.UEInfo['CKSN'], False)
        #
        if isinstance(Proc, GMMAuthenticationCiphering):
            if self.Iu.require_smc(self):
                # if we are here, the valid cksn is the one established during
                # the auth procedure
                return self._ret_smc(Proc.cksn, True)
        #
        elif isinstance(Proc, RANAPSecurityModeControl):
            if not Proc.success:
                self.abort()
                return []
            # self.Iu.SEC['CKSN'] has been taken into use at the RRC layer
        #
        elif Proc == self:
            # something bad happened with one of the GMM common procedure
            pass
        #
        elif Proc is not None:
            self._err = Proc
            assert()
        #
        return self.output()
    
    def output(self):
        if self.errcause:
            # prepare RAU Reject IE
            if self.errcause == self.GMM.ATT_IMSI_PROV_REJECT:
                self.set_msg(8, 11, GMMCause=self.errcause, T3346=self.GMM.ATT_T3346)
            else:
                self.set_msg(8, 11, GMMCause=self.errcause)
            self.encode_msg(8, 11)
            self.ptmsi_realloc = -1
            self._log('INF', 'reject, %r' % self._nas_tx['GMMCause'])
        else:
            # prepare RAUAccept IEs
            IEs = {'ForceStdby'            : {'Value': self.GMM.RAU_FSTDBY},
                   'UpdateResult'          : {'FollowOnProc': self.UEInfo['UpdateType']['FollowOnReq'].get_val(),
                                              'Value': self.UEInfo['UpdateType']['Value'].get_val()},
                   'PeriodicRAUpdateTimer' : self.GMM.RAU_RAU_TIMER,
                   'RAI'                   : {'PLMN': self.UE.PLMN, 'LAC': self.UE.LAC, 'RAC': self.UE.RAC}
                   }
            #
            # in case we want to realloc a PTMSI, we start a PTMSIRealloc,
            # but don't forward its output
            if self.GMM.RAU_PTMSI_REALLOC:
                NasProc = self.GMM.init_proc(GMMPTMSIReallocation)
                void = NasProc.output(embedded=True)
                IEs['AllocPTMSI'] = {'type': NAS.IDTYPE_TMSI, 'ident': NasProc.ptmsi}
                self.ptmsi_realloc = NasProc.ptmsi
            else:
                self.ptmsi_realloc = -1
            # READY timer negotiation
            if 'ReqREADYTimer' in self.UEInfo:
                if self.GMM.RAU_READY_TIMER is None:
                    IEs['NegoREADYTimer'] = self.UEInfo['ReqREADYTimer']
                else:
                    IEs['NegoREADYTimer'] = self.GMM.RAU_READY_TIMER
            #
            if self.GMM.RAU_T3302 is not None:
                IEs['T3302'] = self.GMM.RAU_T3302
            if self.Iu.Config['EquivPLMNList'] is not None:
                IEs['EquivPLMNList'] = self.Iu.Config['EquivPLMNList']
            if self.GMM.RAU_NETFEAT_SUPP is not None:
                IEs['NetFeatSupp'] = self.GMM.RAU_NETFEAT_SUPP
            #
            if isinstance(self.Iu.Config['EmergNumList'], bytes_types):
                IEs['EmergNumList'] = self.Iu.Config['EmergNumList']
            elif self.Iu.Config['EmergNumList'] is not None:
                IEs['EmergNumList'] = [{'ServiceCat': uint_to_bitlist(cat), 'Num': num} for \
                                       (cat, num) in self.Iu.Config['EmergNumList']]
            #
            if self.GMM.RAU_MSINF_REQ is not None:
                IE['ReqMSInfo'] = self.GMM.RAU_MSINF_REQ
            if self.GMM.RAU_T3312_EXT is not None:
                IEs['T3312Ext'] = self.GMM.RAU_T3312_EXT
            if self.GMM.RAU_ADDNETFEAT_SUPP is not None:
                IEs['AddNetFeatSupp'] = self.GMM.RAU_ADDNETFEAT_SUPP
            #
            if 'ExtDRXParam' in self.UEInfo:
                if self.GMM.RAU_EXTDRX is None:
                    IEs['ExtDRXParam'] = self.UEInfo['ExtDRXParam']
                else:
                    IEs['ExtDRXParam'] = self.GMM.RAU_EXTDRX
            #
            # encode the msg with all its IEs
            self.set_msg(8, 9, **IEs)
            self.encode_msg(8, 9)
        #
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'DL', self._nas_tx) )
        ret = self.Iu.ret_ranap_dt(self._nas_tx)
        if self.ptmsi_realloc < 0:
            ret.extend( self._end() )
        else:
            # use the timer of the GMMPTMSIRealloc
            # and wait for a GMMAttachComplete to end the procedure
            self.Timer = NasProc.Timer
            self.init_timer()
        # send Attach reject / accept
        return ret
    
    def _end(self):
        ret = []
        if self.GMM.RAU_IUREL and \
        (self.errcause or not self.UEInfo['UpdateType']['FollowOnReq'].get_val()):
            # trigger an IuRelease with Cause NAS normal-release (83)
            RanapProcRel = self.Iu.init_ranap_proc(RANAPIuRelease, Cause=('nAS', 83))
            if RanapProcRel:
                ret.append(RanapProcRel)
        self.rm_from_gmm_stack()
        return ret


class GMMPTMSIReallocation(GMMSigProc):
    """P-TMSI reallocation: TS 24.008, section 4.7.6
    
    CN-initiated
    
    CN message:
        GMMPTMSIReallocationCommand (PD 8, Type 16), IEs:
        - Type4LV   : AllocPTMSI
        - Type3V    : RAI
        - Type1V    : spare
        - Type1V    : ForceStdby
        - Type3TV   : PTMSISign (T: 25)
    
    UE message:
        GMMPTMSIReallocationComplete (PD 8, Type 17), IEs:
          None
    """
    
    Cont = (
        (TS24008_GMM.GMMPTMSIReallocationCommand, ),
        (TS24008_GMM.GMMPTMSIReallocationComplete, )
        )
    
    Timer = 'T3350'
    
    def output(self, embedded=False):
        # embedded=True is used to embed this procedure within an Attach or RAU
        # hence the output message is not built, only the .ptmsi is available
        # but the procedure still runs and waits for the UE response 
        # after all
        self.ptmsi = self.UE.get_new_tmsi()
        if not embedded:
            # prepare IEs
            self.set_msg(8, 16, AllocPTMSI={'type': NAS.IDTYPE_TMSI, 'ident': self.ptmsi},
                                RAI       ={'PLMN': self.UE.PLMN, 'LAC': self.UE.LAC, 'RAC': self.UE.RAC},
                                ForceStdby={'Value': self.GMM.REA_FSTDBY})
            self.encode_msg(8, 16)
            # log the NAS msg
            if self.TRACK_PDU:
                self._pdu.append( (time(), 'DL', self._nas_tx) )
            #
            self.init_timer()
            # send it over RANAP
            return self.Iu.ret_ranap_dt(self._nas_tx)
        else:
            # when the P-TMSI realloc is embedded, there is no realloc complete
            # to expect...
            self.rm_from_gmm_stack()
            return []
    
    def process(self, pdu):
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'UL', pdu) )
        self.UEInfo = {}
        self.decode_msg(pdu, self.UEInfo)
        #
        # just take the new ptmsi in use
        self.UE.set_ptmsi(self.ptmsi)
        self._log('INF', 'new P-TMSI set, 0x%.8x' % self.ptmsi)
        self.rm_from_gmm_stack()
        return []


class GMMAuthenticationCiphering(GMMSigProc):
    """Authentication and ciphering: TS 24.008, section 4.7.7
    
    CN-initiated
    
    CN messages:
        GMMAuthenticationCipheringRequest (PD 8, Type 18), IEs:
        - Type1V    : IMEISVReq
        - Type1V    : CiphAlgo
        - Type1V    : ACRef
        - Type1V    : ForceStdby
        - Type3TV   : RAND (T: 33)
        - Type1TV   : CKSN (T: 8)
        - Type4TLV  : AUTN (T: 40)
        - Type4TLV  : ReplayedMSNetCap (T: 49)
        - Type1TV   : IntegAlgo (T: 9)
        - Type4TLV  : MAC (T: 67)
        - Type4TLV  : ReplayedMSRACap (T: 51)
    
        GMMAuthenticationCipheringReject (PD 8, Type 20), IEs:
          None
    
    UE messages:
        GMMAuthenticationCipheringResponse (PD 8, Type 19), IEs:
        - Type1V    : spare
        - Type1V    : ACRef
        - Type3TV   : RES (T: 34)
        - Type4TLV  : IMEISV (T: 35)
        - Type4TLV  : RESExt (T: 41)
        - Type4TLV  : MAC (T: 67)
        
        GMMAuthenticationCipheringFailure (PD 8, Type 28), IEs:
        - Type2     : GMMCause
        - Type4TLV  : AUTS (T: 48)
    """
    
    Cont = (
        (TS24008_GMM.GMMAuthenticationCipheringRequest, TS24008_GMM.GMMAuthenticationCipheringReject),
        (TS24008_GMM.GMMAuthenticationCipheringResponse, TS24008_GMM.GMMAuthenticationCipheringFailure)
        )
    
    Timer = 'T3360'
    
    Decod = {
        (8, 19): {
            'RES'    : lambda x: x['V'].get_val(),
            'IMEISV' : lambda x: x[2].decode(),
            'RESExt' : lambda x: x['V'].get_val()
            },
        (8, 28): {
            'AUTS'   : lambda x: x['V'].get_val()
            }
        }
    
    def output(self):
        # get a new CKSN
        self.cksn = self.Iu.get_new_cksn()
        # in case a RAND is configured as a class encoder, we use it for 
        # generating the auth vector
        if 'RAND' in self.__class__.Encod[(8, 18)]:
            RAND = self.__class__.Encod[(5, 18)]['RAND']
        else:
            RAND = None
        #
        if not self.UE.USIM or self.GMM.AUTH_2G:
            # 2G authentication
            self.ctx = 2
            self.vect = self.UE.Server.AUCd.make_2g_vector(self.UE.IMSI, RAND)
        else:
            # 3G authentication
            self.ctx = 3
            self.vect = self.UE.Server.AUCd.make_3g_vector(self.UE.IMSI, self.GMM.AUTH_AMF, RAND)
        #
        if self.vect is None:
            # IMSI is not in the AuC db
            self._log('ERR', 'unable to get an authentication vector from AuC')
            self.rm_from_gmm_stack()
            return []
        #
        # prepare IEs
        IEs = {'IMEISVReq'  : self.GMM.AUTH_IMEI_REQ,
               'CiphAlgo'   : 0,
               'ACRef'      : 0,
               'ForceStdby' : {'Value': self.GMM.AUTH_FSTDBY},
               'RAND'       : self.vect[0],
               'CKSN'       : self.cksn}
        if self.ctx == 3:
            # msg with AUTN
            autn = self.vect[2]
            if self.GMM.AUTH_AUTN_EXT:
                autn += self.GMM.AUTH_AUTN_EXT
            IEs['AUTN'] = autn
        #
        self.set_msg(8, 18, **IEs)
        self.encode_msg(8, 18)
        # log the NAS msg
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'DL', self._nas_tx) )
        #
        self.init_timer()
        # send it over RANAP
        return self.Iu.ret_ranap_dt(self._nas_tx)
    
    def process(self, pdu):
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'UL', pdu) )
        self.UEInfo = {}
        self.decode_msg(pdu, self.UEInfo)
        #
        if pdu['Type'].get_val() == 19:
            return self._process_resp()
        else:
            return self._process_fail()
    
    def _process_resp(self):
        # check if the whole UE response is corresponding to the expected one
        if self.ctx == 3:
            # 3G auth context
            res = self.UEInfo['RES']
            if 'RESExt' in self.UEInfo:
                res += self.UEInfo['RESExt']
            if res != self.vect[1]:
                # incorrect response from the UE: auth reject
                self._log('WNG', '3G authentication reject, XRES %s, RES %s'\
                          % (hexlify(self.vect[1]).decode('ascii'),
                             hexlify(res).decode('ascii'))) 
                self.encode_msg(8, 20)
                self.success = False
            else:
                self._log('DBG', '3G authentication accepted')
                self.success = True
                # set a 3G security context
                self.Iu.set_sec_ctx(self.cksn, 3, self.vect)
        else:
            # 2G auth context
            if self.UEInfo['RES'] != self.vect[1]:
                # incorrect response from the UE: auth reject
                self._log('WNG', '2G authentication reject, XRES %s, RES %s'\
                          % (hexlify(self.vect[1]).decode('ascii'),
                             hexlify(self.UEInfo['RES']).decode('ascii')))
                self.encode_msg(8, 20)
                self.success = False
            else:
                self._log('DBG', '2G authentication accepted')
                self.success = True
                # set a 2G security context
                self.Iu.set_sec_ctx(self.cksn, 2, self.vect)
        #
        self.rm_from_gmm_stack()
        if not self.success:
            if self.TRACK_PDU:
                self._pdu.append( (time(), 'DL', self._nas_tx) )
            return self.Iu.ret_ranap_dt(self._nas_tx)
        else:
            if 'IMEISV' in self.UEInfo:
                self.UE.set_ident_from_ue(NAS.IDTYPE_IMEISV, self.UEInfo['IMEISV'])
            return []
     
    def _process_fail(self):
        self.success = False
        if self.UEInfo['GMMCause'].get_val() == 21 and 'AUTS' in self.UEInfo:
            # synch failure
            # resynchronize the SQN in case the MM stack is not already doing it
            if self.UE.IuCS is not None and self.UE.IuCS.MM.state == 'ACTIVE' \
            and hasattr(self.UE.IuCS.MM, '_auth_resynch'):
                ret = 0
            else:
                ret = self.UE.Server.AUCd.synch_sqn(self.UE.IMSI, self.vect[0], self.UEInfo['AUTS'])
            #
            if ret is None:
                # something did not work
                self._log('ERR', 'unable to resynchronize SQN in AuC')
                self.encode_msg(8, 20)
                self.rm_from_gmm_stack()
                if self.TRACK_PDU:
                    self._pdu.append( (time(), 'DL', self._nas_tx) )
                return self.Iu.ret_ranap_dt(self._nas_tx)
            #
            elif ret:
                # USIM did not authenticate correctly
                self._log('WNG', 'USIM authentication failed for resynch')
                self.encode_msg(8, 20)
                self.rm_from_gmm_stack()
                if self.TRACK_PDU:
                    self._pdu.append( (time(), 'DL', self._nas_tx) )
                return self.Iu.ret_ranap_dt(self._nas_tx)
            #
            else: 
                # resynch OK: restart an auth procedure
                self._log('INF', 'USIM SQN resynchronization done')
                self.rm_from_gmm_stack()
                # restart a new auth procedure
                NasProc = self.GMM.init_proc(GMMAuthenticationCiphering)
                return NasProc.output()
        #
        else:
            # UE refused our auth request...
            self._log('ERR', 'UE rejected AUTN, %s' % self.UEInfo['Cause'])
            self.rm_from_gmm_stack()
            return []


class GMMIdentification(GMMSigProc):
    """Identification: TS 24.008, section 4.7.8
    
    CN-initiated
    
    CN message:
        GMMIdentityRequest (PD 8, Type 21), IEs:
        - Type1V    : ForceStdby
        - Type1V    : IDType

    UE message:
        GMMIdentityResponse (PD 8, Type 22), IEs:
        - Type4LV   : ID
    """
    
    Cont = (
        (TS24008_GMM.GMMIdentityRequest, ),
        (TS24008_GMM.GMMIdentityResponse, )
        )
    
    Timer = 'T3370'
    
    Decod = {
        (8, 22): {
            'ID': lambda x: x[1].decode(),
            }
        }
    
    def output(self):
        # build the Id Request msg, Id type has to be set by the caller
        self.set_msg(8, 21, ForceStdby={'Value': self.GMM.AUTH_FSTDBY})
        self.encode_msg(8, 21)
        # log the NAS msg
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'DL', self._nas_tx) )
        #
        self.init_timer()
        # send it
        return self.Iu.ret_ranap_dt(self._nas_tx)
    
    def process(self, pdu):
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'UL', pdu) )
        self.UEInfo = {}
        self.decode_msg(pdu, self.UEInfo)
        # get the identity IE value
        self.IDType = self._nas_tx['IDType'].get_val()
        #
        if self.UEInfo['ID'][0] != self.IDType :
            self._log('WNG', 'identity responded not corresponding to type requested '\
                      '(%i instead of %i)' % (self.UEInfo['ID'][0], self.IDType))
        self._log('INF', 'identity responded, %r' % self._nas_rx['ID'][1])
        self.UE.set_ident_from_ue(*self.UEInfo['ID'], dom='PS')
        #
        self.rm_from_gmm_stack()
        return []


class GMMInformation(GMMSigProc):
    """GMM information: TS 24.008, section 4.7.12
    
    CN-initiated
    
    CN message:
        GMMInformation (PD 8, Type 33), IEs:
        - Type4TLV  : NetFullName (T: 67)
        - Type4TLV  : NetShortName (T: 69)
        - Type3TV   : LocalTimeZone (T: 70)
        - Type3TV   : UnivTimeAndTimeZone (T: 71)
        - Type4TLV  : LSAIdentity (T: 72)
        - Type4TLV  : NetDLSavingTime (T: 73)

    UE message:
        None
    """
    
    Cont = (
        (TS24008_GMM.GMMInformation, ),
        None
        )
    
    def output(self):
        # build the Information msg, network name and/or time info
        # have to be set by the caller
        self.encode_msg(8, 33)
        # log the NAS msg
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'DL', self._nas_tx) )
        #
        self._log('INF', '%r' % self.Encod[(8, 33)])
        self.rm_from_gmm_stack()
        # send it
        return self.Iu.ret_ranap_dt(self._nas_tx)


class GMMServiceRequest(GMMSigProc):
    """Service request: TS 24.008, section 4.7.13
    
    UE-initiated
    
    CN messages:
        GMMServiceAccept (PD 8, Type 13), IEs:
        - Type4TLV  : PDPCtxtStat (T: 50)
        - Type4TLV  : MBMSCtxtStat (T: 53)
    
        GMMServiceReject (PD 8, Type 14), IEs:
        - Type2     : GMMCause
        - Type4TLV  : T3346 (T: 58)
    
    UE message:
        GMMServiceRequest (PD 8, Type 12), IEs:
        - Type1V    : ServiceType
        - Type1V    : CKSN
        - Type4LV   : PTMSI
        - Type4TLV  : PDPCtxtStat (T: 50)
        - Type4TLV  : MBMSCtxtStat (T: 53)
        - Type4TLV  : ULDataStat (T: 54)
        - Type1TV   : DeviceProp (T: 13)
    """
    
    Cont = (
        (TS24008_GMM.GMMServiceAccept, TS24008_GMM.GMMServiceReject),
        (TS24008_GMM.GMMServiceRequest, )
        )
    
    Decod = {
        (8, 12): {
            'CKSN'        : lambda x: x.get_val(),
            'PTMSI'       : lambda x: x[1].decode(),
            'PDPCtxtStat' : lambda x: {c: x[2]['NSAPI_%i' % c] for c in range(0, 16)},
            'MBMSCtxtStat': lambda x: {c: x[2]['NSAPI_%i' % c] for c in range(0, 16)},
            'ULDataStat'  : lambda x: x[2]
            }
        }
    
    def process(self, pdu):
        # preempt the GMM stack
        self.gmm_preempt()
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'UL', pdu) )
        self.errcause, self.UEInfo = None, {}
        self.decode_msg(pdu, self.UEInfo)
        #
        if self.Iu.require_auth(self, cksn=self.UEInfo['CKSN']):
            return self._ret_auth()
        #
        if self.Iu.require_smc(self):
            # if we are here, there was no auth procedure,
            # hence the cksn submitted by the UE is valid
            return self._ret_smc(self.UEInfo['CKSN'], False)
        #
        return self.postprocess()
    
    def postprocess(self, Proc=None):
        if isinstance(Proc, GMMAuthenticationCiphering):
            if self.Iu.require_smc(self):
                # if we are here, the valid cksn is the one established during
                # the auth procedure
                return self._ret_smc(Proc.cksn, True)
        elif isinstance(Proc, RANAPSecurityModeControl):
            if not Proc.success:
                self.abort()
                return []
            # self.Iu.SEC['CKSN'] has been taken into use at the RRC layer
        elif Proc == self:
            # something bad happened with one of the GMM common procedure
            pass
        elif Proc is not None:
            self._err = Proc
            assert()
        #
        # TODO: check / activate PDP and MBMS contexts
        # ...
        #
        return self.output()
    
    def output(self):
        self._log('INF', 'accepted')
        self.set_msg(8, 13)
        self.encode_msg(8, 13)
        # log the NAS msg
        if self.TRACK_PDU:
            self._pdu.append( (time(), 'DL', self._nas_tx) )
        self.rm_from_gmm_stack()
        return self.Iu.ret_ranap_dt(self._nas_tx)


# filter_init=1, indicates we are the core network side
GMMAttach.init(filter_init=1)
GMMDetachUE.init(filter_init=1)
GMMDetachCN.init(filter_init=1)
GMMRoutingAreaUpdating.init(filter_init=1)
GMMPTMSIReallocation.init(filter_init=1)
GMMAuthenticationCiphering.init(filter_init=1)
GMMIdentification.init(filter_init=1)
GMMInformation.init(filter_init=1)
GMMServiceRequest.init(filter_init=1)

# GMM UE-initiated procedures dispatcher
GMMProcUeDispatcher = {
    1 : GMMAttach,
    5 : GMMDetachUE,
    8 : GMMRoutingAreaUpdating,
    12: GMMServiceRequest
    }
GMMProcUeDispatcherStr = {ProcClass.Cont[1][0]()._name: ProcClass \
                          for ProcClass in GMMProcUeDispatcher.values()}

# GMM CN-initiated procedures dispatcher
GMMProcCnDispatcher = {
    5 : GMMDetachCN,
    16: GMMPTMSIReallocation,
    18: GMMAuthenticationCiphering,
    21: GMMIdentification,
    33: GMMInformation,
    }
GMMProcCnDispatcherStr = {ProcClass.Cont[0][0]()._name: ProcClass \
                          for ProcClass in GMMProcCnDispatcher.values()}

