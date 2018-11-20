# -*- coding: utf-8 -*-
"""
transistor.persistence.exporter
~~~~~~~~~~~~
This module implements an abstract base class that must be implemented to
extract (serialize) the data inside a BaseWorker from a SplashScraper for
persistence in newt.db.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from abc import ABC, abstractmethod


class BaseItemExporter(ABC):
    """
    A worker tool to export the data from the SplashScraper object and pass
    the data into a new object which inherits from class:Item, called
    'items' here.

    A scraper which has completed a scrape job goes in. A container object
    encapsulating all the relevant data we want to further manipulate or
    save from the scrape job, comes out.

    """

    def __init__(self, scraper, items):
        """
        Create an instance.
        :param scraper: an instance of SplashScraper object which has
        already finished a scrape.
        :param items: a class in which the attributes to be persisted
        from the scraper will be written.
        """
        self.scraper = scraper
        self.items = items()

    def __repr__(self):
        return f"<Exporter({self.scraper.__repr__()})>"

    @abstractmethod
    def write(self):
        """
        Create the new container object which can be pickled.

        :return: SplashScraperContainer()
        """
        # create a new container object

        # SplashBrowser properties
        self.items['raw_content']=self.scraper.browser.raw_content
        self.items['status']=self.scraper.browser.status
        # SplashBrowser methods
        self.items['current_request']=self.scraper.browser.get_current_request()
        self.items['current_url']=self.scraper.browser.get_current_url()

        # SplashBrowserMixin properties
        self.items['encoding'] = self.scraper.browser.encoding
        self.items['ucontent'] = self.scraper.browser.ucontent
        self.items['resp_content'] = self.scraper.browser.resp_content
        self.items['resp_headers'] = self.scraper.browser.resp_headers
        self.items['resp_content_type_header'] = \
            self.scraper.browser.resp_content_type_header
        self.items['har'] = self.scraper.browser.har
        self.items['png'] = self.scraper.browser.png
        self.items['endpoint_status'] = self.scraper.browser.endpoint_status
        self.items['crawlera_session'] = self.scraper.browser.crawlera_session
        self.items['html'] = self.scraper.browser.html


        # scraper attributes
        self.items['name']=self.scraper.name
        self.items['number']=self.scraper.number
        self.items['scraper_repr']=self.scraper.__repr__()
        self.items['cookies']=self.scraper.cookies
        self.items['splash_args']=self.scraper.splash_args
        self.items['http_session_valid']=self.scraper.http_session_valid
        self.items['baseurl']=self.scraper.baseurl
        self.items['crawlera_user']=self.scraper.crawlera_user
        self.items['referrer']=self.scraper.referrer
        self.items['searchurl']=self.scraper.searchurl
        self.items['LUA_SOURCE']=self.scraper.LUA_SOURCE
        self.items['_test_true']=self.scraper._test_true
        self.items['_result']=self.scraper._result

        # scraper properties
        # scraper private methods
        # public methods

