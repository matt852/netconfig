import unittest
import os
from app.plugins.log_handler import LogHandler
from tempfile import gettempdir


class TestLogHandler(unittest.TestCase):
    """Unit testing for log handler class."""

    def setUp(self):
        """Initialize static class testing variables."""
        self.tmpfile = os.path.join(gettempdir(), "log.log")
        self.logger = LogHandler(self.tmpfile)

    def tearDown(self):
        """Run on completion of tests."""
        try:
            os.remove(self.tmpfile)
            return True
        # the file may not exist
        # TODO investigate why
        except (IOError, OSError):
            return True

    def test_filename(self):
        """Validate filename is what's expected."""
        self.assertEqual(self.logger.filename, self.tmpfile)

    def test_log_level(self):
        """Validate logging level is correct and can be changed successfully."""
        self.assertEqual(self.logger.level, "INFO")
        self.logger.level = "DEBUG"
        self.assertEqual(self.logger.level, "DEBUG")
