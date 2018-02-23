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
# * File Name : pycrate_mobile/TS23041_CBS.py
# * Created : 2018-02-22
# * Authors : Benoit Michau 
# *--------------------------------------------------------
#*/

__all__ = [
    'CBS_WarningType_dict',
    'CBS_MessageId_dict',
    ]

#------------------------------------------------------------------------------#
# 3GPP TS 23.041: Cell Broadcast Service
# release 13 (d30)
#------------------------------------------------------------------------------#

from .TS23038    import *


#------------------------------------------------------------------------------#
# Warning Type
# TS 23.041, section 9.3.24
#------------------------------------------------------------------------------#

CBS_WarningType_dict = {
    0 : 'Earthquake',
    1 : 'Tsunami',
    2 : 'Earthquake and Tsunami',
    3 : 'Test',
    4 : 'Other'
    #5-0x7f: future use
    }


#------------------------------------------------------------------------------#
# Message Identifier
# TS 23.041, section 9.4.1.2.2
#------------------------------------------------------------------------------#

CBS_MessageId_dict = {
    #0-999: GSMA reserved
    1000 : 'LCS CBS for E-OTD Assistance Data',
    1001 : 'LCS CBS for GPS Ephemeris and Clock Correction Data',
    1002 : 'LCS CBS for GPS Ephemeris and Clock Correction Data',
    1003 : 'LCS CBS for GPS Almanac and Other Data',
    #1004-4095: future use
    #4096-4223: reserved for unsecure SIM download (!)
    #4224-4351: reserved for secured SIM download
    4352: 'ETWS CBS for earthquake warning',
    4353: 'ETWS CBS for tsunami warning',
    4354: 'ETWS CBS for earthquake and tsunami combined warning',
    4355: 'ETWS CBS for test', # silently discarded by the UE
    4356: 'ETWS CBS related to other emergency types',
    #4357-4369: future use
    4370: 'CMAS CBS for CMAS Presidential Level Alerts',
    #     also EU-Alert Level 1 / Korean Public Alert System (KPAS) Class 0, not settable by MMI
    4371: 'CMAS CBS for CMAS Extreme Alerts with Severity of Extreme, Urgency of Immediate, and Certainty of Observed',
    #     also EU-Alert Level 2 / Korean Public Alert System (KPAS) Class 1
    4372: 'CMAS CBS for CMAS Extreme Alerts with Severity of Extreme, Urgency of Immediate, and Certainty of Likely',
    #     also EU-Alert Level 2 / Korean Public Alert System (KPAS) Class 1
    4373: 'CMAS CBS for CMAS Severe Alerts with Severity of Extreme, Urgency of Expected, and Certainty of Observed',
    #     also EU-Alert Level 3 / Korean Public Alert System (KPAS) Class 1
    4374: 'CMAS CBS for CMAS Severe Alerts with Severity of Extreme, Urgency of Expected, and Certainty of Likely',
    #     also EU-Alert Level 3 / Korean Public Alert System (KPAS) Class 1
    4375: 'CMAS CBS for CMAS Severe Alerts with Severity of Severe, Urgency of Immediate, and Certainty of Observed'
    #     also EU-Alert Level 3 / Korean Public Alert System (KPAS) Class 1
    4376: 'CMAS CBS for CMAS Severe Alerts with Severity of Severe, Urgency of Immediate, and Certainty of Likely',
    #     also EU-Alert Level 3 / Korean Public Alert System (KPAS) Class 1
    4377: 'CMAS CBS for CMAS Severe Alerts with Severity of Severe, Urgency of Expected, and Certainty of Observed',
    #     also EU-Alert Level 3 / Korean Public Alert System (KPAS) Class 1
    4378: 'CMAS CBS for CMAS Severe Alerts with Severity of Severe, Urgency of Expected, and Certainty of Likely',
    #     also EU-Alert Level 3 / Korean Public Alert System (KPAS) Class 1
    4379: 'CMAS CBS for Child Abduction Emergency (Amber Alert)',
    #     also EU-Amber / Korean Public Alert System (KPAS) Class 1
    4380: 'CMAS CBS for the Required Monthly Test',
    4381: 'CMAS CBS for CMAS Exercise',
    4382: 'CMAS CBS for operator defined use',
    4383: 'CMAS CBS for CMAS Presidential Level Alerts for additional languages',
    #     also EU-Alert Level 1 / Korean Public Alert System (KPAS) Class 0, not settable by MMI
    4384: 'CMAS CBS for CMAS Extreme Alerts with Severity of Extreme, Urgency of Immediate, and Certainty of Observed for additional languages',
    #     also EU-Alert Level 2 / Korean Public Alert System (KPAS) Class 1
    4385: 'CMAS CBS for CMAS Extreme Alerts with Severity of Extreme, Urgency of Immediate, and Certainty of Likely for additional languages',
    #     also EU-Alert Level 2 / Korean Public Alert System (KPAS) Class 1
    4386: 'CMAS CBS for CMAS Severe Alerts with Severity of Extreme, Urgency of Expected, and Certainty of Observed for additional languages',
    #     also EU-Alert Level 3 / Korean Public Alert System (KPAS) Class 1
    4387: 'CMAS CBS for CMAS Severe Alerts with Severity of Extreme, Urgency of Expected, and Certainty of Likely for additional languages',
    #     also EU-Alert Level 3 / Korean Public Alert System (KPAS) Class 1
    4388: 'CMAS CBS for CMAS Severe Alerts with Severity of Severe, Urgency of Immediate, and Certainty of Observed for additional languages'
    #     also EU-Alert Level 3 / Korean Public Alert System (KPAS) Class 1
    4389: 'CMAS CBS for CMAS Severe Alerts with Severity of Severe, Urgency of Immediate, and Certainty of Likely for additional languages',
    #     also EU-Alert Level 3 / Korean Public Alert System (KPAS) Class 1
    4390: 'CMAS CBS for CMAS Severe Alerts with Severity of Severe, Urgency of Expected, and Certainty of Observed for additional languages',
    #     also EU-Alert Level 3 / Korean Public Alert System (KPAS) Class 1
    4391: 'CMAS CBS for CMAS Severe Alerts with Severity of Severe, Urgency of Expected, and Certainty of Likely for additional languages',
    #     also EU-Alert Level 3 / Korean Public Alert System (KPAS) Class 1
    4392: 'CMAS CBS for Child Abduction Emergency (Amber Alert) for additional languages',
    #     also EU-Amber / Korean Public Alert System (KPAS) Class 1
    4393: 'CMAS CBS for the Required Monthly Test for additional languages',
    4394: 'CMAS CBS for CMAS Exercise for additional languages',
    4395: 'CMAS CBS for operator defined use for additional languages',
    #4396-4399: future CMA / EU-Alert
    #4400-6399: future PWS
    6400: 'EU-Info for the local language',
    #6401-40959: future use
    #40960-45055: operator specific
    #45056-65534: future operator specific
    65535: 'reserved', # used with SIM, not settable by MMI
    }
