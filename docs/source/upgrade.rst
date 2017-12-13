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

    git checkout -- .