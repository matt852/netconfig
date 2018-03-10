import unittest
import tempfile
import os
from app.log_handler import LogHandler


class TestLogHandler(unittest.TestCase):

    def setUp(self):
        """Initialize static class testing variables."""
        self.tmpfile = os.path.join(tempfile.gettempdir(), "log.log")
        self.logger = LogHandler(self.tmpfile)

    def test_filename(self):
        assert self.logger.filename == self.tmpfile

    def test_log_level(self):
        assert self.logger.level == "INFO"
        self.logger.level = "DEBUG"
        assert self.logger.level == "DEBUG"
