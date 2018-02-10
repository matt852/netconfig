import unittest
from app.device_classes.device_definitions.cisco.cisco_nxos import CiscoNXOS


class TestCiscoNXOS(unittest.TestCase):
    """CI testing class for Cisco NXOS devices."""

    def setUp(self):
        """Initialize static class testing variables."""
        self.device = CiscoNXOS('na', 'na', 'na', 'na', 'na', 'na')

    def test_replace_double_spaces_commas(self):
        """Test function for replacing all double spaces in provided input with commas."""
        input_data = '      a   bc    d e ff ghij   k  l m   '
        expected_output = ',a, bc,d e ff ghij, k,l m, '
        actual_output = self.device.replace_double_spaces_commas(input_data)
        self.assertEqual(actual_output, expected_output)


if __name__ == '__main__':
    unittest.main()