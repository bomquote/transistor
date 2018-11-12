# -*- coding: utf-8 -*-
"""
transistor.tests.books_toscrape.test_books_toscrape
~~~~~~~~~~~~
This module implements testing of the books_toscrape example in order to
check Transistor source code.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

import pytest
from bs4 import BeautifulSoup
from pkgutil import get_data
from pathlib import Path
from os.path import dirname as d
from os.path import abspath
from examples.books_to_scrape.scraper import BooksToScrapeScraper


root_dir = d(d(abspath(__file__)))


def get_html(filename):
    """
    Get the appropriate html testfile and return it. Filename should include
    the folder the file is in.

    :param filename: ex. -> "digikey/dkchina_multiple.html"
    """
    data_folder = Path(root_dir)
    file_to_open = data_folder / filename
    f = open(file_to_open, encoding='utf-8')
    return f.read()


@pytest.fixture(scope='function')
def bts_scraper(test_dict):
    """
    A BooksToScrapeScraper test fixture.
    """
    book_title = 'Soumission'
    page = get_html("books_toscrape/books_toscrape_index.html")
    test_dict['_test_page_text'] = page
    test_dict['url'] = 'http://books.toscrape.com'
    scraper = BooksToScrapeScraper(book_title=book_title, **test_dict)
    scraper.start_http_session()
    return scraper


class TestStaticBooksToScrapeScraper:
    """
    Unit test some BooksToScrapeScraper methods using a static html page to hit a
    few methods which can be easily tested without live network request.
    """
    def test_stock(self, bts_scraper):
        """
        Test that the stock attribute has been properly set
        """
        assert bts_scraper.stock == 'In stock'

    def test_price(self, bts_scraper):
        """
        Test that the price attribute has been properly set
        """
        assert bts_scraper.price == '£50.10'

    def test_next_page(self, bts_scraper):
        """
        Test that the _next_page method returns the expected url
        """
        next_page = bts_scraper._next_page()
        assert next_page == r'http://books.toscrape.com/catalogue/page-2.html'

    def test_LUA_SOURCE(self, bts_scraper):
        """
        Test the LUA_SOURCE returns as expected.
        """
        source = bts_scraper.LUA_SOURCE
        expected = get_data(
            'transistor',
            'scrapers/scripts/basic_splash.lua').decode('utf-8')
        assert source == expected



class TestStaticSplashBrowser:
    """
    Unit test some SplashBrowser methods, using the BooksToScrapeScraper test fixture.
    Many of the methods depend on making a live network request. At the moment,
    we are only using a static html page to hit a few methods.
    """

    def test_ucontent(self, bts_scraper):
        """
        Test ucontent method returns as expected.
        """
        assert bts_scraper.browser.ucontent.startswith('<!DOCTYPE html>')

    def test_resp_content(self, bts_scraper):
        """
        Test resp_content returns an empty dict.
        """
        assert bts_scraper.browser.resp_content == {}

    def test_get_current_page_is_soup(self, bts_scraper):
        """
        Test get_current_page() returns a beautifulsoup4 object.
        """
        page = bts_scraper.browser.get_current_page()
        assert type(page) == BeautifulSoup

    def test_get_current_page_to_string(self, bts_scraper):
        """
        Test get_current_page() cast to string is roughly similar to our html.
        """
        get_page = str(bts_scraper.browser.get_current_page())
        html = get_html("books_toscrape/books_toscrape_index.html")
        assert get_page[:100] == html[:100]