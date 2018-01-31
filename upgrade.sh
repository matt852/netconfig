#!/bin/bash

# Set different console colors
red=`tput setaf 1`
green=`tput setaf 2`
magenta=`tput setaf 5`
cyan=`tput setaf 6`
reset=`tput sgr0`


printf "\n ${cyan} NetConfig Upgrade Script \n\n ${reset}"


### Step 1 - Verify script is not running as root
PREFIX="sudo"
if [ "$(whoami)" = "root" ]; then
	# Prevent user from running script directly as root
	printf "\n ${red} NetConfig upgrade should not be run as root.  Please run the upgrade script again as local user 'netconfig'.
	You will be prompted for the user 'netconfig' password when a command needs to be run with elevated privileges. \n\n ${reset}"
	exit
fi


### Step 2 - Get Current Version
CURRENTVERSION=`cat config.py | grep VERSION | cut -d \' -f 2`
printf "\n ${cyan} Current NetConfig version is ${CURRENTVERSION} \n\n ${reset}"


### Step 2 - Set working directory
cd /home/netconfig/netconfig


### Step 3 - Checkout master branch in git
COMMAND="git checkout master"
printf "\n ${cyan} Checking out master NetConfig branch in Git... ${reset} \n\n"
eval $COMMAND


### Step 4 - Verify Git status
printf "\n ${cyan} Verifying Git status... ${reset} \n"
if output=$(git status --porcelain) && [ -z "$output" ]; then
    printf "\n ${green} The NetConfig installation is ready to be updated ${reset} \n\n"
else
    printf "\n ${red} The NetConfig installation cannot be updated as there are Git merge conflicts.\n\n"
    printf "  Please delete or revert any changes made to the following files: \n\n  ${magenta}"
    git status --porcelain
    printf "${reset} \n\n"
    exit
fi


### Step 5 - Pull updated files from master branch
printf "\n ${cyan} Pulling any updated files from master NetConfig branch in Git... ${reset} \n\n"
git pull origin master | grep 'Already up-to-date'

if [ $? == 0 ]
then
	printf "\n ${red} NetConfig files are already up to date with the most recent version on Git.  Skipping pulling updated files from Git. ${reset} \n\n"
	UPDATERESULT=false
else
    printf "\n ${green} NetConfig files updated from master NetConfig branch in Git ${reset} \n\n"
    UPDATERESULT=true
fi


### Step 6 - Delete stale bytecode
COMMAND="find . -name \"*.pyc\" -delete"
printf "\n ${cyan} Cleaning up stale Python bytecode... ${reset} \n\n"
eval $COMMAND


### Step 7 - Uninstall any old Python packages no longer used
COMMAND="${PREFIX} pip uninstall -r old_requirements.txt -y"
printf "\n ${cyan} Removing old Python packages... $(reset) \n\n"
eval $COMMAND


### Step 8 - Install any new Python packages
COMMAND="${PREFIX} pip install -r requirements.txt --upgrade"
printf "\n ${cyan} Updating required Python packages... ${reset} \n\n"
eval $COMMAND


### Step 9 - Verify Nginx NetConfig settings file is correct
MATCHFIELD="\$remote_addr;"
INSERTFIELD1="        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;"
INSERTFIELD2="        proxy_set_header X-Forwarded-Proto \$scheme;"
CHECKCOMMAND=`cat /etc/nginx/sites-available/netconfig | grep proxy_set_header | wc -l`
FILE="/etc/nginx/sites-available/netconfig"

printf "\n ${cyan} Updating NGINX NetConfig settings file... ${reset} \n\n"
if [ "$CHECKCOMMAND" == "2" ]
then
    ${PREFIX} sed -i "s/$MATCHFIELD/$MATCHFIELD\n$INSERTFIELD1\n$INSERTFIELD2/" $FILE
    printf "\n ${green} File updated successfully \n\n"
    ${PREFIX} service nginx restart
    printf "\n ${green} NGINX service restarted successfully ${reset} \n\n"
else
    printf "\n ${red} File does not need to be updated.  Skipping. ${reset} \n\n"
fi


### Step 10 - Upgrade Database
COMMAND="python db_upgrade.py"
printf "\n ${cyan} Upgrading database schema to latest version... ${reset} \n\n"
FILE="app.db"
if [ -f "$FILE" ]
then
    eval $COMMAND
    printf "\n {$green} Database schema updated successfully."
else
    printf "\n {$red} Database file app.db not found.  Database schema not updated.
    If using the local database for device inventory, please manually run the the following command: 
    ${magenta} python /home/netconfig/netconfig/db_upgrade.sh ${reset} \n\n"
fi


### Step 11 - Restart supervisorctl process
COMMAND="${PREFIX} supervisorctl restart netconfig"
printf "\n ${cyan} Restarting supervisorctl NetConfig process... ${reset} \n\n"
eval $COMMAND


### Step 12 - Notify of successful upgrade
NEWVERSION=`cat config.py | grep VERSION | cut -d \' -f 2`

if [ "$UPDATERESULT" == false ]
then
	printf "\n ${green} NetConfig successfully upgraded to version ${NEWVERSION} \n\n ${reset}"
else
	if [ "$CURRENTVERSION" == "$NEWVERSION" ]
	then
	    printf "\n ${red} NetConfig was not upgraded.  Please check your server's access to GitHub and the internet, and try again. \n"
	    printf"  Current NetConfig Version: ${NEWVERSION} \n\n ${reset}" 
	else
        printf "\n ${green} NetConfig successfully upgraded to version ${NEWVERSION} \n\n ${reset}"
    fi
fi