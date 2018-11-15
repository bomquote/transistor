# -*- coding: utf-8 -*-
"""
transistor.tests.unit.browsers.test_splash_browser
~~~~~~~~~~~~
This module implements some unit tests for the SplashBrowser class.

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

from pytest import raises


class TestSplashBrowser:
    """
    Unit test a few methods that are not caught with the live functional testing
    in TestLiveBooksToScrape.
    """

    def test_set_raw_content(self, splash_browser):

        splash_browser._set_raw_content(content=None)
        assert splash_browser._content == b''

        with raises(TypeError) as e:
            splash_browser._set_raw_content(content="content")

    def test_set_status(self, splash_browser):

        splash_browser._set_status(status=None)
        assert splash_browser._status == ''

    def test_get_current_form(self, splash_browser):

        assert splash_browser.get_current_form() == \
        splash_browser._SplashBrowser__state.form

