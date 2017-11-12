# -*- coding: UTF-8 -*-
#/**
# * Software Name : pycrate
# * Version : 0.2
# *
# * Copyright 2016. Benoit Michau. ANSSI.
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
# * File Name : pycrate_asn1c/err.py
# * Created : 2016-03-02
# * Authors : Benoit Michau 
# *--------------------------------------------------------
#*/

#------------------------------------------------------------------------------#
# ASN.1 errors
#------------------------------------------------------------------------------#

# generic ASN.1 error
class ASN1Err(Exception):
    pass

# error when processing ASN.1 text
class ASN1ProcTextErr(ASN1Err):
    pass

# error when encountering an undefined object
class ASN1ProcLinkErr(ASN1Err):
    pass

# error when manipulating an existing ASN1 object
class ASN1ObjErr(ASN1Err):
    pass

# error when encountering an unsupported case
class ASN1NotSuppErr(ASN1Err):
    pass

