# -*- coding: utf-8 -*-
"""
transistor.persistence
~~~~~~~~~~~~
This module implements classes and methods to aid persistence, including
database, spreadsheet export, write to file.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from .extractor import ScrapedDataExtractor
from .container import SplashScraperContainer
from .item import Item, Field
from .newt_db.newt_crud import get_job_results, delete_job

__all__ = ['delete_job', 'Field', 'get_job_results', 'Item','ScrapedDataExtractor',
           'SplashScraperContainer']
