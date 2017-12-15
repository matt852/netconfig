from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('settings.py', silent=True)
db = SQLAlchemy(app)

from app import views, models

manager = Manager(app)
if __name__ == "__main__":
    app.secret_key = os.urandom(25)
    manager.run()
