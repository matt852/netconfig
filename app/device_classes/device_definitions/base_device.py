#!/usr/bin/python3

from app.scripts_bank.lib.netmiko_functions import run_multiple_ssh_commands_in_session


class BaseDevice(object):
    """Base device object for all device vendors and models."""

    def __init__(self, id, hostname, ipv4_addr, device_type, ios_type, local_creds):
        """Initialization function."""
        self.id = id
        self.hostname = hostname
        self.ipv4_addr = ipv4_addr
        self.device_type = device_type
        self.ios_type = ios_type
        self.local_creds = local_creds

    def __del__(self):
        """Deletion function."""
        pass

    def save_config_on_device(self, active_session):
        """Return results from saving configuration on device."""
        return active_session.save_config()

    def reset_session_mode(self, active_session):
        """Check if existing SSH session is in config mode.

        If so, exits config mode.
        """
        if active_session.exit_config_mode():
            # Return True if successful
            return True
        else:
            # Return False if session is not in config mode
            return False

    def revert_session_mode(self, active_session, originalState):
        """Revert SSH session to config mode if it was previously in config mode.

        Not currently used.
        """
        if originalState and not active_session.check_config_mode():
            active_session.enter_config_mode()
        elif active_session.check_config_mode() and not originalState:
            active_session.exit_config_mode()

    def run_ssh_command(self, command, active_session):
        """Execute single command on device using existing SSH session."""
        # Run command
        result = active_session.send_command(command)
        # Run check for invalid input detected, etc
        if "Invalid input detected" in result:
            # Command failed, possibly due to being in configuration mode.  Exit config mode
            active_session.exit_config_mode()
            # Try to retrieve command results again
            try:
                result = self.run_ssh_command(command, active_session)
                # If command still failed, return nothing
                if "Invalid input detected" in result:
                    return ''
            except:
                # If failure to access SSH channel or run command, return nothing
                return ''

        # Return command output
        return result

    def run_ssh_config_commands(self, cmdList, active_session):
        """Execute configuration commands on device.

        Execute one or more configuration commands on device.
        Commands provided via array, with each command on it's own array row.
        Uses existing SSH session.
        """
        return active_session.send_config_set(cmdList).splitlines()

    def run_multiple_commands(self, command, active_session):
        """Execute multiple commands on device using existing SSH session."""
        newCmd = []
        for x in command.splitlines():
            newCmd.append(x)
        run_multiple_ssh_commands_in_session(newCmd, active_session)

    def run_multiple_config_commands(self, command, active_session):
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
        result = self.run_ssh_config_commands(newCmd, active_session)
        saveResult = self.save_config_on_device(active_session)
        for x in saveResult:
            result.append(x)
        return result

    def get_cmd_output(self, command, active_session):
        """Get SSH command output and returns it as an array.

        Executes command on device using existing SSH session.
        Stores and returns output in an array.
        Each array row is separated by newline.
        """
        return self.run_ssh_command(command, active_session).splitlines()

    def get_cmd_output_with_commas(self, command, active_session):
        """Execute command on device and replaces spaces with commas.

        Executes command on device using existing SSH session.
        Stores and returns output in an array.
        Replaces all spaces in returned output with commas.
        Each array row is separated by newline.
        """
        result = self.run_ssh_command(command, active_session)
        return result.replace("  ", ",").splitlines()

    def find_prompt_in_session(self, active_session):
        """Return device prompt from existing SSH session."""
        return active_session.find_prompt()

    def replace_double_spaces_commas(self, x):
        """Replace all double spaces in provided string with a single comma."""
        x = x.replace("  ", ",,")
        while ",," in x:
            x = x.replace(",,", ",")
        return x
