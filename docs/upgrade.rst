Upgrading
=========

Upgrading NetConfig to Latest Version
-------------------------------------

Before Starting
^^^^^^^^^^^^^^^

If running NetConfig on a VM, it is *highly* recommended to take a snapshot prior to upgrading.  In case of any issues, you can roll back any changes by reverting to the previous snapshot.

Upgrade Process
^^^^^^^^^^^^^^^

Change to NetConfig user

.. code-block:: text

    su - netconfig

Change to NetConfig directory

.. code-block:: text

    cd /home/netconfig/netconfig

Checkout master branch

.. code-block:: text

    git checkout master

Pull new files

.. code-block:: text

    git pull origin master

Verify git status

.. code-block:: text

    git status

Run Upgrade script.  If upgrade script is not executable, run the 'chmod' command below first

.. code-block:: text

    chmod +x upgrade.sh
    ./upgrade.sh

Restart NetConfig service

.. code-block:: text

    sudo supervisorctl restart netconfig

Verifying Upgrade
^^^^^^^^^^^^^^^^^

In your web browser, navigate to the home NetConfig page.  In the Top Menu, under About, you should see the latest software version displayed.

.. image:: img/version-info.jpg


Potential Caveats
^^^^^^^^^^^^^^^^^

If any manual changes are made to any NetConfig files (except for the settings and log files), the command 'git pull origin master' may fail or throw an error.  If so, you can stash (delete) any manual changes made, then repull from NetConfig's GitHub respository.  This will replace any custom changes made in files with the standard NetConfig system files, so be careful if any custom changes are critical to your environment.

The command is:

.. code-block::text

    git checkout -- .


Upgrade Script doesn't run:
"""""""""""""""""""""""""""

If the upgrade script doesn't run, make sure it is executable first.

.. code-block:: text

    ls -lah
    # -rw-r--r--   1 netconfig  staff   1.2K Jan  2 14:30 upgrade.sh

If it is missing an 'x' in the above output, run this command:

.. code-block:: text

    chmod +x upgrade.sh

The 'ls -lah' output should now read as follows:

.. code-block:: text

    ls -lah
    # -rwxr-xr-x   1 netconfig  staff   1.2K Jan  2 14:30 upgrade.sh