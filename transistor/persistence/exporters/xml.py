# -*- coding: utf-8 -*-
"""
transistor.persistence.exporters.xml
~~~~~~~~~~~~
This module implements classes that export (serialize) the data inside
a BaseWorker from a SplashScraper to XML.

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

import sys
from xml.sax.saxutils import XMLGenerator
from transistor.persistence.item import Item
from transistor.utility.python import is_listlike
from .base import BaseItemExporter


__all__ = ['XmlItemExporter']

class XmlItemExporter(BaseItemExporter):
    """
    Exports Items in XML format to the specified file object.
    """
    def __init__(self, file, **kwargs):
        """

        :param file:  the file-like object to use for exporting the data.
        It's write method should accept bytes (a disk file opened in
        binary mode, a io.BytesIO object, etc)
        :param kwargs: root_element (str) – The name of root element in
        the exported XML.
        :param kwargs: item_element (str) – The name of each item element
        in the exported XML.

        A typical output of this exporter would be:
            <?xml version="1.0" encoding="utf-8"?>
            <items>
              <item>
                <name>Color TV</name>
                <price>1200</price>
             </item>
              <item>
                <name>DVD player</name>
                <price>200</price>
             </item>
            </items>

        Unless overridden in the serialize_field() method, multi-valued
        fields are exported by serializing each value inside a <value>
        element. This is for convenience, as multi-valued fields are
        very common.

        For example, the item:
        >>> Item(name=['John', 'Doe'], age='23')

        Would be serialized as:
            <?xml version="1.0" encoding="utf-8"?>
            <items>
              <item>
                <name>
                  <value>John</value>
                  <value>Doe</value>
                </name>
                <age>23</age>
              </item>
            </items>
        """
        super().__init__()
        self.item_element = kwargs.pop('item_element', 'item')
        self.root_element = kwargs.pop('root_element', 'items')
        self._configure(kwargs)
        if not self.encoding:
            self.encoding = 'utf-8'
        self.xg = XMLGenerator(file, encoding=self.encoding)

    def _beautify_newline(self, new_item=False):
        if self.indent is not None and (self.indent > 0 or new_item):
            self._xg_characters('\n')

    def _beautify_indent(self, depth=1):
        if self.indent:
            self._xg_characters(' ' * self.indent * depth)

    def start_exporting(self):
        self.xg.startDocument()
        self.xg.startElement(self.root_element, {})
        self._beautify_newline(new_item=True)

    def export_item(self, item):
        self._beautify_indent(depth=1)
        self.xg.startElement(self.item_element, {})
        self._beautify_newline()
        for name, value in self._get_serialized_fields(item, default_value=''):
            self._export_xml_field(name, value, depth=2)
        self._beautify_indent(depth=1)
        self.xg.endElement(self.item_element)
        self._beautify_newline(new_item=True)

    def finish_exporting(self):
        self.xg.endElement(self.root_element)
        self.xg.endDocument()

    def _export_xml_field(self, name, serialized_value, depth):
        self._beautify_indent(depth=depth)
        self.xg.startElement(name, {})
        if hasattr(serialized_value, 'items'):
            self._beautify_newline()
            for subname, value in serialized_value.items():
                self._export_xml_field(subname, value, depth=depth+1)
            self._beautify_indent(depth=depth)
        elif is_listlike(serialized_value):
            self._beautify_newline()
            for value in serialized_value:
                self._export_xml_field('value', value, depth=depth+1)
            self._beautify_indent(depth=depth)
        elif isinstance(serialized_value, str):
            self._xg_characters(serialized_value)
        else:
            self._xg_characters(str(serialized_value))
        self.xg.endElement(name)
        self._beautify_newline()

    # Workaround for https://bugs.python.org/issue17606
    if sys.version_info[:3] >= (2, 7, 4):
        def _xg_characters(self, serialized_value):
            if not isinstance(serialized_value, str):
                serialized_value = serialized_value.decode(self.encoding)
            return self.xg.characters(serialized_value)
    else:  # pragma: no cover
        def _xg_characters(self, serialized_value):
            return self.xg.characters(serialized_value)