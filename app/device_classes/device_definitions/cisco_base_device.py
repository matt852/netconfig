from base_device import BaseDevice
from ...scripts_bank.lib import functions as fn


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

    def cleanup_ios_output(self, x):
        """Clean up returned IOS output from 'show ip interface brief'."""
        x = x.replace('OK?', '')
        x = x.replace('Method', '')
        x = x.replace('YES', '')
        x = x.replace('NO', '')
        x = x.replace('unset', '')
        x = x.replace('NVRAM', '')
        x = x.replace('IPCP', '')
        x = x.replace('CONFIG', '')
        x = x.replace('TFTP', '')
        x = x.replace('manual', '')
        x = self.replace_double_spaces_commas(x)
        x = x.replace('down down', 'down,down')
        x = x.replace(' unassigned', ',unassigned')
        x = x.replace('unassigned ', 'unassigned,')
        return x

    def cleanup_nxos_output(self, x):
        """Clean up returned NX-OS output from 'show ip interface brief'."""
        x = x.replace(' connected', ',connected')
        x = x.replace('connected ', 'connected,')
        x = x.replace(' sfpAbsent', ',sfpAbsent')
        x = x.replace('sfpAbsent ', 'sfpAbsent,')
        x = x.replace(' noOperMem', ',noOperMem')
        x = x.replace('noOperMem ', 'noOperMem,')
        x = x.replace(' disabled', ',disabled')
        x = x.replace('disabled ', 'disabled,')
        x = x.replace(' down', ',down')
        x = x.replace('down ', 'down,')
        x = x.replace(' notconnec', ',notconnec')
        x = x.replace('notconnec ', 'notconnec,')
        x = x.replace(' linkFlapE', ',linkFlapE')
        x = x.replace('linkFlapE ', 'linkFlapE,')
        return x

    def cleanup_cdp_neighbor_output(self, result):
        """Clean up returned 'show cdp neighbor' output."""
        field1 = []
        # Stores table headers as string
        tableHeader = ''
        # Stores table body data as array
        tableBody = []

        for index, line in enumerate(result):
            # Index is index of current loop
            # Line is each line output from the provided 'result' array
            # Temporarily stores each body string, for insertion into above header
            bodyString = ''
            # This is needed in case the hostname is too long and is returned on its own line
            if ',' not in line:
                field1.append(line)
            # If this is the first line, it is the table header
            elif index == 0:
                # These 2 'replace' lines are for NX-OS output
                line = line.replace('Intrfce Hldtme', 'Intrfce,Hldtme')
                line = line.replace('Hldtme Capability', 'Hldtme,Capability')
                # Store table header line in string, with commas to separate fields
                tableHeader = line
            # If line isn't empty, and the word 'Device' is not in the line (for non-needed terminal output)
            elif line and 'Device' not in line:
                # This is needed in case the hostname is too long and is returned on its own line
                if field1:
                    bodyString += field1[0] + ','
                    field1.remove(field1[0])
                # Clean up IOS output
                line = line.replace(' Gig', ',Gig')
                line = line.replace(' Ten', ',Ten')
                line = line.replace(' Fas', ',Fas')
                line = line.replace(' Eth', ',Eth')
                # This line is for IOS Polycom phones
                line = line.replace(' Port ', ',Port ')
                # This line is for NX-OS output
                line = line.replace(' eth ', ',eth ')
                # Clean up whitespace in front of words
                line = line.replace(' ,', ',')
                # If empty space at start of string, it's misinterpreted as a word
                line = line.replace(',,', ',')

                # This is needed in case the capability column comes right next to the platform column,
                #  then there is no comma separating the two, only a whitespace.
                # Count commas in tableHead

                # if same # of commans in line, continue
                # Possible interface names in last column
                interfaceNames = ['Eth', 'eth', 'Ten', 'ten', 'Gig', 'gig', 'Fas', 'fas', 'Port', 'port', 'Mgmt', 'mgmt']
                if tableHeader.count(',') != line.count(','):
                    lineSplit = line.split(',')
                    decrementCounter = -1
                    nextWord = False
                    # If any interface names in the word in line, counting backwards using commas as separators
                    #  This is because some platforms display interfaces as "Eth1/1", others as "Eth 1/1"
                    # We don't use 'a' here.  We just have a for loop so we only run the length of the string,
                    #  and not encounter an accidental infinite loop.
                    for a in lineSplit:
                        if nextWord:
                            lineSplit[decrementCounter] = fn.rreplace(lineSplit[decrementCounter], ' ', ',', 1)
                            break
                        # If true, then the next word needs the last whitespace occurance replaced with a comma
                        if any(x in lineSplit[decrementCounter] for x in interfaceNames):
                            nextWord = True
                        decrementCounter -= 1

                    newLine = ''
                    for x in lineSplit:
                        if ',' in x:
                            y = x.split(',')
                            for z in y:
                                newLine += ',' + z
                        else:
                            newLine += ',' + x

                    bodyString += newLine
                else:
                    # Add cleaned up string to end of bodyString, to append to tableBody array later
                    bodyString += line
                # Add cleaned up output string to returned tableBody array
                tableBody.append(bodyString)

        # Return tableHeader as string, tableBody as array, with each word in a line separated by a comma
        return tableHeader, tableBody

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
        return self.split_on_newline(self.run_ssh_command(command, activeSession))

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
        return self.split_on_newline(self.run_ssh_command(command, activeSession))

    def pull_version(self, activeSession):
        """Pull device version.

        Pulls device version.
        Returns output as array with each new line on a separate row.
        """
        command = self.cmd_show_version()
        return self.split_on_newline(self.run_ssh_command(command, activeSession))
