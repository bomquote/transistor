# -*- coding: utf-8 -*-
"""
This module contains an abstract base class that must be implemented to
extract (serialize) the data we want the worker from a scraper to gather
from a scraper object, for persistence.
"""

from abc import ABC, abstractmethod


class ScrapedDataExtractor(ABC):
    """
    A worker tool to extract the data from the SplashScraper object and pass the
    data into a new class object (called 'shell' here) which can be pickled.

    A raw finished component scraper goes in. A newt.db compatible class object
    containing all the relevant data we want to save from the scrape job,
    comes out.

    The main reason why I use two classes for this (ScrapedDataExtractor and
    SplashScraperShell) is because this class has to be instanced with
    the scraper object itself. And, that scraper object can't be pickled.

    Think about refactoring the way this works, later.
    """

    def __init__(self, scraper, shell):
        """
        Create an instance.
        :param scraper: an instance of SplashScraper object which has already finished
        a scrape.
        :param shell: a class in which the attributes to be persisted from the scraper
         will be written. It seems redundant, but the key here is, it must be able
         to be pickled. And in order to be pickled, it must not contain any
         beautifulsoup4 objects, because they can't be pickled, but the scraper
         will most likely contain those bs4 objects.
        """
        self.scraper = scraper
        self.shell = shell()
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
        self.splash_json = self.scraper.splash_json
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
        Create the new shell object which can be pickled.

        :return: SplashScraperShell()
        """
        # create a new shell object

        # SplashBrowser properties
        self.shell.raw_content = self.raw_content
        self.shell.status = self.scraper.browser.status
        # SplashBrowser methods
        self.shell.current_request = self.scraper.browser.get_current_request()
        self.shell.current_url = self.scraper.browser.get_current_url()

        # scraper attributes
        self.shell.name = self.name
        self.shell.number = self.number
        self.shell.scraper_repr = self.scraper_repr
        self.shell.cookies = self.cookies
        self.shell.splash_json = self.splash_json
        self.shell.http_session_valid = self.http_session_valid
        self.shell.baseurl = self.baseurl
        self.shell.crawlera_user = self.crawlera_user
        self.shell.referrer = self.referrer
        self.shell.searchurl = self.searchurl
        self.shell.LUA_SOURCE = self.LUA_SOURCE
        self.shell._test_true = self._test_true
        self.shell._result = self._result

        # scraper properties
        # scraper private methods
        # public methods
