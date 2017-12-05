#!/usr/bin/python

import sys
import os
from flask import session

# Checks if user is currently logged in
# Returns True if so, False if not
def checkUserLoggedInStatus():
	if 'USER' in session and session['USER']:
		return True
	else:
		return False

# Checks if there's any existing SSH connection
# Returns True is so, False if not
def checkSSHSessionMatchesID(sshid, hostid):
	if sshid == hostid:
		return True
	else:
		return False