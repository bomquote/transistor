# -*- coding: utf-8 -*-
"""
transistor.persistence.newt_db.extractor
~~~~~~~~~~~~
This module implements an abstract base class that must be implemented to
extract (serialize) the data inside a BaseWorker from a SplashScraper for
persistence in newt.db.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from abc import ABC, abstractmethod


class ScrapedDataExtractor(ABC):
    """
    A worker tool to extract the data from the SplashScraper object and pass the
    data into a new class object (called 'container' here) which can be pickled.

    A raw finished component scraper goes in. A simple container class object
    containing all the relevant data we want to save from the scrape job,
    comes out.

    The main reason why I use two classes for this (ScrapedDataExtractor and
    SplashScraperContainer) is because this class has to be instanced with
    the scraper object itself. And, that scraper object can't be pickled.

    todo: consider refactoring the way this works, later.
    """

    def __init__(self, scraper, container):
        """
        Create an instance.
        :param scraper: an instance of SplashScraper object which has already finished
        a scrape.
        :param container: a class in which the attributes to be persisted from the scraper
         will be written. It seems redundant, but the key here is, it must be able
         to be pickled. And in order to be pickled, it must not contain any
         beautifulsoup4 objects, because they can't be pickled, but the scraper
         will most likely contain those bs4 objects.
        """
        self.scraper = scraper
        self.container = container()
        # pre-call the extract method, to set the attributes on this class
        self.extract()

    def __repr__(self):
        return f"<Extractor({self.scraper.__repr__()})>"

    @abstractmethod
    def extract(self):
        """
        Get all the data that we are looking for from the scraper and then
        encapsulate it in the newt compatible object.
        """
        # SplashBrowser properties
        self.raw_content = self.scraper.browser.raw_content
        self.status = self.scraper.browser.status
        # SplashBrowser methods
        self.current_request = self.scraper.browser.get_current_request()
        self.current_url = self.scraper.browser.get_current_url()
        self.timeout_exception = self.scraper.browser.timeout_exception

        # scraper attributes
        self.name = self.scraper.name
        self.number = self.scraper.number
        self.scraper_repr = self.scraper.__repr__()
        self.cookies = self.scraper.cookies
        self.splash_args = self.scraper.splash_args
        self.http_session_valid = self.scraper.http_session_valid
        self.baseurl = self.scraper.baseurl
        self.crawlera_user = self.scraper.crawlera_user
        self.referrer = self.scraper.referrer
        self.searchurl = self.scraper.searchurl
        self.LUA_SOURCE = self.scraper.LUA_SOURCE
        self._test_true = self.scraper._test_true
        self._result = self.scraper._result

        # scraper properties here
        # scraper private methods here
        # public methods here

    @abstractmethod
    def write(self):
        """
        Create the new container object which can be pickled.

        :return: SplashScraperContainer()
        """
        # create a new container object

        # SplashBrowser properties
        self.container.raw_content = self.raw_content
        self.container.status = self.scraper.browser.status
        # SplashBrowser methods
        self.container.current_request = self.scraper.browser.get_current_request()
        self.container.current_url = self.scraper.browser.get_current_url()

        # scraper attributes
        self.container.name = self.name
        self.container.number = self.number
        self.container.scraper_repr = self.scraper_repr
        self.container.cookies = self.cookies
        self.container.splash_args = self.splash_args
        self.container.http_session_valid = self.http_session_valid
        self.container.baseurl = self.baseurl
        self.container.crawlera_user = self.crawlera_user
        self.container.referrer = self.referrer
        self.container.searchurl = self.searchurl
        self.container.LUA_SOURCE = self.LUA_SOURCE
        self.container._test_true = self._test_true
        self.container._result = self._result

        # scraper properties
        # scraper private methods
        # public methods

