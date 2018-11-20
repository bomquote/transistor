# -*- coding: utf-8 -*-
"""
transistor.persistence.exporters
~~~~~~~~~~~~
This module implements classes that extract (serialize) the data inside
a BaseWorker from a SplashScraper for persistence in newt.db,
export to JSON, CSV, XML, Pickle, or customized export accomplished by
subclassing BaseItemExporter and overriding it as needed.

Most of this module is heavily inspired or else copied from Scrapy. It has
been modified to fit Transistor's API in requiring a scraper and items
object. Also, Transistor only supports python 3. Otherwise, this module
generally follows Scrapy's API and uses Scrapy's documentation.

:copyright: Original scrapy.exporters from scrapy==1.5.1 is
Copyright by it's authors and further changes or contributions here are
Copyright (C) 2018 by BOM Quote Limited.
:license: Original scrapy.exporters from scrapy==1.5.1 license is found at
https://github.com/scrapy/scrapy/archive/1.5.1.zip
and further changes or contributions here are licensed under The MIT
License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from .base import BaseItemExporter
from .json import JsonItemExporter, JsonLinesItemExporter
from .xml import XmlItemExporter
from .exporters import (CsvItemExporter, MarshalItemExporter, PickleItemExporter,
                        PprintItemExporter, PythonItemExporter)


__all__ = ['BaseItemExporter', 'CsvItemExporter', 'JsonItemExporter',
           'JsonLinesItemExporter', 'PickleItemExporter', 'PprintItemExporter',
            'MarshalItemExporter', 'PythonItemExporter', 'XmlItemExporter']