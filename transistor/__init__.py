# -*- coding: utf-8 -*-
"""
transistor
~~~~~~~~~~~~
Web data collection and storage for intelligent use cases.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from .books import StatefulBook
from .browsers import SplashBrowser
from .managers import BaseWorkGroupManager
from .scrapers import SplashScraper
from .workers import BaseWorker, BaseGroup, WorkGroup

name = "transistor"

__all__ = [BaseGroup, BaseWorker, BaseWorkGroupManager, SplashBrowser,
           SplashScraper, StatefulBook, WorkGroup]