#!/usr/bin/python3

import logging
import os


class LogHandler(object):
    """Global log handler class."""

    def __init__(self, filename='log/syslog.log', level=None):
        """Initialize class."""
        self.default_user = 'Unknown User'
        self._create_log_directory()
        self.logger = logging.getLogger(__name__)
        self.filename = filename
        # Level options: DEBUG, INFO, WARNING, ERROR, CRITICAL
        # Default to DEBUG
        if not level:
            level = 'DEBUG'
        self.level = level.upper()
        self.logger.setLevel(self.level)
        logging.basicConfig(filename=self.filename,
                            format='%(asctime)s %(levelname)s: %(message)s')

    @staticmethod
    def _create_log_directory():
        for x in os.listdir(os.getcwd()):
            if x == 'log':
                break
        else:
            os.makedirs('log')

    def critical(self, msg, user=None, e=None, exc_info=False):
        """Write formatted 'msg' to logger."""
        # If a specific user is specific, log that user name
        user = user or self.default_user
        self.logger.critical(user + ' - ' + msg, exc_info=exc_info)
        # If exception error message provided, log as well
        if e:
            self.logger.critical(e, exc_info=exc_info)

    def error(self, msg, user=None, e=None, exc_info=False):
        """Write formatted 'msg' to logger."""
        # If a specific user is specific, log that user name
        user = user or self.default_user
        self.logger.error(user + ' - ' + msg, exc_info=exc_info)
        # If exception error message provided, log as well
        if e:
            self.logger.error(e, exc_info=exc_info)

    def warning(self, msg, user=None, e=None, exc_info=False):
        """Write formatted 'msg' to logger."""
        # If a specific user is specific, log that user name
        user = user or self.default_user
        self.logger.warning(user + ' - ' + msg, exc_info=exc_info)
        # If exception error message provided, log as well
        if e:
            self.logger.warning(e, exc_info=exc_info)

    def info(self, msg, user=None, e=None, exc_info=False):
        """Write formatted 'msg' to logger."""
        # If a specific user is specific, log that user name
        user = user or self.default_user
        self.logger.info(user + ' - ' + msg, exc_info=exc_info)
        # If exception error message provided, log as well
        if e:
            self.logger.info(e, exc_info=exc_info)

    def debug(self, msg, user=None, e=None, exc_info=False):
        """Write formatted 'msg' to logger."""
        # If a specific user is specific, log that user name
        user = user or self.default_user
        self.logger.debug(user + ' - ' + msg, exc_info=exc_info)
        # If exception error message provided, log as well
        if e:
            self.logger.debug(e, exc_info=exc_info)
