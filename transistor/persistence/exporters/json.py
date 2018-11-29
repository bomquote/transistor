# -*- coding: utf-8 -*-
"""
transistor.persistence.exporters.json
~~~~~~~~~~~~
This module implements classes that export (serialize) the data inside
a BaseWorker from a SplashScraper to JSON.

Most of this module is heavily inspired or else copied from Scrapy. It has
been modified to fit Transistor's API only supports python 3. Otherwise, this
module generally follows Scrapy's API and uses Scrapy's documentation.

:copyright: Original scrapy.exporters from scrapy==1.5.1 is
Copyright by it's authors and further changes or contributions here are
Copyright (C) 2018 by BOM Quote Limited.
:license: Original scrapy.exporters from scrapy==1.5.1 license is found at
https://github.com/scrapy/scrapy/archive/1.5.1.zip
and further changes or contributions here are licensed under The MIT
License, see LICENSE for more details.
~~~~~~~~~~~~
"""

__all__ = ['JsonLinesItemExporter', 'JsonItemExporter']


from .base import BaseItemExporter
from transistor.utility.python import to_bytes
from transistor.utility.serialize import TransistorJSONEncoder


class JsonLinesItemExporter(BaseItemExporter):
    """
    Exports Items in JSON format to the specified file-like object,
    writing one JSON-encoded item per line. The additional constructor
    arguments are passed to the BaseItemExporter constructor, and the
    leftover arguments to the JSONEncoder constructor, so you can use
    any JSONEncoder constructor argument to customize this exporter.

    Unlike the one produced by JsonItemExporter, the format produced by
    this exporter is well suited for serializing large amounts of data.

    A typical output of this exporter would be:
        {"name": "Color TV", "price": "1200"}
        {"name": "DVD player", "price": "200"}

    Unlike the one produced by JsonItemExporter, the format produced by
    this exporter is well suited for serializing large amounts of data.
    """

    def __init__(self, file, **kwargs):
        """
        :param file: file – the file-like object to use for exporting the data.
        It's write method should accept bytes (a disk file opened in binary
        mode, a io.BytesIO object, etc)
        :param kwargs:
        """
        super().__init__()
        self._configure(kwargs, dont_fail=True)
        self.file = file
        kwargs.setdefault('ensure_ascii', not self.encoding)
        self.encoder = TransistorJSONEncoder(**kwargs)

    def export_item(self, item):
        itemdict = dict(self._get_serialized_fields(item))
        data = self.encoder.encode(itemdict) + '\n'
        self.file.write(to_bytes(data, self.encoding))


class JsonItemExporter(BaseItemExporter):
    """
    Exports Items in JSON format to the specified file-like object,
    writing all objects as a list of objects. The additional constructor
    arguments are passed to the BaseItemExporter constructor, and the
    leftover arguments to the JSONEncoder constructor, so you can use
    any JSONEncoder constructor argument to customize this exporter.

    A typical output of this exporter would be:
        [{"name": "Color TV", "price": "1200"},
        {"name": "DVD player", "price": "200"}]
    """

    def __init__(self, file, **kwargs):
        """
        :param file: file – the file-like object to use for exporting the
        data. Its write method should accept bytes (a disk file opened
        in binary mode, a io.BytesIO object, etc)
        :param kwargs:
        """
        super().__init__()
        self._configure(kwargs, dont_fail=True)
        self.file = file
        # there is a small difference between the behaviour or JsonItemExporter.indent
        # and TransistorJSONEncoder.indent. TransistorJSONEncoder.indent=None is
        # needed to prevent the addition of newlines everywhere
        json_indent = self.indent if self.indent is not None \
                                     and self.indent > 0 else None
        kwargs.setdefault('indent', json_indent)
        kwargs.setdefault('ensure_ascii', not self.encoding)
        self.encoder = TransistorJSONEncoder(**kwargs)
        self.first_item = True

    def _beautify_newline(self):
        if self.indent is not None:
            self.file.write(b'\n')

    def start_exporting(self):
        self.file.write(b"[")
        self._beautify_newline()

    def finish_exporting(self):
        self._beautify_newline()
        self.file.write(b"]")

    def export_item(self, item):
        if self.first_item:
            self.first_item = False
        else:
            self.file.write(b',')
            self._beautify_newline()
        itemdict = dict(self._get_serialized_fields(item))
        data = self.encoder.encode(itemdict)
        self.file.write(to_bytes(data, self.encoding))
