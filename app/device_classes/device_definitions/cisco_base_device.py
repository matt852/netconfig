#!/usr/bin/python3

from app.device_classes.device_definitions.base_device import BaseDevice


class CiscoBaseDevice(BaseDevice):
    """Base class for network device vendor Cisco."""
    
    def __init__(self):
        # TODO: Add Super here and rework classes
        super(CiscoBaseDevice, self).__init__()

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

    def run_enable_interface_cmd(self, interface, active_session):
        """Enable interface on device using existing SSH session."""
        cmd_list = list()
        cmd_list.append("interface %s" % interface)
        cmd_list.append("%s" % (self.get_cmd_enable_interface()))
        cmd_list.append("end")

        return self.run_ssh_config_commands(cmd_list, active_session)

    def run_disable_interface_cmd(self, interface, active_session):
        """Disable interface on device using existing SSH session."""
        cmd_list = list()
        cmd_list.append("interface %s" % interface)
        cmd_list.append("%s" % (self.get_cmd_disable_interface()))
        cmd_list.append("end")

        return self.run_ssh_config_commands(cmd_list, active_session)

    def run_edit_interface_cmd(self, interface, datavlan, voicevlan, other, active_session):
        """Edit interface on device with specified parameters on existing SSH session."""
        cmd_list = list()
        cmd_list.append("interface %s" % interface)

        if datavlan != '0':
            cmd_list.append("switchport access vlan %s" % datavlan)
        if voicevlan != '0':
            cmd_list.append("switchport voice vlan %s" % voicevlan)
        if other != '0':
            # + is used to represent spaces
            other = other.replace('+', ' ')

            # & is used to represent new lines
            for x in other.split('&'):
                cmd_list.append(x)

        cmd_list.append("end")

        return self.run_ssh_config_commands(cmd_list, active_session)

    def cmd_show_inventory(self):
        """Return command to display device inventory."""
        command = 'show inventory'
        return command

    def cmd_show_version(self):
        """Return command to display device version."""
        command = 'show version'
        return command

    def pull_inventory(self, active_session):
        """Pull device inventory.

        Pulls device inventory.
        Returns output as array with each new line on a separate row.
        """
        command = self.cmd_show_inventory()
        return self.run_ssh_command(command, active_session).splitlines()

    def pull_version(self, active_session):
        """Pull device version.

        Pulls device version.
        Returns output as array with each new line on a separate row.
        """
        command = self.cmd_show_version()
        return self.run_ssh_command(command, active_session).splitlines()

    def rename_cdp_interfaces(self, x):
        """Cleanup interface wording."""
        x = x.replace('TenGigabitEthernet', 'Ten ')
        x = x.replace('GigabitEthernet', 'Gig ')
        x = x.replace('FastEthernet', 'Fas ')
        x = x.replace('Ethernet', 'Eth ')
        return x

    def cleanup_cdp_neighbor_output(self, input_data):
        """Clean up returned 'show cdp entry *' output."""
        loop_start = ip_addr_start = True
        data = []
        output = {}
        for line in input_data:
            if "----" in line and loop_start:
                # First loop iteration, skip this
                loop_start = False
            elif "Device ID" in line:
                # Get device hostname
                x = line.split(':')
                output['device_id'] = str(x[1].strip())
            elif "IP" in line and "ddress" in line and ip_addr_start:
                # IOS/IOS-XE is 'IP address'.  NX-OS is 'IPv4 Address'.
                # Need to skip 2nd iteration (mgmt) of IP
                x = line.split(':')
                output['remote_ip'] = str(x[1].strip())
                # Set to skip mgmt IP (if present) for device. Only use first IP address if multiple listed
                ip_addr_start = False
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
                        output['local_iface'] = self.rename_cdp_interfaces(y[1].strip())
                        i = False
                    else:
                        # Second iteration
                        output['port_id'] = self.rename_cdp_interfaces(y[1].strip())
            elif "----" in line:
                # End of the device section. Save all output to 'data[]'
                data.append(output)
                # Reset output variable
                output = {}
                # Reset IP address counter
                ip_addr_start = True

        # There is no "----" at end of cmd output.  End of all output section. Save last device output to 'data[]'
        data.append(output)
        return data
