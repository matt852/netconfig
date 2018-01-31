from app.scripts_bank.lib.netmiko_functions import runMultipleSSHCommandsInSession


class BaseDevice(object):
    """Base device object for all device vendors and models."""

    def __init__(self, id, hostname, ipv4_addr, type, ios_type, local_creds):
        """Initialization function."""
        self.id = id
        self.hostname = hostname
        self.ipv4_addr = ipv4_addr
        self.type = type
        self.ios_type = ios_type
        self.local_creds = local_creds

    def __del__(self):
        """Deletion function."""
        pass

    def reset_session_mode(self, activeSession):
        """Check if existing SSH session is in config mode.

        If so, exits config mode.
        """
        if activeSession.check_config_mode():
            self.exit_config_mode(activeSession)
            # Return True since session was originally in config mode
            return True
        # Return False if session is not in config mode
        return False

    def revert_session_mode(self, activeSession, originalState):
        """Revert SSH session to config mode if it was previously in config mode.

        Not currently used.
        """
        if originalState and not activeSession.check_config_mode():
            self.enter_config_mode(activeSession)
        elif activeSession.check_config_mode() and not originalState:
            self.exit_config_mode()

    def run_ssh_command(self, command, activeSession):
        """Execute single command on device using existing SSH session."""
        # Exit config mode if existing session is currently in config mode
        self.reset_session_mode(activeSession)

        # Run command and return command output
        return activeSession.send_command(command)

    def run_ssh_config_commands(self, cmdList, activeSession):
        """Execute configuration commands on device.

        Execute one or more configuration commands on device.
        Commands provided via array, with each command on it's own array row.
        Uses existing SSH session.
        """
        return activeSession.send_config_set(cmdList).splitlines()

    def run_multiple_commands(self, command, activeSession):
        """Execute multiple commands on device using existing SSH session."""
        newCmd = []
        for x in command.splitlines():
            newCmd.append(x)
        runMultipleSSHCommandsInSession(newCmd, activeSession)

    def run_multiple_config_commands(self, command, activeSession):
        """Execute multiple configuration commands on device.

        Execute multiple configuration commands on device.
        Commands provided via array, with each command on it's own array row.
        Saves configuration settings to memory on device once completed.
        Uses existing SSH session.
        """
        newCmd = []
        for x in command.splitlines():
            newCmd.append(x)
        # Get command output from network device
        result = self.run_ssh_config_commands(newCmd, activeSession)
        saveResult = self.save_config_on_device(activeSession)
        for x in saveResult:
            result.append(x)
        return result

    def get_cmd_output(self, command, activeSession):
        """Get SSH command output and returns it as an array.

        Executes command on device using existing SSH session.
        Stores and returns output in an array.
        Each array row is separated by newline.
        """
        return self.run_ssh_command(command, activeSession).splitlines()

    def get_cmd_output_with_commas(self, command, activeSession):
        """Execute command on device and replaces spaces with commas.

        Executes command on device using existing SSH session.
        Stores and returns output in an array.
        Replaces all spaces in returned output with commas.
        Each array row is separated by newline.
        """
        result = self.run_ssh_command(command, activeSession)
        return result.replace("  ", ",").splitlines()

    def find_prompt_in_session(self, activeSession):
        """Return device prompt from existing SSH session."""
        return activeSession.find_prompt()

    def replace_double_spaces_commas(self, x):
        """Replace all double spaces in provided string with a single comma."""
        x = x.replace("  ", ",,")
        while ",," in x:
            x = x.replace(",,", ",")
        return x
