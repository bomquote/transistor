# -*- coding: utf-8 -*-
"""
transistor.persistence.container
~~~~~~~~~~~~
This module contains classes to encapsulate data returned from a
SplashScraper object after a scrape, in a simple container object.
This helps ensure the container objects are serialized as needed.
For example, able to be pickled and saved in newt.db.

Any changes to this module should also be checked against the ScrapedDataExtractor
in the extractor.py file. The attributes here must match up to the
ScrapedDataExtractor.extract and ScrapedDataExtractor.write methods.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from transistor.browsers.mixin import SplashBrowserMixin


class SplashScraperContainer(SplashBrowserMixin):
    """
    A base class which should be inherited in a subclass which then implements
    a customized SplashScraperContainer instance.
    """

    # -- the Scraper's browser class -> self.browser data -- #

    # self.browser.raw_content
    raw_content = None
    # this is the status code received from splash (NOT THE ENDPOINT)
    # self.browser.status
    status = None
    # self.browser.get_current_request() -> <PreparedRequest [POST]>
    current_request = None
    # self.browser.get_current_url() -> 'http://localhost:8050/execute'
    current_url = None
    # flag for a python-request timeout error which should mean there was
    # some network problem or reason second number in the timeout tuple like
    # (3.0, 700.0)  was not long enough.
    timeout_exception = None

    # /end self.browser

    # -- splash scraper class attributes -- #

    # get the __repr__()
    scraper_repr = None
    name = None
    number = None  # str() or int(), `number` is used to enumerate individual workers
    # the specially prepared self.cookies which would need set by us
    cookies = None
    splash_json = None
    http_session_valid = None
    baseurl = None
    crawlera_user = None
    referrer = None
    searchurl = None
    LUA_SOURCE = None
    _test_true = None
    _result = None
