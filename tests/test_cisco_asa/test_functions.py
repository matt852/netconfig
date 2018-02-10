import unittest
from app.device_classes.device_definitions.cisco.cisco_asa import CiscoASA


class TestCiscoASA(unittest.TestCase):
    """CI testing class for Cisco ASA devices."""

    def setUp(self):
        """Initialize static class testing variables."""
        self.device = CiscoASA('na', 'na', 'na', 'na', 'na', 'na')

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

    def test_cleanup_asa_output(self):
        """Test ASA interface output cleanup function."""
        self.assertEqual(self.device.cleanup_ios_output(self.interface_input_data), self.interface_expected_output)

    def test_count_interface_status(self):
        """Test count_interface_status function."""
        expected_output = {'down': 2, 'disabled': 1, 'total': 4, 'up': 1}
        self.assertEqual(self.device.count_interface_status(self.interface_expected_output), expected_output)

    def test_pull_interface_mac_addresses(self):
        """Test pull_interface_mac_addresses function."""
        expected_output = ''
        self.assertEqual(self.device.pull_interface_mac_addresses(None), expected_output)
    
    def test_replace_double_spaces_commas(self):
        """Test function for replacing all double spaces in provided input with commas."""
        input_data = '      a   bc    d e ff ghij   k  l m   '
        expected_output = ',a, bc,d e ff ghij, k,l m, '
        actual_output = self.device.replace_double_spaces_commas(input_data)
        self.assertEqual(actual_output, expected_output)

if __name__ == '__main__':
    unittest.main()
