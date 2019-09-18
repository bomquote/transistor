# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.persistence.newt_db
~~~~~~~~~~~~
This module serves as an example for how to create a newt.db connection called ndb.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""


import os
import newt.db
from examples.books_to_scrape.settings import DevConfig, ProdConfig, TestConfig
from transistor.utility.utils import get_debug_flag


def get_config():
    if 'appveyor' in os.environ['USERNAME']:
        return TestConfig
    return DevConfig if get_debug_flag() else ProdConfig


CONFIG = get_config()
ndb = newt.db.connection(CONFIG.NEWT_DB_URI)