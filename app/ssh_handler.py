#!/usr/bin/python
import app
from flask import g, session
from operator import attrgetter
from .scripts_bank.lib.functions import setUserCredentials, removeDictKey
from .scripts_bank.lib.netmiko_functions import disconnectFromSSH, getSSHSession, sessionIsAlive


class SSHHandler(object):
    """Handler object for SSH connections."""

    # Global Variables #
    ssh = {}

    def __init__(self):
        """Data handler initialization function."""
        pass

    def getSSHKeyForHost(self, host):
        """Return SSH key for looking up existing SSH sessions for a specific host.

        Store SSH Dict key as host.id followed by '-' followed by username and return.
        """
        try:
            sshKey = str(host.id) + '--' + str(session['UUID'])
            return sshKey
        except KeyError:
            return None

    def checkHostActiveSSHSession(self, host):
        """Check if existing SSH session for host is currently active."""
        sshKey = self.getSSHKeyForHost(host)

        # Return True is SSH session is active, False if not
        try:
            if sessionIsAlive(self.ssh[sshKey]):
                return True
            else:
                return False
        except KeyError:
            # If try statement fails, return False as it's not alive
            return False

    def checkHostExistingSSHSession(self, host):
        """Check if host currenty has an existing SSH session saved."""
        # Retrieve SSH key for host
        sshKey = self.getSSHKeyForHost(host)

        # Return True if host in SSH variable, False if not
        if sshKey in self.ssh:
            return True
        else:
            return False

    def retrieveSSHSession(self, host, savedSession=True):
        """[Re]Connect to 'host' over SSH.  Store session for use later.

        Return active SSH session for provided host if it exists.
        Otherwise gets a session, stores it, and returns it.
        """
        def eraseVarsInMem():
            # Clear all credential based variables from memory
            password = None
            privpw = None
            creds = None

        # Set privileged password initially to an empty string
        privpw = ''

        # If username and password variable are not passed to function, set it as the currently logged in user
        # if ('username' not in kwargs and 'password' not in kwargs):
        if host.local_creds:
            # Set key to host id, --, and username of currently logged in user
            key = str(host.id) + '--' + session['USER']
            saved_id = str(g.db.hget('localusers', key))
            username = str(g.db.hget(str(saved_id), 'user'))
            password = str(g.db.hget(str(saved_id), 'pw'))
            try:
                privpw = str(g.db.hget(str(saved_id), 'privpw'))
            except:
                # If privpw not set for this device, simply leave it as a blank string
                pass
        else:
            username = session['USER']
            saved_id = str(g.db.hget('users', username))
            password = str(g.db.hget(str(saved_id), 'pw'))

        creds = setUserCredentials(username, password, privpw)

        # Retrieve SSH key for host
        sshKey = self.getSSHKeyForHost(host)

        # Default to saving SSH information for program tracking
        if savedSession:
            if not self.checkHostExistingSSHSession(host):
                app.logger.write_log('initiated new SSH connection to %s' % (host.hostname))
                # If no currently active SSH sessions, initiate a new one
                self.ssh[sshKey] = getSSHSession(host, creds)

            # Run test to verify if socket connection is still open or not
            elif not self.checkHostActiveSSHSession(host):
                # If session is closed, reestablish session and log event
                app.logger.write_log('reestablished SSH connection to %s' % (host.hostname))
                self.ssh[sshKey] = getSSHSession(host, creds)

            # Erase sensitive data from memory
            eraseVarsInMem()
            # Return SSH session
            return self.ssh[sshKey]
        else:
            # Just return SSH session without saving session state in self.ssh variable (for threading/one off commands)
            return getSSHSession(host, creds)

    def disconnectSpecificSSHSession(self, host):
        """Disconnect any SSH sessions for a specific host from all users."""
        for x in self.ssh:
            # x is id-uuid
            y = x.split('--')
            # y[0] is host id
            # y[1] is uuid
            if int(y[0]) == int(host.id):
                disconnectFromSSH(self.ssh[x])
                self.ssh.pop(x)
                app.logger.write_log('disconnected SSH session to provided host %s from user %s' % (host.hostname, session['USER']))

    def disconnectAllSSHSessions(self):
        """Disconnect all remaining active SSH sessions tied to a user."""
        for x in self.ssh:
            # x is id-uuid
            y = x.split('--')
            # y[0] is host id
            # y[1] is uuid
            if str(y[1]) == str(session['UUID']):
                disconnectFromSSH(self.ssh[x])
                host = app.datahandler.getHostByID(y[0])
                self.ssh = removeDictKey(self.ssh, x)
                app.logger.write_log('disconnected SSH session to device %s for user %s' % (host.hostname, session['USER']))

        # Try statement needed as 500 error thrown if user is not currently logged in.
        try:
            app.logger.write_log('disconnected all SSH sessions for user %s' % (session['USER']))
        except:
            app.logger.write_log('disconnected all SSH sessions without an active user logged in')

    def countAllSSHSessions(self):
        """Return number of active SSH sessions tied to user."""
        i = 0
        for x in self.ssh:
            # x is id-uuid
            y = x.split('--')
            # y[0] is host id
            # y[1] is uuid
            if str(y[1]) == str(session['UUID']):
                # Increment counter
                i += 1

        return i

    def getNamesOfSSHSessionDevices(self):
        """Return list of hostnames for all devices with an existing active connection."""
        hostList = []
        for x in self.ssh:
            # x is id-uuid
            y = x.split('--')
            # y[0] is host id
            # y[1] is uuid
            if str(y[1]) == str(session['UUID']):
                # Get host by y[0] (host.id)
                hostList.append(app.datahandler.getHostByID(y[0]))

        # Reorder list in alphabetical order
        hostList = sorted(hostList, key=attrgetter('hostname'))
        return hostList
