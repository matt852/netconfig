#!/usr/bin/python

from flask import session


def check_user_logged_in_status():
    """Check if user is currently logged in.

    Return True if they are logged in.
    Return False if not.
    """
    try:
        # Try statement as 500 error thrown if no existing session['USER'] variable set
        if 'USER' in session and session['USER']:
            return True
        else:
            return False
    except:
        return False


def check_ssh_session_matches_id(sshid, hostid):
    """Check if there's any existing SSH connections.

    Return True if there are.
    Return False if not.
    """
    if sshid == hostid:
        return True
    else:
        return False
