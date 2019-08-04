# -*- coding: utf-8 -*-
"""
transistor.crawlers.splash_crawler_abc
~~~~~~~~~~~~
This module implements an abstract base class for a crawler which assumes the
use of a Splash headless browswer/javascript rendering service. It also supports
the optional use of using Crawlera smart proxy service from scrapinghub.com.

This class must be subclassed and all abstract methods implemented. To create final
crawler implementations, methods must be customized per crawl needs.

Notes:
    - self.browser provides a class based from mechanicalsoup with similar API
    - self.browser.session provides direct access to the python-requests object
    - beautifulsoup4 methods can be used on the self.page attribute

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

import os
import ssl
from abc import ABC, abstractmethod
from w3lib.http import basic_auth_header
from requests.utils import dict_from_cookiejar
from requests.adapters import HTTPAdapter
from pkgutil import get_data
from transistor.browsers.splash_browser import SplashBrowser

class SplashCrawler(ABC):
    """
    Base class to help implement a Splash or Splash + Crawlera crawler.

    Note:
        This is the abstract base class and you must subclass it to use it.
    """

    __attrs__ = [
        'auth', 'baseurl', 'browser', 'cookies', 'crawlera_user',
        'http_session_timeout', 'http_session_valid', 'LUA_SOURCE', 'max_retries',
        'name', 'number', 'referrer', 'searchurl', 'splash_args', 'splash_wait'
        'user_agent',
    ]

    # class attrs used for concurrency
    baseurl = None
    name = None
    number = None

    @abstractmethod
    def __init__(self, script=None, **kwargs):
        """
        Create the instance. Required attributes are listed below as kwarg
        parameters. They can be set with kwargs or else should be explicitly
        specified in a sublcass __init__ and then have a call to
        super().__init__() made.

        :param script:() your custom lua script, if any, passed to LUA_SOURCE

        :param: kwargs: <item>:str() where <item> is an appropriate keyword search
        term, like 'book_title' or 'part_number'.  Set this keyword in your subclassed
        scraper as required.

        :param kwargs: baseurl:str() the baseurl like 'http://books.toscrape.com/'

        :param kwargs: searchurl:str() a specific url to execute searches on your
        scrape target's website, if any.

        :param kwargs: referrer: str(): the referrer to include in the headers of your
        scraper. Default is 'https://www.google.com'.

        :param kwargs: user_agent:str() set a custom user-agent header string like
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
        (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'

        :param kwargs: name:str() give the scraper a name for easy reference.

        :param kwargs: max_retries:int() The maximum number of retries each
        connection should attempt. Note, this applies only to failed DNS
        lookups, socket connections and connection timeouts, never to requests
        where data has made it to the server. By default, Requests does not
        retry failed connections. If you need granular control over the
        conditions under which we retry a request, import urllib3's ``Retry``
        class and pass that instead.

        :param kwargs: http_session_timeout:tuple(float, float) => (3.05, 10.05)
        This first number is maximum allowed seconds to connect to our splash
        localhost server. The second timeout number is the number of seconds
        that the client will wait between bytes sent from the server (it is not the
        total timeout).

        :param kwargs: splash_wait:float() controls the time in seconds Splash will
        wait after opening a web page, before taking actions. Default 3.0 sec.

        :param kwargs: splash_args:dict(): a python dict which will be sent in a post
        request to the Splash service. This dict will serve to set the splash.args
        attributes so they are available for use in the LUA script simply by
        referencing splash.args. Default is as below:
        self.splash_args = {
                'lua_source': self.LUA_SOURCE,
                'url': url,
                'crawlera_user': self.crawlera_user,
                # sets Splash to cache the lua script, avoids sending it every request
                'cache_args': 'lua_source',
                'timeout': timeout[1],  # timeout (in seconds) for the render, 3600 max
                'session_id': 'create',
                'referrer': self.referrer if not None else "https://www.google.com",
                'searchurl': self.searchurl,
                'keyword': keyword,  # can be used in the LUA script to submit a form
                'cookies': self.cookies,
                'user_agent': self.user_agent,
                'splash_wait': self.splash_wait,
                'js_source': self.js_source
            }
        """
        super().__init__()

        # The splash lua script. Provide a custom lua script to fit your use case.
        if script:
            self.LUA_SOURCE = script
        else:
            self.LUA_SOURCE = get_data(
                'transistor',
                'scrapers/scripts/basic_splash.lua').decode('utf-8')

        # after calling super().__init__(), call self.start_http_session()

        # ------------------ kwargs ---------------- #
        # Set these as needed in your subclass with keywords or hardcoded.
        self.baseurl = kwargs.pop('baseurl', None)
        self.searchurl = kwargs.pop('searchurl', None)
        self.crawlera_user = kwargs.pop('crawlera_user', None)
        self.name = kwargs.pop('name', None)
        self.referrer = kwargs.pop('referrer', None)
        self.user_agent = kwargs.pop('user_agent',
                                     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                                     "Chrome/73.0.3683.86 Safari/537.36")
        self.max_retries = kwargs.pop('max_retries', 5)
        self.http_session_timeout = kwargs.pop('http_session_timeout', (3.05, 10.05))
        self.splash_args = kwargs.pop('splash_args', None)
        self.splash_wait = kwargs.pop('splash_wait', 3.0)
        self.js_source = kwargs.pop('js_source', None)

        # ----- kwargs only used for testing setup ----- #
        self._test_true = kwargs.get('_test_true', False)
        self._test_page_text = kwargs.get('_test_page_text', None)
        self._test_status_code = kwargs.get('_test_status_code', None)
        self._test_url = kwargs.get('_test_url', None)
        self._test_soup_config = kwargs.get('_test_soup_config', None)
        # ----- end kwargs for testing setup ----- #

        # ------ flags for internal use --------- #
        # For example, if a public method on your scraper returns
        # None undesirably, switch the self._result flag to False.
        # Then, you can just delete scrape results if flagged False.
        self._result = True
        # ------- /end internal use flags -------- #

        # Whether we already have a valid HTTP session with the remote server
        self.http_session_valid = False

        # ssl._create_default_https_context = ssl._create_unverified_context
        self._crawlera_ca = get_data('transistor',
                            'scrapers/certs/crawlera-ca.crt').decode('utf-8')

        ssl.create_default_context(cadata=self._crawlera_ca)

        self.browser = SplashBrowser(
            soup_config={'features': 'lxml'},
            requests_adapters={'http://': HTTPAdapter(max_retries=self.max_retries)})

        self.cookies = dict_from_cookiejar(self.browser.session.cookies)

        # set the splash basic authorization
        self.auth = basic_auth_header(
            username=os.environ.get('SPLASH_USERNAME', 'user'),
            password=os.environ.get('SPLASH_PASSWORD', 'userpass'))
        self.browser.session.headers.update({'Authorization': self.auth})

    def __repr__(self):
        return f'<SplashScraper({self.name})>'

    @abstractmethod
    def start_http_session(self, url=None, **kwargs):
        """
        Start the connection.

        :param: url: The url you would like your scraper to use
        for initial landing. If you do not provide this url, but
        you do have a self.searchurl attribute set, then this method
        will default to use the self.searchurl.

        :param timeout: About the timeout parameter:

        First, you may want to review the python-request docs about timeouts.
        http://docs.python-requests.org/en/master/user/advanced/#timeouts

        If using Crawlera, the recommended timeout (2nd number) from
        crawlera docs is at least 600 seconds. In practice, I've found
        that 600.0 is too low for several websites which we scrape. In
        some cases, while using Crawlera, we need to set this second timeout
        number as high as 1200 seconds.

        If you use Crawlera, you will need to adjust the second timeout
        based on the individual website. If the website uses 150 links to
        load the web page, and you don't optimize your LUA script to drop
        unnecessary links, then you can expect to need up to
        12 seconds x 150 links = 1,800 seconds to fully load the page
        in Crawlera. Scraping is a slow process with Splash + Crawlera.

        https://support.scrapinghub.com/support/solutions/articles/22000188397-crawlera-best-practices
        """
        timeout = kwargs.pop('timeout', self.http_session_timeout)

        if self._test_true:
            self.http_session_valid = True
            return self.browser.open_fake_page(
                page_text=self._test_page_text, status_code=self._test_status_code,
                url=self._test_url, soup_config=self._test_soup_config)

        if not self.http_session_valid:
            # Send the post request to Splash
            if url is None:
                url = self.searchurl
            return self._stateful_post(url=url, splash_args=None, timeout=timeout)

    def open(self, url, splash_args:dict=None, reuse_session=False, *args, **kwargs):
        """
        Open a url page in Splash, by sending a post request to your local
        running Splash service. If you are using Crawlera, you can reuse
        the current session, by setting the reuse_session flag to True.

        This method is intended to provide flexibility in link following, after
        the initial http_connection has been made with start_http_session..

        Note:
        Generally, you should create the first network request for any subclass
        based off this SplashScraper class with start_http_session().

        But, if you do use this open() method bypassing the initial
        start_http_session call, you must explicitly provide the
        splash_args=dict(). And, you also need to set
        self.http_session_valid = True. Otherwise, this class is going to break.

        :param url: the url to open

        :param splash_args: a python dict which will be sent in a post
        request to the Splash service, which will set the dict(key, value) pairs
        to then be accessible from inside the lua script as splash.args.

        :param reuse_session: whether to use the existing crawlera session_id
        in the call to open().

        :param kwargs: timeout: see note in self.start_http_session
        :param kwargs: callback: a user defined function to call after the
        response is returned. Useful for crawling.
        """
        timeout = kwargs.pop('timeout', self.http_session_timeout)

        if reuse_session:
            self._reuse_crawlera_session()

        if splash_args:
            self.splash_args = splash_args

        return self._stateful_post(url, splash_args=splash_args, timeout=timeout,
                                   *args, **kwargs)

    def _stateful_post(self, url, *args, **kwargs):
        """
        Execute sending the post request to the local running Splash service with our
        self.browser object.

        :param url: the url to open
        :param splash_args: a python dict which will be sent in a post request
        to the Splash service. This dict will serve to set the splash.args
        attributes so they are available for use in the LUA script simply by
        referencing splash.args.
        :param timeout: see note in start_http_session() for more detail
        """
        timeout = kwargs.pop('timeout', self.http_session_timeout)
        keyword = kwargs.pop('keyword', None)
        splash_args = kwargs.pop('splash_args', self.splash_args)

        if not splash_args:
            self.splash_args = {
                'lua_source': self.LUA_SOURCE,
                'url': url,
                'crawlera_user': self.crawlera_user,
                # set Splash to cache the lua script, to avoid sending it every request
                'cache_args': 'lua_source',
                'timeout': timeout[1],  # timeout (in seconds) for the render, 3600 max
                'session_id': 'create',
                'referrer': self.referrer if not None else "https://www.google.com",
                'searchurl': self.searchurl,
                'keyword': keyword,  # can be used in the LUA script to submit a form
                'cookies': self.cookies,
                'user_agent': self.user_agent,
                'splash_wait': self.splash_wait,
                'js_source':  ";" if not self.js_source else self.js_source,
                'script': 0 if not self.js_source else 1
            }
        else:
            self.splash_args = splash_args
        response = self.browser.stateful_post(
            # 'http://localhost:8050/render.json'if self.js_source else
            'http://localhost:8050/execute',
            json=self.splash_args,
            timeout=timeout,
            verify=self._crawlera_ca,
            stream=True, *args, **kwargs)
        self.http_session_valid = True
        return response

    @property
    def session_id(self):
        """
        This is the crawlera session id which is returned by X-Crawlera-Session.

        Reusing the same crawlera session during the lifetime of this object may be
        useful, depending on your need.

        """
        return self.browser.crawlera_session

    def _reuse_crawlera_session(self):
        """
        Update the self.splash_json['session_id'] to the current session_id so
        that the current session will be extended with an self.open() request.

        """
        self.splash_args['session_id'] = self.session_id

    @property
    def page(self):
        """return the page"""
        return self.browser.get_current_page()