#!/usr/bin/python

import inspect
import subprocess
import re
import socket
import sys
import time
import os
import lib.functions as fn
import lib.netmiko_functions as nfn
import optparse
import xml.etree.cElementTree as ET
from StringIO import StringIO
from flask import session

def cleanUpIOSOutput(x): # THIS GOES AWAY
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
	x = fn.replaceDoubleSpacesCommas(x)
	x = x.replace('down down', 'down,down')
	x = x.replace(' unassigned', ',unassigned')
	x = x.replace('unassigned ', 'unassigned,')
	return x

def cleanUpNXOSOutput(x): # THIS GOES AWAY
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

def pullHostInterfacesIOS(host, ssh): # THIS GOES AWAY
	output = []

	command = "show ip interface brief"

	# Print existing configuration settings for interface
	result = nfn.runSSHCommandInSession(command, ssh)

	if not result:
		return result
	# Clean up output for table on HTML output
	result = cleanUpIOSOutput(result)

	output = result.split('\n')

	return output

def pullHostInterfacesASA(host, ssh): # THIS GOES AWAY
	output = []

	command = "show interface ip brief"
	
	# Print existing configuration settings for interface
	result = nfn.runSSHCommandInSession(command, ssh)

	if not result:
		return result
	# Clean up output for table on HTML output
	result = cleanUpIOSOutput(result)

	output = result.split('\n')

	return output

def pullHostInterfacesNXOS(host, ssh): # THIS GOES AWAY
	output = []
	outputResult = ''

	#command = "show interface status | exclude -----"
	command = "show interface status | xml"

	# Print existing configuration settings for interface
	result = nfn.runSSHCommandInSession(command, ssh)

	# Returns False if nothing was returned
	if not result:
		return result

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
				# Otherwise store output to string
				else:
					outputResult = outputResult + elem.text + ','

		# This is to skip the first instance of "ROW_interface" in the XML output
		if elem.tag == 'ROW_interface':
			outputResult = outputResult + '\n'
			a = True


	command = 'sh run int | egrep interface|ip.address | ex passive | ex !'

	result = nfn.runSSHCommandInSession(command, ssh)

	# Set intStatus var to False initially
	intStatus = 0
	# Keeps track of the name of the interface we're on currently
	currentInt = ''
	realIP = ''
	realIPList = []
	# This extracts the IP addresses for each interface, and inserts them into the outputResult string
	for x in result.split('\n'):
		#outputResult = outputResult + x + '\n'
		
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
	# Split by newlines
	output = outputResult.split('\n')

	# Return output as List
	return output

def pullInterfaceConfigSession(ssh, interface, host): # THIS GOES AWAY
	output = []
	
	if host.ios_type == 'cisco_nxos':
		command = "show run interface %s | exclude version | exclude Command | exclude !" % (interface)
	elif host.ios_type == 'cisco_ios' or host.ios_type == 'cisco_asa':
		command = "show run interface %s | exclude configuration|!" % (interface)
	else:
		command = "show run interface %s | exclude configuration|!" % (interface)

	# Print existing configuration settings for interface
	result = nfn.runSSHCommandInSession(command, ssh)

	output = result.split('\n')
	return output

def pullInterfaceMacAddressesSession(ssh, interface, host): # THIS GOES AWAY
	output = []

	if host.ios_type == 'cisco_nxos':
		command = "show mac address-table interface %s | exclude VLAN | exclude Legend" % (interface)
	elif host.ios_type == 'cisco_ios' or host.ios_type == 'cisco_asa':
		command = "show mac address-table interface %s" % (interface)
	else:
		command = "show mac address-table interface %s" % (interface)

	# Loop once in case the command requires a dash between 'mac' and 'address-table'
	for a in range(2):
		# Print existing configuration settings for interface
		result = nfn.runSSHCommandInSession(command, ssh)

		if "Invalid input detected" in result and host.ios_type == 'cisco_ios':
			command = "show mac-address-table interface %s" % (interface)
			continue
		else:
			break

	# If invalid input detected both times, return blank as an error, so it won't display the mac address table (since it's empty)
	if "Invalid input detected" in result:
		return '', ssh

	result = fn.replaceDoubleSpacesCommas(result)

	result = result.replace('*', '')
	
	output = result.split('\n')
	return output

def pullInterfaceInfo(ssh, interface, host): # THIS GOES AWAY
	intConfig = pullInterfaceConfigSession(ssh, interface, host)
	if host.type == 'Switch':
		intMac = pullInterfaceMacAddressesSession(ssh, interface, host)
	else:
		intMac = ''
	
	return intConfig, intMac

# Returns output of 'show interface'
def pullInterfaceStats(ssh, interface, host): # THIS GOES AWAY
	output = []
	
	if host.ios_type == 'cisco_nxos':
		command = "show interface %s" % (interface)
	elif host.ios_type == 'cisco_ios' or host.ios_type == 'cisco_asa':
		command = "show interface %s" % (interface)
	else:
		command = "show interface %s" % (interface)

	# Save existing interface statistics
	result = nfn.runSSHCommandInSession(command, ssh)

	output = result.split('\n')
	return output

# Counts number of up, down, and admin down ports in list
def countInterfaceStatus(interfaces, ios_type): #THIS GOES AWAY
	up = 0
	down = 0
	disabled = 0
	total = 0

	if ios_type == 'cisco_ios' or ios_type == 'cisco_asa' or ios_type == 'cisco_iosxe':
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

	elif ios_type == 'cisco_nxos':
		for interface in interfaces:
			if not 'Interface' in interface:
				if 'disabled' in interface:
					disabled += 1
				elif 'notconnect' in interface:
					down += 1
				elif 'sfpAbsent' in interface:
					down += 1
				elif 'down,' in interface:
					down += 1
				elif 'noOperMembers' in interface:
					down += 1
				elif 'connected' in interface:
					up += 1

				total += 1
		# Counter on NX-OS is always off by 1
		total -= 1

	return up, down, disabled, total