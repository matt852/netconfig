import unittest
from app.device_classes.device_definitions.cisco.cisco_ios import CiscoIOS


class TestCiscoIOS(unittest.TestCase):
    """CI testing class for Cisco IOS devices."""

    def setUp(self):
        """Initialize static class testing variables."""
        self.device = CiscoIOS('na', 'na', 'na', 'na', 'na', 'na')

        self.cdp_input_data = '''
-------------------------
Device ID: ABC1234567890AB
Entry address(es):
  IP address: 10.0.53.81
Platform: Polycom SoundPoint IP 123,  Capabilities: Host Phone
Interface: GigabitEthernet2/0/12,  Port ID (outgoing port): Port 1
Holdtime : 138 sec

Version :
Updater: 5.0.8, App: 4.0.8

advertisement version: 2
Duplex: full
Power drawn: 3.900 Watts

-------------------------
Device ID: AP01234
Entry address(es):
  IP address: 10.18.175.20
  IPv6 address: FE80::1234:5678:90AB  (link-local)
Platform: cisco AIR-CAP2702I-A-K9,  Capabilities: Trans-Bridge Source-Route-Bridge IGMP
Interface: GigabitEthernet5/0/25,  Port ID (outgoing port): FastEthernet0
Holdtime : 141 sec

Version :
Cisco IOS Software, C2700 Software (AP3G2-K9W8-M), Version 10.1(2)JA3, RELEASE SOFTWARE (fc1)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2015 by Cisco Systems, Inc.
Compiled Mon 01-Jan-00 01:23 by prod_rel_team

advertisement version: 2
Duplex: full
Power drawn: 15.400 Watts
Power request id: 2367, Power management id: 2
Power request levels are:16800 15400 13000 0 0
Management address(es):
  IP address: 10.18.175.20

-------------------------
Device ID: PC0A1.domain.com
Entry address(es):
  IP address: 192.168.14.44
Platform: cisco WS-C6509-32,  Capabilities: Router Switch IGMP
Interface: FastEthernet4/0/5,  Port ID (outgoing port): bridge1
Holdtime : 131 sec

Version :
Cisco IOS Software, Catalyst 6500 L3 Switch  Software (cat6500e-UNIVERSALK9-M), Version 10.1(2)E3, RELEASE SOFTWARE (fc2)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2016 by Cisco Systems, Inc.
Compiled Mon 01-Jan-00 01:23 by prod_rel_team

advertisement version: 2
VTP Management Domain: 'domainA1'
Native VLAN: 1
Duplex: full
Management address(es):
  IP address: 192.168.14.44

-------------------------
Device ID: Switch02-4A
Entry address(es):
  IP address: 172.18.95.111
Platform: cisco WS-C2960XR-32,  Capabilities: Router Switch IGMP
Interface: TenGigabitEthernet2/0/5,  Port ID (outgoing port): GigabitEthernet1/1/19
Holdtime : 163 sec

Version :
Cisco IOS Software, Catalyst 2960 L3 Switch  Software (cat2900e-UNIVERSALK9-M), Version 10.1(2)E3, RELEASE SOFTWARE (fc2)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2016 by Cisco Systems, Inc.
Compiled Mon 01-Jan-00 01:23 by prod_rel_team

advertisement version: 2
VTP Management Domain: 'VTP_123-45C'
Native VLAN: 1
Duplex: full
Management address(es):
  IP address: 172.18.95.111

----------------------------------------
Device ID:AB-CD-1.domain.com
System Name: HQ-SW-DIST-2

Interface address(es):
    IPv4 Address: 192.168.0.0
Platform: N3K-C3524DA, Capabilities: Switch IGMP Filtering Supports-STP-Dispute
Interface: mgmt0, Port ID (outgoing port): mgmt0
Holdtime: 159 sec

Version:
Cisco Nexus Operating System (NX-OS) Software, Version 1.2(3)N4(5)

Advertisement Version: 1
Duplex: full

MTU: 1500
Mgmt address(es):
    IPv4 Address: 192.168.0.0
----------------------------------------
Device ID:NABC-1234-01-02

Interface address(es):
    IPv4 Address: 10.0.230.24
    IPv4 Address: 10.0.230.25
Platform: V3250, Capabilities: Host
Interface: Ethernet102/1/26, Port ID (outgoing port): e0a
Holdtime: 142 sec

Version:
CloudAdd Release 1.2.3A4: Mon Jan  1 00:00:00 PST 2000

Advertisement Version: 1
----------------------------------------
Device ID:ZY_XWGH_1a.domain.com(ABC1234DEFG)
System Name: HQ-SW-DIST-2

Interface address(es):
    IPv4 Address: 192.168.0.255
Platform: N5K-C5596UP, Capabilities: Switch IGMP Filtering Supports-STP-Dispute
Interface: Ethernet1/1, Port ID (outgoing port): Ethernet1/1
Holdtime: 8 sec

Version:
Cisco Nexus Operating System (NX-OS) Software, Version 1.2(3)N4(5)

Advertisement Version: 2

Native VLAN: 9
Duplex: half

MTU: 1500
Physical Location: Milky Way Galaxy
Mgmt address(es):
    IPv4 Address: 192.168.0.255

'''

    def test_ios_cdp_neighbor_formatting(self):
        """Test IOS CDP neighbor output formatting."""
        expected_output = [{'local_iface': 'Gig 2/0/12', 'port_id': 'Port 1', 'platform': 'Polycom SoundPoint IP 123', 'device_id': 'ABC1234567890AB', 'remote_ip': '10.0.53.81'},
                           {'local_iface': 'Gig 5/0/25', 'port_id': 'Fas 0', 'platform': 'cisco AIR-CAP2702I-A-K9', 'device_id': 'AP01234', 'remote_ip': '10.18.175.20'},
                           {'local_iface': 'Fas 4/0/5', 'port_id': 'bridge1', 'platform': 'cisco WS-C6509-32', 'device_id': 'PC0A1.domain.com', 'remote_ip': '192.168.14.44'},
                           {'local_iface': 'Ten 2/0/5', 'port_id': 'Gig 1/1/19', 'platform': 'cisco WS-C2960XR-32', 'device_id': 'Switch02-4A', 'remote_ip': '172.18.95.111'},
                           {'local_iface': 'mgmt0', 'port_id': 'mgmt0', 'platform': 'N3K-C3524DA', 'device_id': 'AB-CD-1.domain.com', 'remote_ip': '192.168.0.0'},
                           {'local_iface': 'Eth 102/1/26', 'port_id': 'e0a', 'platform': 'V3250', 'device_id': 'NABC-1234-01-02', 'remote_ip': '10.0.230.24'},
                           {'local_iface': 'Eth 1/1', 'port_id': 'Eth 1/1', 'platform': 'N5K-C5596UP', 'device_id': 'ZY_XWGH_1a.domain.com(ABC1234DEFG)', 'remote_ip': '192.168.0.255'}]

        actual_output = self.device.cleanup_cdp_neighbor_output(self.cdp_input_data.splitlines())

        self.assertEqual(len(expected_output), len(actual_output))
        for x, y in zip(expected_output, actual_output):
            self.assertEqual(x['local_iface'], y['local_iface'])
            self.assertEqual(x['port_id'], y['port_id'])
            self.assertEqual(x['platform'], y['platform'])
            self.assertEqual(x['device_id'], y['device_id'])
            self.assertEqual(x['remote_ip'], y['remote_ip'])

if __name__ == '__main__':
    unittest.main()
