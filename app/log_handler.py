import logging


class LogHandler(object):

    def __init__(self, filename="netconfig.log", level="INFO"):

        self.logger = logging.getLogger("__name__")
        self.filename = filename
        self.level = level.upper()

        logging.getLogger().setLevel(self.level)
        logging.basicConfig(filename=self.filename,
                            format='%(asctime)s %(levelname)s: %(message)s')

    def write_log(self, msg, user=None):
        """
        Write 'msg' to logger.
        """
        if user:
            self.logger.info(user + ' - ' + msg)
        else:
            self.logger.info(msg)
