# -*- coding: utf-8 -*-
"""
transistor
~~~~~~~~~~~~
Web data collection and storage for intelligent use cases.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from transistor.books import StatefulBook
from transistor.browsers import SplashBrowser
from transistor.managers import BaseWorkGroupManager
from transistor.scrapers import SplashScraper
from transistor.workers import BaseWorker, BaseGroup, WorkGroup
from transistor.persistence import (delete_job, Field, get_job_results, Item,
                                    SplashScraperItems, BaseItemExporter)

name = "transistor"

__all__ = ['BaseGroup', 'BaseWorker', 'BaseWorkGroupManager', 'delete_job',
           'Field', 'get_job_results', 'Item', 'SplashBrowser', 'SplashScraper',
           'SplashScraperItems', 'StatefulBook', 'BaseItemExporter',
           'WorkGroup']