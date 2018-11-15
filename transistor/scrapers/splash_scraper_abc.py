# -*- coding: utf-8 -*-
"""
transistor.scrapers.splash_scraper_abc
~~~~~~~~~~~~
This module implements an abstract base class for a scraper which assumes the
use of a Splash headless browswer/javascript rendering service. It also supports
the optional use of using Crawlera smart proxy service from scrapinghub.com.

This class must be subclassed and all abstract methods implemented. To create final
scraper implementations, methods must be customized per needs to scrape a target
website.

Notes:
    - self.browser provides a class based from mechanicalsoup with similar API + more
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


class SplashScraper(ABC):
    """
    Base class to help implement any kind of Splash or Splash + Crawlera scraper.

    Note:
        This is the abstract base class and you must subclass it to use it.

    """

    # always just set these class attributes which are used for concurrency
    baseurl = None
    name = None
    number = None

    @abstractmethod
    def __init__(self, name=None, script=None, **kwargs):
        """
        Create the instance. Each subclass should call super().__init__()
        and then set the specific required attributes like self.baseurl and
        self.searchurl.
        """
        super().__init__()

        # ---------------  specify in subclass __init__()  ----------------- #

        self.baseurl = None  # set after calling super().__init__()
        self.referrer = None  # this should be set to base domain url with http(s)://
        self.searchurl = None  # set after calling super().__init__()
        self.crawlera_user = None  # set after calling super().__init__()

        # the splash lua script. Modify this in the subclass __init__ as appropriate.
        if script:
            self.LUA_SOURCE = script
        else:
            self.LUA_SOURCE = get_data(
                'transistor',
                'scrapers/scripts/basic_splash.lua').decode('utf-8')

        # after calling super().__init__(), call self.start_http_session()

        ##################################################################

        # ----- kwargs for testing setup ----- #
        # page_text, status_code=None, url=None, soup_config=None
        self._test_true = kwargs.get('_test_true', False)
        self._test_page_text = kwargs.get('_test_page_text', None)
        self._test_status_code = kwargs.get('_test_status_code', None)
        self._test_url = kwargs.get('_test_url', None)
        self._test_soup_config = kwargs.get('_test_soup_config', None)
        # ----- end kwargs for testing setup ----- #

        # give it a name so we can easily reference it
        self.name = name

        # set this results flag to True. If a public method returns None then
        # this self._result flag will switch to False.
        self._result = True

        # Whether we already have a valid HTTP session with the remote server
        self.http_session_valid = False

        # set the splash_json, look for kwargs
        self.splash_json = kwargs.get('splash_json', None)

        # ssl._create_default_https_context = ssl._create_unverified_context
        self.crawlera_ca = get_data('transistor',
                            'scrapers/certs/crawlera-ca.crt').decode('utf-8')

        ssl.create_default_context(cadata=self.crawlera_ca)

        self.browser = SplashBrowser(
            soup_config={'features': 'lxml'},
            requests_adapters={'http://': HTTPAdapter(max_retries=5)})

        self.cookies = dict_from_cookiejar(self.browser.session.cookies)

        # set the splash basic authorization
        self.auth = basic_auth_header(
            username=os.environ.get('SPLASH_USERNAME', 'user'),
            password=os.environ.get('SPLASH_PASSWORD', 'userpass'))
        self.browser.session.headers.update({'Authorization': self.auth})

    def __repr__(self):
        return f'<SplashScraper({self.name})>'

    @abstractmethod
    def start_http_session(self, url=None, timeout=(3.05, 10.05)):
        """
        Start the connection.

        :param: url: The url you would like your scraper to use for initial
        landing. If you do not provide this url, but you do have a self.searchurl
        attribute set, then this method will default to use the self.searchurl.

        :param timeout: About the timeout parameter:

        First, you may want to review the python-request docs about timeouts.
        http://docs.python-requests.org/en/master/user/advanced/#timeouts

        My interpretation is, for our use case, the first number is just the maximum
        allowed time to connect to our splash localhost server. In practice, this
        execution should be near instant. The 3.05 is listed in the python-request docs
        so we just accept that as the standard here and get on with it.

        The second timeout number is more interesting.  Tt’s the number of seconds
        that the client will wait between bytes sent from the server. It is not
        the total time to timeout.

        Finally, if using Crawlera, the recommended timeout (2nd number here) from
        their docs is at least 600 seconds. In practice, I've found that 600.0 is
        too low for several electronic component websites which we scrape. In some
        cases, while using Crawlera, we need to set this second timeout number as
        high as 1200 seconds.

        If you use Crawlera, you will need to adjust the second timeout based on
        the individual website. If the website uses 150 links to load the web page, and
        you don't optimize your LUA script to drop unnecessary links, then
        you can expect to need up to 12 seconds x 150 links = 1,800 seconds to fully
        load the page in Crawlera. Scraping is a slow process with Splash + Crawlera.

        https://support.scrapinghub.com/support/solutions/articles/22000188397-crawlera-best-practices
        """
        if self._test_true:
            self.http_session_valid = True
            return self.browser.open_fake_page(
                page_text=self._test_page_text, status_code=self._test_status_code,
                url=self._test_url, soup_config=self._test_soup_config)

        if not self.http_session_valid:
            # Send the post request to Splash
            if url is None:
                url = self.searchurl
            return self._stateful_post(url=url, json=None, timeout=timeout)

    def open(self, url, json: dict=None, reuse_session=False, timeout=(3.05, 10.05),
             *args, **kwargs):
        """
        Open a url page in Splash, by sending a post request to your local running
        Splash service. If you are using Crawlera, you can reuse the current session,
        by setting the reuse_session flag to True.

        Primarily, this method is intended to help provide flexibility in link
        following.

        Note:
        Generally, you should create the first network request for any subclass
        based off this SplashScraper class with start_http_session, rather than using
        this open() method.

        But, if you do use this open() method as the first http session (bypassing
        the start_http_session call), you must explicitly provide the json=dict()
        to set the self.crawlera json attribute. And, you also need to set
        self.http_session_valid = False to self.http_session_valid = True.

        Otherwise, this class is going to break if you make the first session call
        from a direct call to this open() method.

        :param url: the url to open

        :param json: a python dict which will be sent in a post request to the Splash
        service, and will serve to set the splash.args, which will allow the
        splash.args to then be fully accessible from inside the lua script.

        :param reuse_session: whether to use the existing crawlera session_id in the
        call to open().

        :param timeout: see note in SplashCrawleraComponentScraper.start_http_session
        """
        if reuse_session:
            self._reuse_crawlera_session()

        return self._stateful_post(url, json=json, timeout=timeout,
                                   *args, **kwargs)

    def _stateful_post(self, url, json=None, *args, **kwargs):
        """
        Execute sending the post request to the local running Splash service with our
        self.browser object.

        :param url: the url to open
        :param json: a python dict which will be sent in a post request to the Splash
        service. This dict will serve to set the splash.args attributes so they are
        available for use in the LUA script simply by referencing splash.args.
        :param timeout: see note in start_http_session() for more detail
        """
        timeout = kwargs.pop('timeout', (3.05, 3600.05))
        keyword = kwargs.get('keyword', None)

        if not json:
            self.splash_json = {
                'lua_source': self.LUA_SOURCE,
                'url': url,
                'crawlera_user': self.crawlera_user,
                # set Splash to cache the lua script, to avoid sending it every request
                'cache_args': 'lua_source',
                'timeout': timeout[1],
                'session_id': 'create',
                'referrer': self.referrer if not None else "https://www.google.com",
                'searchurl': self.searchurl,
                'keyword': keyword,  # can be used in the LUA script to submit a form
                'cookies': self.cookies
            }
        else:
            self.splash_json = json
        response = self.browser.stateful_post(
            'http://localhost:8050/execute',
            json=self.splash_json,
            timeout=timeout,
            verify=self.crawlera_ca,
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
        self.splash_json['session_id'] = self.session_id

    @property
    def page(self):
        """return the page"""
        return self.browser.get_current_page()
