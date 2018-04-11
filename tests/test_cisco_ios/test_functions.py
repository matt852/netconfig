import unittest
from app.device_classes.device_definitions.cisco.cisco_ios import CiscoIOS
try:
    import mock
except ImportError:
    from unittest import mock


class TestCiscoIOS(unittest.TestCase):
    """CI testing class for Cisco IOS devices."""

    def setUp(self):
        """Initialize static class testing variables."""
        self.device = CiscoIOS('na', 'na', 'na', 'na', 'na', 'na')

        self.interface_input_dataA = '''
Interface              IP-Address      OK? Method Status                Protocol
Vlan1                  192.168.0.1     YES DHCP   up                    up
FastEthernet1/0/1      unassigned      YES NVRAM  up                    down
FastEthernet1/0/2      unassigned      YES unset  down                  down
FastEthernet1/0/3      unassigned      YES unset  administratively down down
'''
        self.interface_input_dataB = '''
Interface                      Status         Protocol Description
Vl1                            up             up
Fa1/0/1                        up             down
Fa1/0/2                        down           down
Fa1/0/3                        admin down     down     Connection to ABC Switch
'''

        self.interface_expected_output = [{'status': 'up', 'name': 'Vlan1',
                                           'address': '192.168.0.1', 'protocol': 'up',
                                           'description': '--'},
                                          {'status': 'up', 'name': 'FastEthernet1/0/1',
                                           'address': 'unassigned', 'protocol': 'down',
                                           'description': '--'},
                                          {'status': 'down', 'name': 'FastEthernet1/0/2',
                                           'address': 'unassigned', 'protocol': 'down',
                                           'description': '--'},
                                          {'status': 'admin down', 'name': 'FastEthernet1/0/3',
                                           'address': 'unassigned', 'protocol': 'down',
                                           'description': 'Connection to ABC Switch'}]

    def tearDown(self):
        """Tear down values in memory once completed."""
        self.device = None
        self.interface_input_dataA = None
        self.interface_input_dataB = None
        self.interface_expected_output = None

    def test_cleanup_ios_output(self):
        """Test IOS interface output cleanup function."""
        actual_output = self.device.cleanup_ios_output(self.interface_input_dataA, self.interface_input_dataB)

        self.assertEqual(actual_output, self.interface_expected_output)

    def test_count_interface_status(self):
        """Test count_interface_status function."""
        count_interface_status_comparison = {'down': 2,
                                             'disabled': 1,
                                             'total': 4,
                                             'up': 1}

        actual_output = self.device.count_interface_status(self.interface_expected_output)
        self.assertEqual(actual_output, count_interface_status_comparison)

    def test_replace_double_spaces_commas(self):
        """Test function for replacing all double spaces in provided input with commas."""
        input_data = '      a   bc    d e ff ghij   k  l m   '
        expected_output = ',a, bc,d e ff ghij, k,l m, '
        actual_output = self.device.replace_double_spaces_commas(input_data)
        self.assertEqual(actual_output, expected_output)

    def test_rename_cdp_interfaces(self):
        """Test function to cleanup interface wording."""
        self.assertEqual(self.device.renameCDPInterfaces('TenGigabitEthernet'), 'Ten ')
        self.assertEqual(self.device.renameCDPInterfaces('GigabitEthernet'), 'Gig ')
        self.assertEqual(self.device.renameCDPInterfaces('FastEthernet'), 'Fas ')
        self.assertEqual(self.device.renameCDPInterfaces('Ethernet'), 'Eth ')
        self.assertEqual(self.device.renameCDPInterfaces('Test123'), 'Test123')

    @mock.patch.object(CiscoIOS, 'run_ssh_command')
    def test_pull_device_poe_status(self, mocked_method):
        """Test MAC address table formatting."""
        self.device.ios_type = 'cisco_ios'
        mocked_method.return_value = '''
Interface Admin  Oper       Power   Device              Class Max
                            (Watts)
--------- ------ ---------- ------- ------------------- ----- ----
Gi1/0/1   auto   off        0.0     n/a                 n/a   30.0
Gi1/0/2   auto   on         3.9     Polycom SoundPoint  2     30.0
Gi1/0/3   auto   off        0.0     n/a                 n/a   30.0
Interface Admin  Oper       Power   Device              Class Max
                            (Watts)
--------- ------ ---------- ------- ------------------- ----- ----
Gi2/0/1   auto   off        0.0     n/a                 n/a   30.0
Gi2/0/2   auto   on         6.0     IP Phone 6789       1     30.0
'''

        ios_expected_output = {'GigabitEthernet1/0/1': 'off',
                               'GigabitEthernet2/0/2': 'on',
                               'GigabitEthernet1/0/3': 'off',
                               'GigabitEthernet1/0/2': 'on',
                               'GigabitEthernet2/0/1': 'off'}

        self.assertEqual(self.device.pull_device_poe_status(None), ios_expected_output)

if __name__ == '__main__':
    unittest.main()
