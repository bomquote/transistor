# -*- coding: utf-8 -*-
"""
transistor.tests.conftest
~~~~~~~~~~~~
This module defines pytest fixtures and other constants available to all tests.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

import pytest
from os.path import dirname as d
from os.path import abspath, join
from unittest.mock import Mock, patch

root_dir = d(d(abspath(__file__)))


@pytest.fixture(scope='function')
def test_dict():
    """
    Need to set dict[_test_page_text] = get_html()
    :return dict
    """
    return {"_test_true": True, "_test_page_text": '', "_test_status_code": 200,
            "autostart": True}
