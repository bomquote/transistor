# -*- coding: utf-8 -*-
"""
transistor.utility.utils
~~~~~~~~~~~~
This module contains various utilities useful to maintain in Transistor source code.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

import json
import os
import base64
from pathlib import Path
from transistor._internal import _Missing
from . import browsercookie


def get_chrome_cookies(name):
    """
    Get the relevant LOCAL cookies from site.  Common cookie items.

    domain, name, version, comment, comment_url, discard, domain_initial_dot,
    domain_specified, expires, path, path_specified, port, port_specified,
    rfc2109, secure, value, _rest
    """
    cj = browsercookie.chrome()
    cookies = '{'
    for cookie in cj:
        c = json.dumps(dict(name=cookie.name, value=cookie.value, path=cookie.path,
                 domain=cookie.domain, expires=cookie.expires, secure=cookie.secure,
                            ))
        if name in c:
            cookies = cookies + str(c) + ', '
    cookies = cookies[0:-2] + '}'
    return cookies


def lua_script(name):
    """
    This is an example of one potential way to include your actual local chrome cookies
    in the lua script. In reality, I haven't needed this yet.  But, I might, and I
    don't want to delete this right now, in case I later do need it. Further, it
    probably doesn't work correctly yet, as is. YMMV.
    :param name:
    """
    chrome_cookies = get_chrome_cookies(name=name)

    _cookie = """
           assert(splash:init_cookies({})""".format(chrome_cookies)

    _script = """
           assert(splash:set_custom_headers({
           ["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
           ["Accept-Encoding"] = "gzip, deflate, sdch",
           ["Accept-Language"] = "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
           ["Connection"] = "keep-alive",
           ["DNT"] = "1",
           ["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",}))
           assert(splash:go(args.url))
           assert(splash:wait(3.0))
           return splash:html()
        """
    return _cookie + _script


def obsolete_setter(setter, attrname):
    """
    From scrapy.http.common and used in SplashBrowser. Probably, for no good reason,
    and should be refactored out, at some point.
    """
    def newsetter(self, value):
        c = self.__class__.__name__
        msg = "%s.%s is not modifiable, use %s.replace() instead" % (c, attrname, c)
        raise AttributeError(msg)
    return newsetter


def get_env():
    """
    Get the environment the app is running in, indicated by the
    :envvar:`TRANSISTOR_ENV` environment variable. The default is
    ``'production'``.
    """
    return os.environ.get('TRANSISTOR_ENV') or 'production'


def get_debug_flag():
    """
    Get whether debug mode should be enabled for the app, indicated
    by the :envvar:`TRANSISTOR_DEBUG` environment variable. The default is
    ``True`` if :func:`.get_env` returns ``'development'``, or ``False``
    otherwise.
    """
    val = os.environ.get('TRANSISTOR_DEBUG')

    if not val:
        return get_env() == 'development'

    return val.lower() not in ('0', 'false', 'no')


class cached_property(property):
    """
    from werkzeug.utils

    A decorator that converts a function into a lazy property.  The
    function wrapped is called the first time to retrieve the result
    and then that calculated result is used the next time you access
    the value::

        class Foo(object):

            @cached_property
            def foo(self):
                # calculate something important here
                return 42

    The class has to have a `__dict__` in order for this property to
    work.
    """

    # implementation detail: A subclass of python's builtin property
    # decorator, we override __get__ to check for a cached value. If one
    # choses to invoke __get__ by hand the property will still work as
    # expected because the lookup logic is replicated in __get__ for
    # manual invocation.

    _missing = _Missing()

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __set__(self, obj, value):
        obj.__dict__[self.__name__] = value

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, self._missing)
        if value is self._missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value


def png_to_file(self, filename):
    """
    Write the png to a file for viewing.
    :param filename: str(): a name to give the saved file
    :return: a saved filename.png in the img folder for viewing.
    """
    path = Path().cwd()
    data_folder = path / u'img'
    filepath = data_folder / filename

    if self.png:
        png_data = self.png.encode('utf-8')
        with open(str(filepath), 'wb') as fh:
            fh.write(base64.decodebytes(png_data))
            print(f'Saved to {filepath}')
    print(f'self.png is None')
    return None