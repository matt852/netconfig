import logging


class LogHandler(object):

    def __init__(self, filename="netconfig.log", level="INFO"):

        self.logger = logging.getLogger("__name__")
        logging.getLogger().setLevel(level.upper())
        logging.basicConfig(filename=filename,
                            format='%(asctime)s %(levelname)s: %(message)s')

    def write_log(self, msg, user=None):
        """
        Write 'msg' to logger.
        """
        if user:
            self.logger.info(user + ' - ' + msg)
        else:
            self.logger.info(msg)
