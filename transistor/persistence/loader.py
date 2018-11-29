# -*- coding: utf-8 -*-
"""
transistor.persistence.loader
~~~~~~~~~~~~
This module implements objects used for populating scraped
Items. Items provide the container of scraped data, while Item Loaders
provide the mechanism for populating that container.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""


class ItemLoader:
    """
    :attr spider: an instance of SplashScraper or SplashCrawler object which has
        already finished a scrape/crawl job.
    :attr items: a class in which the attributes to be persisted
    from the spider will be written.
    """
    spider = None
    items = None
    written = False

    _write_attrs = [
        'browser.raw_content', 'browser.status', 'browser.get_current_request()'
        'browser.get_current_url()', 'browser.encoding', 'browser.ucontent',
        'browser.resp_content',  'browser.resp_headers',
        'browser.resp_content_type_header', 'browser.har', 'browser.png',
        'browser.endpoint_status', 'browser.crawlera_session',
        'browser.html', 'name', 'number', '__repr__()', 'cookies',
        'splash_args', 'http_session_valid', 'baseurl', 'crawlera_user',
        'referrer', 'searchurl', 'LUA_SOURCE', '_test_true', '_result'
    ]


    @staticmethod
    def serialize_field(field, name:str, value):
        """
        Return the serialized value for the given field. You can override
        this method (in your custom Item Exporters) if you want to control
        how a particular field or value will be serialized/exported.

        By default, this method looks for a serializer declared in the
        item field and returns the result of applying that serializer to
        the value. If no serializer is found, it returns the value unchanged.
        :param field:  (Field object or an empty dict) – the field being
        serialized. If a raw dict is being exported (not Item) field
        value is an empty dict.
        :param name:  the name of the field being serialized
        :param value: the value being serialized
        """
        serializer = field.get('serializer', lambda x: x)
        return serializer(value)

    def write(self):
        """
        Create the new class::Item() container object. This is
        the Transistor equivalent to the Scrapy API for Item Loaders.

        :return: class Items()
        """

        # SplashBrowser properties
        self.items['raw_content'] = self.spider.browser.raw_content
        self.items['status'] = self.spider.browser.status
        # SplashBrowser methods
        self.items['current_request'] = self.spider.browser.get_current_request()
        self.items['current_url'] = self.spider.browser.get_current_url()

        # SplashBrowserMixin properties
        self.items['encoding'] = self.spider.browser.encoding
        self.items['ucontent'] = self.spider.browser.ucontent
        self.items['resp_content'] = self.spider.browser.resp_content
        self.items['resp_headers'] = self.spider.browser.resp_headers
        self.items['resp_content_type_header'] = \
            self.spider.browser.resp_content_type_header
        self.items['har'] = self.spider.browser.har
        self.items['png'] = self.spider.browser.png
        self.items['endpoint_status'] = self.spider.browser.endpoint_status
        self.items['crawlera_session'] = self.spider.browser.crawlera_session
        self.items['html'] = self.spider.browser.html

        # spider attributes
        self.items['name']=self.spider.name
        self.items['number']=self.spider.number
        self.items['scraper_repr']=self.spider.__repr__()
        self.items['cookies']=self.spider.cookies
        self.items['splash_args']=self.spider.splash_args
        self.items['http_session_valid']=self.spider.http_session_valid
        self.items['baseurl']=self.spider.baseurl
        self.items['crawlera_user']=self.spider.crawlera_user
        self.items['referrer']=self.spider.referrer
        self.items['searchurl']=self.spider.searchurl
        self.items['LUA_SOURCE']=self.spider.LUA_SOURCE
        self.items['_test_true']=self.spider._test_true
        self.items['_result']=self.spider._result

        # finally, set the written flag for the worker use
        self.items.written = True

        # scraper properties
        # scraper private methods
        # public methods

    def to_json(self, item):
        """
        # todo: create a switch to serialize all the write attributes to JSON.
            This may fix the newt.db issue.
        :param item:
        :return:
        """
        raise NotImplementedError