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
# * File Name : pycrate_corenet/ProcProto.py
# * Created : 2017-07-13
# * Authors : Benoit Michau 
# *--------------------------------------------------------
#*/

from pycrate_mobile.TS24007 import *
from .utils import *

#------------------------------------------------------------------------------#
# RAN-supported procedures (HNBAP, RUA, RANAP, S1AP)
#------------------------------------------------------------------------------#

class LinkSigProc(SigProc):
    """wrapping class that defines common methods for Iu-based and S1-based
    signaling procedures; relies heavily on the ASN.1 definitions
    """
    
    # to keep track of the PDU(s) exchanged within this procedure
    TRACK_PDU = True
    
    # PDU type look-up
    _ptype_lut = {
        'ini': 'initiatingMessage',
        'suc': 'successfulOutcome',
        'uns': 'unsuccessfulOutcome'
        }
    
    # default criticality for encoding ASN.1 undefined IE / Ext
    _criticality_undef = 'ignore'
    
    # ASN.1 procedure description (HNBAP.HNBAP_PDU_Descriptions.*)
    Desc = None
    
    # Custom decoders:
    # for each type of PDU (ini / suc / uns), provides specific functions (or None)
    # for given IEs and Exts name
    # this allows to collect IEs / Exts in their original ASN.1 value, or after 
    # a specific transformation
    Decod = {
        'ini': ({}, {}),
        'suc': None,
        'uns': None,
        }
    
    # Custom encoders:
    # for each type of PDU (ini / suc / uns), provides specific static values
    # for given IEs and Exts name
    # this allows to override values passed at runtime or set static values
    Encod = {
        'ini': ({}, {}),
        'suc': None,
        'uns': None,
        }
    
    #--------------------------------------------------------------------------#
    
    @classmethod
    def init(cls):
        """class initialization required to build .Cont attribute with PDU(s) 
        content and extend .Decod and .Encod from .Desc attribute (ASN.1 
        procedure description)
        """
        # 1) get procedure code and criticality from description
        desc = cls.Desc()
        cls.Code = desc['procedureCode']
        cls.Crit = desc['criticality']
        
        # 2) retrieve PDU(s) content from description
        # -> get dict of protocolIEs (ident: value's type)
        # -> get dict of protocolExtensions (ident: extvalue's type)
        # -> set list of mandatory IEs
        # -> add in the Encod and Decod dicts the numerical `ident` index 
        # for given encoders / decoders
        cls.Cont = {'ini': None, 'suc': None, 'uns': None}
        for ptype in (('InitiatingMessage', 'ini'),
                      ('SuccessfulOutcome', 'suc'),
                      ('Outcome', 'suc'), # this is used in RANAP
                      ('UnsuccessfulOutcome', 'uns')):
            if ptype[0] in desc:
                encod, decod = cls.Encod[ptype[1]], cls.Decod[ptype[1]]
                content, cont_ies, cont_exts, mand = desc[ptype[0]], {}, {}, []
                if 'protocolIEs' in content._cont:
                    # get the ASN.1 set of defined {ident : value's type}
                    set_ies = content._cont['protocolIEs']._cont._cont['value']._const_tab
                    for ident in set_ies('id'):
                        cont_ies[ident] = set_ies('id', ident)
                        if cont_ies[ident]['presence'] == 'mandatory':
                            mand.append( ident )
                        try:
                            pyname = pythonize_name(cont_ies[ident]['Value']._tr._name)
                        except:
                            pass
                        else:
                            if pyname in encod[0]:
                                encod[0][ident] = encod[0][pyname]
                            if pyname in decod[0]:
                                decod[0][ident] = decod[0][pyname]
                if 'protocolExtensions' in content._cont:
                    # get the ASN.1 set of defined {ident : extvalue's type}
                    set_exts = content._cont['protocolExtensions']._cont._cont['extensionValue']._const_tab
                    for ident in set_exts('id'):
                        cont_exts[ident] = set_exts('id', ident)
                        if cont_exts[ident]['presence'] == 'mandatory':
                            mand.append( ident )
                        try:
                            pyname = pythonize_name(cont_exts[ident]['Extension']._tr._name)
                        except:
                            pass
                        else:
                            if pyname in encod[1]:
                                encod[1][ident] = encod[1][pyname]
                            if pyname in decod[1]:
                                decod[1][ident] = decod[1][pyname]
                if not cont_ies:
                    cont_ies = None
                if not cont_exts:
                    cont_exts = None
                cls.Cont[ptype[1]] = (content, cont_ies, cont_exts, mand)
    
    #--------------------------------------------------------------------------#
    
    def decode_pdu(self, pdu, ret):
        """decode the pdu and populate ret (dict) with the collected values
        
        select the expected content in self.Cont, according to the pdu type
        select the potential decoders in self.Decod
        raise HNBAPErr if an error requiring procedure rejection is found
        
        when unknown identifiers are encountered:
        IE buffer value is set with key 'id_%id',
        Extension buffer value is wet with key 'idext_%id'
        
        this enables to collect also IE and Extension that are not part of the
        original ASN.1 specification
        """
        # 1) select the correct PDU and content
        ptype = pdu[0][:3]
        Cont, IEs, Extensions, mand = self.Cont[ptype]
        Decod = self.Decod[ptype]
        #
        val = pdu[1]
        # 2) check the PDU criticality
        # actually, the sender can modify the criticality of an IE,
        # the criticality from the ASN.1 has to be used only in case the IE
        # is not present in the PDU
        #if val['criticality'] != self.Crit:
        #    # this actually happens in real life: must not raise()...
        #    #raise(HNBAPErr('invalid PDU criticality'))
        #    self._log('WNG', 'decode_pdu: incorrect PDU criticality, %s' % val['criticality'])
        #
        # 3) ensure the PDU content has been properly decoded
        if not isinstance(val['value'], tuple) or \
        val['value'][0] != Cont._tr._name:
            raise(HNBAPErr('invalid PDU content'))
        #
        # 4) get the value part of the PDU with IEs and Extensions,
        # and copy the list of mandatory IEs
        val, mand = val['value'][1], mand[:]
        #
        # 5) collect the list of IEs' values
        if 'protocolIEs' in val:
            for ie in val['protocolIEs']:
                # get the value identifier and corresponding ASN.1 object
                ident = ie['id']
                try:
                    IE = IEs[ident]
                except:
                    # unknown IE, c'est pas grave...
                    self._log('INF', 'decode_pdu: unknown IE ident in PDU, %r' % ie)
                    ret['id_%i' % ident] = ie['value']
                else:
                    name = IE['Value']._tr._name
                    # check the ie criticality
                    #if ie['criticality'] != IE['criticality']:
                    #    #raise(HNBAPErr('invalid IE criticality in PDU, id %i' % ident))
                    #    self._log('WNG', 'decode_pdu: incorrect IE %s criticality, %s'\
                    #              % (ident, ie['criticality']))
                    # ensure the value content has been properly decoded
                    if ie['value'][0] != name:
                        raise(HNBAPErr('invalid IE value in PDU, id %i' % ident))
                    # collect and eventually transform the ie value
                    if ident in Decod[0]:
                        ret[pythonize_name(name)] = Decod[0][ident](ie['value'][1])
                    else:
                        ret[pythonize_name(name)] = ie['value'][1]
                    # remove the value identifier from the list of mandatory values
                    if ident in mand:
                        mand.remove(ident)
        #
        # 6) collect the list of Extensions' values
        if 'protocolExtensions' in val:
            for ie in val['protocolExtensions']:
                # get the value identifier and corresponding ASN.1 object
                ident = ie['id']
                try:
                    IE = Extensions[ident]
                except:
                    # unknown Extension, c'est pas grave non plus...
                    self._log('INF', 'decode_pdu: unknown Ext ident in PDU, %r' % ie)
                    ret['idext_%i' % ident] = ie['extensionValue']
                else:
                    name = IE['Extension']._tr._name
                    # check the ie criticality
                    #if ie['criticality'] != IE['criticality']:
                    #    #raise(HNBAPErr('invalid Extension criticality in PDU, id %i' % ident))
                    #    self._log('WNG', 'decode_pdu: incorrect Extension %s criticality, %s'\
                    #              % (ident, ie['criticality']))
                    # ensure the value content has been properly decoded
                    if ie['extensionValue'][0] != name:
                        raise(HNBAPErr('invalid Extension value in PDU, id %i' % ident))
                    # collect and eventually transform the ie value
                    if ident in Decod[1]:
                        ret[pythonize_name(name)] = Decod[1][ident](ie['extensionValue'][1])
                    else:
                        ret[pythonize_name(name)] = ie['extensionValue'][1]
                    # remove the value identifier from the list of mandatory values
                    if ident in mand:
                        mand.remove(ident)
        #
        # 7) if not all mandatory IEs have not been decoded, raise
        if mand:
            raise(HNBAP('missing mandatory IEs in PDU, %r' % mand))
    
    def encode_pdu(self, ptype, **kw):
        """encode the provided IEs' values from **kw into the PDU of type ptype 
        ('ini', 'suc' or 'uns') and stack it in self._snd
        
        values provided in self.Encod will be set in priority, potentially 
        overriding those in **kw
        
        values can be passed by their structure name and value:
        e.g. 'UE_Usage_Type': 1,
        or by their identifier and buffer value 
        e.g. 'id_290': b'\x01'
        (tip: id_$ident will never clash with an IE name which starts with an 
        upper case)
        
        when passing values by their identifier:
        'id_%id' must be used when part of the IEs,
        'idext_%id' must be used when part of the Exts
        
        this enables also to add IE and Extension that are not part of the 
        original ASN.1 specification
        """
        # 1) select the correct PDU and content
        Cont, IEs, Extensions, mand = self.Cont[ptype]
        Encod = self.Encod[ptype]
        pdu_ies, pdu_exts = [], []
        #
        # 2) encode the list of IEs' values
        if IEs is not None:
            for (ident, IE) in IEs.items():
                name, val = IE['Value']._tr._name, None
                pyname, idname = pythonize_name(name), 'id_%i' % ident
                if pyname in Encod[0]:
                    # static object value provided
                    val = (IE['Value']._tr._name, Encod[0][pyname])
                    if pyname in kw:
                        del kw[pyname]
                elif idname in Encod[0]:
                    # static buffer value provided
                    val = Encod[0][idname]
                    if idname in kw:
                        del kw[idname]
                elif pyname in kw:
                    # object value provided at runtime
                    val = (IE['Value']._tr._name, kw[pyname])
                    del kw[pyname]
                elif idname in kw:
                    # buffer value provided at runtime
                    val = kw[idname]
                    del kw[idname]
                if val is not None:
                    pdu_ies.append({'id': ident,
                                    'criticality': IE['criticality'],
                                    'value': val})
                elif ident in mand:
                    self._log('WNG', 'encode_pdu: missing mandatory IE, ident %i' % ident)
        #
        # 3) encode the list of Extensions' values
        if Extensions is not None:
            for (ident, IE) in Extensions.items():
                name, val = IE['Extension']._tr._name, None
                pyname, idname = pythonize_name(name), 'idext_%i' % ident
                if pyname in Encod[1]:
                    # static object value provided
                    val = (IE['Value']._tr._name, Encod[1][pyname])
                    if pyname in kw:
                        del kw[pyname]
                elif idname in Encod[0]:
                    # static buffer value provided
                    val = Encod[0][idname]
                    if idname in kw:
                        del kw[idname]
                elif pyname in kw:
                    # object value provided at runtime
                    val = (IE['Value']._tr._name, kw[pyname])
                    del val[pyname]
                elif idname in kw:
                    # buffer value provided at runtime
                    val = kw[idname]
                    del kw[idname]
                if val is not None:
                    pdu_exts.append({'id': ident,
                                     'criticality': IE['criticality'],
                                     'extensionValue': val})
                elif ident in mand:
                    self._log('WNG', 'encode_pdu: missing mandatory Ext, ident %i' % ident)
        #
        # 4) enable also undefined buffer values passed at runtime to be encoded
        for name in kw:
            if name[:3] == 'id_':
                ident = int(name[3:])
                if isinstance(kw[name], tuple):
                    crit = kw[name][0]
                    val  = kw[name][1]
                else:
                    crit = self._criticality_default
                    val = kw[name]
                pdu_ies.append({'id': ident,
                                'criticality': crit,
                                'value': val})
            elif name[:6] == 'idext_':
                ident = int(name[6:])
                if isinstance(kw[name], tuple):
                    crit = kw[name][0]
                    val  = kw[name][1]
                else:
                    crit = self._criticality_default
                    val = kw[name]
                pdu_exts.append({'id': ident,
                                 'criticality': crit,
                                 'value': val})
        #
        # 5) build the whole PDU
        val = {}
        if pdu_ies:
            val['protocolIEs'] = pdu_ies
        if pdu_exts:
            val['protocolExtensions'] = pdu_exts
        self._snd.append( (self._ptype_lut[ptype],
                           {'procedureCode': self.Code,
                            'criticality': self.Crit,
                            'value': (Cont._tr._name, val)}) )
    
    #--------------------------------------------------------------------------#
    
    def recv(self, pdu):
        """process the PDU received by the signaling stack
        """
        self._log('ERR', 'recv() not implemented')
    
    def send(self):
        """return a list of PDU(s) to be sent by the signaling stack
        """
        self._log('ERR', 'send() not implemented')
        return self._snd
    
    def trigger(self):
        """return a list of new procedure(s) which were created during previous 
        processing
        """
        self._log('ERR', 'trigger() not implemented')
        return []
    
    def abort(self):
        """abort the procedure, e.g. due to a timeout or an error indication
        """
        pass


#------------------------------------------------------------------------------#
# NAS signaling procedures
#------------------------------------------------------------------------------#

_get_first  = lambda x: x[1]
_get_second = lambda x: x[2]

class NASSigProc(SigProc):
    """wrapping class that defines common methods for NAS signaling procedures
    """
    
    # to keep track of the NAS message(s) exchanged within this procedure
    TRACK_MSG = True
    
    # procedure NAS message content:
    # CN-initiated msg class (None or tuple), UE-initiated msg class (None or tuple)
    Cont = (None, None)
    
    # Custom decoders:
    # for each type of NAS msg defined in Cont, provides specific functions (or None)
    # for given IE name
    # this allows to collect IEs in their original NAS value, or after a specific transformation
    Decod = {}
    
    # Custom encoders:
    # for each type of NAS msg defined in Cont, provides specific static values
    # for given IE name
    # this allows to override values passed at runtime or set static values
    Encod = {}
    
    # NAS message processing filter, built at class init
    Filter = []
    
    #--------------------------------------------------------------------------#
    
    @classmethod
    def init(cls, filter_init=1):
        """class initialization required to build .Filter attribute describing
        NAS message type accepted by the procedure handler, and default .Decod
        attribute to extract only V part of LV / TV / TLV IEs.
        
        filter_init = 0, builds a Filter with CN-initiated message
        filter_init = 1, builds a Filter with UE-initiated message
        """
        ContLUT, Encod, Decod, Filter = {}, {}, {}, []
        #
        # CN-initiated NAS msg
        if cls.Cont[0] is not None:
            for i, msgclass in enumerate(cls.Cont[0]):
                msg  = msgclass()
                mid  = (msg['ProtDisc'](), msg['Type']())
                mies = msg[1+msg._by_name.index('Type'):]
                ContLUT[mid] = (0, i)
                if mid not in cls.Encod:
                    Encod[mid] = {}
                else:
                    Encod[mid] = cls.Encod[mid]
                if mid not in cls.Decod:
                    Decod[mid] = {}
                else:
                    Decod[mid] = cls.Decod[mid]
                # build default decoders when not user-defined
                for ie in mies:
                    if ie._name not in Decod[mid]:
                        if isinstance(ie, (Type1TV, Type3TV, Type4LV, Type6LVE)):
                            Decod[mid][ie._name] = _get_first
                        elif isinstance(ie, (Type4TLV, Type6TLVE)):
                            Decod[mid][ie._name] = _get_second
                
        #
        # UE-initiated NAS msg
        if cls.Cont[1] is not None:
            for i, msgclass in enumerate(cls.Cont[1]):
                msg  = msgclass()
                mid  = (msg['ProtDisc'](), msg['Type']())
                mies = msg[1+msg._by_name.index('Type'):]
                ContLUT[mid] = (1, i)
                if mid not in cls.Encod:
                    Encod[mid] = {}
                else:
                    Encod[mid] = cls.Encod[mid]
                if mid not in cls.Decod:
                    Decod[mid] = {}
                else:
                    Decod[mid] = cls.Decod[mid]
                # build default decoders when not user-defined
                for ie in mies:
                    if ie._name not in Decod[mid]:
                        if isinstance(ie, (Type1TV, Type3TV, Type4LV, Type6LVE)):
                            Decod[mid][ie._name] = _get_first
                        elif isinstance(ie, (Type4TLV, Type6TLVE)):
                            Decod[mid][ie._name] = _get_second
        #
        Filter = []
        if cls.Cont[filter_init] is not None:
            [Filter.append( (msgclass()['ProtDisc'](), msgclass()['Type']()) ) 
             for msgclass in cls.Cont[filter_init]]
        #
        cls.ContLUT, cls.Encod, cls.Decod, cls.Filter = ContLUT, Encod, Decod, Filter
    
    #--------------------------------------------------------------------------#
    
    def _prepare(self, encod=None):
        # _prepare() must be called by each NASSigProc.__init__() method
        #
        self.Name = self.__class__.__name__
        #
        # set empty dicts for the NAS messages of the instance
        self.Encod = {msgid: {} for msgid in self.__class__.Encod}
        #
        if encod:
            for k, v in encod.items():
                self.set_msg(*k, **v)
        #
        # to store PDU traces
        self._pdu = []
        # NAS message received from / to be sent to the UE
        self._nas_rx = None
        self._nas_tx = None
    
    #--------------------------------------------------------------------------#
    
    def decode_msg(self, msg, ret):
        """decode the NAS msg and populate ret (dict) with the collected IE 
        values (all fields after the `Type' field)
        
        select specific IE decoders in self.Decod for the given message
        to potentially transform IE values collected
        """
        self._nas_rx, payload, ProtDisc = msg, False, -1
        for ie in msg._content:
            if payload and not ie.get_trans():
                if ie._name in Decod:
                    ret[ie._name] = Decod[ie._name](ie)
                else:
                    # this will include potential unknown IE, which name will
                    # be _T_$tag
                    ret[ie._name] = ie
            elif ie._name == 'ProtDisc':
                ProtDisc = ie()
            elif ie._name == 'Type':
                Type = ie()
                # entering msg payload after this
                payload = True
                # get decoding transforms if defined
                try:
                    Decod = self.Decod[(ProtDisc, Type)]
                except:
                    Decod = {}
    
    def encode_msg(self, pd, typ):
        """encode the NAS msg from protocol discriminator `pd' and type `typ'
        with IE values provided in self.Encod, and set the encoded message in 
        self._nas_tx.
        if IE values are set for the class (self.__class__.Encod), they will
        overwrite those from self.Encod.
        
        values can be passed by their IE name and value:
        e.g. 'UE_Usage_Type': 1,
        or by their tag and buffer or integral value for unspecified IE:
        e.g. '_T_29': b'\x01',
        
        this enables also to add IE that are not part of the original specification
        """
        # select the instance encoder
        try:
            Encod = self.Encod[(pd, typ)]
        except:
            Encod = {}
        # update it with the class encoder
        ClaEncod = self.__class__.Encod[(pd, typ)]
        if ClaEncod:
            Encod.update(ClaEncod)
        #
        # instantiate the msg with those values
        i, j = self.ContLUT[(pd, typ)]
        self._nas_tx = self.Cont[i][j](val=Encod)
        #
        # add potential unspecified extension
        ext = [k for k in Encod.keys() if k[:3] == '_T_']
        if ext:
            if isinstance(self._nas_tx, Layer3):
                for k in ext:
                    tag = int(k[3:])
                    if tag & 0x80:
                        self._nas_tx.append( Type2(k, val=[tag]) )
                    else:
                        self._nas_tx.append( Type4TLV(k, val={'T':tag, 'V':Encod[k]}) )
            else:
                #isinstance(self._nas_tx, Layer3EPS)
                for k in ext:
                    tag = int(k[3:])
                    if tag & 0x80:
                        self._nas_tx.append( Type2(k, val=[tag]) )
                    elif tag & 0x70 == 0x70:
                        self._nas_tx.append( Type6TLVE(k, val={'T':tag, 'V':Encod[k]}) )
                    else:
                        self._nas_tx.append( Type4TLV(k, val={'T':tag, 'V':Encod[k]}) )
    
    # in many NAS procedures, encod_msg() will be called automatically by output()
    # instead, set_msg() must be used for preparing a payload from an external procedure
    
    def set_msg(self, pd, typ, **kw):
        """prepare a specific encoder dict for a given NAS message
        """
        # select the encoder and duplicate it
        try:
            Encod = self.Encod[(pd, typ)]
        except:
            return
        Encod.update(kw)
    
    #--------------------------------------------------------------------------#
    
    def output(self):
        """return a NAS msg to be sent by the signaling stack
        """
        self._log('ERR', 'output() not implemented')
        return None
    
    def process(self, msg):
        """process the NAS msg received by the signaling stack
        """
        self._log('ERR', 'process() not implemented')
        return None
    
    def postprocess(self, proc=None):
        """post-processing after a nested procedure `proc' has ended
        """
        self._log('ERR', 'postprocess() not implemented')
        return None
    
    def abort(self):
        """abort the procedure, e.g. due to a timeout or an error indication
        """
        pass

