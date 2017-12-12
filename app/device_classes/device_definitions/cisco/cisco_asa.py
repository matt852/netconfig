from ..cisco_base_device import CiscoBaseDevice

class CiscoASA(CiscoBaseDevice):

	def cmd_run_config(self):
		command = 'show running-config'
		return command

	def cmd_start_config(self):
		command = 'show startup-config'
		return command

	def pull_run_config(self, activeSession): #required
		command = self.cmd_run_config()
		return self.get_cmd_output(command, activeSession)

	def pull_start_config(self, activeSession): #required
		command = self.cmd_start_config()
		return self.get_cmd_output(command, activeSession)

	# Not supported on ASA's
	def pull_cdp_neighbor(self, activeSession): #required
		return ''

	def pull_interface_config(self, activeSession):
		command = "show run interface %s | exclude configuration|!" % (self.interface)
		return self.get_cmd_output(command, activeSession)

	# Not supported on ASA's
	def pull_interface_mac_addresses(self, activeSession):
		return ''

	def pull_interface_statistics(self, activeSession):
		command = "show interface %s" % (self.interface)
		return self.get_cmd_output(command, activeSession)

	def pull_interface_info(self, activeSession):
		intConfig = self.pull_interface_config(activeSession)
		intMac = self.pull_interface_mac_addresses(activeSession)
		intStats = self.pull_interface_statistics(activeSession)

		return intConfig, intMac, intStats

	def pull_device_uptime(self, activeSession):
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
		command = "show interface ip brief"
		result = self.run_ssh_command(command, activeSession)
		# Returns False if nothing was returned
		if not result:
			return result
		return self.split_on_newline(self.cleanup_ios_output(result))

	def count_interface_status(self, interfaces): #required
		up = down = disabled = total = 0

		for interface in interfaces:
			if not 'Interface' in interface:
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
		
