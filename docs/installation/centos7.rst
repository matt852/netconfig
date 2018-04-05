Installation Guide for CentOS 7
================================================================

This document assumes a fresh CentOS 7 minimal installation. It also assumes
you will use this server with a local database (noted where to diverge if using
Netbox). 


Prerequisites
^^^^^^^^^^^^^

Updates and requirements.

.. code-block:: text

    # yum install -y epel-release
    # yum update -y
    # yum install -y gcc python python-devel python-pip nginx redis supervisor python-gunicorn openssl-devel git openldap-devel uwsgi policycoreutils-python

    Optional (but useful):
    # yum install 
    
    You likely got a kernel update. Reboot:
    # reboot


Create new Netconfig user
^^^^^^^^^^^^^^^^^^^^^^^^^

Set up the service account, give it a secure password, and add it to the NGINX
group.

.. code-block:: text

    # adduser netconfig
    # passwd netconfig
    # usermod -a -G nginx netconfig
    # usermod -a -G wheel netconfig

Switch to the new Netconfig user

.. code-block:: text

    su - netconfig


Download NetConfig
^^^^^^^^^^^^^^^^^^

Download NetConfig and install required Python packages

.. code-block:: text

    cd ~/
    git clone -b master https://github.com/v1tal3/netconfig.git
    cd netconfig
    sudo pip install --upgrade pip
    sudo pip install -r requirements.txt


Configure NGINX
^^^^^^^^^^^^^^^

Edit the default nginx config file:

.. code-block:: text

    sudo vi /etc/nginx/nginx.conf

Delete the server{} section as we're going to use a site-specific config. Make
sure that you get the correct braces when you delete and that the http section
still closes at the end of file. 

Now we add the config file for netconfig.

.. code-block:: text

    sudo vi /etc/nginx/conf.d/netconfig.conf

Replace “netconfig.domain.com” with your actual domain name.

*Contents of /etc/nginx/conf.d/netconfig.conf*

.. code-block:: text
  :emphasize-lines: 3, 9

    server {
        listen            80;
        server_name       netconfig.domain.com;
        return            301 https://$host$request_uri;
    }
    
    server {
        listen 443;
        server_name netconfig.domain.com;

        ssl on;
        ssl_certificate /etc/nginx/ssl/server.crt;
        ssl_certificate_key /etc/nginx/ssl/server.key;

        location / {
            proxy_pass http://localhost:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        location /netconfig {
            alias    /home/netconfig/netconfig/app/;
        }
    }

Save and exit the file.

Netconfig Service
^^^^^^^^^^^^^^^^^

Create and fill out netconfig.service file

.. code-block:: text

    sudo vi /etc/systemd/system/netconfig.service

*Contents of /etc/systemd/system/netconfig.service*

.. code-block:: text

    [Unit]
    Description=uWSGI instance to serve NetConfig
    After=network.target

    [Service]
    User=netconfig
    Group=nginx
    WorkingDirectory=/home/netconfig/netconfig
    Environment="PATH=/usr/bin/python"
    ExecStart=/usr/bin/uwsgi --ini netconfig.ini

    [Install]
    WantedBy=multi-user.target

Start and Enable Netconfig services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Reload the systemd config manager and start/enable the new service.

.. code-block:: text

    sudo systemctl daemon-reload
    sudo systemctl start netconfig
    sudo systemctl enable netconfig

Supervisord Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

Add netconfig to supervisor configuration file for gUnicorn under the program section.
In a default supervisor configuration, this starts at line 79. sudo vi /etc/supervisord.conf

.. code-block:: text

    sudo vi /etc/supervisord.conf

*Contents of /etc/supervisord.conf*

.. code-block:: text

    [program:netconfig]
    command = gunicorn app:app -b localhost:8000
    directory = /home/netconfig/netconfig
    user = netconfig

Then enable supervisord.

.. code-block:: text

    sudo systemctl enable supervisord

Configure Self-Signed SSL Cert
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run these commands to generate a self-signed SSL certificate

Create a new directory for the certs and move into it:

.. code-block:: text

    sudo mkdir /etc/nginx/ssl
    cd /etc/nginx/ssl

Now, generate the self-signed SSL certs.

When prompted to create a key file password, anything will work (line 1).  
This will be the same password used when prompted during certificate creation
when it prompts you.

When generating the certificate, fill out the relevant details as requested 
(Country, State, etc.).  However when asked for the Common Name, set it to your
domain name of the server.

.. code-block:: text

    sudo openssl genrsa -des3 -out server.key 2048
    sudo openssl req -new -key server.key -out server.csr
    sudo cp server.key server.key.org
    sudo openssl rsa -in server.key.org -out server.key
    sudo openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt


Restart Services
^^^^^^^^^^^^^^^^

Enable and restart services for the program:

.. code-block:: text
    sudo systemctl enable nginx
    sudo systemctl restart nginx
    sudo systemctl enable supervisord
    sudo systemctl restart supervisord
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl restart netconfig

Configure NetConfig Settings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Copy settings template file.

.. code-block:: text

    cd ~/netconfig
    cp instance/settings_template.py instance/settings.py

Modify the contents of the file:

.. code-block:: text

    vi instance/settings.py

The only required settings that need to be changed in the file are as follows:

    * SECRET_KEY - Generate a random key to use with the program. You can provide you own, or use the provided "generate_secret_key.py" script to generate one for you. This can be run with the command "python ~/netconfig/generate_secret_key.py"

    * DATALOCATION - Specify if you want to use a local database on the server, and configure the inventory manually, or use an existing Netbox installation

    * NETBOXSERVER - If using an existing Netbox installation, this is the Netbox server hostname. Otherwise this value is not used

Create local database
^^^^^^^^^^^^^^^^^^^^^

If using local SQLAlchemy database, create the database (this step is not needed if using Netbox)

.. code-block:: text

    python db_create.py

Restart NetConfig Service
^^^^^^^^^^^^^^^^^^^^^^^^^

Restart Netconfig service for all changes to take effect

.. code-block:: text

    sudo supervisorctl restart netconfig

Start and enable Redis:

.. code-block:: text

    sudo systemctl enable redis
    sudo systemctl start redis

Final security changes
^^^^^^^^^^^^^^^^^^^^^^

Open the proper ports using firewall-cmd:

.. code-block:: text

    sudo firewall-cmd --permanent --add-port 80/tcp
    sudo firewall-cmd --permanent --add-port 443/tcp
    sudo firewall-cmd --reload

And apply the needed SELinux permissions:

.. code-block:: text

    sudo setsebool -P httpd_can_network_connect 1

Important next steps!
^^^^^^^^^^^^^^^^^^^^^

If using Netbox, please consult the Netbox Integration section for instructions on setting up Netbox to interface with Netconfig

Credit
^^^^^^

Credit to Reddit user /u/thewhitedragon for writing the template used for this
instruction set.

Credit /u/admiralspark for the CentOS instructions. 