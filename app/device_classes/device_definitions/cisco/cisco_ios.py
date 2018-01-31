import re
from app.device_classes.device_definitions.cisco_base_device import CiscoBaseDevice


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
        command = "show cdp entry *"
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
        result = self.get_cmd_output(command, activeSession)
        return self.cleanup_cdp_neighbor_output(result)

    def pull_interface_config(self, activeSession):
        """Retrieve configuration for interface on device."""
        command = "show run interface %s | exclude configuration|!" % (self.interface)
        return self.get_cmd_output(command, activeSession)

    def pull_interface_mac_addresses(self, activeSession):
        """Retrieve MAC address table for interface on device."""
        # TODO: This entire function needs to be better optimized
        #  Possibly split into two functions: one each for IOS and IOS-XE
        command = "show mac address-table interface %s" % (self.interface)
        for a in range(2):
            result = self.run_ssh_command(command, activeSession)
            if self.check_invalid_input_detected(result):
                command = "show mac-address-table interface %s" % (self.interface)
                continue
            else:
                break
        if self.check_invalid_input_detected(result):
            return '', ''
        else:
            # Stores table body data as array
            tableBody = []
            data = []

            # Remove any asterisks
            result = result.replace('*', '')

            # In IOS-XE, there are multiple protocols separated by commas.
            # Separate these by underscores instead to preserve formatting in HTML output
            result = result.replace(',', '_')
            result = self.replace_double_spaces_commas(result).splitlines()

            for index, line in enumerate(result):
                # This is primarily for IOS-XE devices.  We only want Unicast Entries
                # We want to stop output once we reach Multicast Entries
                if 'Unicast Entries' in line:
                    # Do not store this line as output
                    pass
                elif 'Multicast Entries' in line:
                    # We are done with Unicast entries, so break out of loop
                    break
                # Loop until header is filled, as the header isn't always in the very first line
                # elif not data['tableHeader'] and ',' in line:
                #     # Skip this iteration if there's only a single comma.  The header should have multiple fields
                #     if line.count(',') > 1:
                #         # Store table header line in string, with commas to separate fields
                #         data['tableHeader'] = line
                elif line and 'Mac' not in line and '--' not in line:
                    # Regexp to search for any substring in line that contains an underscore.
                    # Then replaces the whitespace around it with commas.
                    # This is for IOS-XE devices with multiple protocols that interface with HTML formatting.
                    regExp = re.compile(r'\s[a-zA-Z0-9]*_[a-zA-Z0-9_]*\s')
                    if regExp.search(line):
                        # Save matched string to variable
                        regexMatchList = regExp.findall(line)
                        # Strip first and last character (whitespace) of string
                        regexMatchStr = regexMatchList[0][1:-1]
                        # Add commas back in to beginning and end of line
                        regexMatchStr = ',' + regexMatchStr + ','
                        # Insert modified substring back into line
                        line = re.sub(regExp, regexMatchStr, line)

                    # Remove any single spaces in front of commas
                    line = line.replace(' ,', ',')
                    tableBody.append(line)

            # Different output for IOS vs IOS-XE.  Need to cleanup
            for line in tableBody:
                # Skip IOS-XE header
                if 'protocols' not in line:
                    # Split line on commas
                    x = line.split(',')
                    # Remove empty fields from string, specifically if first field is empty (1-2 digit vlan causes this)
                    x = filter(None, x)
                    if x:
                        y = {}
                        y['vlan'] = x[0].strip()
                        y['macAddr'] = x[1].strip()
                        if self.ios_type == 'cisco_ios':
                            y['port'] = x[3].strip()
                        else:
                            y['port'] = x[4].strip()
                        # Assign dictionary to list, for use in HTML page
                        data.append(y)
            return data

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
        command = 'show version | include uptime'
        uptime = self.get_cmd_output(command, activeSession)
        for x in uptime:
            output = x.split(' ', 3)[-1]
        return output

    def pull_host_interfaces(self, activeSession):
        """Retrieve list of interfaces on device."""
        result = self.run_ssh_command('show ip interface brief', activeSession)

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
