from unittest import main, TestCase
from mock import MagicMock


class TestSSHHandler(TestCase):
    """Unit testing for SSH handler class."""

    ssh = {}

    def setUp(self):
        """Initialize static class testing variables."""
        self.ssh = {'1--ABCDUUID1': 'NetmikoObject-1'}
        self.mock = MagicMock()
        self.session = {'UUID': 'ABCUUID1'}

    def tearDown(self):
        """Run on completion of tests."""
        self.ssh = None
        self.session['UUID'] = None

    def test_get_ssh_key_for_device(self):
        """Validate returning SSH key for looking up existing SSH sessions for a specific device.

        Also validate storing SSH Dict key as device.id followed by '-' followed by username and return.
        """
        pass

    def test_check_device_active_ssh_session(self):
        """Validate checking if existing SSH session for device is currently active."""
        pass

    def test_check_device_existing_ssh_session(self):
        """Validate checking if device currenty has an existing SSH session saved."""
        pass

    def test_retrieve_ssh_session(self):
        """Test connecting to 'device' over SSH.  Store session for use later.

        Return active SSH session for provided device if it exists.
        Otherwise gets a session, stores it, and returns it.
        """
        pass

    def test_disconnect_specific_ssh_session(self):
        """Validate disconnecting any SSH sessions for a specific device from all users."""
        pass

    def test_disconnect_all_ssh_sessions(self):
        """Validate disconnecting all remaining active SSH sessions tied to a user."""
        pass

    def test_count_all_ssh_sessions(self):
        """Validate returning number of active SSH sessions tied to user."""
        pass

    # @mock.patch('app.datahandler.get_device_by_id')
    def test_get_names_of_ssh_session_devices(self):
        """Validate getting names of devices with SSH connection stored by ID."""
        pass
        '''
        mock_getdeviceid_func_patcher = patch('app.datahandler.get_device_by_id')

        # Start patching 'app.datahandler.get_device_by_id'.
        mock_getdeviceid_func = mock_getdeviceid_func_patcher.start()

        # Configure the mock to return a name of a test device.
        mock_getdeviceid_func.return_value = Mock(["Test-Device-1"])

        # Call the function to test.
        deviceList = self.ssh.get_names_of_ssh_session_devices()

        # Stop patching.
        mock_getdeviceid_func_patcher.stop()

        # Assert that the returned value completed successfully.
        self.assertEqual(deviceList, "Test-Device-1")
        '''


if __name__ == "__main__":
    main()
