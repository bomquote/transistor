# -*- coding: utf-8 -*-
"""
transistor.tests.unit.utility.test_utility_serialize
~~~~~~~~~~~~
This module implements testing of the books_toscrape example in order to
check Transistor source code.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
import json
import unittest
import datetime
from decimal import Decimal

from requests import Request, Response
from transistor.utility.serialize import TransistorJSONEncoder


class JsonEncoderTestCase(unittest.TestCase):

    def setUp(self):
        self.encoder = TransistorJSONEncoder()

    def test_encode_decode(self):
        dt = datetime.datetime(2010, 1, 2, 10, 11, 12)
        dts = "2010-01-02 10:11:12"
        d = datetime.date(2010, 1, 2)
        ds = "2010-01-02"
        t = datetime.time(10, 11, 12)
        ts = "10:11:12"
        dec = Decimal("1000.12")
        decs = "1000.12"
        s = {'foo'}
        ss = ['foo']
        dt_set = {dt}
        dt_sets = [dts]

        for input, output in [('foo', 'foo'), (d, ds), (t, ts), (dt, dts),
                              (dec, decs), (['foo', d], ['foo', ds]), (s, ss),
                              (dt_set, dt_sets)]:
            self.assertEqual(self.encoder.encode(input), json.dumps(output))


    def test_encode_request(self):
        r = Request('GET', "http://www.example.com/lala")
        rs = self.encoder.encode(r)
        self.assertIn(r.method, rs)
        self.assertIn(r.url, rs)

    def test_encode_response(self):
        r = Response()
        r.url = "http://www.example.com/lala"
        rs = self.encoder.encode(r)
        self.assertIn(r.url, rs)
        self.assertIn(str(r.status_code), rs)