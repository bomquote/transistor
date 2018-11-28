# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.persistence
~~~~~~~~~~~~
This module serves as an example of how to setup a persistence model for Transistor
with postgresql + newt.db.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from .serialization import BookItems, BookItemsLoader
from .newt_db import ndb