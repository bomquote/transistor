# -*- coding: utf-8 -*-
"""
transistor.utility.serialize
~~~~~~~~~~~~
This module implements various built-in serializers.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

import json
import datetime
import decimal
from requests import Request, Response
from transistor.persistence.item import BaseItem


class TransistorJSONEncoder(json.JSONEncoder):

    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"

    def default(self, o):
        if isinstance(o, set):
            return list(o)
        elif isinstance(o, datetime.datetime):
            return o.strftime("%s %s" % (self.DATE_FORMAT, self.TIME_FORMAT))
        elif isinstance(o, datetime.date):
            return o.strftime(self.DATE_FORMAT)
        elif isinstance(o, datetime.time):
            return o.strftime(self.TIME_FORMAT)
        elif isinstance(o, decimal.Decimal):
            return str(o)
        elif isinstance(o, BaseItem):
            return dict(o)
        elif isinstance(o, Request):
            return f"<{type(o).__name__}, {o.method}, {o.url}>"
        elif isinstance(o, Response):
            return f"<{type(o).__name__}, {o.status_code}, {o.url}>"
        else:
            return super(TransistorJSONEncoder, self).default(o)


class TransistorJSONDecoder(json.JSONDecoder):
    pass