#!/usr/bin/python

#####################################################################################################
# Written by Matt Vitale																			#
# Creation date			2-5-2017																	#
# Last modifed date		2-5-2017																	#
#                                                                                                   #
# Use: This file will be used to test different scripts that require an SSH connection and output   #
#####################################################################################################


# Prints values for all provided parameters (except creds), and returns output passed to it
def testRunSSHCommandOnce(command, deviceType, host, result):
	print "command:"
	print command
	print "deviceType:"
	print deviceType
	print "host:"
	print host
	return result
