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
        # This needs to be defined for the test
        self.device.interface = None

    @mock.patch.object(CiscoIOS, 'run_ssh_command')
    def test_IOS_pull_interface_mac_addresses(self, mocked_method):
        """Test MAC address table formatting."""
        self.device.ios_type = 'cisco_ios'
        mocked_method.return_value = '''
          Mac Address Table
-------------------------------------------

Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
   1    1234.5678.90ab    DYNAMIC     Po1
  10    90ab.1234.5678    DYNAMIC     Gi1/0/1
 100    5678.90ab.1234    DYNAMIC     Po100
        '''

        ios_expected_output = [{'vlan': '1', 'macAddr': '1234.5678.90ab', 'port': 'Po1'},
                               {'vlan': '10', 'macAddr': '90ab.1234.5678', 'port': 'Gi1/0/1'},
                               {'vlan': '100', 'macAddr': '5678.90ab.1234', 'port': 'Po100'}]

        self.assertEqual(self.device.pull_interface_mac_addresses(None), ios_expected_output)

    @mock.patch.object(CiscoIOS, 'run_ssh_command')
    def test_IOSXE_pull_interface_mac_addresses(self, mocked_method):
        """Test MAC address table formatting."""
        self.device.ios_type = 'cisco_xe'
        mocked_method.return_value = '''
Unicast Entries
 vlan     mac address     type        protocols               port
---------+---------------+--------+---------------------+-------------------------
   1      1234.5678.90ab   dynamic ip,ipx,assigned,other Port-channel1
  10      90ab.1234.5678   dynamic ip,ipx,assigned,other TenGigabitEthernet1/0/1
 100      5678.90ab.1234   dynamic ip,ipx,assigned,other Port-channel100

Multicast Entries
 vlan     mac address     type    ports
---------+---------------+-------+--------------------------------------------
   1      aaaa.bbbb.cccc   system Te1/1/1,Te1/1/2,Te1/1/3,Te1/1/4,Te1/1/5
                                  Po1,Po10,Po100
        '''

        iosxe_expected_output = [{'vlan': '1', 'macAddr': '1234.5678.90ab', 'port': 'Port-channel1'},
                                 {'vlan': '10', 'macAddr': '90ab.1234.5678', 'port': 'TenGigabitEthernet1/0/1'},
                                 {'vlan': '100', 'macAddr': '5678.90ab.1234', 'port': 'Port-channel100'}]

        self.assertEqual(self.device.pull_interface_mac_addresses(None), iosxe_expected_output)

if __name__ == '__main__':
    unittest.main()
