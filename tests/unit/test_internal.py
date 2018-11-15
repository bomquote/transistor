# -*- coding: utf-8 -*-
"""
transistor.tests.test_internal
~~~~~~~~~~~~
This module tests internally used helpers and constants.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from transistor._internal import _missing

class TestInternal:
    """
    Unit test the _internal module.
    """

    def test_missing(self):

        assert _missing.__repr__() == 'no value'
        assert _missing.__reduce__() == '_missing'