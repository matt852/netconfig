from ..cisco_base_device import CiscoBaseDevice


class CiscoIOS(CiscoBaseDevice):
    """Class for IOS type devices from vendor Cisco."""

    def cmd_run_config(self):
        """Return command to display running configuration on device."""
        command = 'show running-config'
        return command

    def cmd_start_config(self):
        """Return command to display startup configuration on device."""
        command = 'show startup-config'
        return command

    def cmd_cdp_neighbor(self):
        """Return command to display CDP/LLDP neighbors on device."""
        command = "show cdp neighbors | begin ID"
        return command

    def pull_run_config(self, activeSession):
        """Retrieve running configuration on device."""
        command = self.cmd_run_config()
        return self.get_cmd_output(command, activeSession)

    def pull_start_config(self, activeSession):
        """Retrieve startup configuration on device."""
        command = self.cmd_start_config()
        return self.get_cmd_output(command, activeSession)

    def pull_cdp_neighbor(self, activeSession):
        """Retrieve CDP/LLDP neighbor information from device."""
        command = self.cmd_cdp_neighbor()
        result = self.get_cmd_output_with_commas(command, activeSession)
        tableHeader, tableBody = self.cleanup_cdp_neighbor_output(result)
        return tableHeader, tableBody

    def pull_interface_config(self, activeSession):
        """Retrieve configuration for interface on device."""
        command = "show run interface %s | exclude configuration|!" % (self.interface)
        return self.get_cmd_output(command, activeSession)

    def pull_interface_mac_addresses(self, activeSession):
        """Retrieve MAC address table for interface on device."""
        command = "show mac address-table interface %s" % (self.interface)
        for a in range(2):
            result = self.run_ssh_command(command, activeSession)
            if self.check_invalid_input_detected(result):
                command = "show mac-address-table interface %s" % (self.interface)
                continue
            else:
                break
        if self.check_invalid_input_detected(result):
            return ''
        else:
            return self.split_on_newline(self.replace_double_spaces_commas(result).replace('*', ''))

    def pull_interface_statistics(self, activeSession):
        """Retrieve statistics for interface on device."""
        command = "show interface %s" % (self.interface)
        return self.get_cmd_output(command, activeSession)

    def pull_interface_info(self, activeSession):
        """Retrieve various informational command output for interface on device."""
        intConfig = self.pull_interface_config(activeSession)
        intMac = self.pull_interface_mac_addresses(activeSession)
        intStats = self.pull_interface_statistics(activeSession)

        return intConfig, intMac, intStats

    def pull_device_uptime(self, activeSession):
        """Retrieve device uptime."""
        command = 'show version | include uptime'
        uptime = self.get_cmd_output(command, activeSession)
        for x in uptime:
            output = x.split(' ', 3)[-1]
        return output

    def pull_host_interfaces(self, activeSession):
        """Retrieve list of interfaces on device."""
        command = "show ip interface brief"
        result = self.run_ssh_command(command, activeSession)
        # Returns False if nothing was returned
        if not result:
            return result
        return self.split_on_newline(self.cleanup_ios_output(result))

    def count_interface_status(self, interfaces):
        """Return count of interfaces.

        Up is total number of up/active interfaces.
        Down is total number of down/inactive interfaces.
        Disable is total number of administratively down/manually disabled interfaces.
        Total is total number of interfaces counted.
        """
        up = down = disabled = total = 0
        for interface in interfaces:
            if 'Interface' not in interface:
                if 'administratively down,down' in interface:
                    disabled += 1
                elif 'down,down' in interface:
                    down += 1
                elif 'up,down' in interface:
                    down += 1
                elif 'up,up' in interface:
                    up += 1
                elif 'manual deleted' in interface:
                    total -= 1

                total += 1

        return up, down, disabled, total
