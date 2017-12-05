from flask import Flask, flash, redirect, render_template, request, session, abort
import os
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from config import basedir

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('settings.py', silent=True)
db = SQLAlchemy(app)

from app import views, models

manager = Manager(app)
if __name__ == "__main__":
    app.secret_key = os.urandom(25)
    manager.run()

# Notes:
# To install python-ldap on Mac OSX, run this command from Terminal:
# export CFLAGS="-I$(xcrun --show-sdk-path)/usr/include/sasl"
