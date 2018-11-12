# -*- coding: utf-8 -*-
"""
transistor.exceptions
~~~~~~~~~~~~
This module contains exception classes for Transistor.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
class NoResults(Exception):
    pass


class UnknownFormat(Exception):
    pass


class ProviderBlocking(Exception):
    pass


class UnknownError(Exception):
    pass


class BrokenScraper(Exception):
    pass


class BadRequest(Exception):

    """*400* `Bad Request`

    Raise if the browser sends something to the application the application
    or server cannot handle.

    code = 400
    description = (
        'The browser (or proxy) sent a request that this server could '
        'not understand.'
    )
    """
    pass


class Unauthorized(Exception):

    """*401* `Unauthorized`

    Raise if the user is not authorized.  Also used if you want to use HTTP
    basic auth.

    code = 401
    description = (
        'The server could not verify that you are authorized to access the URL
        requested.  You probably supplied the wrong credentials.'
    )
    """
    pass