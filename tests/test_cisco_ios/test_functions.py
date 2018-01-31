import unittest
from app.device_classes.device_definitions.cisco.cisco_ios import CiscoIOS


class TestCiscoIOS(unittest.TestCase):
    """CI testing class for Cisco IOS devices."""

    def setUp(self):
        """Initialize static class testing variables."""
        self.device = CiscoIOS('na', 'na', 'na', 'na', 'na', 'na')

        self.interface_input_data = '''
Interface              IP-Address      OK? Method Status                Protocol
Vlan1                  192.168.0.1     YES DHCP   up                    up
FastEthernet1/0/1      unassigned      YES NVRAM  up                    down
FastEthernet1/0/2      unassigned      YES unset  down                  down
FastEthernet1/0/3      unassigned      YES unset  administratively down down
'''

        self.interface_expected_output = [{'status': 'up', 'name': 'Vlan1',
                                           'address': '192.168.0.1', 'protocol': 'up',
                                           'method': 'DHCP'},
                                          {'status': 'up', 'name': 'FastEthernet1/0/1',
                                           'address': 'unassigned', 'protocol': 'down',
                                           'method': 'NVRAM'},
                                          {'status': 'down', 'name': 'FastEthernet1/0/2',
                                           'address': 'unassigned', 'protocol': 'down',
                                           'method': 'unset'},
                                          {'status': 'administratively', 'name': 'FastEthernet1/0/3',
                                           'address': 'unassigned', 'protocol': 'down',
                                           'method': 'unset'}]

    def test_cleanup_ios_output(self):
        """Test IOS interface output cleanup function."""
        actual_output = self.device.cleanup_ios_output(self.interface_input_data)

        self.assertEqual(actual_output, self.interface_expected_output)

    def test_count_interface_status(self):
        """Test count_interface_status function."""
        count_interface_status_comparison = {'down': 2,
                                             'disabled': 1,
                                             'total': 4,
                                             'up': 1}

        actual_output = self.device.count_interface_status(self.interface_expected_output)
        self.assertEqual(actual_output, count_interface_status_comparison)

    def atest_iosxe_cdp_neighbor_formatting(self):
        """Test IOS-XE CDP neighbor output formatting."""
        expected_output = [{'local_iface': 'Ten 1/1/12', 'port_id': 'Gig 2/0/52', 'hold_time': '157', 'platform': 'WS-C2960X', 'device_id': 'IOSSWITCH123.DOMAIN.COM'},
                           {'local_iface': 'Ten 1/0/8', 'port_id': 'Gig 1/0/10', 'hold_time': '126', 'platform': 'WS-C2960G', 'device_id': 'ROUTER123.DOMAIN.COM'},
                           {'local_iface': 'Fas 2/1/32', 'port_id': 'Eth 3/15', 'hold_time': '135', 'platform': 'N5K-C6103', 'device_id': 'BIGSWITCH1.domain.com(SERIAL12345)'},
                           {'local_iface': 'Ten 1/1/2', 'port_id': 'Eth 3/15', 'hold_time': '132', 'platform': 'WS-C2960X', 'device_id': '12-34-56-78.domain.com'},
                           {'local_iface': 'Gig 1/1/31', 'port_id': 'Ten 1/1/1', 'hold_time': '10', 'platform': 'WS-C3750X', 'device_id': 'Switch-Router-123.DOMAIN.COM'},
                           {'local_iface': 'Eth 1/0/9', 'port_id': 'Gig 1/0/5', 'hold_time': '2', 'platform': 'WS-C3850X', 'device_id': 'OFFICE-ABCDEF'},
                           {'local_iface': 'Ten 1/1/11', 'port_id': 'Gig 4/0/14', 'hold_time': '148', 'platform': 'WS-C4509R', 'device_id': 'DATACENTER-AB'},
                           {'local_iface': 'Eth 2/3/4', 'port_id': 'Fas 2/0/1', 'hold_time': '135', 'platform': 'AL-1751VR', 'device_id': 'abcd1234.domain.com'}]

        actual_output = self.device.cleanup_cdp_neighbor_output(self.iosxe_cdp_input_data.splitlines())

        self.assertEqual(len(expected_output), len(actual_output))
        for x, y in zip(expected_output, actual_output):
            self.assertEqual(x['local_iface'], y['local_iface'])
            self.assertEqual(x['port_id'], y['port_id'])
            self.assertEqual(x['hold_time'], y['hold_time'])
            self.assertEqual(x['platform'], y['platform'])
            self.assertEqual(x['device_id'], y['device_id'])


if __name__ == '__main__':
    unittest.main()
