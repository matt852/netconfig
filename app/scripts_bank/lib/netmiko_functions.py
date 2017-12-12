#!/usr/bin/python

#####################################################################################################
# Written by Matt Vitale																			#
#####################################################################################################

import pdb
import netmiko as nm
import functions as fn
import socket

def sessionIsAlive(ssh):
	null = chr(0)
	try:
		# Try sending ASCII null byte to maintain the connection alive
		ssh.write_channel(null)
		return True
	except (socket.error, EOFError):
		# If unable to send, we can tell for sure that the connection is unusable
		return False
	return False

# Returns True if SSH session contains "skipped" (was unsuccessful)
# Returns False otherwise
def sshSkipCheck(x):
	try:
		if "skipped" in str(x):
			return True
		return False
	except:
			return False

# Connects to host via SSH with provided username and password, and type of device specified
def connectToSSH(deviceType, host, creds):
	# Try to connect to the host
	try:
		ssh = nm.ConnectHandler(device_type=deviceType, ip=host, username=creds.un, password=creds.pw)
	#except nm.AuthenticationException:
	#	return "%s skipped - authentication error\n" % (host)
	except:
		return "%s skipped - connection timeout\n" % (host)
	# Returns active SSH session to host
	return ssh

# Disconnects from active SSH session
def disconnectFromSSH(ssh):
	try:
		if ssh:
			# Disconnect from the host
			ssh.disconnect()
	except:
		pass

# Runs command on host via SSH and returns output
def runSSHCommandOnce(command, deviceType, host, creds):
	ssh = connectToSSH(deviceType, host, creds)
	# Verify ssh connection established and didn't return an error
	if sshSkipCheck(ssh):
		return False
	# Get command output from device
	result = ssh.send_command(command)
	# Disconnect from SSH session
	disconnectFromSSH(ssh)
	# Return output of command
	return result

# Run multiple commands on host via SSH and returns output
def runMultipleSSHCommandsWithCmdHead(cmdList, deviceType, host, creds):
	result = []
	ssh = connectToSSH(deviceType, host, creds)
	# Verify ssh connection established and didn't return an error
	if sshSkipCheck(ssh):
		return False
	for x in cmdList:
		result.append("Command: %s" % x)
		# Get command output from multiple commands configured on device
		result.append(ssh.send_command(x))
		# Split by newlines
		#output = result.split('\n')
	# Disconnect from SSH session
	disconnectFromSSH(ssh)
	# Return output of command
	return result

# Run multiple commands in list on host via SSH and returns all output from applying the config
def runMultipleSSHCommandsInSession(cmdList, ssh):
	result = []
	for x in cmdList:
		result.append("Command: %s" % x)
		# Get command output from multiple commands configured on device
		result.append(ssh.send_command(x))
	# Get command output from multiple commands configured on device
	#result = ssh.send_config_set(cmdList)
	# Split by newlines
	#output = result.split('\n')
	# Return output of command
	return result

# Creates an SSH session, verifies it worked, then returns the session itself
def getSSHSession(deviceType, host, creds):
	ssh = connectToSSH(deviceType, host, creds)
	# Verify ssh connection established and didn't return an error
	if sshSkipCheck(ssh):
		return "ERROR: In function nfn.getSSHSession, sshSkipCheck failed using host %s and deviceType %s\n" % (host, deviceType)
	# Return output of command
	return ssh

# Runs command on provided existing SSH session and returns output
def runSSHCommandInSession(command, ssh):
	# Get command output from device
	result = ssh.send_command(command)
	# Return output of command
	return result

# Runs command on provided existing SSH session and returns output
def runSSHCommandInSessionNoCR(command, ssh):
	# Since we set normalie to False, we need to do this.
	# The normalize() function in NetMiko does rstrip and adds a CR to the end of the command
	command = command.rstrip()
	# Get command output from device
	result = ssh.send_command(command, normalize=False)
	# Return output of command
	return result

# Runs config command on provided existing SSH session and returns output
def runSSHCfgCommandInSession(command, ssh):
	# Get command output from device
	result = ssh.send_config_set(command, exit_config_mode=False)
	# Return output of command, omitting any lines with just the command displayed only (just how netmiko works with config commands)
	return result

def runSSHCfgCommandInSessionNoCR(command, ssh):
	# Since we set normalie to False, we need to do this.
	# The normalize() function in NetMiko does rstrip and adds a CR to the end of the command
	#command = command.rstrip()
	# Get command output from device
	result = ssh.send_config_set(command, exit_config_mode=False)
	# Return output of command, omitting any lines with just the command displayed only (just how netmiko works with config commands)
	return result

# Enters 'configure terminal' mode on provided existing SSH session and returns output
def runEnterConfigModeInSession(ssh): # THIS GOES AWAY
	# Get command output from device
	result = ssh.config_mode()
	# Return output of command
	return result

# Exits 'configure terminal' mode on provided existing SSH session and returns output
def runExitConfigModeInSession(ssh): # THIS GOES AWAY
	# Get command output from device
	result = ssh.exit_config_mode()
	# Return output of command
	return result

# Run multiple commands in list on host via SSH and returns all output from applying the config
def runMultipleSSHConfigCommandsInSession(cmdList, ssh):
	# Get command output from multiple commands configured on device
	result = ssh.send_config_set(cmdList)
	# Split by newlines
	output = result.split('\n')
	# Return output of command
	return output

# Get prompt from host
def findPromptInSession(ssh):
	return ssh.find_prompt()