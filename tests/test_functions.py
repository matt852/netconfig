import unittest
from app.scripts_bank.lib.functions import contains_skipped, remove_dict_key, set_user_credentials, is_integer


class TestFunctions(unittest.TestCase):
    """CI testing class for Cisco IOS devices."""

    def setUp(self):
        """Initialize static class testing variables."""
        pass

    def test_setUserCredentials(self):
        """Test creds class is returned properly."""
        actual_output = set_user_credentials("admin", "Password1", "Priv2")
        self.assertEqual(actual_output.un, "admin")
        self.assertEqual(actual_output.pw, "Password1")
        self.assertEqual(actual_output.priv, "Priv2")

    def test_containsSkipped(self):
        """Test function if the word 'skipped' is in the provided string."""
        input_data = "Unable to connect - skipped connection attempt."
        actual_output = contains_skipped(input_data)
        expected_output = True

        self.assertEqual(actual_output, expected_output)
        self.assertIsInstance(actual_output, bool)

    def test_removeDictKey(self):
        """Test removal of key from dictionary."""
        testDict = {"name": "Cisco", "type": "switch"}
        testKey = "name"
        actual_output = remove_dict_key(testDict, testKey)
        expected_output = {"type": "switch"}

        self.assertEqual(actual_output, expected_output)
        self.assertIsInstance(actual_output, dict)

    def test_isInteger(self):
        """Test function for determining if a provided variable is an integer."""
        test_values = [1, '58', '90173', '1a', 'abc', 'bca1', '2.', ' ']
        expected_output = [True, True, True, False, False, False, False, False]
        actual_output = []
        for x in test_values:
            actual_output.append(is_integer(x))
        self.assertEqual(actual_output, expected_output)


if __name__ == '__main__':
    unittest.main()
