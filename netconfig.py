#!/usr/bin/python3

from app import app, db
from os import environ


@app.shell_context_processor
def make_shell_context():
    return {'db': db}


if __name__ == "__main__":
    environ['FLASK_ENV'] = 'development'
    # app.run(host='127.0.0.1', port=5000, debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True, environ='development')
