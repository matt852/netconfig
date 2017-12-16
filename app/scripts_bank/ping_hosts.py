#!/usr/bin/python

# import subprocess
# import os


def reachable(hosts):
    """"Determine if device is pingable from NetConfig.

    Input hosts variable from DB, with hosts.hostname, hosts.ipv4_addr, etc.
    Returns Dictionary with True or False tagged to each hosts hostname, if reachable via ping.
    Pings 1 time with a 1 second timeout.
    """
    hostDict = {}
    for x in hosts.items:
        hostDict[x.hostname] = True
    return hostDict
    '''# This works, but disabled to increase speed.  It is ineffecient in its current form
    hostDict = {}
    processes = []
    FNULL = open(os.devnull, 'w')

    for x in hosts.items:
        #status = True if os.system("ping -c 1 -t 1 " + x.ipv4_addr) is 0 else False
        process = subprocess.Popen(["ping", "-c", "1", "-t", "1", x.ipv4_addr], stdout=FNULL, stderr=subprocess.STDOUT)
        processes.append(process)

    for process, x in zip(processes, hosts.items):
        response = process.wait()
        if response == 0:
            hostDict[x.hostname] = True
        else:
            hostDict[x.hostname] = False

    return hostDict
    '''
