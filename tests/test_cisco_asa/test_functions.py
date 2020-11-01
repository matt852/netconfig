import unittest
from app.device_classes.device_definitions.cisco.cisco_asa import CiscoASA
try:
    import mock
except ImportError:
    from unittest import mock


class TestCiscoASA(unittest.TestCase):
    """CI testing class for Cisco ASA devices."""

    def setUp(self):
        """Initialize static class testing variables."""
        self.device = CiscoASA('na', 'na', 'na', 'na', 'na', 'na')

        self.interface_input_data = '''
Interface GigabitEthernet0/0 "outside", is up, line protocol is up
  Hardware is i82574L rev00, BW 1000 Mbps, DLY 10 usec
	Full-Duplex(Full-duplex), 100 Mbps(100 Mbps)
	Input flow control is unsupported, output flow control is off
	Description: Outside interface test description AB/CD:EF
	MAC address 1234.5678.90ab, MTU 1500
	IP address 12.34.56.78, subnet mask 255.255.255.0
	580891374 packets input, 141402675747 bytes, 0 no buffer
	Received 827649 broadcasts, 0 runts, 0 giants
	0 input errors, 0 CRC, 0 frame, 0 overrun, 0 ignored, 0 abort
	0 pause input, 0 resume input
	0 L2 decode drops
	531622184 packets output, 459437300629 bytes, 0 underruns
	0 pause output, 0 resume output
	0 output errors, 0 collisions, 2 interface resets
	0 late collisions, 0 deferred
	0 input reset drops, 0 output reset drops
	input queue (blocks free curr/low): hardware (495/435)
	output queue (blocks free curr/low): hardware (511/365)
  Traffic Statistics for "outside":
	988545884 packets input, 238178577470 bytes
        531622184 packets output, 449867306524 bytes
	606500 packets dropped
      1 minute input rate 293 pkts/sec,  51475 bytes/sec
      1 minute output rate 111 pkts/sec,  26283 bytes/sec
      1 minute drop rate, 0 pkts/sec
      5 minute input rate 339 pkts/sec,  86060 bytes/sec
      5 minute output rate 133 pkts/sec,  34761 bytes/sec
      5 minute drop rate, 0 pkts/sec
  Control Point Interface States:
	Interface number is 3
	Interface config status is active
	Interface state is active
Interface GigabitEthernet0/1 "inside", is down, line protocol is down
  Hardware is i82574L rev00, BW 1000 Mbps, DLY 10 usec
	Auto-Duplex(Full-duplex), Auto-Speed(1000 Mbps)
	Input flow control is unsupported, output flow control is off
	Description: Inside interface test to router
	MAC address 1234.5678.90ab, MTU 1500
	IP address 10.1.2.3, subnet mask 255.255.255.0
	577364917 packets input, 434450698481 bytes, 0 no buffer
        Received 19516407 broadcasts, 0 runts, 0 giants
	0 input errors, 0 CRC, 0 frame, 0 overrun, 0 ignored, 0 abort
	0 pause input, 0 resume input
	0 L2 decode drops
	653407727 packets output, 151389571032 bytes, 0 underruns
	0 pause output, 0 resume output
	0 output errors, 0 collisions, 2 interface resets
	0 late collisions, 0 deferred
	0 input reset drops, 0 output reset drops
	input queue (blocks free curr/low): hardware (475/362)
	output queue (blocks free curr/low): hardware (510/94)
  Traffic Statistics for "inside":
	577363868 packets input, 423771904711 bytes
	653407727 packets output, 138892399047 bytes
	1542397 packets dropped
      1 minute input rate 225 pkts/sec,  30718 bytes/sec
      1 minute output rate 369 pkts/sec,  65976 bytes/sec
      1 minute drop rate, 2 pkts/sec
      5 minute input rate 193 pkts/sec,  31598 bytes/sec
      5 minute output rate 286 pkts/sec,  68438 bytes/sec
      5 minute drop rate, 1 pkts/sec
  Control Point Interface States:
	Interface number is 4
	Interface config status is active
	Interface state is active
Interface GigabitEthernet0/2 "", is administratively down, line protocol is down
  Hardware is i82574L rev00, BW 1000 Mbps, DLY 10 usec
	Auto-Duplex, Auto-Speed
	Input flow control is unsupported, output flow control is off
	Available but not configured via nameif
	MAC address 1234.5678.90ab, MTU not set
	IP address unassigned
	0 packets input, 0 bytes, 0 no buffer
	Received 0 broadcasts, 0 runts, 0 giants
	0 input errors, 0 CRC, 0 frame, 0 overrun, 0 ignored, 0 abort
	0 pause input, 0 resume input
	0 L2 decode drops
	0 packets output, 0 bytes, 0 underruns
	0 pause output, 0 resume output
	0 output errors, 0 collisions, 2 interface resets
        0 late collisions, 0 deferred
	0 input reset drops, 0 output reset drops
	input queue (blocks free curr/low): hardware (511/511)
	output queue (blocks free curr/low): hardware (511/511)
  Control Point Interface States:
	Interface number is 5
	Interface config status is not active
	Interface state is not active
'''

        self.interface_expected_output = [{'status': 'up', 'name': 'GigabitEthernet0/0',
                                           'address': '12.34.56.78', 'protocol': 'up',
                                           'description': 'Outside interface test de..'},
                                          {'status': 'down', 'name': 'GigabitEthernet0/1',
                                           'address': '10.1.2.3', 'protocol': 'down',
                                           'description': 'Inside interface test to ..'},
                                          {'status': 'admin down', 'name': 'GigabitEthernet0/2',
                                           'address': 'unassigned', 'protocol': 'down',
                                           'description': '--'}]

    def test_cleanup_asa_output(self):
        """Test ASA interface output cleanup function."""
        self.assertEqual(self.device.cleanup_asa_output(self.interface_input_data), self.interface_expected_output)

    def test_count_interface_status(self):
        """Test count_interface_status function."""
        expected_output = {'down': 1, 'disabled': 1, 'total': 3, 'up': 1}
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

    def test_clean_interface_description(self):
        """Test creating description if doesn't exist. Truncate as necessary."""
        input_data = {}
        # Test over 3 different iterations
        for x in range(3):
            if x == 0:
                input_data['description'] = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
                expected_output = 'ABCDEFGHIJKLMNOPQRSTUVWXY..'
            elif x == 1:
                input_data['description'] = 'ABCDEFG'
                expected_output = 'ABCDEFG'
            elif x == 2:
                input_data['description'] = ''
                expected_output = ''
            actual_output = self.device.clean_interface_description(input_data)
            self.assertEqual(actual_output, expected_output)

    @mock.patch.object(CiscoASA, 'run_ssh_command')
    def test_pull_device_poe_status(self, mocked_method):
        """Test MAC address table formatting."""
        mocked_method.return_value = '''
                         ^
ERROR: % Invalid input detected at '^' marker.
'''

        asa_expected_output = {}

        self.assertEqual(self.device.pull_device_poe_status(None), asa_expected_output)


if __name__ == '__main__':
    unittest.main()
