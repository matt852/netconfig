from logging import FileHandler, Formatter, getLogger
from logging import INFO, DEBUG, ERROR, WARNING
from flask import session

# This enables us to use different log levels


class LogHandler(object):
    """Global log handler class."""

    def __init__(self, filename="netconfig.log", level="INFO"):
        """Initialize class."""
        self.filename = filename
        self.level = level.upper()
        self.logger = getLogger(__name__)
        self.logger.setLevel(self.level)
        # Create a file handler
        self.handler = FileHandler(filename)
        self.handler.setLevel(INFO)
        # Create a logging format
        self.formatter = Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
        self.handler.setFormatter(formatter)
        # Add the handlers to the logger
        self.logger.addHandler(self.handler)

    def write_log(self, msg, user=None):
        """Write formatted 'msg' to logger."""
        # If a specific user is specific, log that user name
        if user:
            self.logger.info(user + ' - ' + msg)
        else:
            # Otherwise use currently logged in user
            try:
                # Log with currently logged in user
                self.logger.info(session['USER'] + ' - ' + msg)
            except (RuntimeError, KeyError):
                # If no user logged in, just log message only
                self.logger.info(msg)
