import os
import logging
import logging.config
import tempfile

import ccfw_project_data

"""
sets up basic functionality of the framework. most of which needs to be initialized prior to the
tools being loaded

logging
pathing
project data
"""

# LOGGING #


global logger_name
logger_name = 'DCCF'
logger_path = tempfile.gettempdir() + '\\' + logger_name + '.log'

global default_log_level
default_log_level = 30


def configure_logger(name, log_path):
    """
    set up formatting for logger including where the log is written to

    :param name: name of the logger
    :type name: string
    :param log_path: path for the logger to write to
    :type log_path: string
    :return: the project logger
    :rtype: logger
    """

    log_dict = {
        'version': 1,
        'formatters': {
            'default': {'format': '%(asctime)s - %(levelname)s - line number: %(lineno)d - %(module)s - %(message)s',
                        'datefmt': '%d-%m-%Y %H:%M:%S'}
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'default',
                'filename': log_path,
                'maxBytes': 1024,
                'backupCount': 3
            }
        },
        'loggers': {
            logger_name: {
                'level': 'DEBUG',
                'handlers': ['console', 'file']
            }
        },
        'disable_existing_loggers': False
    }

    logging.config.dictConfig(log_dict)
    logger = logging.getLogger(name)
    return logger


global logger
logger = configure_logger(logger_name, logger_path)
logger.info('logger initialized')


def get_logger_level():
    """
    calls logger.getEffectiveLevel() which return an int value for the current log level
    based onm the below chart

    not set = 0
    debug = 10
    info = 20
    warning = 30
    error = 40
    critical = 50

    :return: logger level
    :rtype: integer
    """

    '''
    ints mapped to log severity level


    '''
    return logger.getEffectiveLevel()


def set_logger_level(level):
    """
    set the log level for all handlers (console and file for us)

    :param level:
    :type level:
    """
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


def get_all_loggers_by_name():
    """
    prints out all of the loggers used in maya
    """
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for log in loggers:
        print('log name :: {}'.format(log.name))


# PATHING #

# TAs will be responsible for making sure shelf.jason exists
relative_jason_path = '\\Content\\Art\\Maya\\shelf.json'
relative_project_xml_path = 'project_data.xml'
relative_sitepackages_path = 'site-packages'

logger.info('project paths initialized')


# Pathing
relative_jason_path = '\\Content\\Art\\Maya\\shelf.json'
relative_project_xml_path = 'project_data.xml'
relative_sitepackages_path = 'site-packages'

framework_paths = ccfw_project_data.set_paths(relative_jason_path, relative_project_xml_path, relative_sitepackages_path)
logger.info(' framework initialized')

project_data = ccfw_project_data.get_project_XML_data(framework_paths)
logger.info(' project data initialized')