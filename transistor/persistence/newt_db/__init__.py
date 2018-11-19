# -*- coding: utf-8 -*-
"""
transistor.persistence.newt_db
~~~~~~~~~~~~
This module implements container classes for storing python objects in newt.db.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from ..container import SplashScraperContainer
from ..extractor import ScrapedDataExtractor

from .newt_crud import get_job_results, delete_job