#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu
"""
(c) 2014 - Ronan Delacroix
SNMP utilities - This requires the pySNMP library
:author: Ronan Delacroix
"""

from pysnmp.entity.rfc3413.oneliner import cmdgen

def snmp_get(oid, ip_address):


    errorIndication, errorStatus, \
                 errorIndex, varBinds = cmdgen.CommandGenerator().getCmd(
        # SNMP v1
        #cmdgen.CommunityData('test-agent', 'public', 0),
        # SNMP v2
        cmdgen.CommunityData('test-agent', 'public'),
        # SNMP v3
        #cmdgen.UsmUserData('test-user', 'authkey1', 'privkey1'),
        cmdgen.UdpTransportTarget((ip_address, 161)),
        # Plain OID
        oid,
        # ((mib-name, mib-symbol), instance-id)
        (('SNMPv2-MIB', 'sysObjectID'), 0)
    )

    if errorIndication:
        raise Exception(errorIndication)
    else:
        if errorStatus:
            raise Exception(errorStatus.prettyPrint() + ' at ' +  errorIndex and varBinds[int(errorIndex)-1] or '?')

    return str(varBinds[0][1])