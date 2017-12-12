Original Install Guide for Ubuntu 16.04 in home directory
=========================================================

Installation Start
------------------

This document starts with an initial, clean installation of Ubuntu 16.04 Server already setup and ready


Update Ubuntu
-------------

Update Ubuntu, install required system packages, and reboot

		sudo apt-get update && sudo apt-get -y upgrade && sudo apt-get -y dist-upgrade && sudo apt-get -y autoremove
		sudo reboot now
		sudo apt-get -y install python python-pip nginx redis-server supervisor libssl-dev libsasl2-dev gunicorn git


Create new Netconfig user
-------------------------

Create a new netconfig user to install and run Netconfig under.
Set any password you choose.
When prompted for full name, room number, phone numbers, etc, you can leave them all blank

		sudo adduser netconfig
		sudo usermod -aG sudo netconfig

Switch to the new Netconfig user

		su - netconfig


Download NetConfig
------------------

Download NetConfig and install required Python packages

		cd ~/
		git clone -b master https://github.com/v1tal3/netconfig.git
		cd netconfig
		sudo pip install --upgrade pip
		sudo pip install -r requirements.txt


Configure NGINX
---------------


Remove default in NGINX sites-enabled, and create a new site for Netconfig.
Replace "domain.com" with your actual Domain

		sudo rm /etc/nginx/sites-enabled/default
		sudo touch /etc/nginx/sites-available/netconfig
		sudo vi /etc/nginx/sites-available/netconfig



Begin contents of /etc/nginx/sites-available/netconfig
------------------------------------------------------

------------------------------------------------------
        server {
                listen						80;
                server_name				netconfig.domain.com;
                return						301 https://$host$request_uri;
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
                            alias		/home/netconfig/netconfig/app/;
                }
        }
------------------------------------------------------

End contents of /etc/nginx/sites-available/netconfig
------------------------------------------------------


Create symlink
--------------

Create symlink for netconfig file into nginx/sites-enabled

		sudo ln -s /etc/nginx/sites-available/netconfig /etc/nginx/sites-enabled



Service
-------

Create and fill out netconfig.service

		sudo touch /etc/systemd/system/netconfig.service
		sudo vi /etc/systemd/system/netconfig.service



Begin contents of /etc/systemd/system/netconfig.service
-------------------------------------------------------

-------------------------------------------------------
        [Unit]
        Description=uWSGI instance to serve NetConfig
        After=network.target

        [Service]
        User=netconfig
        Group=www-data
        WorkingDirectory=/home/netconfig/netconfig
        Environment="PATH=/usr/bin/python"
        ExecStart=/usr/bin/uwsgi --ini netconfig.ini

        [Install]
        WantedBy=multi-user.target
-------------------------------------------------------

End contents of /etc/systemd/system/netconfig.service
-----------------------------------------------------


Start and Enable Netconfig services
-----------------------------------

Start and enable services related to NetConfig running in the background

		sudo systemctl daemon-reload
		sudo systemctl start netconfig
		sudo systemctl enable netconfig



-------------------------
Supervisord Configuration
-------------------------

Create and fill out netconfig.conf for gUnicorn

		sudo touch /etc/supervisor/conf.d/netconfig.conf
		sudo vi /etc/supervisor/conf.d/netconfig.conf



Begin Contents of /etc/supervisor/conf.d/netconfig.conf
-------------------------------------------------------

-------------------------------------------------------
        [program:netconfig]
        command = gunicorn app:app -b localhost:8000
        directory = /home/netconfig/netconfig
        user = netconfig
-------------------------------------------------------

End Contents of /etc/supervisor/conf.d/netconfig.conf
-------------------------------------------------------


Restart Services
----------------

		sudo pkill gunicorn
		sudo supervisorctl reread
		sudo supervisorctl update
		sudo supervisorctl restart netconfig


Configure Self-Signed SSL Cert
------------------------------

Run these commands to generate a self-signed SSL certificate

Create a new directory for the certs and move into it

		sudo mkdir /etc/nginx/ssl
		cd /etc/nginx/ssl

Generate the self-signed SSL certs.
When prompted to create a certificate password, anything will work
When generating the certificate, fill out the relevant details as requested (Country, State, etc.).
However for common name, set it to your domain (domain.com)

		sudo openssl genrsa -des3 -out server.key 2048										--> (can use anything for password)
		sudo openssl req -new -key server.key -out server.csr		          --> (for password, enter whatever was used above)
		sudo cp server.key server.key.org
		sudo openssl rsa -in server.key.org -out server.key				        --> (for password, enter whatever was in the first line)
		sudo openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt


Restart NGINX services

		sudo systemctl restart nginx


Configure NetConfig Settings
----------------------------

Copy settings template file

		cd ~/netconfig
		cp instance/settings_template.py instance/settings.py

Modify the contents of the file:

		vi instance/settings.py

The only required settings that need to be changed in the file are as follows:

		SECRET_KEY - Generate a random key to use with the program.		You can provide you own, or use the provided "generate_secret_key.py" script to generate one for you.		This can be run with the command "python ~/netconfig/generate_secret_key.py"

		DATALOCATION - Specify if you want to use a local database on the server, and configure the inventory manually, or use an existing Netbox installation

		NETBOXSERVER - If using an existing Netbox installation, this is the Netbox server hostname.		Otherwise this value is not used


Create local database
---------------------

If using local SQLAlchemy database, create the database (this step is not needed if using Netbox)

		python db_create.py


Restart NetConfig Service
-------------------------

Restart Netconfig service for all changes to take effect

		sudo supervisorctl restart netconfig


Important next steps!
---------------------

If using Netbox, please consult NETBOX-INTEGRATION.txt for instructions on setting up Netbox to interface with Netconfig
