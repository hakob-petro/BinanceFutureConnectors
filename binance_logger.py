# -*- coding: utf-8 -*-

# Standard modules
import json
import logging
from logging import getLogger, FileHandler, Formatter, StreamHandler, Logger

# Project modules
from constants import ProjectConstants

__all__ = [
    "JsonFormatter",
    "init_logger"
]


class JsonFormatter(Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    """

    def __init__(self, fmt_dict: dict = None, time_format: str = "%Y-%m-%dT%H:%M:%S", msec_format: str = "%s.%03dZ"):
        """
        :param fmt_dict: Key: logging format attribute pairs. Defaults to {"message": "message"}.
        :type fmt_dict: dict
        :param time_format: time.strftime() format string. Default: "%Y-%m-%dT%H:%M:%S"
        :type time_format: str
        :param msec_format: Microsecond formatting. Appended at the end. Default: "%s.%03dZ"
        :type msec_format: str
        """
        super(JsonFormatter, self).__init__()
        self.fmt_dict = fmt_dict if fmt_dict is not None else {"message": "message"}
        self.default_time_format = time_format
        self.default_msec_format = msec_format
        self.datefmt = None

    def usesTime(self) -> bool:
        """
        Overwritten to look for the attribute in the format dict values instead of the fmt string.
        """
        return "asctime" in self.fmt_dict.values()

    def formatMessage(self, record) -> dict:
        """
        Overwritten to return a dictionary of the relevant LogRecord attributes instead of a string.
        KeyError is raised if an unknown attribute is provided in the fmt_dict.
        """
        return {fmt_key: record.__dict__[fmt_val] for fmt_key, fmt_val in self.fmt_dict.items()}

    def format(self, record) -> str:
        """
        Mostly the same as the parent's class method, the difference being that a dict is manipulated and dumped as JSON
        instead of a string.
        """
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        message_dict = self.formatMessage(record)
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            message_dict["exc_info"] = record.exc_text
        if record.stack_info:
            message_dict["stack_info"] = self.formatStack(record.stack_info)
        return json.dumps(message_dict, default=str)


def init_logger(log_file_path: str = ProjectConstants.LOG_FILE) -> Logger:
    """
    Initialize logger.

    :param log_file_path: Loging file.
    :return logging.Logger: Logger object
    """
    if ProjectConstants.VERBOSE == 3:
        logging.getLogger().setLevel(logging.INFO)
    elif ProjectConstants.VERBOSE == 2:
        logging.getLogger().setLevel(logging.DEBUG)
    elif ProjectConstants.VERBOSE == 1:
        logging.getLogger().setLevel(logging.WARNING)
    elif ProjectConstants.VERBOSE == 0:
        logging.getLogger().setLevel(logging.ERROR)

    logger = getLogger()
    logger.setLevel(logging.INFO)
    console_formatter = Formatter(
        '%(asctime)s  %(process)d  %(processName)s  %(thread)d  %(threadName)s  %(name)s  %(lineno)d'
        '  %(filename)s  %(funcName)s  %(levelname)s: %(message)s')

    json_formatter = JsonFormatter({
        "timestamp": "asctime",
        "process_id": "process",
        "process_name": "processName",
        "thread_id": "thread",
        "thread_name": "threadName",
        "logger_name": "name",
        "line_num": "lineno",
        "file_name": "filename",
        "func_name": "funcName",
        "level": "levelname",
        "message": "message"
    })

    console_handler = StreamHandler()
    console_handler.setFormatter(console_formatter)
    file_handler = FileHandler(log_file_path)
    file_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger
