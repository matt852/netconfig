#!/usr/bin/python

import inspect
import subprocess
import socket
import sys
import os
from lib.functions import setUserCredentials, replaceDoubleSpacesCommas
import lib.netmiko_functions as nfn
from flask import session

# Save the config on an active SSH session
def saveConfigOnSession(ssh, host):
	output = []
	if host.ios_type == 'cisco_nxos':
		command = 'copy running-config startup-config'
	else:
		command = 'wr mem'
	result = nfn.runSSHCommandInSession(command, ssh)
	output = result.split('\n')
	return output

# Enter 'configuration terminal' from host by provided IP address
def enterConfigModeInSession(ssh): # THIS GOES AWAY
	output = []

	# Get output from network device when entering config mode
	result = nfn.runEnterConfigModeInSession(ssh)

	# Split output by newline
	output = result.split('\n')

	# Return config
	return output

# Enter 'configuration terminal' from host by provided IP address
def exitConfigModeInSession(ssh): # THIS GOES AWAY
	output = []

	# Get output from network device when exiting config mode
	result = nfn.runExitConfigModeInSession(ssh)

	# Split output by newline
	output = result.split('\n')

	# Return config
	return output

# Get command output from host by provided IP address
def getCmdOutput(ssh, command):
	output = []

	# Get command output from network device
	result = nfn.runSSHCommandInSession(command, ssh)

	# Split output by newline
	output = result.split('\n')

	# Return config
	return output

# Get command output from host by provided IP address without submitting a Carriage Return at the end
def getCmdOutputNoCR(ssh, command):
	output = []

	# Get command output from network device
	result = nfn.runSSHCommandInSessionNoCR(command, ssh)

	# Split output by newline
	output = result.split('\n')

	# Return config
	return output

# Get configuration command output from host by provided IP address
def getCfgCmdOutput(ssh, command):
	output = []

	# Get configuration command output from network device
	result = nfn.runSSHCfgCommandInSession(command, ssh)

	# Split output by newline
	output = result.split('\n')

	# Remove first item in list, as Netmiko returns the command ran only in the output
	output.pop(0)

	# Return config
	return output

# Get configuration command output from host by provided IP address without submitting a Carriage Return at the end
def getCfgCmdOutputNoCR(ssh, command):
	output = []

	# Get configuration command output from network device
	result = nfn.runSSHCfgCommandInSessionNoCR(command, ssh)

	# Split output by newline
	output = result.split('\n')

	# Remove first item in list, as Netmiko returns the command ran only in the output
	output.pop(0)

	# Return config
	return output

# Get command output from host by provided IP address
def getCmdOutputWithCommas(ssh, command):
	output = []

	# Get command output from network device
	result = nfn.runSSHCommandInSession(command, ssh)

	result = replaceDoubleSpacesCommas(result)

	# Split output by newline
	output = result.split('\n')

	# Return config
	return output

def getMultiCmdOutput(ssh, command, host): # THIS GOES AWAY
	newCmd = []

	for x in command.split('\n'):
		newCmd.append(x)

	# Get command output from network device
	result = nfn.runMultipleSSHCommandsInSession(newCmd, ssh)

	return result

def getMultiConfigCmdOutput(ssh, command, host): # THIS GOES AWAY
	newCmd = []

	for x in command.split('\n'):
		newCmd.append(x)

	# Get command output from network device
	result = nfn.runMultipleSSHConfigCommandsInSession(newCmd, ssh)
	saveResult = saveConfigOnSession(ssh, host)
	for x in saveResult:
		result.append(x)

	return result