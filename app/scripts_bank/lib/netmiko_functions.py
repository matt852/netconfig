#!/usr/bin/python3

import socket
import netmiko as nm
import app
from threading import Thread


def session_is_alive(ssh):
    """Determine if stored Netmiko SSH session is established and active."""
    null = chr(0)
    try:
        # Try sending ASCII null byte to maintain the connection alive
        ssh.write_channel(null)
        return True
    except (socket.error, EOFError):
        # If unable to send, we can tell for sure that the connection is unusable
        return False
    return False


def ssh_skip_check(x):
    """Determine if SSH connection attempt was skipped from Netmiko.

    Returns True if SSH session contains "skipped" (was unsuccessful).
    Returns False otherwise.
    """
    if "skipped" in str(x):
        return True
    else:
        return False


def connect_to_ssh(device, creds):
    """Connect to device via SSH with provided username and password, and type of device specified."""
    # Try to connect to the device
    try:
        if creds.priv:
            ssh = nm.ConnectHandler(session_log='output.txt', device_type=device.ios_type.strip(), ip=device.ipv4_addr.strip(), username=creds.un, password=creds.pw, secret=creds.priv, timeout=app.app.config['SSH_TIMEOUT'])
            # Enter into enable mode
            ssh.enable()
        else:
            ssh = nm.ConnectHandler(session_log='output.txt', device_type=device.ios_type.strip(), ip=device.ipv4_addr.strip(), username=creds.un, password=creds.pw, timeout=app.app.config['SSH_TIMEOUT'])

    # except nm.AuthenticationException:
    #    return "%s skipped - authentication error\n" % (device)
    except:
        return "%s skipped - connection timeout\n" % (device)
    # Returns active SSH session to device
    return ssh


def disconnect_from_ssh(ssh):
    """Disconnect from active SSH session."""
    # Daemonize work to run in background
    def daemon():
        try:
            # Disconnect from the device
            ssh.disconnect()
        except:
            pass
    d = Thread(name='daemon', target=daemon)
    d.setDaemon(True)
    d.start()


def run_ssh_command_once(command, device, creds):
    """Run command on device via SSH and returns output."""
    ssh = connect_to_ssh(device, creds)
    # Verify ssh connection established and didn't return an error
    if ssh_skip_check(ssh):
        return False
    # Get command output from device
    result = ssh.send_command(command)
    # Disconnect from SSH session
    disconnect_from_ssh(ssh)
    # Return output of command
    return result


def run_multiple_ssh_commands_with_cmd_head(cmd_list, device, creds):
    """Run multiple commands on device via SSH and returns output."""
    result = []
    ssh = connect_to_ssh(device, creds)
    # Verify ssh connection established and didn't return an error
    if ssh_skip_check(ssh):
        return False
    for x in cmd_list:
        result.append("Command: %s" % x)
        # Get command output from multiple commands configured on device
        result.append(ssh.send_command(x))
    # Disconnect from SSH session
    disconnect_from_ssh(ssh)
    # Return output of command
    return result


def run_multiple_ssh_commands_in_session(cmd_list, ssh):
    """Run multiple commands in list on device via SSH and returns all output from applying the config."""
    result = []
    for x in cmd_list:
        result.append("Command: %s" % x)
        # Get command output from multiple commands configured on device
        result.append(ssh.send_command(x))
    # Return output of command
    return result


def get_ssh_session(device, creds):
    """Create an SSH session, verifies it worked, then returns the session itself."""
    ssh = connect_to_ssh(device, creds)
    # Verify ssh connection established and didn't return an error
    if ssh_skip_check(ssh):
        return "ERROR: In function nfn.get_ssh_session, ssh_skip_check failed using device %s\n" % (device.hostname)
    # Return output of command
    return ssh
