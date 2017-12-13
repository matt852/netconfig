NetConfig
=========

What NetConfig Is
------------------

NetConfig started out as a graphical overlay for my existing Python scripts, and I've been expanding it's features ever since.  It was originally built specifically for Cisco switches, routers, and firewalls, using IOS, IOS-XE, NX-OS, and ASA operating systems.  All device data is pulled in real-time via SSH and Netmiko.

NetConfig can retrieve a list of devices in one of two ways:

- Stored in a local SQLAlchemy database file
- Retrieved via API calls on an existing NetBox installation

In version 1.1, vendor neutral support was added using individual device files.

What NetConfig Isn't
---------------------

- Automation tool.
- Error checking tool.  All manual commands entered are submitted as is, just like if entered via a manual SSH session

Features
--------

NetConfig was originally built as a graphical overlay for common CLI based interactions with non-API supported Cisco networking equipment.  At the core of the program is a need to access accurate, real-time information about any SSH enabled network device.  NetConfig accomplishes this by refreshing all page contents each time the page is refreshed, by pulling the information via SSH at the time of the page refresh.

NetConfig provides:

- Real-time information into your network devices
- Graphical overlay for existing Network devices without support for API's or other web-based interfaces

Installation
------------

Reference the Installation Guide section for instructions how on how to install NetConfig.
Install instructions were written for an Ubuntu 16.04 64-bit server.  NetConfig has not been tested with other OS's.

Upgrade
-------

Reference the Upgrading secion for instructions on upgrading the software

NetBox Integration
------------------

Reference the Netbox-Integration secion for instructions on pulling device inventory from an existing Netbox installation
Netbox can be found here: https://github.com/digitalocean/netbox

Screenshots
-----------

.. image:: img/index.jpg

.. image:: img/example-switch.jpg

Important Caveats
-----------------

For all devices, Netconfig expects the hostname configured to match the actual hostname of the device (case-sensitive).  If not, some features may not work properly.

Contribute
----------

* Source Code: https://github.com/v1tal3/netconfig
* Issue Tracker: https://github.com/v1tal3/netconfig/issues
* Documentation: https://netconfig.readthedocs.io/en/latest/
* Subreddit: https://www.reddit.com/r/netconfig/

Support
-------

If you are having issues, please let us know
Please file an issue in the GitHub issue tracker

License
-------

NetConfig is licensed under the GPL v3.0 license.  You can download a copy of the license :download:`here <license.txt>`