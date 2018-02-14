import unittest
from app.device_classes.device_definitions.cisco.cisco_nxos import CiscoNXOS


class TestCiscoNXOS(unittest.TestCase):
    """CI testing class for Cisco NXOS devices."""

    def setUp(self):
        """Initialize static class testing variables."""
        self.device = CiscoNXOS('na', 'na', 'na', 'na', 'na', 'na')

        self.interface_input_data = '''

mgmt0,--,--,connected,1 Gbps,
Ethernet3/1,10.1.2.3,Uplink 3/1,notconnect,10 Gbps,
Ethernet5/6,--,Testing,down,100 Mbps,
TenGigabitEthernet3/2,--,Description 1/11,sfpAbsent,1 Gbps,
Vlan234,192.168.0.1,--,disabled,Auto,
port-channel10,--,--,noOperMembers,Auto,
'''

        self.interface_expected_output = [{'status': 'connected', 'protocol': 'up',
                                           'description': '--', 'address': '--', 'name': 'mgmt0'},
                                          {'status': 'notconnect', 'protocol': 'down',
                                           'description': 'Uplink 3/1', 'address': '10.1.2.3', 'name': 'Ethernet3/1'},
                                          {'status': 'down', 'protocol': 'down',
                                           'description': 'Testing', 'address': '--', 'name': 'Ethernet5/6'},
                                          {'status': 'sfpAbsent', 'protocol': 'down',
                                           'description': 'Description 1/11', 'address': '--', 'name': 'TenGigabitEthernet3/2'},
                                          {'status': 'disabled', 'protocol': 'down',
                                           'description': '--', 'address': '192.168.0.1', 'name': 'Vlan234'},
                                          {'status': 'noOperMembers', 'protocol': 'down',
                                           'description': '--', 'address': '--', 'name': 'port-channel10'}]

    def test_cleanup_nxos_output(self):
        """Test IOS interface output cleanup function."""
        actual_output = self.device.cleanup_nxos_output(self.interface_input_data)

        self.assertEqual(actual_output, self.interface_expected_output)

    def test_count_interface_status(self):
        """Test count_interface_status function."""
        count_interface_status_comparison = {'down': 4,
                                             'disabled': 1,
                                             'total': 6,
                                             'up': 1}

        actual_output = self.device.count_interface_status(self.interface_expected_output)
        self.assertEqual(actual_output, count_interface_status_comparison)

    def test_replace_double_spaces_commas(self):
        """Test function for replacing all double spaces in provided input with commas."""
        input_data = '      a   bc    d e ff ghij   k  l m   '
        expected_output = ',a, bc,d e ff ghij, k,l m, '
        actual_output = self.device.replace_double_spaces_commas(input_data)
        self.assertEqual(actual_output, expected_output)


if __name__ == '__main__':
    unittest.main()