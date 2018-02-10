from app.device_classes.device_definitions.cisco_base_device import CiscoBaseDevice
import re
import xml.etree.cElementTree as ET
try:
    from StringIO import StringIO  # Python 2
except ImportError:
    from io import StringIO  # Python 3
from app.scripts_bank.lib.functions import containsSkipped


class CiscoNXOS(CiscoBaseDevice):
    """Class for NX-OS type devices from vendor Cisco."""

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

    def pull_run_config(self, activeSession):
        """Retrieve running configuration on device."""
        command = self.cmd_run_config()
        return self.get_cmd_output(command, activeSession)

    def pull_start_config(self, activeSession):
        """Retrieve startup configuration on device."""
        command = self.cmd_start_config()
        return self.get_cmd_output(command, activeSession)

    def pull_cdp_neighbor(self, activeSession):
        """Retrieve CDP/LLDP neighbor information from device.

        This should be redone using XML pulls/parsing.
        """
        command = self.cmd_cdp_neighbor()
        result = self.get_cmd_output(command, activeSession)
        return self.cleanup_cdp_neighbor_output(result)

    def pull_interface_config(self, activeSession):
        """Retrieve configuration for interface on device."""
        command = "show run interface %s | exclude version | exclude Command | exclude !" % (self.interface)
        return self.get_cmd_output(command, activeSession)

    def pull_interface_mac_addresses(self, activeSession):
        """Retrieve MAC address table for interface on device."""
        # This is needed because if interface is a vlan, then a different command is used
        if 'Vlan' in self.interface:
            # The interface will read as 'Vlan#', and the command requires a space between 'Vlan' and '#'
            command = "show mac address-table %s | xml" % (self.interface.replace('Vlan', 'Vlan '))
        else:
            command = "show mac address-table interface %s | xml" % (self.interface)
        # command = "show mac address-table interface %s | exclude VLAN | exclude Legend" % (self.interface)
        result = self.run_ssh_command(command, activeSession)

        # If unable to pull interfaces, return False for both variables
        if self.check_invalid_input_detected(result) or containsSkipped(result) or not result:
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
        outputResult = ''
        command = "show interface status | xml"
        result = self.run_ssh_command(command, activeSession)

        # If unable to pull interfaces, return False for both variables
        if containsSkipped(result) or not result:
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
            nameStatus = False
            for elem in root.iter():
                if a:
                    if not elem.tag.isspace() and not elem.text.isspace():
                        # This is in case there is no name/description:
                        # Reset counter var to True on each loop back to a new 'interface'
                        if elem.tag == 'interface':
                            nameStatus = True
                        # Name input provided, set var to False to skip the '--' ahead
                        elif elem.tag == 'name':
                            nameStatus = False
                        # No Name column provided, use '--' instead
                        elif elem.tag == 'state' and nameStatus:
                            outputResult = outputResult + 'ip,--,'

                        # Skip certain columns
                        if elem.tag == 'vlan' or elem.tag == 'duplex' or elem.tag == 'type':
                            pass
                        # Placeholder 'ip' for upcoming IP address lookup in new function
                        elif elem.tag == 'name':
                            # Truncate description (name column) to 25 characters only
                            outputResult = outputResult + 'ip,' + elem.text[:25] + ','
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
                            outputResult = outputResult + elem.text + ','
                        # Otherwise store output to string
                        else:
                            outputResult = outputResult + elem.text + ','

                # This is to skip the first instance of "ROW_interface" in the XML output
                if elem.tag == 'ROW_interface':
                    outputResult = outputResult + '\n'
                    a = True

            command = 'sh run int | egrep interface|ip.address | ex passive | ex !'

            result = self.run_ssh_command(command, activeSession)

            # Set intStatus var to False initially
            intStatus = 0
            # Keeps track of the name of the interface we're on currently
            currentInt = ''
            realIP = ''
            realIPList = []
            # This extracts the IP addresses for each interface, and inserts them into the outputResult string
            for x in result.splitlines():
                # Line is an interface
                if 'interface' in x:
                    currentInt = x.split(' ')
                    intStatus += 1

                # No IP address, so use '--' instead
                if 'interface' in x and intStatus == 2:
                    # Reset counter
                    intStatus = 1
                    a = currentInt[1] + ',ip'
                    b = currentInt[1] + ',--'
                else:
                    realIPList = x.split(' ')
                    realIP = realIPList[-1]
                    a = currentInt[1] + ',ip'
                    b = currentInt[1] + ',' + realIP
                    outputResult = outputResult.replace(a, b)

            # Cleanup any remaining instances of 'ip' in outputResult
            outputResult = outputResult.replace(',ip,', ',--,')
            # Return interfaces
            # return tableHeader, outputResult.splitlines()
            totalResult = self.cleanup_nxos_output(outputResult)
            return totalResult

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
            elif 'down' in x['status']:
                data['down'] += 1
            elif 'up' in x['status']:
                data['up'] += 1

            data['total'] += 1

        return data

    def get_interface_status(self, interface):
        """Return status of interface."""
        down_strings = ['down', 'notconnect', 'noOperMembers', 'sfpAbsent']

        if 'disabled' in interface:
            return 'disabled'
        elif any(x in interface for x in down_strings):
            return 'down'
        elif 'connected' in interface:
            return 'up'
        else:
            return 'unknown'
