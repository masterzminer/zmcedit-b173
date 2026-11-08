import traceback
import logging
from logging.handlers import RotatingFileHandler
import directories
from arguments import LOG_LEVEL
from log_level import LogLevel

_logger = None

def trace(*values: object):
    _log_at(values, level=LogLevel.TRACE)


def debug(*values: object):
    _log_at(values, level=LogLevel.DEBUG)


def info(*values: object):
    _log_at(values, level=LogLevel.INFO)


def warn(*values: object):
    _log_at(values, level=LogLevel.WARN)


def error(*values: object, hide_traceback = False):
    _log_at(values, level=LogLevel.ERROR)
    if not hide_traceback:
        traceback.print_exc()


def _log_at(*values: object, level: LogLevel):
    pass
    # Skip if too low level of logging
    if level.value < LOG_LEVEL.value:
        return

    _logger.log(
        # Log value
        msg=" ".join(map(str, *values)),
        # Always using info for the built in log level, using a custom level instead
        level=logging.INFO,
        # Add the custom level
        extra={"custom_level": level.name},
        # 3 stacks, one for this function, one for the sub type function, one for this module
        stacklevel=3
    )


def init():
    global _logger
    # Using a custom logger to avoid the bs that other random modules have, this is just for logs directly given to the zmcedit application
    _logger = logging.getLogger("zMCEdit")

    _logger.propagate = False
    _logger.handlers.clear()

    _logger.setLevel(logging.INFO)

    fmt = logging.Formatter('[%(custom_level)-5s][%(module)-15s][%(lineno)-4d]: %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    _logger.addHandler(ch)

    # TODO fix the issue with an invalid filter Test showing up

    # Keep up to one backup log file, essentially just hold onto one 10mb log file before allowing old logs to be erased
    fh = RotatingFileHandler(directories.LOG_FILE, maxBytes = 10 * 1240 * 1240, backupCount=1)
    fh.setLevel(logging.INFO)
    fh.setFormatter(fmt)
    _logger.addHandler(fh)

init()