from base_device import BaseDevice
from ...scripts_bank.lib import netmiko_functions as nfn
from ...scripts_bank.lib import functions as fn
from flask import g, session

class CiscoBaseDevice(BaseDevice):

	def check_invalid_input_detected(self, x):
		if "Invalid input detected" in x:
			return True
		else:
			return False

	def get_cmd_enter_configuration_mode(self): #required
		command = "config term"
		return command

	def get_cmd_enable_interface(self): #required
		command = "no shutdown"
		return command

	def get_cmd_disable_interface(self): #required
		command = "shutdown"
		return command

	def cleanup_ios_output(self, x):
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

	def run_enable_interface_cmd(self, interface, activeSession):
		cmdList = []
		cmdList.append("interface %s" % interface)
		cmdList.append("%s" % (self.get_cmd_enable_interface()))
		cmdList.append("end")

		return self.run_ssh_config_commands(cmdList, activeSession)

	def run_disable_interface_cmd(self, interface, activeSession):
		cmdList = []
		cmdList.append("interface %s" % interface)
		cmdList.append("%s" % (self.get_cmd_disable_interface()))
		cmdList.append("end")

		return self.run_ssh_config_commands(cmdList, activeSession)

	def get_save_config_cmd(self):
		if self.ios_type == 'cisco_nxos':
			return "copy running-config startup-config"
		else:
			return "write memory"

	def save_config_on_device(self, activeSession): #required
		command = self.get_save_config_cmd()
		return self.split_on_newline(nfn.runSSHCommandInSession(command, activeSession))

	def run_edit_interface_cmd(self, interface, datavlan, voicevlan, other, activeSession):
		cmdList=[]
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
		cmdList.append(self.get_save_config_cmd())

		return self.run_ssh_config_commands(cmdList, activeSession)

	def cmd_show_inventory(self):
		command = 'show inventory'
		return command

	def cmd_show_version(self):
		command = 'show version'
		return command

	def pull_inventory(self, activeSession): #required
		command = self.cmd_show_inventory()
		return self.split_on_newline(self.run_ssh_command(command, activeSession))

	def pull_version(self, activeSession): #required
		command = self.cmd_show_version()
		return self.split_on_newline(self.run_ssh_command(command, activeSession))


