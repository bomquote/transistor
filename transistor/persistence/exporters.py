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
import sys
from xml.sax.saxutils import XMLGenerator
from transistor.persistence.item import BaseItem, Item
from transistor.utility.python import to_bytes, is_listlike, to_unicode
from transistor.utility.serialize import TransistorJSONEncoder

__all__ = ['BaseItemExporter', 'PprintItemExporter', 'PickleItemExporter',
           'CsvItemExporter', 'XmlItemExporter', 'JsonLinesItemExporter',
           'JsonItemExporter', 'MarshalItemExporter']

class BaseItemExporter:
    """
    This is the (abstract) base class for all Item Exporters. It provides
    support for common features used by all (concrete) Item Exporters,
    such as defining what fields to export, whether to export empty fields,
    or which encoding to use.

    These features can be configured through the constructor arguments
    which populate their respective instance attributes: fields_to_export,
    export_empty_fields, encoding, indent.

    Further, in Transistor, currently the Scrapy equivalent to
    `Item Loader` is built into this `BaseItemExporter`
    class, in the `write` method.

    An Item Exporter is BaseWorker tool to export the data from the
    SplashScraper object and pass the data into a new object which
    inherits from class:Item, called 'items' here.

    A scraper which has completed a scrape job goes in. A container object
    encapsulating all the relevant data we want to further manipulate or
    save from the scrape job, comes out.

    So Transistor's BaseItemExporter.write() is roughly equivalent to
    Scrapy's ItemLoader.load_item() method.

    Transistor does not yet have an equivalent to Scrapy's concept of
    `Item Pipeline`, which uses multiple `Item Exporters` to group scraped
    items to different files according to the value of one of their fields.
    """

    def __init__(self, scraper, items, **kwargs):
        """
        Create an instance.
        :param scraper: an instance of SplashScraper object which has
        already finished a scrape.
        :param items: a class in which the attributes to be persisted
        from the scraper will be written.
        :param kwargs: fields_to_export: A list with the name of the
        fields that will be exported, or None if you want to export
        all fields. Defaults to None. Some exporters (like CsvItemExporter)
        respect the order of the fields defined in this attribute. Some
        exporters may require fields_to_export list in order to export
        the data properly when spiders return dicts (not Item instances).
        :param kwargs: export_empty_fields: Whether to include
        empty/unpopulated item fields in the exported data. Defaults to
        False. Some exporters (like CsvItemExporter) ignore this attribute
        and always export all empty fields. This option is ignored for
        dict items.
        :param kwargs: encoding: defaults to 'utf-8'. The encoding that
        will be used to encode unicode values. This only affects unicode
        values (which are always serialized to str using this encoding).
        Other value types are passed unchanged to the specific serialization
        library.
        :param kwargs: ident: Amount of spaces used to indent the output on
        each level. Defaults to 0. `indent=None` selects the most compact
        representation, all items in the same line with no indentation
        `indent<=0` each item on its own line, no indentation
        `indent>0` each item on its own line, indented with the provided
        numeric value
        """
        self.scraper = scraper
        self.items = items()
        self._configure(kwargs)

    def __repr__(self):
        return f"<Exporter({self.scraper.__repr__()})>"


    def _configure(self, options, dont_fail=False):
        """
        Configure the exporter by poping options from the ``options`` dict.
        If dont_fail is set, it won't raise an exception on unexpected options
        (useful for using with keyword arguments in subclasses constructors)
        :return:
        """
        self.encoding = options.pop('encoding', None)
        self.fields_to_export = options.pop('fields_to_export', None)
        self.export_empty_fields = options.pop('export_empty_fields', False)
        self.indent = options.pop('indent', None)
        if not dont_fail and options:
            raise TypeError("Unexpected options: %s" % ', '.join(options.keys()))


    def export_item(self, item):
        """
        Exports the given item. This method must be implemented in subclasses.
        :param item:
        """
        raise NotImplementedError


    def serialize_field(self, field, name:str, value):
        """
        Return the serialized value for the given field. You can override
        this method (in your custom Item Exporters) if you want to control
        how a particular field or value will be serialized/exported.

        By default, this method looks for a serializer declared in the
        item field and returns the result of applying that serializer to
        the value. If no serializer is found, it returns the value unchanged.
        :param field:  (Field object or an empty dict) – the field being
        serialized. If a raw dict is being exported (not Item) field
        value is an empty dict.
        :param name:  the name of the field being serialized
        :param value: the value being serialized
        """
        serializer = field.get('serializer', lambda x: x)
        return serializer(value)

    def start_exporting(self):
        """
        Signal the beginning of the exporting process. Some exporters may
        use this to generate some required header (for example, the
        XmlItemExporter). You must call this method before exporting any items.
        :return:
        """
        pass

    def finish_exporting(self):
        """
        Signal the end of the exporting process. Some exporters may use
        this to generate some required footer (for example, the XmlItemExporter).
        You must always call this method after you have no more items to export.
        :return:
        """
        pass

    def _get_serialized_fields(self, item, default_value=None, include_empty=None):
        """Return the fields to export as an iterable of tuples
        (name, serialized_value)
        """
        if include_empty is None:
            include_empty = self.export_empty_fields
        if self.fields_to_export is None:
            if include_empty and not isinstance(item, dict):
                field_iter = item.fields.keys()
            else:
                field_iter = item.keys()
        else:
            if include_empty:
                field_iter = self.fields_to_export
            else:
                field_iter = (x for x in self.fields_to_export if x in item)

        for field_name in field_iter:
            if field_name in item:
                field = {} if isinstance(item, dict) else item.fields[field_name]
                value = self.serialize_field(field, field_name, item[field_name])
            else:
                value = default_value

            yield field_name, value


    def write(self):
        """
        Create the new class::Item() container object. This is
        the Transistor equivalent to the Scrapy API for Item Loaders.

        :return: SplashScraperItems()
        """
        # create a new container object

        # SplashBrowser properties
        self.items['raw_content']=self.scraper.browser.raw_content
        self.items['status']=self.scraper.browser.status
        # SplashBrowser methods
        self.items['current_request']=self.scraper.browser.get_current_request()
        self.items['current_url']=self.scraper.browser.get_current_url()

        # SplashBrowserMixin properties
        self.items['encoding'] = self.scraper.browser.encoding
        self.items['ucontent'] = self.scraper.browser.ucontent
        self.items['resp_content'] = self.scraper.browser.resp_content
        self.items['resp_headers'] = self.scraper.browser.resp_headers
        self.items['resp_content_type_header'] = \
            self.scraper.browser.resp_content_type_header
        self.items['har'] = self.scraper.browser.har
        self.items['png'] = self.scraper.browser.png
        self.items['endpoint_status'] = self.scraper.browser.endpoint_status
        self.items['crawlera_session'] = self.scraper.browser.crawlera_session
        self.items['html'] = self.scraper.browser.html


        # scraper attributes
        self.items['name']=self.scraper.name
        self.items['number']=self.scraper.number
        self.items['scraper_repr']=self.scraper.__repr__()
        self.items['cookies']=self.scraper.cookies
        self.items['splash_args']=self.scraper.splash_args
        self.items['http_session_valid']=self.scraper.http_session_valid
        self.items['baseurl']=self.scraper.baseurl
        self.items['crawlera_user']=self.scraper.crawlera_user
        self.items['referrer']=self.scraper.referrer
        self.items['searchurl']=self.scraper.searchurl
        self.items['LUA_SOURCE']=self.scraper.LUA_SOURCE
        self.items['_test_true']=self.scraper._test_true
        self.items['_result']=self.scraper._result

        # scraper properties
        # scraper private methods
        # public methods


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
        self.scraper = kwargs.pop('scraper', None)
        self.items = kwargs.pop('items', Item)
        super().__init__(scraper=self.scraper, items=self.items)
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
        self.scraper = kwargs.pop('scraper', None)
        self.items = kwargs.pop('items', Item)
        super().__init__(scraper=self.scraper, items=self.items)
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


class CsvItemExporter(BaseItemExporter):

    def __init__(self, file, include_headers_line=True, join_multivalued=',', **kwargs):
        self.scraper = kwargs.pop('scraper', None)
        self.items = kwargs.pop('items', Item)
        super().__init__(scraper=self.scraper, items=self.items)
        self._configure(kwargs, dont_fail=True)
        if not self.encoding:
            self.encoding = 'utf-8'
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
        self.csv_writer.writerow(values)

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
        self.scraper = kwargs.pop('scraper', None)
        self.items = kwargs.pop('items', Item)
        super().__init__(scraper=self.scraper, items=self.items)
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
        self.scraper = kwargs.pop('scraper', None)
        self.items = kwargs.pop('items', Item)
        super().__init__(scraper=self.scraper, items=self.items)
        self._configure(kwargs)
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
        self.scraper = kwargs.pop('scraper', None)
        self.items = kwargs.pop('items', Item)
        super().__init__(scraper=self.scraper, items=self.items)
        self._configure(kwargs)
        self.file = file

    def export_item(self, item):
        marshal.dump(dict(self._get_serialized_fields(item)), self.file)

    def write(self):
        super().write()
        # return self.items


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
        self.scraper = kwargs.pop('scraper', None)
        self.items = kwargs.pop('items', Item)
        super().__init__(scraper=self.scraper, items=self.items)
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
