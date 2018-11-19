# -*- coding: utf-8 -*-
"""
transistor.persistence.item
~~~~~~~~~~~~
This module implements a common output data format by providing the
`Item()` class. `Item()` objects are simple containers used
to collect the scraped data. They provide a dictionary-like API with a
convenient syntax for declaring their available fields.

This code was originally copied from the Scrapy.item module. It was
then modified to remove six, because we are not supporting python 2.

Reference:
https://github.com/scrapy/scrapy/blob/master/scrapy/item.py

:copyright: Original scrapy.item.py from scrapy==1.5.1 is
Copyright by it's authors and further changes or contributions here are
Copyright (C) 2018 by BOM Quote Limited.
:license: Original scrapy.item.py from scrapy==1.5.1 license is found at
https://github.com/scrapy/scrapy/archive/1.5.1.zip
and further changes or contributions here are licensed under The MIT
License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from pprint import pformat
from collections import MutableMapping

from abc import ABCMeta


from transistor.utility.trackref import object_ref


class BaseItem(object_ref):
    """Base class for all scraped items."""
    pass


class Field(dict):
    """Container of field metadata"""


class ItemMeta(ABCMeta):

    def __new__(mcs, class_name, bases, attrs):
        classcell = attrs.pop('__classcell__', None)
        new_bases = tuple(base._class for base in bases if hasattr(base, '_class'))
        _class = super(ItemMeta, mcs).__new__(mcs, 'x_' + class_name, new_bases, attrs)

        fields = getattr(_class, 'fields', {})
        new_attrs = {}
        for n in dir(_class):
            v = getattr(_class, n)
            if isinstance(v, Field):
                fields[n] = v
            elif n in attrs:
                new_attrs[n] = attrs[n]

        new_attrs['fields'] = fields
        new_attrs['_class'] = _class
        if classcell is not None:
            new_attrs['__classcell__'] = classcell
        return super(ItemMeta, mcs).__new__(mcs, class_name, bases, new_attrs)


class DictItem(MutableMapping, BaseItem):

    fields = {}

    def __init__(self, *args, **kwargs):
        self._values = {}
        if args or kwargs:  # avoid creating dict for most common case
            for k, v in dict(*args, **kwargs).items():
                self[k] = v

    def __getitem__(self, key):
        return self._values[key]

    def __setitem__(self, key, value):
        if key in self.fields:
            self._values[key] = value
        else:
            raise KeyError("%s does not support field: %s" %
                (self.__class__.__name__, key))

    def __delitem__(self, key):
        del self._values[key]

    def __getattr__(self, name):
        if name in self.fields:
            raise AttributeError("Use item[%r] to get field value" % name)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if not name.startswith('_'):
            raise AttributeError("Use item[%r] = %r to set field value" %
                (name, value))
        super(DictItem, self).__setattr__(name, value)

    def __len__(self):
        return len(self._values)

    def __iter__(self):
        return iter(self._values)

    __hash__ = BaseItem.__hash__

    def keys(self):
        return self._values.keys()

    def __repr__(self):
        return pformat(dict(self))

    def copy(self):
        return self.__class__(self)

class Item(DictItem, metaclass=ItemMeta):
    pass