# -*- coding: utf-8 -*-
"""
transistor.browsers.splash_browser
~~~~~~~~~~~~
This module implements the SplashBrowser class.

Splash browser is a subclass of mechanicalsoup.StatefulBrowser which
adds a few new methods and overrides most existing methods to make it work
with Splash and/or Splash + Crawlera.

It is important that the lua script be formatted with below:

If using Splash + Crawlera:

local entries = splash:history()
local last_response = entries[#entries].response
return {
    url = splash:url(),
    headers = last_response.headers,
    http_status = last_response.status,
    cookies = splash:get_cookies(),
    html = splash:html(),
    har=splash:har(),
    png=splash:png()
}

If only using Splash:

return {
    url = splash:url(),
    cookies = splash:get_cookies(),
    html = splash:html(),
    har=splash:har(),
    png=splash:png()
}

Except, it is not mandatory to return the har, cookies, or png.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

import bs4
import sys
import random
import gevent
from requests import Response
from requests.exceptions import Timeout
from mechanicalsoup.stateful_browser import _BrowserState, StatefulBrowser
from mechanicalsoup.utils import LinkNotFoundError
from mechanicalsoup.form import Form
from transistor.utility.utils import obsolete_setter
from transistor.browsers.mixin import SplashBrowserMixin


class SplashBrowser(StatefulBrowser, SplashBrowserMixin):
    """
    Make a few changes and overrides to enable a mechanicalsoup StatefulBrowser to
    work with Splash alone or Splash + Crawlera.

    Note: `select_form`, `submit` and `submit_selected` need refactored
    to work with Splash. Not useful/broken at the moment.
    """
    retry = 0

    def __init__(self, *args, **kwargs):
        self._set_raw_content(content=b'')
        self._set_status(status='')
        self.__state = _BrowserState()
        self._test_true = False
        self.timeout_exception = False
        kwargs.pop('encoding', None)  # encoding is always utf-8
        super().__init__(*args, **kwargs)

    def _get_raw_content(self):
        return self._content

    def _set_raw_content(self, content):
        if content is None:
            self._content = b''
        elif not isinstance(content, bytes):
            raise TypeError(
                "Response content must be bytes.")
        else:
            self._content = content

    raw_content = property(_get_raw_content, obsolete_setter(_set_raw_content, 'raw_content'))

    def _get_status(self):
        return self._status

    def _set_status(self, status):
        if status is None:
            self._status = ''
        else:
            self._status = status

    # this is the status code received from Splash service (NOT THE WEBSITE ENDPOINT)
    status = property(_get_status, obsolete_setter(_set_status, 'status'))

    def get_current_form(self):
        """Get the currently selected form as a :class:`Form` object.
        See :func:`select_form`.
        """
        return self.__state.form

    def get_current_page(self):
        """Get the current page as a soup object."""
        return self.__state.page

    def get_current_url(self):
        """Get the current url as a soup object. """
        return self.__state.url

    def get_current_request(self):
        """Get the last sent python-requests <PreparedRequest[POST]> object."""
        return self.__state.request

    def _update_state(self, response):
        """Dry up the setters from http post and get methods."""

        self._set_raw_content(response.content)
        self._set_status(response.status_code)
        self._add_soup(response, self.soup_config)
        self.__state = _BrowserState(page=response.soup,
                                     url=response.url,
                                     request=response.request)

    def open(self, url, *args, **kwargs):
        """Open the URL and store the Browser's state in this object.
        All arguments are forwarded to :func:`SplashCrawleraBrowser.stateful_post`.


        :return: Forwarded from :func:`Browser.stateful_post`.
        """
        if self.get_verbose() == 1:
            sys.stdout.write('.')
            sys.stdout.flush()
        elif self.get_verbose() >= 2:
            print(url)

        resp = self.stateful_post(url, *args, **kwargs)

        return resp

    def open_fake_page(self, page_text, status_code=None, url=None, soup_config=None):
        """Mock version of :func:`open`.

        Behave as if opening a page whose text is ``page_text``, but do not
        perform any network access. If ``url`` is set, pretend it is the page's
        URL. Useful mainly for testing.
        """
        soup_config = soup_config or self.soup_config
        self._test_true = True
        self._set_raw_content(page_text.encode())
        self._set_status(status_code)

        self.__state = _BrowserState(
            page=bs4.BeautifulSoup(page_text, **soup_config),
            url=url)

    def refresh(self):
        """Reload the current page with the same request as originally done.
        Any change (`select_form`, or any value filled-in in the form) made to
        the current page before refresh is discarded.

        :raise ValueError: Raised if no refreshable page is loaded, e.g., when
            using the shallow ``Browser`` wrapper functions.

        :return: Response of the request."""
        old_request = self.__state.request
        if old_request is None:
            raise ValueError('The current page is not refreshable. Either no '
                             'page is opened or low-level browser methods '
                             'were used to do so.')

        resp = self.session.send(old_request)

        self._update_state(resp)

        return resp

    def select_form(self, selector="form", nr=0):
        """Select a form in the current page.

        :param selector: CSS selector or a bs4.element.Tag object to identify
            the form to select.
            If not specified, ``selector`` defaults to "form", which is
            useful if, e.g., there is only one form on the page.
            For ``selector`` syntax, see the `.select() method in BeautifulSoup
            <https://www.crummy.com/software/BeautifulSoup/bs4/doc/#css-selectors>`__.
        :param nr: A zero-based index specifying which form among those that
            match ``selector`` will be selected. Useful when one or more forms
            have the same attributes as the form you want to select, and its
            position on the page is the only way to uniquely identify it.
            Default is the first matching form (``nr=0``).

        :return: The selected form as a soup object. It can also be
            retrieved later with :func:`get_current_form`.
        """
        if isinstance(selector, bs4.element.Tag):
            if selector.name != "form":
                raise LinkNotFoundError
            self.__state.form = Form(selector)
        else:
            # nr is a 0-based index for consistency with mechanize
            found_forms = self.get_current_page().select(selector,
                                                         limit=nr + 1)
            if len(found_forms) != nr + 1:
                if self.__debug:
                    print('select_form failed for', selector)
                    self.launch_browser()
                raise LinkNotFoundError()
            self.__state.form = Form(found_forms[-1])

        return self.get_current_form()

    def submit(self, form, url=None, **kwargs):
        """
        Prepares and sends a form request.

        NOTE: To submit a form with a :class:`StatefulBrowser` instance, it is
        recommended to use :func:`StatefulBrowser.submit_selected` instead of
        this method so that the browser state is correctly updated.

        :param form: The filled-out form.
        :param url: URL of the page the form is on. If the form action is a
            relative path, then this must be specified.
        :param \*\*kwargs: Arguments forwarded to `requests.Session.request
            <http://docs.python-requests.org/en/master/api/#requests.Session.request>`__.

        :return: `requests.Response
            <http://docs.python-requests.org/en/master/api/#requests.Response>`__
            object with a *soup*-attribute added by :func:`add_soup`.
        """
        if isinstance(form, Form):
            form = form.form
        response = self._request(form, url, **kwargs)
        self._add_soup(response, self.soup_config)
        return response

    def submit_selected(self, btnName=None, *args, **kwargs):
        """Submit the form that was selected with :func:`select_form`.

        :return: Forwarded from :func:`Browser.submit`.

        If there are multiple submit input/button elements, passes ``btnName``
        to :func:`Form.choose_submit` on the current form to choose between
        them. All other arguments are forwarded to :func:`Browser.submit`.
        """
        self.get_current_form().choose_submit(btnName)

        referer = self.get_current_url()
        if referer:
            if 'headers' in kwargs:
                kwargs['headers']['Referer'] = referer
            else:
                kwargs['headers'] = {'Referer': referer}

        resp = self.submit(self.__state.form, url=self.__state.url, **kwargs)

        # updates the state
        self._update_state(resp)

        return resp

    @staticmethod
    def __looks_like_html(blob):
        """Guesses entity type when Content-Type header is missing.
        Since Content-Type is not strictly required, some servers leave it out.
        """
        text = blob.lstrip().lower()
        return text.startswith('<html') or text.startswith('<!doctype')

    def _add_soup(self, response, soup_config):
        """Attaches a soup object to a requests response."""
        if self.resp_headers:
            if ("text/html" in self.resp_content_type_header or
                    SplashBrowser.__looks_like_html(self.html)):
                response.soup = bs4.BeautifulSoup(self.html, **soup_config)
        elif SplashBrowser.__looks_like_html(self.html):
            response.soup = bs4.BeautifulSoup(self.html, **soup_config)
        else:
            response.soup = None
        return response

    def post(self, *args, **kwargs):
        """Straightforward wrapper around `requests.Session.post
        <http://docs.python-requests.org/en/master/api/#requests.Session.post>`__.

        :return: `requests.Response
            <http://docs.python-requests.org/en/master/api/#requests.Response>`__
            object with a *soup*-attribute added by :func:`_add_soup`.
        """

        try:
            response = self.session.post(*args, **kwargs)
            self._update_state(response)
            return response
        except Timeout:
            self.timeout_exception = True
            print(f'Timeout exception.')
            resp = Response()
            resp.status_code = 408
            self._update_state(resp)
            return resp

    def stateful_post(self, url, *args, **kwargs):
        """Post to the URL and store the Browser's state, as received from
        the response object, in this object.

        All arguments are forwarded to :func:`SplashCrawleraBrowser.post`.

        :return: Forwarded from :func:`SplashCrawleraBrowser.post`.
        """

        if self.get_verbose() == 1:
            sys.stdout.write('.')
            sys.stdout.flush()
        elif self.get_verbose() >= 2:
            print(url)

        resp = self.post(url, *args, **kwargs)

        response_callback = self._response_callback(resp)

        return response_callback

    def _response_callback(self, resp):
        """
        Callback for after response received. If status code is not 200 then
        recursively retry. Retry up to five times.

        Flesh this out and do different things based on status code. Probably,
        better to get a way from searching strings.

        :returns response object
        """
        def callback(response):
            """Recursively call"""
            return self._response_callback(response)

        print(f'self.ucontent[0:1000] -> {self.ucontent[0:1000]}')
        # print(f'info -> {self.resp_content["info"]}')
        # print(f'error -> {self.resp_content["error"]}')
        if resp.status_code == 200:
            return resp

        if self.retry < 5:
            # check for http503 in content which has a few different meanings
            # see note 'HANDLING BANS' about 503 bans when handling your own session:
            # https://support.scrapinghub.com/support/solutions/articles/22000188402-using-crawlera-sessions-to-make-multiple-requests-from-the-same-ip
            # crawlera sessions operate with (at least) 12 second between requests..
            # ..so we wait a random time from 12 - 20 seconds, hope to improve yield

            # check for http503 in content: slavebanned, serverbusy, or noslaves
            if b'http503' in self.raw_content or '503' in str(self.status):
                self.retry += 1
                print(f'resp_code -> 503')
                print(f'Retying attempt {self.retry}.')
                gevent.sleep(random.randint(12, 20))
                response = self.refresh()
                return callback(response)

            # check for http504 in content which means some sort of timeout
            if b'http504' in self.raw_content or '504' in str(self.status):
                self.retry += 1
                print(f'resp_code -> 504')
                print(self.resp_headers)
                print(f'Retying attempt {self.retry}.')
                gevent.sleep(random.randint(12, 20))
                response = self.refresh()
                return callback(response)

        print(f'Retried {self.retry} times and all were unsuccessful.')
        return resp