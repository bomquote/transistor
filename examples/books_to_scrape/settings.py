# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.settings
~~~~~~~~~~~~
This module implements an example application configuration.
A configuration like this would primarily be needed to provide database URI
parameters for newt.db or an alternative persistence model. Also, a place to
store attributes like CRAWLERA_REGIONS is helpful, if you use Crawlera.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
import os
from transistor.utility.utils import get_debug_flag


class Constants:
    """Constants used throughout the application.
    All constants settings/data that are not actual/official configuration
    options for libraries like Flask, Celery, or other extensions goes here.
    """
    ENVIRONMENT = property(lambda self: self.__class__.__name__)


class Config(Constants):
    """Base configuration."""
    basedir = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(
        os.path.dirname(__file__)))))

    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # `transistor\transistor`

    # Logging Settings
    # ------------------------------
    # This config section will deal with the logging settings, adjust as needed.

    # Logging Config Path
    # see https://docs.python.org/library/logging.config.html#logging.config.fileConfig
    # for more details. Should either be None or a path to a file
    # If this is set to a path, consider setting USE_DEFAULT_LOGGING to False
    # otherwise there may be interactions between the log configuration file
    # and the default logging setting.
    #
    # If set to a file path, this should be an absolute file path
    LOG_CONF_FILE = None
    # When set to True this will enable the default logging configuration
    # LOG_DEFAULT_CONF below to determine logging
    USE_DEFAULT_LOGGING = True

    # Path to store the INFO and ERROR logs
    #
    # If set to a file path, this should be an absolute path
    LOG_PATH = os.path.join(APP_DIR, 'logs')

    LOG_DEFAULT_CONF = {
        'version': 1,
        'disable_existing_loggers': False,

        'formatters': {
            'standard': {
                'format': '%(asctime)s %(levelname)-7s %(name)-25s %(message)s'
            },
            'advanced': {
                'format': '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            }
        },
        'handlers': {
            'console': {
                'level': 'NOTSET',
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
            },
            'infolog': {
                'level': 'INFO',
                'formatter': 'standard',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_PATH, 'info.log'),
                'mode': 'a',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
            },
            'errorlog': {
                'level': 'ERROR',
                'formatter': 'standard',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(LOG_PATH, 'error.log'),
                'mode': 'a',
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5,
            }
        },
        'loggers': {
            'transistor': {
                'handlers': ['infolog', 'errorlog'],
                'level': 'INFO',
                'propagate': True
            },
        }
    }

    CRAWLERA_REGIONS = ['CRAWLERA_ALL', 'CRAWLERA_USA', 'CRAWLERA_CN']

    # /rabbitmq - only relevant if you use rabbitmq
    broker_url = 'amqp://guest:guest@localhost:5672//'
    broker_heartbeat = 0
    default_exchange_type = 'direct'
    # /end rabbitmq

class ProdConfig(Config):
    """Production configuration."""
    ENV = 'prod'
    DEBUG = False
    NEWT_DB_URI = f"host=localhost port=5433 dbname=newtdb user={os.environ.get('PG_USER')} password={os.environ.get('PG_PW')}"


class DevConfig(Config):
    """Development configuration."""
    ENV = 'dev'
    DEBUG = True
    NEWT_DB_URI = "host=localhost port=5432 dbname=newtdb user=postgres password=password"


class TestConfig(Config):
    """Testing configuration"""
    TESTING = True

    if 'appveyor' in os.environ['USERNAME']:
        NEWT_DB_URI = "host=localhost port=5432 dbname=postgres user=postgres password=Password12!"

    else:
        # local development
        if get_debug_flag():
            NEWT_DB_URI = "host=localhost port=5432 dbname=newtdbtest user=postgres password=password"

        # must be live server testdb
        else:
            NEWT_DB_URI = f"host=localhost port=5433 dbname=newtdbtest user={os.environ.get('PG_USER')} password={os.environ.get('SCRDBTEST_PW')}"