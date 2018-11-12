# -*- coding: utf-8 -*-
"""
transistor.conf
~~~~~~~~~~~~
This module implements some configuration helpers for Transistor.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

import os


def closest_transistor_cfg(path='.', prevpath=None):
    """Return the path to the closest transistor.cfg file by traversing the current
    directory and its parents.
    """
    if path == prevpath:
        return ''
    path = os.path.abspath(path)
    cfgfile = os.path.join(path, 'transistor.cfg')
    if os.path.exists(cfgfile):
        return cfgfile
    return closest_transistor_cfg(os.path.dirname(path), path)