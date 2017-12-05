#!/usr/bin/python

#####################################################################################################
# Written by Matt Vitale																			#
#####################################################################################################

from platform import system as system_name # Returns the system/OS name
from os import system as system_call       # Execute a shell command

# Returns True if host (str) responds to a ping request
def ping(host):
    # Ping parameters as function of OS
	# Works with Windows, OS X, or Linux
    parameters = "-n 1" if system_name().lower()=="windows" else "-c 1"

    # Pinging
    return system_call("ping " + parameters + " " + host) == 0

# Returns True if subnet mask is for a single host, otherwise returns false
def isSubnetMaskAHost(x):
	if x == '255.255.255.255':
		return True
	else:
		return False

# Validate input is a valid IP address. Returns True if valid, False if invalid
def validateIPAddress(ip):
	# Split string by decimals
	a = ip.split('.')
	# If there's more or less than 3 decimals (4 octets), return False
	if len(a) != 4:
		return False
	# For each octet in the string, split by decimal
	for x in a:
		# If it's not a number, return False
		if not x.isdigit():
			return False
		# Convert string to integer
		i = int(x)
		# If octet is out of the valid IP address range, return False
		if i < 0 or i > 255:
			return False
	# If all checks pass, return True
	return True

# Validate input is a valid subnet mask. Returns True if valid, False if invalid
def validateSubnetMask(mask):
	# List which inludes all valid options for each octet in a subnet mask
	validMaskOctets = [0, 128, 192, 224, 240, 248, 252, 254, 255]
	# Split string by decimals
	a = mask.split('.')
	# If there's more or less than 3 decimals (4 octets), return False
	if len(a) != 4:
		return False
	# For each octet in the string, split by decimal
	for x in a:
		# If it's not a number, return False
		if not x.isdigit():
			return False
		# Convert string to integer
		x = int(x)
		# Octets can be any in the validMaskOctets list
		if x not in validMaskOctets:
			return False
	# If all checks pass, return True
	return True

# Validate input is a valid port. Returns True if valid, False if invalid
def validatePortNumber(port):
	# If it's not a number, return False
	if not port.isdigit():
		return False
	# Convert string to integer
	x = int(port)
	# If port is out of the valid port range, return False
	if x < 1 or x > 65535:
		return False
	# If all checks pass, return True
	else:
		return True

# Validate input is a valid port protocol. Returns True if valid, False if invalid
def validatePortProtocol(proto):
	# List which inludes all valid options for each octet in a subnet mask
	validProtocol = ['TCP', 'UDP']
	# If inputted string doesn't match a valid protocol, return False
	if proto.upper() not in validProtocol:
		return False
	# If all checks pass, return True
	else:
		return True

# Increments an IP address by 1, then returns it to user (ex: 10.0.0.0 becomes 10.0.0.1)
def incrementIPByOne(ip):
	# Split IP by '.'
	aList = ip.split('.')
	# Get last octect
	a = aList[-1]
	# Convert string to int
	a = int(a)
	# Add 1 to the last octet
	a += 1
	# Convert it back to a string
	a = str(a)
	# Recombine the IP address as a string with the new parameters
	ip = "%s.%s.%s.%s" % (aList[0], aList[1], aList[2], a)
	# Return IP address incremented by 1
	return ip
