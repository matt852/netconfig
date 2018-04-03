import os
from celery import Celery
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_script import Manager
from .data_handler import DataHandler
from .log_handler import LogHandler
from .ssh_handler import SSHHandler


app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('settings.py', silent=True)
db = SQLAlchemy(app)
Bootstrap(app)
try:
    datahandler = DataHandler(app.config['DATALOCATION'],
                              netboxURL=app.config['NETBOXSERVER'])
except KeyError:
    datahandler = DataHandler('local')

logger = LogHandler(app.config['SYSLOGFILE'])

sshhandler = SSHHandler()

# Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'])
celery.conf.update(app.config)

# Blueprints
from app.errors import bp as errors_bp
app.register_blueprint(errors_bp)

from app import views, models

manager = Manager(app)
if __name__ == "__main__":
    app.secret_key = os.urandom(25)
    manager.run()
