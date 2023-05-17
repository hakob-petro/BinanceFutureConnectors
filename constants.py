# -*- coding: utf-8 -*-

# Standard modules
import os
import json
from typing import Final
import configparser

__all__ = [
    "ProjectConstants"
]


class ConstantsBase:
    """
    Parse config file of json format and return ConfigParser object. Base class for all constant namespace classes.
    """
    config = configparser.ConfigParser(allow_no_value=True)
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "config.json"), "r", encoding="utf-8") as f:
        dict_obj = json.load(f)
    config.read_dict(dict_obj)


class ProjectConstants(ConstantsBase):
    __slots__ = ()
    VERBOSE: Final[int] = ConstantsBase.config.getint("Project", "VERBOSE")
    LOG_FILE: Final[str] = ConstantsBase.config.get("Project", "LOG_FILE")
    CONN_NUM: Final[int] = ConstantsBase.config.getint("Project", "CONN_NUM")
    CONN_TIMEOUT: Final[int] = ConstantsBase.config.getint("Project", "CONN_TIMEOUT")
    BINANCE_FUTURES_WS: Final[str] = ConstantsBase.config.get("Project", "BINANCE_FUTURES_WS")
    DATA_DIR: Final[str] = ConstantsBase.config.get("Project", "DATA_DIR")
