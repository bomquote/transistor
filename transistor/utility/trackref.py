# -*- coding: utf-8 -*-
"""
transistor.persistence.item
~~~~~~~~~~~~
This module provides some functions and classes to record and report
references to live object instances.

If you want live objects for a particular class to be tracked, you only have to
subclass from object_ref (instead of object).

About performance: This library has a minimal performance impact when enabled,
and no performance penalty at all when disabled (as object_ref becomes just an
alias to object in that case).

This code was originally copied from the Scrapy.utils.trackref module. It was
then modified to remove six, because we are not supporting python 2.

Reference:
https://github.com/scrapy/scrapy/blob/master/scrapy/utils/trackref.py

:copyright: Original scrapy.utils.trackref from scrapy==1.5.1 is
Copyright by it's authors and further changes or contributions here are
Copyright (C) 2018 by BOM Quote Limited.
:license: Original scrapy.utils.trackref from scrapy==1.5.1 license is found at
https://github.com/scrapy/scrapy/archive/1.5.1.zip
and further changes or contributions here are licensed under The MIT
License, see LICENSE for more details.
"""

from __future__ import print_function
import weakref
from time import time
from operator import itemgetter
from collections import defaultdict


NoneType = type(None)
live_refs = defaultdict(weakref.WeakKeyDictionary)


class object_ref(object):
    """Inherit from this class (instead of object) to a keep a record of live
    instances"""

    __slots__ = ()

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        live_refs[cls][obj] = time()
        return obj

def format_live_refs(ignore=NoneType):
    """Return a tabular representation of tracked objects"""
    s = "Live References\n\n"
    now = time()
    for cls, wdict in sorted(live_refs.items(),
                             key=lambda x: x[0].__name__):
        if not wdict:
            continue
        if issubclass(cls, ignore):
            continue
        oldest = min(wdict.items())
        s += "%-30s %6d   oldest: %ds ago\n" % (
            cls.__name__, len(wdict), now - oldest
        )
    return s


def print_live_refs(*a, **kw):
    """Print tracked objects"""
    print(format_live_refs(*a, **kw))


def get_oldest(class_name):
    """Get the oldest object for a specific class name"""
    for cls, wdict in live_refs.items():
        if cls.__name__ == class_name:
            if not wdict:
                break
            return min(wdict.items(), key=itemgetter(1))[0]


def iter_all(class_name):
    """Iterate over all objects of the same class by its class name"""
    for cls, wdict in live_refs.items():
        if cls.__name__ == class_name:
            return wdict.items()