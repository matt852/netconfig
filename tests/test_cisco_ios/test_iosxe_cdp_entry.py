import unittest
from app.device_classes.device_definitions.cisco.cisco_ios import CiscoIOS


class TestCiscoIOS(unittest.TestCase):
    """CI testing class for Cisco IOS devices."""

    def setUp(self):
        """Initialize static class testing variables."""
        self.device = CiscoIOS('na', 'na', 'na', 'na', 'na', 'na')

        self.cdp_input_data = '''
-------------------------
Device ID: SWITCH-ABCD-123.DOMAIN.COM
Entry address(es):
  IP address: 10.0.0.1
Platform: cisco WS-C2960X-48FPS-L,  Capabilities: Switch IGMP
Interface: TenGigabitEthernet1/2/3,  Port ID (outgoing port): GigabitEthernet1/2/3
Holdtime : 144 sec

Version :
Cisco IOS Software, C2960X Software (C2960X-UNIVERSALK9-M), Version 12.3(4)E5, RELEASE SOFTWARE (fc3)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2000 by Cisco Systems, Inc.
Compiled Mon 01-JAN-00 00:01 by prod_rel_team

advertisement version: 1
Protocol Hello:  OUI=0x00000C, Protocol ID=0x0112; payload len=27, value=00000000FFFFFFFF0102250B000000000000AC7E8A2E0580FF0000
VTP Management Domain: 'abc123'
Native VLAN: 1
Duplex: full
Management address(es):
  IP address: 10.0.0.1
Unidirectional Mode: off

-------------------------
Device ID: ROUTER-12-AB-34.domain.com
Entry address(es):
  IP address: 172.16.0.1
Platform: cisco WS-C3750X-24FPS-L,  Capabilities: Switch IGMP
Interface: TenGigabitEthernet1/1/1,  Port ID (outgoing port): GigabitEthernet2/2/2
Holdtime : 176 sec

Version :
Cisco IOS Software, C3750X Software (C3750X-UNIVERSALK9-M), Version 12.3(4)E5, RELEASE SOFTWARE (fc0)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2000 by Cisco Systems, Inc.
Compiled Mon 01-JAN-00 00:01 by prod_rel_team

advertisement version: 2
Protocol Hello:  OUI=0x00000C, Protocol ID=0x0112; payload len=27, value=00000000FFFFFFFF01022503000000000000AC7E8A550780FF0000
VTP Management Domain: 'none'
Native VLAN: 2
Duplex: full
Management address(es):
  IP address: 172.16.0.1
Unidirectional Mode: off

-------------------------
Device ID: SwitchName
Entry address(es):
  IP address: 192.168.0.1
Platform: WS-C3750X-24FPS-L,  Capabilities: Switch IGMP
Interface: Ethernet1/2/3,  Port ID (outgoing port): FastEthernet5/0/49
Holdtime : 157 sec

Version :
Cisco IOS Software, C3750X Software (C3750X-UNIVERSALK9-M), Version 12.3(4)E5, RELEASE SOFTWARE (fc0)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2000 by Cisco Systems, Inc.
Compiled Mon 01-JAN-00 00:01 by prod_rel_team

advertisement version: 3
Protocol Hello:  OUI=0x00000C, Protocol ID=0x0112; payload len=27, value=00000000FFFFFFFF01022503000000000000AC7E8A550780FF0000
Native VLAN: 3
Duplex: full
Management address(es):
  IP address: 192.168.0.1
Unidirectional Mode: off

'''

    def test_iosxe_cdp_neighbor_formatting(self):
        """Test IOS-XE CDP neighbor output formatting."""
        expected_output = [{'local_iface': 'Ten 1/2/3', 'port_id': 'Gig 1/2/3', 'platform': 'cisco WS-C2960X-48FPS-L', 'device_id': 'SWITCH-ABCD-123.DOMAIN.COM', 'remote_ip': '10.0.0.1'},
                           {'local_iface': 'Ten 1/1/1', 'port_id': 'Gig 2/2/2', 'platform': 'cisco WS-C3750X-24FPS-L', 'device_id': 'ROUTER-12-AB-34.domain.com', 'remote_ip': '172.16.0.1'},
                           {'local_iface': 'Eth 1/2/3', 'port_id': 'Fas 5/0/49', 'platform': 'WS-C3750X-24FPS-L', 'device_id': 'SwitchName', 'remote_ip': '192.168.0.1'}]

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
