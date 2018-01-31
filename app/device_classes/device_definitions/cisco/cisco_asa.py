from app.device_classes.device_definitions.cisco_base_device import CiscoBaseDevice


class CiscoASA(CiscoBaseDevice):
    """Class for ASA type devices from vendor Cisco."""

    def cmd_run_config(self):
        """Return command to display running configuration on device."""
        command = 'show running-config'
        return command

    def cmd_start_config(self):
        """Return command to display startup configuration on device."""
        command = 'show startup-config'
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
        """Not supported on ASA's, so intentionally returns blank string."""
        return ''

    def pull_interface_config(self, activeSession):
        """Retrieve configuration for interface on device."""
        command = "show run interface %s | exclude configuration|!" % (self.interface)
        return self.get_cmd_output(command, activeSession)

    def pull_interface_mac_addresses(self, activeSession):
        """Not supported on ASA's, so intentionally returns blank string."""
        return ''

    def pull_interface_statistics(self, activeSession):
        """Retrieve statistics for interface on device."""
        command = "show interface %s" % (self.interface)
        return self.get_cmd_output(command, activeSession)

    def pull_interface_info(self, activeSession):
        """Retrieve various informational command output for interface on device."""
        intConfig = self.pull_interface_config(activeSession)
        intMacAddr = self.pull_interface_mac_addresses(activeSession)
        intStats = self.pull_interface_statistics(activeSession)

        return intConfig, intMacAddr, intStats

    def pull_device_uptime(self, activeSession):
        """Retrieve device uptime."""
        command = 'show version | include up'
        output = self.get_cmd_output(command, activeSession)
        for x in output:
            if 'failover' in x:
                break
            elif 'file' in x:
                pass
            else:
                uptime = x.split(' ', 2)[2]
        return uptime

    def pull_host_interfaces(self, activeSession):
        """Retrieve list of interfaces on device."""
        result = self.run_ssh_command('show interface ip brief', activeSession)
        return self.cleanup_ios_output(result)

    def count_interface_status(self, interfaces):
        """Return count of interfaces.

        Up is total number of up/active interfaces.
        Down is total number of down/inactive interfaces.
        Disable is total number of administratively down/manually disabled interfaces.
        """
        data = {}
        data['up'] = data['down'] = data['disabled'] = data['total'] = 0

        for x in interfaces:
            if 'administratively' in x['status']:
                data['disabled'] += 1
            elif 'down' in x['protocol']:
                data['down'] += 1
            elif 'up' in x['status'] and 'up' in x['protocol']:
                data['up'] += 1
            elif 'manual deleted' in x['status']:
                data['total'] -= 1

            data['total'] += 1

        return data
