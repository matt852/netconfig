#!/usr/bin/python

import lib.netmiko_functions as nfn


def getCmdOutput(ssh, command):
    """Get command output from host by provided IP address."""
    output = []

    # Get command output from network device
    result = nfn.runSSHCommandInSession(command, ssh)

    # Split output by newline
    output = result.split('\n')

    # Return config
    return output


def getCmdOutputNoCR(ssh, command):
    """Get command output from host by provided IP address without submitting a Carriage Return at the end."""
    output = []

    # Get command output from network device
    result = nfn.runSSHCommandInSessionNoCR(command, ssh)

    # Split output by newline
    output = result.split('\n')

    # Return config
    return output


def getCfgCmdOutput(ssh, command):
    """Get configuration command output from host by provided IP address."""
    output = []

    # Get configuration command output from network device
    result = nfn.runSSHCfgCommandInSession(command, ssh)

    # Split output by newline
    output = result.split('\n')

    # Remove first item in list, as Netmiko returns the command ran only in the output
    output.pop(0)

    # Return config
    return output
