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
        # result = self.run_ssh_command('show interface ip brief', activeSession)
        result = self.run_ssh_command('show interface detail', activeSession)
        return self.cleanup_asa_output(result)

    def count_interface_status(self, interfaces):
        """Return count of interfaces.

        Up is total number of up/active interfaces.
        Down is total number of down/inactive interfaces.
        Disable is total number of administratively down/manually disabled interfaces.
        """
        data = {}
        data['up'] = data['down'] = data['disabled'] = data['total'] = 0

        for x in interfaces:
            if 'admin' in x['status']:
                data['disabled'] += 1
            elif 'down' in x['protocol']:
                data['down'] += 1
            elif 'up' in x['status'] and 'up' in x['protocol']:
                data['up'] += 1
            elif 'manual deleted' in x['status']:
                data['total'] -= 1

            data['total'] += 1

        return data

    def clean_interface_description(self, x):
        """Create description if doesn't exist. Truncate as necessary."""
        # If no description was configured, manually set it to an empty string
        try:
            x['description']
        except KeyError:
            # Set to '--' if empty
            x['description'] = "--"
        # Truncate description to 25 characters if longer then 25 characters
        return (x['description'][:25] + '..') if len(x['description']) > 25 else x['description'].strip()

    def cleanup_asa_output(self, asaOutput):
        """Clean up returned ASA output from 'show ip interface brief'."""
        data = []
        # Used to set if we're on the first loop or not
        notFirstLoop = False

        for line in asaOutput.splitlines():
            try:
                # This is the first line of each new interface
                if "line protocol is" in line:
                    # If on first loop, skip
                    if notFirstLoop:
                        interface['description'] = self.clean_interface_description(interface)
                        data.append(interface)
                    else:
                        # Set 'notFirstLoop' to True now
                        notFirstLoop = True
                    # Create new empty interface dict
                    interface = {}
                    # Split on commas
                    x = line.split()
                    interface['name'] = x[1]
                    # If interface is administratively down
                    if "admin" in x[4]:
                        interface['status'] = "admin down"
                    else:
                        interface['status'] = x[4].strip(',')
                    interface['protocol'] = x[-1]
                elif "IP address" in line:
                    x = line.split()
                    interface['address'] = x[2].strip(',')
                elif "Description" in line:
                    # Remove the word "Description" from line, keep rest of string
                    interface['description'] = line.replace('Description:', '').strip()
            except IndexError:
                continue

        # If no description was configured, manually set it to an empty string
        interface['description'] = self.clean_interface_description(interface)
        # Needed for last interface in output
        data.append(interface)
        return data
