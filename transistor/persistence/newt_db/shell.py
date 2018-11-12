# -*- coding: utf-8 -*-
"""
transistor.persistence.newt_db.shell
~~~~~~~~~~~~
This module contains classes to encapsulate data returned from a SplashScraper object
after a scrape in a format that is able to be pickled and saved in newt.db.

Any changes to this module should also be checked against the ScrapedDataExtractor
in the extractor.py file. The attributes here must match up to the
ScrapedDataExtractor.extract and ScrapedDataExtractor.write methods.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

import newt.db
from transistor.browsers.mixin import SplashBrowserMixin


class SplashScraperShell(SplashBrowserMixin):
    """
    A base class which should be inherited in a subclass which then implements
    a customized SplashScraperShell instance.
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


class SplashComponentScraperNewt(newt.db.Persistent, SplashScraperShell):
    """
    A class to hold the pickleable results set from an executed scrape.

    Returned raw content from Splash which is application/json in bytes.
    The raw content is then transformed by the SplashBrowswerMixin properties.

    So, to standardize, just create a class that includes the mixin and we
    should be DRY and have access to the self.browser properties that matter most.

    """

    # -- names of your customized scraper class attributes go here -- #


    part_number = None # str() # the manufacturing part number which we searched
    # self.splash_json
    china = None  # bool(), whether or not we want to target the china domain
    _script = None  # a component scraper implementation detail, for choosing LUA_SOURCE

    # /end your customized class attrs
    # -- names of your customized scraper methods and @property methods go below -- #
    # - NOTE: all results should be in a form WHICH CAN BE PICKLED.
    # - NOTE: BS4 objects like NavigatableString and Tag can not be pickled...
    # ...so ensure you cast results you intend to save to string with a str(object)

    has_match = None
    error_page = None
    cny_rate = None

    # /end your customized @property methods

    # -- your component scraper private method results go below -- #
    # -- NOTE: these are just those private methods which results you may...
    # ...want to later inspect, like for troubleshooting failed scrape results -- #

    # all, returns default "No Match" just for an standard error message
    # if there is another problem | "No Page" | "Error Page" | "No Result" |
    _no_match = None
    # all, a bool, property
    _ok_to_parse = None
    # all, a str()
    _matching_records_count = None
    # ONLY IF SINGLE RESULT, a str()
    _single_stock_parser = None
    # ONLY IF SINGLE RESULT, a python dict
    _single_price_break_parser = None
    # ONLY IF MULTIPLE RESULT, a str()
    _multiple_stock_parser = None
    # ONLY IF MULTIPLE RESULT, a python dict
    _multiple_stock_detail_parser = None
    # ONLY IF MULTIPLE RESULT, a python dict
    _multiple_price_break_parser = None

    # /end private

    # -- Finally, the results of the PUBLIC methods which you want to save! -- #

    # str()
    stock = None
    # JSON string
    pricing = None

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return f"<SplashComponentScraperNewt({self.name, self.part_number})>"
