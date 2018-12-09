# -*- coding: utf-8 -*-
"""
transistor.tests.persistence.test_exporters
~~~~~~~~~~~~

This code was nearly completely copied from the Scrapy.tests.test_exporters.
It was modified to fit Transistor's few API differences and Python 3 only
support.

Reference:
https://github.com/scrapy/scrapy/blob/master/scrapy/tests/test_exporters.py

:copyright: Original scrapy.tests.test_exporters from scrapy==1.5.1 is
Copyright by it's authors and further changes or contributions here are
Copyright (C) 2018 by BOM Quote Limited.
:license: Original scrapy.tests.test_exporters from scrapy==1.5.1 license is
found at https://github.com/scrapy/scrapy/archive/1.5.1.zip
and further changes or contributions here are licensed under The MIT
License, see LICENSE for more details.
"""

import re
import json
import marshal
import pickle
import tempfile
import unittest
from io import BytesIO
from datetime import datetime
import lxml.etree
from tests.conftest import bts_static_scraper
from transistor import Item, Field
from transistor.utility.python import to_unicode
from transistor.persistence.exporters import (
    BaseItemExporter, PprintItemExporter, PickleItemExporter, CsvItemExporter,
    XmlItemExporter, JsonLinesItemExporter, JsonItemExporter,
    PythonItemExporter, MarshalItemExporter
)


class ATestItem(Item):
    name = Field()
    age = Field()


class BaseItemExporterTest(unittest.TestCase):

    def setUp(self):
        self.i = ATestItem(name='John£', age='22')
        self.output = BytesIO()
        self.ie = self._get_exporter()

    def _get_exporter(self, **kwargs):
        return BaseItemExporter(**kwargs)

    def _check_output(self):
        pass

    def _assert_expected_item(self, exported_dict):
        for k, v in exported_dict.items():
            exported_dict[k] = to_unicode(v)
        self.assertEqual(self.i, exported_dict)

    @staticmethod
    def _get_nonstring_types_item():
        return {
            'boolean': False,
            'number': 22,
            'time': datetime(2015, 1, 1, 1, 1, 1),
            'float': 3.14,
        }

    def assertItemExportWorks(self, item):
        self.ie.start_exporting()
        try:
            self.ie.export_item(item)
        except NotImplementedError:
            if self.ie.__class__ is not BaseItemExporter:
                raise
        self.ie.finish_exporting()
        self._check_output()

    def test_export_item(self):
        self.assertItemExportWorks(self.i)

    def test_export_dict_item(self):
        self.assertItemExportWorks(dict(self.i))

    def test_serialize_field(self):
        res = self.ie.serialize_field(self.i.fields['name'], 'name', self.i['name'])
        self.assertEqual(res, 'John£')

        res = self.ie.serialize_field(self.i.fields['age'], 'age', self.i['age'])
        self.assertEqual(res, '22')

    def test_fields_to_export(self):
        ie = self._get_exporter(fields_to_export=['name'])
        self.assertEqual(list(ie._get_serialized_fields(self.i)),
                         [('name', 'John£')])

        ie = self._get_exporter(fields_to_export=['name'], encoding='latin-1')
        _, name = list(ie._get_serialized_fields(self.i))[0]
        assert isinstance(name, str)
        self.assertEqual(name, 'John£')

    def test_field_custom_serializer(self):
        def custom_serializer(value):
            return str(int(value) + 2)

        class CustomFieldItem(Item):
            name = Field()
            age = Field(serializer=custom_serializer)

        i = CustomFieldItem(name='John£', age='22')

        ie = self._get_exporter()
        self.assertEqual(ie.serialize_field(i.fields['name'], 'name', i['name']),
                         'John£')
        self.assertEqual(ie.serialize_field(i.fields['age'], 'age', i['age']), '24')


class TestPythonItemExporter(BaseItemExporterTest):

    def _get_exporter(self, **kwargs):
        return PythonItemExporter(binary=False, **kwargs)

    def test_invalid_option(self):
        with self.assertRaisesRegex(TypeError, "Unexpected options: invalid_option"):
            PythonItemExporter(invalid_option='something', scraper=bts_static_scraper,
                               items=ATestItem)

    def test_nested_item(self):
        i1 = ATestItem(name='Joseph', age='22')
        i2 = dict(name='Maria', age=i1)
        i3 = ATestItem(name='Jesus', age=i2)
        ie = self._get_exporter()
        exported = ie.export_item(i3)
        self.assertEqual(type(exported), dict)
        self.assertEqual(exported, {'age': {'age': {'age': '22', 'name': 'Joseph'},
                                            'name': 'Maria'}, 'name': 'Jesus'})
        self.assertEqual(type(exported['age']), dict)
        self.assertEqual(type(exported['age']['age']), dict)

    def test_export_list(self):
        i1 = ATestItem(name='Joseph', age='22')
        i2 = ATestItem(name='Maria', age=[i1])
        i3 = ATestItem(name='Jesus', age=[i2])
        ie = self._get_exporter()
        exported = ie.export_item(i3)
        self.assertEqual(exported, {'age': [{'age': [{'age': '22', 'name': 'Joseph'}],
                                             'name': 'Maria'}], 'name': 'Jesus'})
        self.assertEqual(type(exported['age'][0]), dict)
        self.assertEqual(type(exported['age'][0]['age'][0]), dict)

    def test_export_item_dict_list(self):
        i1 = ATestItem(name=u'Joseph', age='22')
        i2 = dict(name='Maria', age=[i1])
        i3 = ATestItem(name='Jesus', age=[i2])
        ie = self._get_exporter()
        exported = ie.export_item(i3)
        self.assertEqual(exported, {'age': [{'age': [{'age': '22', 'name': 'Joseph'}],
                                             'name': 'Maria'}], 'name': 'Jesus'})
        self.assertEqual(type(exported['age'][0]), dict)
        self.assertEqual(type(exported['age'][0]['age'][0]), dict)

    def test_export_binary(self):
        exporter = PythonItemExporter(binary=True)
        value = ATestItem(name='John£', age='22')
        expected = {b'name': b'John\xc2\xa3', b'age': b'22'}
        self.assertEqual(expected, exporter.export_item(value))

    def test_nonstring_types_item(self):
        item = self._get_nonstring_types_item()
        ie = self._get_exporter()
        exported = ie.export_item(item)
        self.assertEqual(exported, item)


class PprintItemExporterTest(BaseItemExporterTest):

    def _get_exporter(self, **kwargs):
        return PprintItemExporter(self.output, **kwargs)

    def _check_output(self):
        self._assert_expected_item(eval(self.output.getvalue()))


class PickleItemExporterTest(BaseItemExporterTest):

    def _get_exporter(self, **kwargs):
        return PickleItemExporter(self.output, **kwargs)

    def _check_output(self):
        self._assert_expected_item(pickle.loads(self.output.getvalue()))

    def test_export_multiple_items(self):
        i1 = ATestItem(name='hello', age='world')
        i2 = ATestItem(name='bye', age='world')
        f = BytesIO()
        ie = PickleItemExporter(f)
        ie.start_exporting()
        ie.export_item(i1)
        ie.export_item(i2)
        ie.finish_exporting()
        f.seek(0)
        self.assertEqual(pickle.load(f), i1)
        self.assertEqual(pickle.load(f), i2)

    def test_nonstring_types_item(self):
        item = self._get_nonstring_types_item()
        fp = BytesIO()
        ie = PickleItemExporter(fp)
        ie.start_exporting()
        ie.export_item(item)
        ie.finish_exporting()
        self.assertEqual(pickle.loads(fp.getvalue()), item)


class MarshalItemExporterTest(BaseItemExporterTest):

    def _get_exporter(self, **kwargs):
        self.output = tempfile.TemporaryFile()
        return MarshalItemExporter(self.output, **kwargs)

    def _check_output(self):
        self.output.seek(0)
        self._assert_expected_item(marshal.load(self.output))

    def test_nonstring_types_item(self):
        item = self._get_nonstring_types_item()
        item.pop('time')  # datetime is not marshallable
        fp = tempfile.TemporaryFile()
        ie = MarshalItemExporter(fp)
        ie.start_exporting()
        ie.export_item(item)
        ie.finish_exporting()
        fp.seek(0)
        self.assertEqual(marshal.load(fp), item)


class CsvItemExporterTest(BaseItemExporterTest):
    def _get_exporter(self, **kwargs):
        return CsvItemExporter(self.output, **kwargs)

    def assertCsvEqual(self, first, second, msg=None):
        first = to_unicode(first)
        second = to_unicode(second)
        csvsplit = lambda csv: [sorted(re.split(r'(,|\s+)', line))
                                for line in csv.splitlines(True)]
        return self.assertEqual(csvsplit(first), csvsplit(second), msg)

    def _check_output(self):
        self.assertCsvEqual(to_unicode(self.output.getvalue()),
                            'age,name\r\n22,John£\r\n')

    def assertExportResult(self, item, expected, **kwargs):
        fp = BytesIO()
        ie = CsvItemExporter(fp, **kwargs)
        ie.start_exporting()
        ie.export_item(item)
        ie.finish_exporting()
        self.assertCsvEqual(fp.getvalue(), expected)

    def test_header_export_all(self):
        self.assertExportResult(
            item=self.i,
            fields_to_export=self.i.fields.keys(),
            expected=b'age,name\r\n22,John\xc2\xa3\r\n',
        )

    def test_header_export_all_dict(self):
        self.assertExportResult(
            item=dict(self.i),
            expected=b'age,name\r\n22,John\xc2\xa3\r\n',
        )

    def test_header_export_single_field(self):
        for item in [self.i, dict(self.i)]:
            self.assertExportResult(
                item=item,
                fields_to_export=['age'],
                expected=b'age\r\n22\r\n',
            )

    def test_header_export_two_items(self):
        for item in [self.i, dict(self.i)]:
            output = BytesIO()
            ie = CsvItemExporter(output)
            ie.start_exporting()
            ie.export_item(item)
            ie.export_item(item)
            ie.finish_exporting()
            self.assertCsvEqual(output.getvalue(),
                                b'age,name\r\n22,John\xc2\xa3\r\n22,John\xc2\xa3\r\n')

    def test_header_no_header_line(self):
        for item in [self.i, dict(self.i)]:
            self.assertExportResult(
                item=item,
                include_headers_line=False,
                expected=b'22,John\xc2\xa3\r\n',
            )

    def test_join_multivalue(self):
        class ATestItem2(Item):
            name = Field()
            friends = Field()

        for cls in ATestItem2, dict:
            self.assertExportResult(
                item=cls(name='John', friends=['Mary', 'Paul']),
                include_headers_line=False,
                expected='"Mary,Paul",John\r\n',
            )

    def test_join_multivalue_not_strings(self):
        self.assertExportResult(
            item=dict(name='John', friends=[4, 8]),
            include_headers_line=False,
            expected='"[4, 8]",John\r\n',
        )

    def test_nonstring_types_item(self):
        self.assertExportResult(
            item=self._get_nonstring_types_item(),
            include_headers_line=False,
            expected='22,False,3.14,2015-01-01 01:01:01\r\n'
        )


class XmlItemExporterTest(BaseItemExporterTest):

    def _get_exporter(self, **kwargs):
        return XmlItemExporter(self.output, **kwargs)

    def assertXmlEquivalent(self, first, second, msg=None):
        def xmltuple(elem):
            children = list(elem.iterchildren())
            if children:
                return [(child.tag, sorted(xmltuple(child)))
                        for child in children]
            else:
                return [(elem.tag, [(elem.text, ())])]
        def xmlsplit(xmlcontent):
            doc = lxml.etree.fromstring(xmlcontent)
            return xmltuple(doc)
        return self.assertEqual(xmlsplit(first), xmlsplit(second), msg)

    def assertExportResult(self, item, expected_value):
        fp = BytesIO()
        ie = XmlItemExporter(fp)
        ie.start_exporting()
        ie.export_item(item)
        ie.finish_exporting()
        self.assertXmlEquivalent(fp.getvalue(), expected_value)

    def _check_output(self):
        expected_value = b'<?xml version="1.0" encoding="utf-8"?>\n<items><item><age>22</age><name>John\xc2\xa3</name></item></items>'
        self.assertXmlEquivalent(self.output.getvalue(), expected_value)

    def test_multivalued_fields(self):
        self.assertExportResult(
            ATestItem(name=[u'John\xa3', u'Doe']),
            b'<?xml version="1.0" encoding="utf-8"?>\n<items><item><name><value>John\xc2\xa3</value><value>Doe</value></name></item></items>'
        )

    def test_nested_item(self):
        i1 = ATestItem(name=u'foo\xa3hoo', age='22')
        i2 = dict(name=u'bar', age=i1)
        i3 = ATestItem(name=u'buz', age=i2)

        self.assertExportResult(i3,
            b'<?xml version="1.0" encoding="utf-8"?>\n'
            b'<items>'
                b'<item>'
                    b'<age>'
                        b'<age>'
                            b'<age>22</age>'
                            b'<name>foo\xc2\xa3hoo</name>'
                        b'</age>'
                        b'<name>bar</name>'
                    b'</age>'
                    b'<name>buz</name>'
                b'</item>'
            b'</items>'
        )

    def test_nested_list_item(self):
        i1 = ATestItem(name=u'foo')
        i2 = dict(name=u'bar', v2={"egg": ["spam"]})
        i3 = ATestItem(name=u'buz', age=[i1, i2])

        self.assertExportResult(i3,
            b'<?xml version="1.0" encoding="utf-8"?>\n'
            b'<items>'
                b'<item>'
                    b'<age>'
                        b'<value><name>foo</name></value>'
                        b'<value><name>bar</name><v2><egg><value>spam</value></egg></v2></value>'
                    b'</age>'
                    b'<name>buz</name>'
                b'</item>'
            b'</items>'
        )

    def test_nonstring_types_item(self):
        item = self._get_nonstring_types_item()
        self.assertExportResult(item,
            b'<?xml version="1.0" encoding="utf-8"?>\n'
            b'<items>'
               b'<item>'
                   b'<float>3.14</float>'
                   b'<boolean>False</boolean>'
                   b'<number>22</number>'
                   b'<time>2015-01-01 01:01:01</time>'
               b'</item>'
            b'</items>'
        )


class JsonLinesItemExporterTest(BaseItemExporterTest):

    _expected_nested = {'name': u'Jesus', 'age': {'name': 'Maria', 'age': {'name': 'Joseph', 'age': '22'}}}

    def _get_exporter(self, **kwargs):
        return JsonLinesItemExporter(self.output, **kwargs)

    def _check_output(self):
        exported = json.loads(to_unicode(self.output.getvalue().strip()))
        self.assertEqual(exported, dict(self.i))

    def test_nested_item(self):
        i1 = ATestItem(name=u'Joseph', age='22')
        i2 = dict(name=u'Maria', age=i1)
        i3 = ATestItem(name=u'Jesus', age=i2)
        self.ie.start_exporting()
        self.ie.export_item(i3)
        self.ie.finish_exporting()
        exported = json.loads(to_unicode(self.output.getvalue()))
        self.assertEqual(exported, self._expected_nested)

    def test_extra_keywords(self):
        self.ie = self._get_exporter(sort_keys=True)
        self.test_export_item()
        self._check_output()
        self.assertRaises(TypeError, self._get_exporter, foo_unknown_keyword_bar=True)

    def test_nonstring_types_item(self):
        item = self._get_nonstring_types_item()
        self.ie.start_exporting()
        self.ie.export_item(item)
        self.ie.finish_exporting()
        exported = json.loads(to_unicode(self.output.getvalue()))
        item['time'] = str(item['time'])
        self.assertEqual(exported, item)


class JsonItemExporterTest(JsonLinesItemExporterTest):

    _expected_nested = [JsonLinesItemExporterTest._expected_nested]

    def _get_exporter(self, **kwargs):
        return JsonItemExporter(self.output, **kwargs)

    def _check_output(self):
        exported = json.loads(to_unicode(self.output.getvalue().strip()))
        self.assertEqual(exported, [dict(self.i)])

    def assertTwoItemsExported(self, item):
        self.ie.start_exporting()
        self.ie.export_item(item)
        self.ie.export_item(item)
        self.ie.finish_exporting()
        exported = json.loads(to_unicode(self.output.getvalue()))
        self.assertEqual(exported, [dict(item), dict(item)])

    def test_two_items(self):
        self.assertTwoItemsExported(self.i)

    def test_two_dict_items(self):
        self.assertTwoItemsExported(dict(self.i))

    def test_nested_item(self):
        i1 = ATestItem(name=u'Joseph\xa3', age='22')
        i2 = ATestItem(name=u'Maria', age=i1)
        i3 = ATestItem(name=u'Jesus', age=i2)
        self.ie.start_exporting()
        self.ie.export_item(i3)
        self.ie.finish_exporting()
        exported = json.loads(to_unicode(self.output.getvalue()))
        expected = {'name': u'Jesus', 'age': {'name': 'Maria', 'age': dict(i1)}}
        self.assertEqual(exported, [expected])

    def test_nested_dict_item(self):
        i1 = dict(name=u'Joseph\xa3', age='22')
        i2 = ATestItem(name=u'Maria', age=i1)
        i3 = dict(name=u'Jesus', age=i2)
        self.ie.start_exporting()
        self.ie.export_item(i3)
        self.ie.finish_exporting()
        exported = json.loads(to_unicode(self.output.getvalue()))
        expected = {'name': u'Jesus', 'age': {'name': 'Maria', 'age': i1}}
        self.assertEqual(exported, [expected])

    def test_nonstring_types_item(self):
        item = self._get_nonstring_types_item()
        self.ie.start_exporting()
        self.ie.export_item(item)
        self.ie.finish_exporting()
        exported = json.loads(to_unicode(self.output.getvalue()))
        item['time'] = str(item['time'])
        self.assertEqual(exported, [item])


class CustomItemExporterTest(unittest.TestCase):

    def test_exporter_custom_serializer(self):
        class CustomItemExporter(BaseItemExporter):
            def serialize_field(self, field, name, value):
                if name == 'age':
                    return str(int(value) + 1)
                else:
                    return super().serialize_field(field, name, value)

        i = ATestItem(name=u'John', age='22')
        ie = CustomItemExporter()

        self.assertEqual(ie.serialize_field(i.fields['name'], 'name', i['name']), 'John')
        self.assertEqual(ie.serialize_field(i.fields['age'], 'age', i['age']), '23')

        i2 = {'name': u'John', 'age': '22'}
        self.assertEqual(ie.serialize_field({}, 'name', i2['name']), 'John')
        self.assertEqual(ie.serialize_field({}, 'age', i2['age']), '23')