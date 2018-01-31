#!/usr/bin/python



class UserCredentials(object):
    """Stores interface authentication session results when searching for a client on the network."""

    def __init__(self, un, pw, priv):
        """Initialization method."""
        self.un = un
        self.pw = pw
        self.priv = priv


"""Global variables."""
# Credentials class variable.  Stores as creds.un and creds.pw for username and password
creds = UserCredentials('', '', '')


def setUserCredentials(username, password, privPassword=''):
    """Return creds class with username and password in it."""
    creds.un = username
    creds.pw = password
    creds.priv = privPassword
    return creds


def containsSkipped(x):
    """Return if the word 'skipped' is in the provided string.

    Returns True if string contains the word "skipped".
    Returns False otherwise.
    """
    try:
        if "skipped" in str(x):
            return True
        else:
            return False
    except:
        return False


def removeDictKey(d, key):
    """Remove key from dictionary."""
    r = dict(d)
    del r[key]
    return r


def isInteger(x):
    """Test if provided value is an integer or not."""
    try:
        int(x)
        return True
    except ValueError:
        return False
