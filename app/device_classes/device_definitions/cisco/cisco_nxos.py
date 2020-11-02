#!/usr/bin/python3

from app.device_classes.device_definitions.cisco_base_device import CiscoBaseDevice
from app.scripts_bank.lib.functions import contains_skipped
from io import StringIO
import re
import xml.etree.cElementTree as ET


class CiscoNXOS(CiscoBaseDevice):
    """Class for NX-OS type devices from vendor Cisco."""

    def __init__(self):
        super(CiscoNXOS, self).__init__()

    def cmd_run_config(self):
        """Return command to display running configuration on device."""
        command = 'show running-config | exclude !'
        return command

    def cmd_start_config(self):
        """Return command to display startup configuration on device."""
        command = 'show startup-config | exclude !'
        return command

    def cmd_cdp_neighbor(self):
        """Return command to display CDP/LLDP neighbors on device."""
        command = 'show cdp entry all'
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
        """Retrieve CDP/LLDP neighbor information from device.

        This should be redone using XML pulls/parsing.
        """
        command = self.cmd_cdp_neighbor()
        result = self.get_cmd_output(command, active_session)
        return self.cleanup_cdp_neighbor_output(result)

    def pull_interface_config(self, active_session):
        """Retrieve configuration for interface on device."""
        command = "show run interface %s | exclude version | exclude Command | exclude !" % (self.interface)
        return self.get_cmd_output(command, active_session)

    def pull_interface_mac_addresses(self, active_session):
        """Retrieve MAC address table for interface on device."""
        # This is needed because if interface is a vlan, then a different command is used
        if 'Vlan' in self.interface:
            # The interface will read as 'Vlan#', and the command requires a space between 'Vlan' and '#'
            command = "show mac address-table %s | xml" % (self.interface.replace('Vlan', 'Vlan '))
        else:
            command = "show mac address-table interface %s | xml" % (self.interface)
        # command = "show mac address-table interface %s | exclude VLAN | exclude Legend" % (self.interface)
        result = self.run_ssh_command(command, active_session)

        # If unable to pull interfaces, return False for both variables
        if self.check_invalid_input_detected(result) or contains_skipped(result) or not result:
            return False
        else:
            data = []
            result = re.findall("\<\?xml.*reply\>", result, re.DOTALL)
            # Strip namespaces
            it = ET.iterparse(StringIO(result[0]))
            for _, el in it:
                if '}' in el.tag:
                    el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
            root = it.root

            # This variable is to skip the first instance of "ROW_mac_address" in the XML output
            a = False
            device = {}
            for elem in root.iter():
                if a:
                    if not elem.tag.isspace() and not elem.text.isspace():
                        # Placeholder 'ip' for upcoming IP address lookup in new function
                        if elem.tag == 'disp_mac_addr':
                            device['macAddr'] = elem.text
                        elif elem.tag == 'disp_vlan':
                            device['vlan'] = elem.text
                        elif elem.tag == 'disp_port':
                            device['port'] = elem.text

                # Save data to dictionary and reset it to null for next loop iteration
                if elem.tag == 'ROW_mac_address':
                    if device:
                        data.append(device)
                    device = {}
                    a = True

        # Needed for last device in XML list
        data.append(device)
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
        # Return empty result - unsupported on NX-OS
        return {}

    def pull_device_interfaces(self, active_session):
        """Retrieve list of interfaces on device."""
        output_result = ''
        command = "show interface status | xml"
        result = self.run_ssh_command(command, active_session)

        # If unable to pull interfaces, return False for both variables
        if contains_skipped(result) or not result:
            return False, False
        else:
            result = re.findall("\<\?xml.*reply\>", result, re.DOTALL)
            # Strip namespaces
            it = ET.iterparse(StringIO(result[0]))
            for _, el in it:
                if '}' in el.tag:
                    el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
            root = it.root

            # This variable is to skip the first instance of "ROW_interface" in the XML output
            a = False
            name_status = False
            for elem in root.iter():
                if a:
                    if not elem.tag.isspace() and not elem.text.isspace():
                        # This is in case there is no name/description:
                        # Reset counter var to True on each loop back to a new 'interface'
                        if elem.tag == 'interface':
                            name_status = True
                        # Name input provided, set var to False to skip the '--' ahead
                        elif elem.tag == 'name':
                            name_status = False
                        # No Name column provided, use '--' instead
                        elif elem.tag == 'state' and name_status:
                            output_result = output_result + 'ip,--,'

                        # Skip certain columns
                        if elem.tag == 'vlan' or elem.tag == 'duplex' or elem.tag == 'type':
                            pass
                        # Placeholder 'ip' for upcoming IP address lookup in new function
                        elif elem.tag == 'name':
                            # Truncate description (name column) to 25 characters only
                            output_result = output_result + 'ip,' + elem.text[:25] + ','
                        elif elem.tag == 'speed':
                            if elem.text == 'a-1000' or elem.text == '1000':
                                elem.text = '1 Gbps'
                            elif elem.text == 'auto':
                                elem.text = 'Auto'
                            elif elem.text == 'a-10G' or elem.text == '10G':
                                elem.text = '10 Gbps'
                            elif elem.text == 'a-100' or elem.text == '100':
                                elem.text = '100 Mbps'
                            else:
                                pass
                            output_result = output_result + elem.text + ','
                        # Otherwise store output to string
                        else:
                            output_result = output_result + elem.text + ','

                # This is to skip the first instance of "ROW_interface" in the XML output
                if elem.tag == 'ROW_interface':
                    output_result = output_result + '\n'
                    a = True

            command = 'sh run int | egrep interface|ip.address | ex passive | ex !'

            result = self.run_ssh_command(command, active_session)

            # Set int_status var to False initially
            int_status = 0
            # Keeps track of the name of the interface we're on currently
            current_int = ''
            real_ip = ''
            real_ip_list = []
            # This extracts the IP addresses for each interface, and inserts them into the output_result string
            for x in result.splitlines():
                # Line is an interface
                if 'interface' in x:
                    current_int = x.split(' ')
                    int_status += 1

                # No IP address, so use '--' instead
                if 'interface' in x and int_status == 2:
                    # Reset counter
                    int_status = 1
                    a = current_int[1] + ',ip'
                    b = current_int[1] + ',--'
                else:
                    real_ip_list = x.split(' ')
                    real_ip = real_ip_list[-1]
                    a = current_int[1] + ',ip'
                    b = current_int[1] + ',' + real_ip
                    output_result = output_result.replace(a, b)

            # Cleanup any remaining instances of 'ip' in output_result
            output_result = output_result.replace(',ip,', ',--,')
            # Return interfaces
            # return tableHeader, output_result.splitlines()
            total_result = self.cleanup_nxos_output(output_result)
            return total_result

    def count_interface_status(self, interfaces):
        """Return count of interfaces.

        Up is total number of up/active interfaces.
        Down is total number of down/inactive interfaces.
        Disable is total number of administratively down/manually disabled interfaces.
        Total is total number of interfaces counted.
        """
        data = {}
        data['up'] = data['down'] = data['disabled'] = data['total'] = 0

        for x in interfaces:
            if 'disabled' in x['status']:
                data['disabled'] += 1
            elif 'down' in x['protocol']:
                data['down'] += 1
            elif 'up' in x['protocol']:
                data['up'] += 1

            data['total'] += 1

        return data

    def get_interface_status(self, interface):
        """Return status of interface."""
        down_strings = ['down', 'notconnect', 'noOperMembers', 'sfpAbsent', 'disabled']

        if any(x in interface for x in down_strings):
            return 'down'
        elif 'connected' in interface:
            return 'up'
        else:
            return 'unknown'

    def cleanup_nxos_output(self, nxos_output):
        """Clean up returned NX-OS output from 'show ip interface brief'."""
        data = []

        for line in nxos_output.splitlines():
            if line:
                x = line.split(',')
                try:
                    interface = {}
                    interface['name'] = x[0]
                    interface['address'] = x[1]
                    # Truncate description to 25 characters if longer then 25 characters
                    interface['description'] = (x[2][:25] + '..') if len(x[2]) > 25 else x[2]
                    # Set to '--' if empty
                    interface['description'] = interface['description'] or '--'
                    interface['status'] = x[3]
                    interface['protocol'] = self.get_interface_status(x[3])
                    data.append(interface)
                except IndexError:
                    continue

        return data
