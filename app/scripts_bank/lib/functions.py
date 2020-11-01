#!/usr/bin/python3

from datetime import datetime
from flask import jsonify
from urllib.request import urlopen


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


def set_user_credentials(username, password, priv_password):
    """Return creds class with username and password in it."""
    creds.un = username
    creds.pw = password
    creds.priv = priv_password
    return creds


def contains_skipped(x):
    """Return if the word 'skipped' is in the provided string.

    Returns True if string contains the word "skipped".
    Returns False otherwise.
    """
    try:
        if 'skipped' in str(x):
            return True
        else:
            return False
    except:
        return False


def remove_dict_key(d, key):
    """Remove key from dictionary."""
    r = dict(d)
    del r[key]
    return r


def is_integer(x):
    """Test if provided value is an integer or not."""
    try:
        int(x)
        return True
    except ValueError:
        return False


def check_for_version_update(config):
    """Check for NetConfig updates on GitHub."""
    try:
        # with urlopen(config['GH_MASTER_BRANCH_URL']) as a:
        # master_config = a.read().decode('utf-8')
        master_config = urlopen(config['GH_MASTER_BRANCH_URL'])
        master_config = master_config.read().decode('utf-8')
        # Reverse lookup as the VERSION variable should be close to the bottom
        if master_config:
            for x in master_config.splitlines():
                if 'VERSION' in x:
                    x = x.split('=')
                    try:
                        # Strip whitespace and single quote mark
                        master_version = x[-1].strip().strip("'")
                    except IndexError:
                        continue
                    # Verify if current version matches most recent GitHub release
                    if master_version != config['VERSION']:
                        # Return False if the current version does not match the most recent version
                        return jsonify(status="False", masterVersion=master_version)
            # If VERSION can't be found, successfully compared, or is identical, just return True
            return jsonify(status="True")
        else:
            # Error when accessing URL. Default to True
            return "True"
    except IOError as e:
        # Catch exception if unable to access URL, or access to internet is blocked/down. Default to True
        return "True"
    except Exception as e:
        # Return True for all other exceptions
        return "True"


# Get current timestamp for when starting a script
def get_current_time():
    """Get current timestamp."""
    current_time = datetime.now()
    return current_time


# Returns time elapsed between current time and provided time in 'start_time'
def get_script_run_time(start_time):
    """Calculate time elapsed since start_time was first measured."""
    end_time = get_current_time() - start_time
    return end_time


def interface_replace_slash(x):
    """Replace all forward slashes in string 'x' with an underscore."""
    x = x.replace('_', '/')
    return x
