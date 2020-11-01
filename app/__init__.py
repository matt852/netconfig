#!/usr/bin/python3

import os
from app.plugins.data_handler import DataHandler
from app.momentjs import MomentJS
from app.plugins.log_handler import LogHandler
from app.plugins.ssh_handler import SSHHandler
from config import Config
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from flask_script import Manager
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__, instance_relative_config=True)
app.config.from_object(Config)
app.config.from_pyfile('settings.py', silent=True)
app.jinja_env.globals['momentjs'] = MomentJS
db = SQLAlchemy(app)
migrate = Migrate(app, db)
Bootstrap(app)
datahandler = DataHandler('local')
logger = LogHandler(filename=app.config['SYSLOGFILE'])
sshhandler = SSHHandler()

# Removing NetBox support for now
# try:
#     datahandler = DataHandler(app.config['DATALOCATION'],
#                               netbox_url=app.config['NETBOXSERVER'])
# except KeyError:
#     datahandler = DataHandler('local')

# Errors blueprint
from app.errors import bp as errors_bp
app.register_blueprint(errors_bp)

# Authentication blueprint
from app.auth import bp as auth_bp
app.register_blueprint(auth_bp, url_prefix='/auth')

from app import views, models

manager = Manager(app)
if __name__ == "__main__":
    app.secret_key = os.urandom(25)
    manager.run()
