# -*- coding: utf-8 -*-
"""
transistor.tasks.books
~~~~~~~~~~~~
This module implements classes, functions, and methods for Transistor to ingest
data from spreadsheets.  During ingest, it transforms target data into tasks,
to be later assigned in the course of gevent based asynchronous I/O execution.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
from .bookstate import StatefulBook