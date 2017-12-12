NetConfig
========


What Is NetConfig?
------------------

NetConfig started out as a graphical overlay for my existing Python scripts, and I've been expanding it's features ever since.  It was originally built specifically for Cisco switches, routers, and firewalls, using IOS, IOS-XE, NX-OS, and ASA operating systems.  All device data is pulled in real-time via SSH and Netmiko.

NetConfig can retrieve a list of devices in one of two ways:

- Stored in a local SQLAlchemy database file
- Retrieved via API calls on an existing NetBox installation

In version 1.1, vendor neutral support was added using individual device files.

What NetConfig Is Not
---------------------

- Automation tool.
- Error checking tool.  All manual commands entered are submitted as is, just like if entered via a manual SSH session

Features
--------

- Real-time information into your network devices
- Graphical overlay for existing Network devices without support for API's or 

Using NetConfig
---------------

For all devices, Netconfig expects the hostname configured to match the actual hostname of the device (case-sensitive).  If not, some features may not work properly.

Installation
------------

Reference INSTALL.md for instructions how on how to install NetConfig.
Install instructions were written for an Ubuntu 16.04 64-bit server.  NetConfig has not been tested with other OS's

Upgrade
-------

Reference UPGRADE.md for instructions on upgrading the software

NetBox Integration
------------------

Reference NETBOX-INTEGRATION.txt for instructions on pulling device inventory from an existing Netbox installation
Netbox can be found here: https://github.com/digitalocean/netbox

Contribute
----------

- Issue Tracker: github.com/v1tal3/$project/issues
- Source Code: github.com/v1tal3/$project

Support
-------

If you are having issues, please let us know
Please file an issue in the GitHub issue tracker

License
-------

The project is licensed under the GPL v3.0 license
