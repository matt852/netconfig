#!/usr/bin/python

#####################################################################################################
# Written by Matt Vitale																			#
#####################################################################################################

from platform import system as system_name # Returns the system/OS name
from os import system as system_call       # Execute a shell command
import re

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
	ippatt = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
	ipv4 = re.compile(ippatt)
	if not ipv4.match(ip):
		return False
	return True

# Validate input is a valid subnet mask. Returns True if valid, False if invalid
def validateSubnetMask(mask):
	if not isinstance(mask, str):
		mask = str(mask)
	validmask = re.compile('(0|128|192|224|240|252|254|255)')
	octets = mask.split('.')
	if (not all(map(validmask.match, octets))) or (not len(octets) == 4):
		return False
	for index, octet in enumerate(octets):
		if not octet == '255':
			if not all(x == '0' for x in octets[index+1:]):
				return False
	return True

# Validate input is a valid port. Returns True if valid, False if invalid
def validatePortNumber(port):
	if (not isinstance(port, int)) or (port not in range(1, 65536)):
		return False
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
