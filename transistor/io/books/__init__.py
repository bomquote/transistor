# -*- coding: utf-8 -*-
"""
transistor.io.books
~~~~~~~~~~~~
This module implements classes, functions, and methods for Transistor to ingest and
export data.  During ingest, it should provide a facility to transform target data
into tasks, later assigned in the course of gevent based asynchronous I/O execution.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
from .bookstate import StatefulBook