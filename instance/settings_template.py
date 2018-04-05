#!/usr/bin/python


# Generate a Secret Key to be used with NetConfig.
# Do not share or reuse this outside of this file/program
# A secret-key generation script has been provided in the NetConfig
#  root directory, and can be run with 'python generate_secret_key.py'
SECRET_KEY = ''

# Netconfig has the option of tracking device inventory in 2 locations:
#  1) In a local SQLAlchemy database, with devices
#      manually added, updated, and deleted
#  2) In an existing Netbox installation
#      pulled via Netbox's database via API call
#
# Here you can specify whether to use a local SQLAlchemy database
#  or pull from Netbox via API
# Valid options: 'local', 'netbox'
# Default = local
DATALOCATION = 'local'

# If using a Netbox server - URL for accessing Netbox.
# Example: 'http://netbox.domain.com' or 'http://10.0.0.1' if not using DNS
NETBOXSERVER = ''


# Set system hostname by replacing 'localhost' with system hostname
# Default = localhost
HOSTNAME = 'localhost'

# DataTables settings
# Set number of items displayed at a time for table views
# Default = 10
DEFAULT_DATATABLES_ENTRY_COUNT = 10

# Session inactivity timer
# Set timeout for storing browser based session information, in minutes
# Default = 60
SESSIONTIMEOUT = 60

# Redis user information inactivity timer
# Set timeout for clearing username in Redis, in seconds
# This sets the username 'key' to expire,
#  and any password left associated with it,
#  if the user forgets to log out (passwords are cleared after a user logs out)
# Default/Recommended is set to SESSIONTIMEOUT,
#  but can be changed to something different
REDISKEYTIMEOUT = SESSIONTIMEOUT * 60

# Increase number if more than 10k devices in database
# Used when stored device inventory in local SQLAlchemy database
# This should not need to be modified
POSTS_PER_PAGE = 10000

# Debug settings - only enable True for debugging issues (WIP)
# Default = False
DEBUG = False

# Enable auto-checking if an update is available on GitHub
# If set to True, but unable to access the internet, the default behaviour will not display anything
# If set to False, no outbound internet checks will occur
# Default = True
CHECK_FOR_UDPATES = True
