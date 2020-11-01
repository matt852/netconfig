#!/usr/bin/python3

import app
from flask import g, session
from operator import attrgetter
from app.scripts_bank.lib.functions import set_user_credentials, remove_dict_key
from app.scripts_bank.lib.netmiko_functions import disconnect_from_ssh, get_ssh_session, session_is_alive


class SSHHandler(object):
    """Handler object for SSH connections."""

    # Global Variables #
    ssh = {}

    def __init__(self):
        """Data handler initialization function."""
        pass

    def get_ssh_key_for_device(self, device):
        """Return SSH key for looking up existing SSH sessions for a specific device.

        Store SSH Dict key as device.id followed by '-' followed by username and return.
        """
        try:
            ssh_key = str(device.id) + '--' + str(session['UUID'])
            return ssh_key
        except KeyError:
            return None

    def check_device_active_ssh_session(self, device):
        """Check if existing SSH session for device is currently active."""
        sshKey = self.get_ssh_key_for_device(device)

        # Return True is SSH session is active, False if not
        try:
            if session_is_alive(self.ssh[sshKey]):
                return True
            else:
                return False
        except KeyError:
            # If try statement fails, return False as it's not alive
            return False

    def check_device_existing_ssh_session(self, device):
        """Check if device currenty has an existing SSH session saved."""
        # Retrieve SSH key for device
        sshKey = self.get_ssh_key_for_device(device)

        # Return True if device in SSH variable, False if not
        if sshKey in self.ssh:
            return True
        else:
            return False

    def retrieve_ssh_session(self, device, saved_session=True):
        """[Re]Connect to 'device' over SSH.  Store session for use later.

        Return active SSH session for provided device if it exists.
        Otherwise gets a session, stores it, and returns it.
        """
        def erase_vars_in_mem():
            # Clear all credential based variables from memory
            password = None
            privpw = None
            creds = None

        # Set privileged password initially to an empty string
        privpw = ''

        # If username and password variable are not passed to function, set it as the currently logged in user
        # if ('username' not in kwargs and 'password' not in kwargs):
        if device.local_creds:
            # Set key to device id, --, and username of currently logged in user
            key = str(device.id) + '--' + session['USER']
            saved_id = g.db.hget('localusers', key)
            username = g.db.hget(saved_id, 'user')
            password = g.db.hget(saved_id, 'pw')
            try:
                privpw = g.db.hget(saved_id, 'privpw')
            except:
                # If privpw not set for this device, simply leave it as a blank string
                pass
        else:
            username = session['USER']
            saved_id = g.db.hget('users', username)
            password = g.db.hget(saved_id, 'pw')

        creds = set_user_credentials(username, password, privpw)

        # Retrieve SSH key for device
        sshKey = self.get_ssh_key_for_device(device)

        # Default to saving SSH information for program tracking
        if saved_session:
            if not self.check_device_existing_ssh_session(device):
                app.logger.info('initiated new SSH connection to %s' % (device.hostname))
                # If no currently active SSH sessions, initiate a new one
                self.ssh[sshKey] = get_ssh_session(device, creds)

            # Run test to verify if socket connection is still open or not
            elif not self.check_device_active_ssh_session(device):
                # If session is closed, reestablish session and log event
                app.logger.info('reestablished SSH connection to %s' % (device.hostname))
                self.ssh[sshKey] = get_ssh_session(device, creds)

            # Erase sensitive data from memory
            erase_vars_in_mem()
            # Return SSH session
            return self.ssh[sshKey]
        else:
            # Just return SSH session without saving session state in self.ssh variable (for threading/one off commands)
            return get_ssh_session(device, creds)

    def disconnect_specific_ssh_session(self, device):
        """Disconnect any SSH sessions for a specific device from all users."""
        for x in self.ssh:
            # x is id-uuid
            y = x.split('--')
            # y[0] is device id
            # y[1] is uuid
            if int(y[0]) == int(device.id):
                disconnect_from_ssh(self.ssh[x])
                self.ssh.pop(x)
                app.logger.info('disconnected SSH session to provided device %s from user %s' % (device.hostname, session['USER']))

    def disconnect_all_ssh_sessions(self):
        """Disconnect all remaining active SSH sessions tied to a user."""
        for x in self.ssh:
            # x is id-uuid
            y = x.split('--')
            # y[0] is device id
            # y[1] is uuid
            if str(y[1]) == str(session['UUID']):
                disconnect_from_ssh(self.ssh[x])
                device = app.datahandler.get_device_by_id(y[0])
                self.ssh = remove_dict_key(self.ssh, x)
                app.logger.info('disconnected SSH session to device %s for user %s' % (device.hostname, session['USER']))

        # Try statement needed as 500 error thrown if user is not currently logged in.
        try:
            app.logger.info('disconnected all SSH sessions for user %s' % (session['USER']))
        except:
            app.logger.info('disconnected all SSH sessions without an active user logged in')

    def count_all_ssh_sessions(self):
        """Return number of active SSH sessions tied to user."""
        i = 0
        for x in self.ssh:
            # x is id-uuid
            y = x.split('--')
            # y[0] is device id
            # y[1] is uuid
            if str(y[1]) == str(session['UUID']):
                # Increment counter
                i += 1

        return i

    def get_names_of_ssh_session_devices(self):
        """Return list of devicenames for all devices with an existing active connection."""
        device_list = []
        for x in self.ssh:
            # x is id-uuid
            y = x.split('--')
            # y[0] is device id
            # y[1] is uuid
            if str(y[1]) == str(session['UUID']):
                # Get device by y[0] (device.id)
                device_list.append(app.datahandler.get_device_by_id(y[0]))

        # Reorder list in alphabetical order
        device_list = sorted(device_list, key=attrgetter('hostname'))
        return device_list
