#!/usr/bin/python

#####################################################################################################
# Written by Matt Vitale																			#
#####################################################################################################

import functions as fn
import ip_functions as ifn
import netmiko_functions as nfn

# Returns line for under network object group, different if it's a single IP or a range
# Todo: add skip checks here if the string is empty
def addConfigNetworkOGLine(ip, mask, cmdList):
	# If it's a host IP address, use 'host' instead of mask
	if ifn.isSubnetMaskAHost(mask):
		cmdList.append(" network-object host %s" % (ip))
	else:
		cmdList.append(" network-object %s %s" % (ip, mask))
	# Return command to configure
	return cmdList

# Returns line for under service object group
def addConfigServiceOGLine(port, protocol, sourceOrDest, cmdList):
	if sourceOrDest == 's':
		word1 = "source"
	elif sourceOrDest == 'd':
		word1 = "destination"
	else:
		fn.debugScript('Incorrect value passed to fwn.addConfigServiceOGLine() - var \'sourceOrDest\' must be either \'s\' or \'d\'')

	cmdList.append(" service-object %s %s eq %s" % (protocol.lower(), word1, port))
	# Return command to configure
	return cmdList

# Returns two command lines for creating a new object-group with a description
# Uses user initials and change ticket, if available.  Otherwise skips it
# Requires 'typeOfOG' to be either "network" or "service", depending on type of OG desired
# Requres 'sourceOrDest' to be either 's' or 'd', if the object-group will be used as a source or destionation OG
# Counter is if this object-group has been run multiple times for the same function - it prevents duplicate object-group names
# cmdList is the existing set of configs in list format to append any new lines to
def addConfigNewOG(typeOfOG, sourceOrDest, changeTicket, userInitials, name, counter, cmdList):
	if counter == 0:
		counter = ''
	else:
		counter = counter + 1

	if typeOfOG == 'network':
		if sourceOrDest == 's':
			word1 = "source"
		elif sourceOrDest == 'd':
			word1 = "destination"
		else:
			fn.debugScript('Incorrect value passed to fwn.addConfigNewOG() - var \'sourceOrDest\' must be either \'s\' or \'d\'')

		word2 = "IP addresses"

	elif typeOfOG == 'service':
		if sourceOrDest == 's':
			word1 = "source"
		elif sourceOrDest == 'd':
			word1 = "destination"
		else:
			fn.debugScript('Incorrect value passed to fwn.addConfigNewOG() - var \'sourceOrDest\' must be either \'s\' or \'d\'')

		word2 = "ports"

	else:
		fn.debugScript('Incorrect value passed to fwn.addConfigNewOG() - var \'typeOfOG\' must be either \'network\' or \'service\'')

	if typeOfOG == 'network':
		if sourceOrDest == 's':
			nameOG = "%s%s_Src-OG" % (name, str(counter))
		elif sourceOrDest == 'd':
			nameOG = "%s%s_Dst-OG" % (name, str(counter))
	elif typeOfOG == 'service':
		nameOG = "%s%s_Ports-OG" % (name, str(counter))
	else:
		fn.debugScript('Error when assigning object-group name in fwn.addConfigNewOG()')

	# Store object-group name into command variable
	cmdList.append("object-group %s %s" % (typeOfOG, nameOG))
	# Add a description to the object-group
	cmdList.append(" description Group of %s %s for %s - (%s %s)" % (word1, word2, name, userInitials, changeTicket))
	# Return full object-group name with description as one big string, and the name of the object-group separately
	return cmdList, nameOG

# Removes line from under an object-group.  If there's nothing left in the object-group, deletes the object-group also
# Returns True if this ip/mask was the only one in an object-group, and subsequently the OG was deleted as well
# Returns False if just the ip/mask was removed from an OG, but the OG itself was not removed
def removeNetworkLineFromOG(ip, mask, cmdList):
	# If it's a host IP address, use 'host' instead of mask
	if ifn.isSubnetMaskAHost(mask):
		command = " network-object host %s" % (ip)
	else:
		command = " network-object %s %s" % (ip, mask)

	# Find the index where the command we're removing is located
	a = cmdList.index(command)
	# Remove the command from the primary list
	del cmdList[a]
	# If the new line contains "object-group" that's now in the index slot ahead of the slot previously occupied by the command we removed, it was the last object in the OG
	#   The slot previously occupied by the command we removed contains ' exit'
	#   And if the previous line was a description, it was the only line in that object-group
	if "object-group" in cmdList[a+1] and "description" in cmdList[a-1]:
		# Delete the object-group header as well as the description lines
		for x in range(3):
			del cmdList[a]
			a -= 1

		# Returns True if the parent object-group was deleted
		return cmdList, True
	# Returns False if the parent object-group was not deleted (it was not the only object in the OG)
	return cmdList, False

# Split a string of text by spaces, reduces any spots of multiple whitespace to a single space only
def splitString(x):
	# Store line in a new string variable
	line = x
	# Strips any newlines from string
	line = fn.stripNewline(line)
	# Reduce all spacing to just a single space per section
	line = fn.replaceDoubleSpaces(line)
	# Split string by spaces
	return line.split(" ")

# Runs packet-tracer to see if given parameters are already allowed through a firewall's ACL
# Returns True if it is allowed, False if it isn't allowed. Includes packet-tracer result
def checkAccessThroughACL(iface, sIP, dIP, port, proto, ssh):
	# Set initial variables for later loop
	actionFound = False
	outputIntFound = False
	inputIntFound = False

	iface = fn.stripNewline(iface)
	sIP = fn.stripNewline(sIP)
	dIP = fn.stripNewline(dIP)
	port = fn.stripNewline(port)
	proto = fn.stripNewline(proto)
	# Set packet-tracer command to test each iteration, and log result if it's already allowed or not
	command = "packet-tracer input %s %s %s %s %s %s" % (iface, proto.lower(), sIP, port, dIP, port)
	# Send source interface, source IP, destination IP, port, protocol, and ssh session to test if this access is already allowed
	result = nfn.runSSHCommandInSession(command, ssh)

	# Check result to see if it worked
	# If fails, the 2nd to last returned line will be "Action: drop". The last line is the "Drop-reason: (acl-drop) Flow is denied by configured rule"
	# If succeeded, the last returned line will be "Action: allow". There is no reason

	# Splits results by new lines
	resultList = result.split("\n")
	# Decrement counter
	i = -1
	# Repeat for total number of lines in list
	for j in range(len(resultList)):
		# Search last few lines of returned list, starting from the bottom
		if 'Action:' in resultList[i]:
			# Call function above.  We'll be looking for the last field
			lineList = splitString(resultList[i])
			# Check if the 1st word is 'Action:', in case it's in the drop-reason for whatever reason
			if lineList[0] == 'Action:':
				# Access is allowed
				if lineList[1] == 'allow':
					# Return True and a blank response for reason
					# We do not need to check if the interfaces are the same for allowed traffic
					return True, ''
				# Access is not allowed
				elif lineList[1] == 'drop':
					# If access isn't allowed, first verify if the intput and output interface are the same
					# If they are, return True instead as no changes are needed for inter-vlan communication
					actionFound = True
					# Decrement counter by 1, repeat
					i -= 1

		# If the line is for the input or output interface, enter 'if' statement
		elif '-interface:' in resultList[i]:
			# Call function above.  We'll be looking for the last field
			lineList = splitString(resultList[i])
			if lineList[0] == 'output-interface:':
				# Store output interface
				outputInt = lineList[1]
				# Set variable to True
				outputIntFound = True
				# Decrement counter by 1, repeat
				i -= 1
			elif lineList[0] == 'input-interface:':
				# Store input interface
				inputInt = lineList[1]
				# Set variable to True
				inputIntFound = True
				# Decrement counter by 1, repeat
				i -= 1

		# If we've found the packet-tracer action result, AND the output interface, AND the input interface
		# Then compare to see if the input and output interface are the same.
		# If so, return TRUE, as we don't need to configure anything.
		# If not, they're different interfaces and return False
		elif actionFound and inputIntFound and outputIntFound:
			# If the traffic is on the same interface, no changes needed
			if inputInt == outputInt:
				# Return True and a blank response for reason
				return True, ''
			else:
				# Return False and the drop-reason as the response reason
				return False, resultList[i+1]

		else:
			# Decrement counter by 1, repeat
			i -= 1
	# If we ever hit this return line, then 'Action:' wasn't found in the packet-tracer result output.  Throw an error
	returnError = "Unable to determine if access currently exists for access from %s to %s on port %s %s. Defaulting to configuring access." % (sIP, dIP, proto, port)
	return False, returnError

def getSourceInterfaceForHost(ssh, sourceIP):
	# Loop once only in case initial source isn't in ASA routing table, then search for default route
	for k in range(2):
		# Command to check for interface source would originate from
		command = "show route %s | inc via" % (sourceIP)
		# Get result of above command when run on the firewall
		result = nfn.runSSHCommandInSession(command, ssh)

		# This is blank if it isn't in the routing table; AKA check for default route next
		if fn.isEmpty(result):
			sourceIP = "0.0.0.0"
			continue
		else:
			break

	# Split returned results by line
	result = result.split("\n")
	# Store last line of list into a new string variable
	resultStr = result[-1]
	# Reduce all spacing to just a single space per section
	resultStr = fn.replaceDoubleSpaces(resultStr)
	# Split string by spaces.  We are looking for the last field
	resultList = resultStr.split(" ")
	# Return interface name
	return resultList[-1]