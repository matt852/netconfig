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
from flask import session

def executeSSHCmdsViaNFN(ssh, cmdList):
	result = nfn.runMultipleSSHCommandsInSession(cmdList, ssh)
	return result

def executeSSHConfigCmdsViaNFN(ssh, cmdList):
	result = nfn.runMultipleSSHConfigCommandsInSession(cmdList, ssh)
	return result

def enableInterface(ssh, iface): # THIS GOES AWAY
	cmdList = []
	cmdList.append("interface %s" % iface)
	cmdList.append("no shutdown")
	cmdList.append("end")
	
	return executeSSHConfigCmdsViaNFN(ssh, cmdList)

def disableInterface(ssh, iface): # THIS GOES AWAY
	cmdList = []
	cmdList.append("interface %s" % iface)
	cmdList.append("shutdown")
	cmdList.append("end")
	
	return executeSSHConfigCmdsViaNFN(ssh, cmdList)

def editInterface(ssh, iface, datavlan, voicevlan, other, host):
	cmdList=[]
	cmdList.append("interface %s" % iface)

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
	cmdList.append(fn.returnSaveConfigCommand(host))
	
	return executeSSHConfigCmdsViaNFN(ssh, cmdList)
