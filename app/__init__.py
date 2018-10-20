import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from flask_script import Manager
from config import Config
from .data_handler import DataHandler
from .log_handler import LogHandler
from .ssh_handler import SSHHandler


app = Flask(__name__, instance_relative_config=True)
app.config.from_object(Config)
app.config.from_pyfile('settings.py', silent=True)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
Bootstrap(app)
try:
    datahandler = DataHandler(app.config['DATALOCATION'],
                              netboxURL=app.config['NETBOXSERVER'])
except KeyError:
    datahandler = DataHandler('local')

logger = LogHandler(filename=app.config['SYSLOGFILE'])

sshhandler = SSHHandler()

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
