from .base_device import BaseDevice


class CiscoBaseDevice(BaseDevice):
    """Base class for network device vendor Cisco."""

    def check_invalid_input_detected(self, x):
        """Check for invalid input when executing command on device."""
        if "Invalid input detected" in x:
            return True
        else:
            return False

    def get_cmd_enter_configuration_mode(self):
        """Return command for entering configuration mode."""
        command = "config term"
        return command

    def get_cmd_exit_configuration_mode(self):
        """Return command for exiting configuration mode."""
        command = "end"
        return command

    def get_cmd_enable_interface(self):
        """Return command for enabling interface on device."""
        command = "no shutdown"
        return command

    def get_cmd_disable_interface(self):
        """Return command for disabling interface on device."""
        command = "shutdown"
        return command

    def cleanup_ios_output(self, iosOutput):
        """Clean up returned IOS output from 'show ip interface brief'."""
        data = []

        for line in iosOutput.splitlines():
            try:
                x = line.split()
                if x[0] == "Interface":
                    continue
                else:
                    interface = {}
                    interface['name'] = x[0]
                    interface['address'] = x[1]
                    interface['method'] = x[3]
                    interface['status'] = x[4]
                    interface['protocol'] = x[5]
                    data.append(interface)
            except IndexError:
                continue

        return data

    def cleanup_nxos_output(self, nxosOutput):
        """Clean up returned NX-OS output from 'show ip interface brief'."""
        data = []

        for line in nxosOutput.splitlines():
            if line:
                x = line.split(',')
                try:
                    interface = {}
                    interface['name'] = x[0]
                    interface['address'] = x[1]
                    interface['description'] = x[2]
                    interface['method'] = ''
                    interface['protocol'] = x[3]
                    interface['status'] = self.get_interface_status(x[3])
                    data.append(interface)
                except IndexError:
                    continue

        return data

    def run_enable_interface_cmd(self, interface, activeSession):
        """Enable interface on device using existing SSH session."""
        cmdList = []
        cmdList.append("interface %s" % interface)
        cmdList.append("%s" % (self.get_cmd_enable_interface()))
        cmdList.append("end")

        return self.run_ssh_config_commands(cmdList, activeSession)

    def run_disable_interface_cmd(self, interface, activeSession):
        """Disable interface on device using existing SSH session."""
        cmdList = []
        cmdList.append("interface %s" % interface)
        cmdList.append("%s" % (self.get_cmd_disable_interface()))
        cmdList.append("end")

        return self.run_ssh_config_commands(cmdList, activeSession)

    def get_save_config_cmd(self):
        """Return command for saving configuration settings on device."""
        if self.ios_type == 'cisco_nxos':
            return "copy running-config startup-config"
        else:
            return "write memory"

    def save_config_on_device(self, activeSession):
        """Return command for saving configuration settings on device."""
        command = self.get_save_config_cmd()
        return self.run_ssh_command(command, activeSession).splitlines()

    def run_edit_interface_cmd(self, interface, datavlan, voicevlan, other, activeSession):
        """Edit interface on device with specified parameters on existing SSH session."""
        cmdList = []
        cmdList.append("interface %s" % interface)

        if datavlan != '0':
            cmdList.append("switchport access vlan %s" % datavlan)
        if voicevlan != '0':
            cmdList.append("switchport voice vlan %s" % voicevlan)
        if other != '0':
            # + is used to represent spaces
            other = other.replace('+', ' ')

            # & is used to represent new lines
            for x in other.split('&'):
                cmdList.append(x)

        cmdList.append("end")

        return self.run_ssh_config_commands(cmdList, activeSession)

    def cmd_show_inventory(self):
        """Return command to display device inventory."""
        command = 'show inventory'
        return command

    def cmd_show_version(self):
        """Return command to display device version."""
        command = 'show version'
        return command

    def pull_inventory(self, activeSession):
        """Pull device inventory.

        Pulls device inventory.
        Returns output as array with each new line on a separate row.
        """
        command = self.cmd_show_inventory()
        return self.run_ssh_command(command, activeSession).splitlines()

    def pull_version(self, activeSession):
        """Pull device version.

        Pulls device version.
        Returns output as array with each new line on a separate row.
        """
        command = self.cmd_show_version()
        return self.run_ssh_command(command, activeSession).splitlines()

    def renameCDPInterfaces(self, x):
        """Cleanup interface wording."""
        x = x.replace('TenGigabitEthernet', 'Ten ')
        x = x.replace('GigabitEthernet', 'Gig ')
        x = x.replace('FastEthernet', 'Fas ')
        x = x.replace('Ethernet', 'Eth ')
        return x

    def cleanup_cdp_neighbor_output(self, inputData):
        """Clean up returned 'show cdp entry *' output."""
        loopStart = ipAddrStart = True
        data = []
        output = {}
        for line in inputData:
            if "----" in line and loopStart:
                # First loop iteration, skip this
                loopStart = False
            elif "Device ID" in line:
                # Get device hostname
                x = line.split(':')
                output['device_id'] = str(x[1].strip())
            elif "IP" in line and "ddress" in line and ipAddrStart:
                # IOS/IOS-XE is 'IP address'.  NX-OS is 'IPv4 Address'.
                # Need to skip 2nd iteration (mgmt) of IP
                x = line.split(':')
                output['remote_ip'] = str(x[1].strip())
                # Set to skip mgmt IP (if present) for device. Only use first IP address if multiple listed
                ipAddrStart = False
            elif "Platform" in line:
                # Get platform.  In same line as capabilities, so split line by comma
                x = line.split(',')
                # We don't want the capabilities, so just get first part (platform)
                y = x[0].split(':')
                output['platform'] = str(y[1].strip())
            elif "Interface" in line:
                # Get local and remote interface
                x = line.split(',')
                # Counter for determining if on local or remote interface
                i = True
                for y in x:
                    # First iteration is local interface, 2nd is remote
                    y = y.split(':')
                    if i:
                        # First iteration
                        output['local_iface'] = self.renameCDPInterfaces(y[1].strip())
                        i = False
                    else:
                        # Second iteration
                        output['port_id'] = self.renameCDPInterfaces(y[1].strip())
            elif "----" in line:
                # End of the device section. Save all output to 'data[]'
                data.append(output)
                # Reset output variable
                output = {}
                # Reset IP address counter
                ipAddrStart = True

        # There is no "----" at end of cmd output.  End of all output section. Save last device output to 'data[]'
        data.append(output)
        return data
