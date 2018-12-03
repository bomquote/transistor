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

import io
import csv
import pprint
import marshal
import pickle
from transistor.persistence.item import BaseItem, Item
from transistor.utility.python import to_bytes, is_listlike, to_unicode

from .base import BaseItemExporter

__all__ = ['PprintItemExporter', 'PickleItemExporter', 'PythonItemExporter',
           'CsvItemExporter', 'MarshalItemExporter']


class CsvItemExporter(BaseItemExporter):
    """
    Exports Items in CSV format to the given file-like object. If the
    fields_to_export attribute is set, it will be used to define the CSV
    columns and their order. The export_empty_fields attribute has no
    effect on this exporter.
    """

    def __init__(self, file, include_headers_line=True, join_multivalued=',', **kwargs):
        """

        :param file: the file-like object to use for exporting the data. Its write
        method should accept bytes (a disk file opened in binary mode, a io.BytesIO
        object, etc)
        :param include_headers_line:  If enabled, makes the exporter output a header
        line with the field names taken from BaseItemExporter.fields_to_export or
        the first exported item fields.
        :param join_multivalued:
        :param kwargs:
        """
        super().__init__()
        self._configure(kwargs, dont_fail=True)
        if not self.encoding:
            self.encoding = 'utf_8_sig'
        self.include_headers_line = include_headers_line
        self.stream = io.TextIOWrapper(
            file,
            line_buffering=False,
            write_through=True,
            encoding=self.encoding,
            newline='' # Windows needs this https://github.com/scrapy/scrapy/issues/3034
        )
        self.csv_writer = csv.writer(self.stream, **kwargs)
        self._headers_not_written = True
        self._join_multivalued = join_multivalued

    def serialize_field(self, field, name, value):
        serializer = field.get('serializer', self._join_if_needed)
        return serializer(value)

    def _join_if_needed(self, value):
        if isinstance(value, (list, tuple)):
            try:
                return self._join_multivalued.join(value)
            except TypeError:  # list in value may not contain strings
                pass
        return value

    def export_item(self, item):
        if self._headers_not_written:
            self._headers_not_written = False
            self._write_headers_and_set_fields_to_export(item)

        fields = self._get_serialized_fields(item, default_value='',
                                             include_empty=True)
        values = list(self._build_row(x for _, x in fields))
        return self.csv_writer.writerow(values)

    def _build_row(self, values):
        for s in values:
            yield s

    def _write_headers_and_set_fields_to_export(self, item):
        if self.include_headers_line:
            if not self.fields_to_export:
                if isinstance(item, dict):
                    # for dicts try using fields of the first item
                    self.fields_to_export = list(item.keys())
                else:
                    # use fields declared in Item
                    self.fields_to_export = list(item.fields.keys())
            row = list(self._build_row(self.fields_to_export))
            self.csv_writer.writerow(row)


class PickleItemExporter(BaseItemExporter):
    """
    Exports Items in pickle format to the given file-like object.
    """
    def __init__(self, file, protocol=2, **kwargs):
        """
        :param file: the file-like object to use for exporting the data.
        It's write method should accept bytes (a disk file opened in
        binary mode, a io.BytesIO object, etc)
        :param protocol:int(): the pickle protocol to use.

        For more info, refer to documentation:
        https://docs.python.org/3/library/pickle.html
        """
        super().__init__(**kwargs)
        self.file = file
        self.protocol = protocol

    def export_item(self, item):
        d = dict(self._get_serialized_fields(item))
        pickle.dump(d, self.file, self.protocol)


class MarshalItemExporter(BaseItemExporter):
    """
    Marshal is not a general “persistence” module. For general persistence
    and transfer of Python objects through RPC calls, see the modules pickle
    and shelve. Generally, you should use pickle instead of marshal.
    https://docs.python.org/3/library/marshal.html
    """
    def __init__(self, file, **kwargs):
        self.file = file
        super().__init__(**kwargs)

    def export_item(self, item):
        marshal.dump(dict(self._get_serialized_fields(item)), self.file)


class PprintItemExporter(BaseItemExporter):
    """
    Exports Items in pretty print format to the specified file object.

    A typical output of this exporter would be:
        {'name': 'Color TV', 'price': '1200'}
        {'name': 'DVD player', 'price': '200'}

    Longer lines (when present) are pretty-formatted.
    """
    def __init__(self, file, **kwargs):
        """
        :param file: file – the file-like object to use for exporting the
        data. Its write method should accept bytes (a disk file opened
        in binary mode, a io.BytesIO object, etc)
        :param kwargs:
        """
        super().__init__(**kwargs)
        self._configure(kwargs)
        self.file = file

    def export_item(self, item):
        itemdict = dict(self._get_serialized_fields(item))
        self.file.write(to_bytes(pprint.pformat(itemdict) + '\n'))


class PythonItemExporter(BaseItemExporter):
    """The idea behind this exporter is to have a mechanism to serialize items
    to built-in python types so any serialization library (like
    json, msgpack, binc, etc) can be used on top of it. Its main goal is to
    seamless support what BaseItemExporter does plus nested items.
    """
    def _configure(self, options, dont_fail=False):
        self.binary = options.pop('binary', True)
        super(PythonItemExporter, self)._configure(options, dont_fail)
        if not self.encoding:
            self.encoding = 'utf-8'

    def serialize_field(self, field, name, value):
        serializer = field.get('serializer', self._serialize_value)
        return serializer(value)

    def _serialize_value(self, value):
        if isinstance(value, BaseItem):
            return self.export_item(value)
        if isinstance(value, dict):
            return dict(self._serialize_dict(value))
        if is_listlike(value):
            return [self._serialize_value(v) for v in value]
        encode_func = to_bytes if self.binary else to_unicode
        if isinstance(value, (str, bytes)):
            return encode_func(value, encoding=self.encoding)
        return value

    def _serialize_dict(self, value):
        for key, val in value.items():
            key = to_bytes(key) if self.binary else key
            yield key, self._serialize_value(val)

    def export_item(self, item):
        result = dict(self._get_serialized_fields(item))
        if self.binary:
            result = dict(self._serialize_dict(result))
        return result
