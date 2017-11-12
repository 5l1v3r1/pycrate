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
# * File Name : pycrate_mobile/TS24008_SM.py
# * Created : 2017-06-22
# * Authors : Benoit Michau
# *--------------------------------------------------------
#*/

#------------------------------------------------------------------------------#
# 3GPP TS 24.008: Mobile radio interface layer 3 specification
# release 13 (d90)
#------------------------------------------------------------------------------#

from pycrate_core.utils import *
from pycrate_core.elt   import *
from pycrate_core.base  import *

from .TS24008_IE import *
#from .TS24301_IE import AddUpdateType, UENetCap
from .TS24007    import *

#------------------------------------------------------------------------------#
# GPRS Session Management header
# TS 24.008, section 10.1 to 10.4
#------------------------------------------------------------------------------#

# PS Mobility Management procedures dict
_PS_SM_dict = {
    65: "GPRS - Activate PDP context request",
    66: "GPRS - Activate PDP context accept",
    67: "GPRS - Activate PDP context reject",
    68: "GPRS - Request PDP context activation",
    69: "GPRS - Request PDP context activation rejection",
    70: "GPRS - Deactivate PDP context request",
    71: "GPRS - Deactivate PDP context accept",
    72: "GPRS - Modify PDP context request(Network to MS direction)",
    73: "GPRS - Modify PDP context accept (MS to network direction)",
    74: "GPRS - Modify PDP context request(MS to network direction)",
    75: "GPRS - Modify PDP context accept (Network to MS direction)",
    76: "GPRS - Modify PDP context reject",
    77: "GPRS - Activate secondary PDP context request",
    78: "GPRS - Activate secondary PDP context accept",
    79: "GPRS - Activate secondary PDP context reject",
    85: "GPRS - SM Status",
    86: "GPRS - Activate MBMS Context Request",
    87: "GPRS - Activate MBMS Context Accept",
    88: "GPRS - Activate MBMS Context Reject",
    89: "GPRS - Request MBMS Context Activation",
    90: "GPRS - Request MBMS Context Activation Reject",
    91: "GPRS - Request Secondary PDP Context Activation",
    92: "GPRS - Request Secondary PDP Context Activation Reject",
    93: "GPRS - Notification"
    }

class SMHeader(Envelope):
    _GEN = (
        Uint('TransId', val=0, bl=4), # TODO: this may be extended to 12 bits
        Uint('ProtDisc', val=10, bl=4, dic=ProtDisc_dict),
        Uint8('Type', val=85, dic=_PS_SM_dict),
        )

#------------------------------------------------------------------------------#
# Activate PDP context request
# TS 24.008, section 9.5.1
#------------------------------------------------------------------------------#

class SMActivatePDPContextRequest(Layer3):
    _GEN = tuple(SMHeader(val={'Type':65})._content) + (
        NSAPI(),
        LLC_SAPI(),
        Type4LV('QoS', val={'V':11*b'\x00'}, IE=QoS()),
        Type4LV('PDPAddr', val={'V':b'\x00\x01'}, IE=PDPAddr()),
        Type4TLV('APN', val={'T':0x28, 'V':b'\x00'}, trans=True),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type1TV('ReqType', val={'T':0xA, 'V':1}, dic=RequestType_dict, trans=True),
        Type1TV('DeviceProp', val={'T':0xC, 'V':0}, IE=DeviceProp(), trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )


#------------------------------------------------------------------------------#
# Activate PDP context accept
# TS 24.008, section 9.5.2
#------------------------------------------------------------------------------#

class SMActivatePDPContextAccept(Layer3):
    _GEN = tuple(SMHeader(val={'Type':66})._content) + (
        LLC_SAPI(),
        Type4LV('QoS', val={'V':11*b'\x00'}, IE=QoS()),
        Uint('spare', val=0, bl=4),
        RadioPriority(),
        Type4TLV('PDPAddr', val={'T':0x2B, 'V':b'\x00\x01'}, IE=PDPAddr(), trans=True),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type4TLV('PacketFlowId', val={'T':0x34, 'V':b'\x00'}, IE=PacketFlowId(), trans=True),
        Type4TLV('SMCause', val={'T':0x39, 'V':b'\x00'}, IE=SMCause(), trans=True),
        Type1TV('ConType', val={'T':0xB, 'V':0}, dic=ConnectivityType_dict, trans=True),
        Type1TV('WLANOffloadInd', val={'T':0xC, 'V':0}, IE=WLANOffloadAccept(), trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )


#------------------------------------------------------------------------------#
# Activate PDP context reject
# TS 24.008, section 9.5.3
#------------------------------------------------------------------------------#

class SMActivatePDPContextReject(Layer3):
    _GEN = tuple(SMHeader(val={'Type':67})._content) + (
        SMCause(),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type4TLV('BackOffTimer', val={'T':0x37, 'V':b'\x00'}, IE=GPRSTimer3(), trans=True),
        Type4TLV('ReattemptInd', val={'T':0x6B, 'V':b'\x00'}, IE=ReattemptInd(), Trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )


#------------------------------------------------------------------------------#
# Activate Secondary PDP Context Request
# TS 24.008, section 9.5.4
#------------------------------------------------------------------------------#

class SMActivateSecondaryPDPContextRequest(Layer3):
    _GEN = tuple(SMHeader(val={'Type':77})._content) + (
        NSAPI(),
        LLC_SAPI(),
        Type4LV('QoS', val={'V':11*b'\x00'}, IE=QoS()),
        Type4LV('LinkedTI', val={'V':b'\x00'}, IE=LinkedTI()),
        Type4TLV('TFT', val={'T':0x36, 'V':b'\x00'}, IE=TFT(), trans=True),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type1TV('DeviceProp', val={'T':0xC, 'V':0}, IE=DeviceProp(), trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )


#------------------------------------------------------------------------------#
# Activate Secondary PDP Context Accept
# TS 24.008, section 9.5.5
#------------------------------------------------------------------------------#

class SMActivateSecondaryPDPContextAccept(Layer3):
    _GEN = tuple(SMHeader(val={'Type':78})._content) + (
        LLC_SAPI(),
        Type4LV('QoS', val={'V':11*b'\x00'}, IE=QoS()),
        Uint('spare', val=0, bl=4),
        RadioPriority(),
        Type4TLV('PacketFlowId', val={'T':0x34, 'V':b'\x00'}, IE=PacketFlowId(), trans=True),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type1TV('WLANOffloadInd', val={'T':0xC, 'V':0}, IE=WLANOffloadAccept(), trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )


#------------------------------------------------------------------------------#
# Activate Secondary PDP Context Reject
# TS 24.008, section 9.5.6
#------------------------------------------------------------------------------#

class SMActivateSecondaryPDPContextReject(Layer3):
    _GEN = tuple(SMHeader(val={'Type':79})._content) + (
        SMCause(),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type4TLV('BackOffTimer', val={'T':0x37, 'V':b'\x00'}, IE=GPRSTimer3(), trans=True),
        Type4TLV('ReattemptInd', val={'T':0x6B, 'V':b'\x00'}, IE=ReattemptInd(), Trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )


#------------------------------------------------------------------------------#
# Request PDP Context Activation
# TS 24.008, section 9.5.7
#------------------------------------------------------------------------------#

class SMRequestPDPContextActivation(Layer3):
    _GEN = tuple(SMHeader(val={'Type':68})._content) + (
        Type4LV('PDPAddr', val={'V':b'\x00\x01'}, IE=PDPAddr()),
        Type4TLV('APN', val={'T':0x28, 'V':b'\x00'}, trans=True),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )

#------------------------------------------------------------------------------#
# Request PDP Context Activation Rejection
# TS 24.008, section 9.5.8
#------------------------------------------------------------------------------#

class SMRequestPDPContextActivationReject(Layer3):
    _GEN = tuple(SMHeader(val={'Type':69})._content) + (
        SMCause(),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )

#------------------------------------------------------------------------------#
# Modify PDP context request (Network to MS direction)
# TS 24.008, section 9.5.9
#------------------------------------------------------------------------------#

class SMModifyPDPContextRequestMT(Layer3):
    _GEN = tuple(SMHeader(val={'Type':72})._content) + (
        Uint('spare', val=0, bl=4),
        RadioPriority(),
        LLC_SAPI(),
        Type4LV('QoS', val={'V':11*b'\x00'}, IE=QoS()),
        Type4TLV('PDPAddr', val={'T':0x2B, 'V':b'\x00\x01'}, IE=PDPAddr(), trans=True),
        Type4TLV('PacketFlowId', val={'T':0x34, 'V':b'\x00'}, IE=PacketFlowId(), trans=True),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type4TLV('TFT', val={'T':0x36, 'V':b'\x00'}, IE=TFT(), trans=True),
        Type1TV('WLANOffloadInd', val={'T':0xC, 'V':0}, IE=WLANOffloadAccept(), trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )

#------------------------------------------------------------------------------#
# Modify PDP context request (MS to Network direction)
# TS 24.008, section 9.5.10
#------------------------------------------------------------------------------#

class SMModifyPDPContextRequestMO(Layer3):
    _GEN = tuple(SMHeader(val={'Type':74})._content) + (
        Type3TV('LLC_SAPI', val={'T':0x32, 'V':b'\x00'}, bl={'V':8}, IE=LLC_SAPI(), trans=True),
        Type4TLV('QoS', val={'T':0x30, 'V':11*b'\x00'}, IE=QoS(), trans=True),
        Type4TLV('TFT', val={'T':0x31, 'V':b'\x00'}, IE=TFT(), trans=True),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type1TV('DeviceProp', val={'T':0xC, 'V':0}, IE=DeviceProp(), trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )


#------------------------------------------------------------------------------#
# Modify PDP Context Accept (MS to Network direction)
# TS 24.008, section 9.5.11
#------------------------------------------------------------------------------#

class SMModifyPDPContextAcceptMO(Layer3):
    _GEN = tuple(SMHeader(val={'Type':73})._content) + (
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )

#------------------------------------------------------------------------------#
# Modify PDP Context Accept (Network to MS direction)
# TS 24.008, section 9.5.12
#------------------------------------------------------------------------------#

class SMModifyPDPContextAcceptMT(Layer3):
    _GEN = tuple(SMHeader(val={'Type':75})._content) + (
        Type4TLV('QoS', val={'T':0x30, 'V':11*b'\x00'}, IE=QoS(), trans=True),
        Type3TV('LLC_SAPI', val={'T':0x32, 'V':b'\x00'}, bl={'V':8}, IE=LLC_SAPI(), trans=True),
        Type1TV('RadioPriority', val={'T':0x8, 'V':0}, IE=RadioPriority(), trans=True),
        Type4TLV('PacketFlowId', val={'T':0x34, 'V':b'\x00'}, IE=PacketFlowId(), trans=True),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type1TV('WLANOffloadInd', val={'T':0xC, 'V':0}, IE=WLANOffloadAccept(), trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )

#------------------------------------------------------------------------------#
# Modify PDP Context Reject
# TS 24.008, section 9.5.13
#------------------------------------------------------------------------------#

class SMModifyPDPContextReject(Layer3):
    _GEN = tuple(SMHeader(val={'Type':76})._content) + (
        SMCause(),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type4TLV('BackOffTimer', val={'T':0x37, 'V':b'\x00'}, IE=GPRSTimer3(), trans=True),
        Type4TLV('ReattemptInd', val={'T':0x6B, 'V':b'\x00'}, IE=ReattemptInd(), Trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )

#------------------------------------------------------------------------------#
# Deactivate PDP Context Request
# TS 24.008, section 9.5.14
#------------------------------------------------------------------------------#

class SMDeactivatePDPContextRequest(Layer3):
    _GEN = tuple(SMHeader(val={'Type':70})._content) + (
        SMCause(),
        Type1TV('TearDownInd', val={'T':0x9, 'V':0}, IE=TearDownInd(), trans=True),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type4TLV('MBMSProtConfig', val={'T':0x35, 'V':b'\x00'}, trans=True),
        Type4TLV('T3396', val={'T':0x37, 'V':b'\x00'}, IE=GPRSTimer3(), trans=True),
        Type1TV('WLANOffloadInd', val={'T':0xC, 'V':0}, IE=WLANOffloadAccept(), trans=True)
        )


#------------------------------------------------------------------------------#
# Deactivate PDP Context Accept
# TS 24.008, section 9.5.15
#------------------------------------------------------------------------------#

class SMDeactivatePDPContextAccept(Layer3):
    _GEN = tuple(SMHeader(val={'Type':71})._content) + (
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type4TLV('MBMSProtConfig', val={'T':0x35, 'V':b'\x00'}, trans=True)
        )


#------------------------------------------------------------------------------#
# Request Secondary PDP Context Activation
# TS 24.008, section 9.5.15a
#------------------------------------------------------------------------------#

class SMRequestSecondaryPDPContextActivation(Layer3):
    _GEN = tuple(SMHeader(val={'Type':91})._content) + (
        Type4LV('QoS', val={'V':11*b'\x00'}, IE=QoS()),
        Type4LV('LinkedTI', val={'V':b'\x00'}, IE=LinkedTI()),
        Type4TLV('TFT', val={'T':0x36, 'V':b'\x00'}, IE=TFT(), trans=True),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type1TV('WLANOffloadInd', val={'T':0xC, 'V':0}, IE=WLANOffloadAccept(), trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )


#------------------------------------------------------------------------------#
# Request Secondary PDP Context Activation Reject
# TS 24.008, section 9.5.15b
#------------------------------------------------------------------------------#

class SMRequestSecondaryPDPContextActivationReject(Layer3):
    _GEN = tuple(SMHeader(val={'Type':92})._content) + (
        SMCause(),
        Type4TLV('ProtConfig', val={'T':0x27, 'V':b'\x80'}, IE=ProtConfig(), trans=True),
        Type4TLV('NBIFOMContainer', val={'T':0x33, 'V':b'\x00'}, trans=True)
        )


#------------------------------------------------------------------------------#
# Notification
# TS 24.008, section 9.5.16a
#------------------------------------------------------------------------------#

class SMNotification(Layer3):
    _GEN = tuple(SMHeader(val={'Type':93})._content) + (
        Type4LV('NotificationInd', val={'V':b'\x00'}, IE=NotificationInd()),
        )


#------------------------------------------------------------------------------#
# SM Status
# TS 24.008, section 9.5.21
#------------------------------------------------------------------------------#

class SMStatus(Layer3):
    _GEN = tuple(SMHeader(val={'Type':85})._content) + (
        SMCause(),
        )

#------------------------------------------------------------------------------#
# Activate MBMS Context Request
# TS 24.008, section 9.5.22
#------------------------------------------------------------------------------#

class SMActivateMBMSContextRequest(Layer3):
    _GEN = tuple(SMHeader(val={'Type':86})._content) + (
        ENSAPI('MBMS_NSAPI'),
        LLC_SAPI(),
        Type4LV('MBMSBearerCap', val={'V':b'\x00'}, IE=MBMSBearerCap()),
        Type4LV('MCastAddr', val={'V':b'\x00\x01'}, IE=PDPAddr()),
        Type4LV('APN', val={'V':b'\x00'}),
        Type4TLV('MBMSProtConfig', val={'T':0x35, 'V':b'\x00'}, trans=True),
        Type1TV('DeviceProp', val={'T':0xC, 'V':0}, IE=DeviceProp(), trans=True)
        )


#------------------------------------------------------------------------------#
# Activate MBMS Context Accept
# TS 24.008, section 9.5.23
#------------------------------------------------------------------------------#

class SMActivateMBMSContextAccept(Layer3):
    _GEN = tuple(SMHeader(val={'Type':87})._content) + (
        Type4LV('TMGI', val={'V':b'\x00\x00\x00'}, IE=TMGI()),
        LLC_SAPI(),
        Type4TLV('MBMSProtConfig', val={'T':0x35, 'V':b'\x00'}, trans=True)
        )


#------------------------------------------------------------------------------#
# Activate MBMS Context Reject
# TS 24.008, section 9.5.24
#------------------------------------------------------------------------------#

class SMActivateMBMSContextReject(Layer3):
    _GEN = tuple(SMHeader(val={'Type':88})._content) + (
        SMCause(),
        Type4TLV('MBMSProtConfig', val={'T':0x35, 'V':b'\x00'}, trans=True),
        Type4TLV('BackOffTimer', val={'T':0x37, 'V':b'\x00'}, IE=GPRSTimer3(), trans=True),
        Type4TLV('ReattemptInd', val={'T':0x6B, 'V':b'\x00'}, IE=ReattemptInd(), Trans=True)
        )


#------------------------------------------------------------------------------#
# Request MBMS Context Activation
# TS 24.008, section 9.5.25
#------------------------------------------------------------------------------#

class SMRequestMBMSContextActivation(Layer3):
    _GEN = tuple(SMHeader(val={'Type':89})._content) + (
        NSAPI(),
        Type4LV('MCastAddr', val={'V':b'\x00\x01'}, IE=PDPAddr()),
        Type4LV('APN', val={'V':b'\x00'}),
        Type4TLV('MBMSProtConfig', val={'T':0x35, 'V':b'\x00'}, trans=True)
        )


#------------------------------------------------------------------------------#
# Request MBMS Context Activation Reject
# TS 24.008, section 9.5.26
#------------------------------------------------------------------------------#

class SMRequestMBMSContextActivationReject(Layer3):
    _GEN = tuple(SMHeader(val={'Type':90})._content) + (
        SMCause(),
        Type4TLV('MBMSProtConfig', val={'T':0x35, 'V':b'\x00'}, trans=True)
        )


#------------------------------------------------------------------------------#
# SM dispatchers
#------------------------------------------------------------------------------#

SMTypeClasses = {
    65: SMActivatePDPContextRequest,
    66: SMActivatePDPContextAccept,
    67: SMActivatePDPContextReject,
    68: SMRequestPDPContextActivation,
    69: SMRequestPDPContextActivationReject,
    70: SMDeactivatePDPContextRequest,
    71: SMDeactivatePDPContextAccept,
    72: SMModifyPDPContextRequestMT,
    73: SMModifyPDPContextAcceptMO,
    74: SMModifyPDPContextRequestMO,
    75: SMModifyPDPContextAcceptMT,
    76: SMModifyPDPContextReject,
    77: SMActivateSecondaryPDPContextRequest,
    78: SMActivateSecondaryPDPContextAccept,
    79: SMActivateSecondaryPDPContextReject,
    85: SMStatus,
    86: SMActivateMBMSContextRequest,
    87: SMActivateMBMSContextAccept,
    88: SMActivateMBMSContextReject,
    89: SMRequestMBMSContextActivation,
    90: SMRequestMBMSContextActivationReject,
    91: SMRequestSecondaryPDPContextActivation,
    92: SMRequestSecondaryPDPContextActivationReject,
    93: SMNotification
    }

def get_sm_msg_instances():
    return {k: SMTypeClasses[k]() for k in SMTypeClasses}

