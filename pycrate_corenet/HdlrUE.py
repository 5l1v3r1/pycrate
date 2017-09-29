# -*- coding: UTF-8 -*-
#/**
# * Software Name : pycrate
# * Version : 0.1
# *
# * Copyright © 2017. Benoit Michau. ANSSI.
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
# * File Name : pycrate_corenet/HdlrUE.py
# * Created : 2017-06-28
# * Authors : Benoit Michau 
# *--------------------------------------------------------
#*/

from .utils      import *
from .HdlrUEIuCS import *
from .HdlrUEIuPS import *
from .HdlrUES1   import *


class UEd(SigStack):
    """UE handler within a CorenetServer instance
    responsible for UE-related RAN signaling and NAS signaling
    """
    
    #--------------------------------------------------------------------------#
    # debug and tracing level
    #--------------------------------------------------------------------------#
    #
    # verbosity level
    DEBUG              = ('ERR', 'WNG', 'INF', 'DBG')
    # to log UE-related RANAP and S1AP for all UE
    TRACE_ASN_RANAP_CS = False
    TRACE_ASN_RANAP_PS = False
    TRACE_ASN_S1AP     = False
    # to log UE NAS MM / CC / SMS for all UE
    TRACE_NAS_CS       = False
    # to log UE NAS GMM / SM for all UE
    TRACE_NAS_PS       = False
    # to log UE NAS encrypted EMM / EMM / ESM for all UE
    TRACE_NAS_EMMENC   = False
    TRACE_NAS_EPS      = False
    
    #--------------------------------------------------------------------------#
    # UE global informations
    #--------------------------------------------------------------------------#
    #
    # fixed identities
    IMSI   = None
    IMEI   = None
    IMEISV = None
    # capabilities
    Cap    = {}
    # temporary identities (TMSI / PTMSI are uint32)
    TMSI   = None
    PTMSI  = None
    MTMSI  = None
    
    #--------------------------------------------------------------------------#
    # CorenetServer reference
    #--------------------------------------------------------------------------#
    #
    Server = None
    
    #--------------------------------------------------------------------------#
    # RAN-related infos
    #--------------------------------------------------------------------------#
    # 
    # Radio Access Technology (str)
    RAT = None
    # specific Iu / S1 signaling handler
    IuCS = None
    IuPS = None
    S1   = None
    #
    # location parameters
    PLMN = None # string of digits
    LAC  = None # uint16
    RAC  = None # uint8
    SAC  = None # uintX
    TAC  = None # uintX
    
    def _log(self, logtype, msg):
        if logtype[:3] == 'TRA':
            hdr, msg = msg.split('\n', 1)
            log('[TRA] [UE: %s] %s[%s]\n%s%s%s'\
                % (self.IMSI, hdr, logtype[6:], TRACE_COLOR_START, msg, TRACE_COLOR_END))
        elif logtype in self.DEBUG:
            log('[%s] [UE: %s] %s' % (logtype, self.IMSI, msg))
    
    def __init__(self, server, imsi, **kw):
        self.Server = server
        if imsi:
            self.IMSI = imsi
        elif 'tmsi' in kw:
            self.TMSI = kw['tmsi']
        elif 'ptmsi' in kw:
            self.PTMSI = kw['ptmsi']
        #
        if 'config' in kw:
            self.set_config(kw['config'])
    
    def set_config(self, config):
        self.MSISDN = config['MSISDN']
        self.IPAddr = config['IPAddr']
        self.USIM   = config['USIM']
    
    def set_ran(self, ran, ctx_id):
        #
        if ran.__class__.__name__[:3] == 'HNB':
            #
            if self.S1 is not None and self.S1.ENB is not None:
                # error: already linked with another ran
                raise(CorenetErr('UE already connected through a S1 link'))
            #
            # IuCS stack
            if self.IuCS is None:
                # create a handler
                self.IuCS = UEIuCSd(self, ran, ctx_id)
            elif self.IuCS.RNC is None:
                self.IuCS.set_ran(ran)
                self.IuCS.set_ctx(ctx_id)
            elif self.IuCS.RNC == ran:
                self.IuCS.set_ctx(ctx_id)
            else:
                # error: already linked with another HNB
                raise(CorenetErr('UE already connected through another IuCS link'))
            # IuPS stack
            if self.IuPS is None:
                # create a handler
                self.IuPS = UEIuPSd(self, ran, ctx_id)
            elif self.IuPS.RNC is None:
                self.IuPS.set_ran(ran)
                self.IuPS.set_ctx(ctx_id)
            elif self.IuPS.RNC == ran:
                self.IuPS.set_ctx(ctx_id)
            else:
                # error: already linked with another HNB
                raise(CorenetErr('UE already connected through another IuPS link'))
        #
        elif ran.__class__.__name__[:3] == 'ENB':
            #
            if self.IuCS is not None and self.IuCS.RNC is not None or \
            self.IuPS is not None and self.IuPS.RNC is not None:
                # error: already linked with another ran
                raise(CorenetErr('UE already connected through an Iu link'))
            #
            # S1 stack
            if self.S1 is None:
                self.S1 = UES1d(self, ran, ctx_id)
            elif self.S1.ENB is None:
                self.S1.set_ran(ran)
                self.S1.set_ctx(ctx_id)
            elif self.S1.ENB == ran:
                self.S1.set_ctx(ctx_id)
            else:
                # error: already linked with another ENB
                raise(CorenetErr('UE already connected through another S1 link'))
        #
        else:
            assert()
        #
        self.RAT = ran.RAT
    
    def unset_ran(self):
        if self.IuCS is not None and self.IuCS.RNC is not None:
            self.IuCS.unset_ran()
            self.IuCS.unset_ctx()
        if self.IuPS is not None and self.IuPS.RNC is not None:
            self.IuPS.unset_ran()
            self.IuPS.unset_ctx()
        if self.S1 is not None and self.S1.ENB is not None:
            self.S1.unset_ran()
            self.S1.unset_ctx()
        del self.RAT
    
    def merge_cs_handler(self, iucs):
        if self.IuCS is not None and self.IuCS.MM.state != UEMMd.state:
            return False
        else:
            self.IuCS   = iucs
            iucs.UE     = self
            iucs.MM.UE  = self
            iucs.CC.UE  = self
            iucs.SMS.UE = self
            return True
    
    def merge_ps_handler(self, iups):
        if self.IuPS is not None and self.IuPS.GMM.state != UEGMMd.state:
            print('iups: ', iups, iups.GMM, iups.GMM.state)
            print('self.IuPS: ', self.IuPS, self.IuPS.GMM, self.IuPS.GMM.state)
            return False
        else:
            self.IuPS   = iups
            iups.UE     = self
            iups.GMM.UE = self
            iups.SM.UE  = self
            return True
    
    #--------------------------------------------------------------------------#
    # UE identity
    #--------------------------------------------------------------------------#
    
    def set_ident_from_ue(self, idtype, ident):
        # to be used only to set identities reported by the UE
        if idtype == 1:
            if self.IMSI is None:
                self.IMSI = ident
            elif ident != self.IMSI:
                self._log('WNG', 'incorrect IMSI, %s instead of %s' % (ident, self.IMSI))
        elif idtype == 2:
            if self.IMEI is None:
                self.IMEI = ident
            elif ident != self.IMEI:
                self._log('WNG', 'IMEI changed, new %s, old %s' % (ident, self.IMEI))
                self.IMEI = ident
        elif idtype == 3:
            if self.IMEISV is None:
                self.IMEISV = ident
            elif ident != self.IMEISV:
                self._log('WNG', 'IMEISV changed, new %s, old %s' % (ident, self.IMEISV))
                self.IMEISV = ident
        elif idtype == 4:
            if self.TMSI is None:
                self.TMSI = ident
            elif ident != self.TMSI:
                self._log('WNG', 'incorrect TMSI, %s instead of %s' % (ident, self.TMSI))
        else:
            self._log('INF', 'unhandled identity, type %i, ident %s' % (idtype, ident))
    
    def get_new_tmsi(self):
        # use the Python random generator
        return random.getrandbits(32)
    
    def set_tmsi(self, tmsi):
        # delete current TMSI from the Server LUT
        if self.TMSI is not None:
            try:
                del self.Server.TMSI[self.TMSI]
            except:
                pass
        # set the new TMSI
        self.TMSI = tmsi
        # update the Server LUT
        self.Server.TMSI[tmsi] = self.IMSI
    
    def set_ptmsi(self, ptmsi):
        # delete current PTMSI from the Server LUT
        if self.PTMSI is not None:
            try:
                del self.Server.PTMSI[self.PTMSI]
            except:
                pass
        # set the new PTMSI
        self.PTMSI = ptmsi
        # update the Server LUT
        self.Server.PTMSI[ptmsi] = self.IMSI
    
    def set_mtmsi(self, mtmsi):
        # delete current MTMSI from the Server LUT
        if self.MTMSI is not None:
            try:
                del self.Server.MTMSI[self.MTMSI]
            except:
                pass
        # set the new PTMSI
        self.MTMSI = mtmsi
        # update the Server LUT
        self.Server.MTMSI[mtmsi] = self.IMSI
    
    #--------------------------------------------------------------------------#
    # UE location
    #--------------------------------------------------------------------------#
    
    def set_plmn(self, plmn):
        if plmn != self.PLMN:
            self.PLMN = plmn
            self._log('INF', 'locate to PLMN %s' % self.PLMN)
    
    def set_lac(self, lac):
        if lac != self.LAC:
            self.LAC = lac
            self._log('INF', 'locate to LAC %.4x' % self.LAC)
    
    def set_rac(self, rac):
        if rac != self.RAC:
            self.RAC = rac
            self._log('INF', 'routing to RAC %.2x' % self.RAC)
        
    def set_tac(self, tac):
        if tac != self.TAC:
            self.TAC = tac
            # TBC
            self._log('INF', 'tracking to TAC')
    
    def set_lai(self, plmn, lac):
        self.set_plmn(plmn)
        self.set_lac(lac)

