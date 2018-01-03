#!/bin/bash
#
# Pieces of this script have been copied/modified from the original upgrade.sh script as found in NetBox,
#  released under the Apache 2.0 license
# A copy of this can be found here: https://github.com/digitalocean/netbox/
#

# Optionally use sudo if not already root, and always prompt for password
# before running the command
PREFIX="sudo"
if [ "$(whoami)" = "root" ]; then
	# When running upgrade as root, ask user to confirm if they wish to
	# continue
	read -n1 -rsp $'Running NetConfig upgrade as root, press any key to continue or ^C to cancel\n'
	PREFIX=""
fi

# Delete stale bytecode
COMMAND="find . -name \"*.pyc\" -delete"
echo "Cleaning up stale Python bytecode ($COMMAND)..."
eval $COMMAND

# Uninstall any Python packages which are no longer needed
#COMMAND="${PREFIX}${PIP} uninstall -r old_requirements.txt -y"
#echo "Removing old Python packages ($COMMAND)..."
#eval $COMMAND

# Install any new Python packages
COMMAND="${PREFIX} pip install -r requirements.txt --upgrade"
echo "Updating required Python packages ($COMMAND)..."
eval $COMMAND

# Restart supervisorctl process
COMMAND="${PREFIX} supervisorctl restart netconfig"
echo "Restarting supervisorctl NetConfig process..."
eval $COMMAND