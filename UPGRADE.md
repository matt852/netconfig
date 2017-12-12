Upgrading Instructions
==============================

Change to NetConfig user
------------------------

	su - netconfig

Change to NetConfig directory
-----------------------------

	cd /home/netconfig/netconfig

Checkout master branch
----------------------

	git checkout master

Pull new files
--------------

	git pull origin master

If above command fails, stash any changes then try again (optional)
-------------------------------------------------------------------

Note: This is only needed if manual changes were made to any NetConfig files.
This command will remove these manual changes prior to pulling any NetConfig updates, to prevent any code conflicts.

	git checkout -- .

Verify git status (optional)
----------------------------

	git status

Restart NetConfig service
-------------------------

	sudo supervisorctl restart netconfig
