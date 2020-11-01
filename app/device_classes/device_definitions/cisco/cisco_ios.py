#!/usr/bin/python3

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

    def pull_run_config(self, active_session):
        """Retrieve running configuration on device."""
        command = self.cmd_run_config()
        return self.get_cmd_output(command, active_session)

    def pull_start_config(self, active_session):
        """Retrieve startup configuration on device."""
        command = self.cmd_start_config()
        return self.get_cmd_output(command, active_session)

    def pull_cdp_neighbor(self, active_session):
        """Retrieve CDP/LLDP neighbor information from device."""
        command = self.cmd_cdp_neighbor()
        result = self.get_cmd_output(command, active_session)
        return self.cleanup_cdp_neighbor_output(result)

    def pull_interface_config(self, active_session):
        """Retrieve configuration for interface on device."""
        command = "show run interface %s | exclude configuration|!" % (self.interface)
        return self.get_cmd_output(command, active_session)

    def pull_interface_mac_addresses(self, active_session):
        """Retrieve MAC address table for interface on device."""
        # TODO: This entire function needs to be better optimized
        #  Possibly split into two functions: one each for IOS and IOS-XE
        command = "show mac address-table interface %s" % (self.interface)
        for a in range(2):
            result = self.run_ssh_command(command, active_session)
            if self.check_invalid_input_detected(result):
                command = "show mac-address-table interface %s" % (self.interface)
                continue
            else:
                break
        if self.check_invalid_input_detected(result):
            return '', ''
        else:
            # Stores table body data as array
            table_body = []
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
                    reg_exp = re.compile(r'\s[a-zA-Z0-9]*_[a-zA-Z0-9_]*\s')
                    if reg_exp.search(line):
                        # Save matched string to variable
                        regex_match_list = reg_exp.findall(line)
                        # Strip first and last character (whitespace) of string
                        regex_match_str = regex_match_list[0][1:-1]
                        # Add commas back in to beginning and end of line
                        regex_match_str = ',' + regex_match_str + ','
                        # Insert modified substring back into line
                        line = re.sub(reg_exp, regex_match_str, line)

                    # Remove any single spaces in front of commas
                    line = line.replace(' ,', ',')
                    table_body.append(line)

            # Different output for IOS vs IOS-XE.  Need to cleanup
            for line in table_body:
                # Skip IOS-XE header
                if 'protocols' not in line:
                    # Split line on commas
                    x = line.split(',')
                    # Remove empty fields from string, specifically if first field is empty (1-2 digit vlan causes this)
                    x = list(filter(None, x))
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

    def pull_interface_statistics(self, active_session):
        """Retrieve statistics for interface on device."""
        command = "show interface %s" % (self.interface)
        return self.get_cmd_output(command, active_session)

    def pull_interface_info(self, active_session):
        """Retrieve various informational command output for interface on device."""
        int_config = self.pull_interface_config(active_session)
        int_mac_addr = self.pull_interface_mac_addresses(active_session)
        int_stats = self.pull_interface_statistics(active_session)

        return int_config, int_mac_addr, int_stats

    def pull_device_uptime(self, active_session):
        """Retrieve device uptime."""
        command = 'show version | include uptime'
        uptime = self.get_cmd_output(command, active_session)
        for x in uptime:
            output = x.split(' ', 3)[-1]
        return output

    def pull_device_poe_status(self, active_session):  # TODO - WRITE TEST FOR
        """Retrieve PoE status for all interfaces."""
        status = {}
        command = 'show power inline | begin Interface'
        result = self.get_cmd_output(command, active_session)
        check_strings = ['Interface', 'Watts', '---']

        # If output returned from command execution, parse output
        if result:
            for x in result:
                # If any string from check_strings in line, or line is blank, skip to next loop iteration
                if any(y in x for y in check_strings) or not x:
                    continue
                line = x.split()

                # Convert interface short abbreviation to long name
                reg_exp = re.compile(r'[A-Z][a-z][0-9]\/')
                if reg_exp.search(line[0]):
                    if line[0][0] == 'G':
                        line[0] = line[0].replace('Gi', 'GigabitEthernet')
                    elif line[0][0] == 'F':
                        line[0] = line[0].replace('Fa', 'FastEthernet')
                    elif line[0][0] == 'T':
                        line[0] = line[0].replace('Te', 'TenGigabitEthernet')
                    elif line[0][0] == 'E':
                        line[0] = line[0].replace('Eth', 'Ethernet')

                # Line[0] is interface name
                # Line[2] is operational status
                status[line[0]] = line[2]
        # Return dictionary with results
        return status

    def pull_device_interfaces(self, active_session):
        """Retrieve list of interfaces on device."""
        result_a = self.run_ssh_command('show ip interface brief', active_session)
        result_b = self.run_ssh_command('show interface description', active_session)

        return self.cleanup_ios_output(result_a, result_b)

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

    def cleanup_ios_output(self, ios_output_a, ios_output_b):
        """Clean up returned IOS output from 'show ip interface brief'."""
        data = []

        for a, b in zip(ios_output_a.splitlines(), ios_output_b.splitlines()):
            try:
                x = a.split()  # show ip interface brief output
                y = b.split()  # show interface description output
                if x[0] == "Interface":
                    continue
                else:
                    interface = {}
                    desc_line = ''
                    interface['name'] = x[0]
                    interface['address'] = x[1]
                    if 'admin' in y[1]:
                        interface['status'] = y[1] + " " + y[2]
                        interface['protocol'] = y[3]
                        # Get all elements from 4th index onward, but combine into readable string
                        for z in y[4:]:
                            desc_line = desc_line + str(z) + " "
                    else:
                        interface['status'] = y[1]
                        interface['protocol'] = y[2]
                        # Get all elements from 3rd index onward, but combine into readable string
                        for z in y[3:]:
                            desc_line = desc_line + str(z) + " "
                    # Truncate description to 25 characters if longer then 25 characters
                    interface['description'] = (desc_line[:25] + '..') if len(desc_line) > 25 else desc_line.strip()
                    # Set to '--' if empty
                    interface['description'] = interface['description'] or '--'
                    data.append(interface)
            except IndexError:
                continue

        return data
