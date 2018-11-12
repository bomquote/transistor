# -*- coding: utf-8 -*-
"""
transistor._internal
~~~~~~~~~~~~
This module provides internally used helpers and constants.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""


class _Missing(object):

    def __repr__(self):
        return 'no value'

    def __reduce__(self):
        return '_missing'


_missing = _Missing()
