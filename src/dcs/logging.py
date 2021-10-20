
import logging
from termcolor import colored

# https://alexandra-zaharia.github.io/posts/make-your-own-custom-color-formatter-with-python-logging/

class ColorFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

    grey = '\x1b[38;21m'
    blue = '\x1b[38;5;39m'
    yellow = '\x1b[38;5;226m'
    red = '\x1b[38;5;196m'
    bold_red = '\x1b[31;1m'
    reset = '\x1b[0m'

    def __init__(self, fmt="%(levelname)-10s %(message)s"):
        super().__init__(fmt)
        # "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.reset + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset,
            # 21: self.blue + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

    # ch.setLevel(logging.DEBUG)

class AddLocationFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.

    Rather than use actual contextual information, we just use random
    data in this demo.
    """

    def __init__(self, suppress=[]):
        self.where = ""
        self.suppress = suppress

    def set_location(self, where):
        self.where = where

    dword_types = {
      'HC0': { "prefix": '\033[1;37;104m' }, # white on blue
      'HC1': { "prefix": '\033[0;37;104m' }, # grey on blue
      'HC2': { "prefix": '\033[0;37;104m' },
      'HC3': { "prefix": '\033[0;37;104m' },
      'MCM': { "prefix": '\033[1;34m' }, # bold blue
      'MSK': { "prefix": '\033[30m', "suppress": False },
      'ADC': { "prefix": '\033[90m', "suppress": False },
      'TRK': { "prefix": '\033[0;32m' },
      'EOT': { "prefix": '\033[0;34m' },
      'EOD': { "prefix": '\033[0;34m' },
      'SKP': { "prefix": '\033[0;31m' },
    }

    def filter(self, record):

        rectype = record.msg[:3]

        if rectype in self.suppress:
            return False

        if rectype not in self.dword_types:
            return True

        opt = self.dword_types[rectype]

        if 'suppress' in opt and opt['suppress']:
            return False

        record.msg = f"{self.where}{opt['prefix']} {record.msg:45s}"

        return True
