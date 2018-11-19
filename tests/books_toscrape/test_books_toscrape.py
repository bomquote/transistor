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
from gevent import monkey
monkey.patch_all()
import pytest
from requests import Response
from bs4 import BeautifulSoup
from pkgutil import get_data
from pathlib import Path
from os.path import dirname as d
from os.path import abspath
from transistor import StatefulBook, WorkGroup
from transistor.persistence.newt_db.collections import ScrapeLists
from ..conftest import get_job_results, delete_job
from examples.books_to_scrape.persistence.newt_db import ndb
from examples.books_to_scrape.scraper import BooksToScrapeScraper
from examples.books_to_scrape.manager import BooksWorkGroupManager

root_dir = d(d(abspath(__file__)))


def get_html(filename):
    """
    Get the appropriate html testfile and return it. Filename should include
    the folder the file is in.

    :param filename: ex. -> "digidog/digidog_china_multiple.html"
    """
    data_folder = Path(root_dir)
    file_to_open = data_folder / filename
    f = open(file_to_open, encoding='utf-8')
    return f.read()


def get_file_path(filename):
    """
    Find the book_title excel file path.
    """
    root_dir = d(d(abspath(__file__)))
    root = Path(root_dir)
    filepath = root / 'books_toscrape' / filename
    return r'{}'.format(filepath)


@pytest.fixture(scope='function')
def bts_static_scraper(test_dict):
    """
    A BooksToScrapeScraper static test fixture.
    """
    book_title = 'Soumission'
    page = get_html("books_toscrape/books_toscrape_index.html")
    test_dict['_test_page_text'] = page
    test_dict['url'] = 'http://books.toscrape.com'
    scraper = BooksToScrapeScraper(book_title=book_title, **test_dict)
    scraper.start_http_session()
    return scraper


@pytest.fixture(scope='function')
def bts_live_scraper():
    """
    A BooksToScrapeScraper live fixture for TestLiveBooksToScrape.
    """
    scraper = BooksToScrapeScraper(book_title='Black Dust')
    scraper.start_http_session(url='http://books.toscrape.com')
    return scraper


@pytest.fixture(scope='function')
def bts_manager(_BooksToScrapeGroup):
    """
    A BooksToScrape Manager test fixture for live network call.
    """
    file = get_file_path('book_titles.xlsx')
    trackers = ['books.toscrape.com']
    stateful_book = StatefulBook(file, trackers, keywords='titles', autorun=True)
    groups = [
        WorkGroup(
            class_=_BooksToScrapeGroup,
            workers=3,  # this creates 3 scrapers and assigns each a book as a task
            name='books.toscrape.com',
            kwargs={'url': 'http://books.toscrape.com/', 'timeout': (3.0, 20.0)})
    ]
    manager = BooksWorkGroupManager('books_scrape', stateful_book, groups=groups,
                                    pool=5)
    return manager


class TestStaticBooksToScrapeScraper:
    """
    Unit test some BooksToScrapeScraper methods using a static html page to hit a
    few methods which can be easily tested without live network request.
    """
    def test_stock(self, bts_static_scraper):
        """
        Test that the stock attribute has been properly set
        """
        assert bts_static_scraper.stock == 'In stock'

    def test_price(self, bts_static_scraper):
        """
        Test that the price attribute has been properly set
        """
        assert bts_static_scraper.price == '£50.10'

    def test_next_page(self, bts_static_scraper):
        """
        Test that the _next_page method returns the expected url
        """
        next_page = bts_static_scraper._next_page()
        assert next_page == r'http://books.toscrape.com/catalogue/page-2.html'

    def test_LUA_SOURCE(self, bts_static_scraper):
        """
        Test the LUA_SOURCE returns as expected.
        """
        source = bts_static_scraper.LUA_SOURCE
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

    def test_ucontent(self, bts_static_scraper):
        """
        Test ucontent method returns as expected.
        """
        assert bts_static_scraper.browser.ucontent.startswith('<!DOCTYPE html>')

    def test_resp_content(self, bts_static_scraper):
        """
        Test resp_content returns an empty dict.
        """
        assert bts_static_scraper.browser.resp_content == {}

    def test_get_current_page_is_soup(self, bts_static_scraper):
        """
        Test get_current_page() returns a beautifulsoup4 object.
        """
        page = bts_static_scraper.browser.get_current_page()
        assert type(page) == BeautifulSoup

    def test_get_current_page_to_string(self, bts_static_scraper):
        """
        Test get_current_page() cast to string is roughly similar to our html.
        """
        get_page = str(bts_static_scraper.browser.get_current_page())
        html = get_html("books_toscrape/books_toscrape_index.html")
        assert get_page[:100] == html[:100]


class TestLiveBooksToScrape:
    """
    Run through a live scrape of books.toscrape.com, save to newt_db,
    and check the newt_db results are what we expect.
    """

    def test_live_manager(self, bts_manager):
        """
        Test that the stock attribute has been properly set
        """

        # todo: move this to a setup fixture
        # first, setup newt.db for testing
        ndb.root._scrapes = ScrapeLists()
        ndb.commit()

        # now, perform the scrape
        bts_manager.main()

        # when the scrape is completed then check the results

        result = get_job_results('books_scrape')

        book_titles = []
        prices = []
        stocks = []
        for r in result:
            book_titles.append(r.book_title)
            prices.append(r.price)
            stocks.append(r.stock)

        assert len(book_titles) == 3
        assert len(prices) == 3
        assert len(stocks) == 3

        assert 'Soumission' in book_titles
        assert 'Rip it Up and Start Again' in book_titles
        assert 'Black Dust' in book_titles
        assert '£50.10' in prices
        assert 'In stock' in stocks

        assert result[0].har['log']['browser']['comment'] == 'PyQt 5.9, Qt 5.9.1'
        assert result[0].png

        # the below should currently return None if not using Crawlera
        assert result[0].endpoint_status is None
        assert result[0].crawlera_session is None
        assert result[0].resp_content_type_header is None


        # todo: move this to a teardown fixture
        delete_job('books_scrape')
        del ndb.root._scrapes
        ndb.commit()

    def test_live_scraper_browser_open(self, bts_live_scraper):
        """Test the scraper.browser.open method returns Response"""

        link = 'http://books.toscrape.com/catalogue/black-dust_976/index.html'
        bts_live_scraper.splash_args = {
            'lua_source': bts_live_scraper.LUA_SOURCE,
            'url': link,
            'crawlera_user': bts_live_scraper.crawlera_user,
            # set Splash to cache the lua script, to avoid sending it every request
            'cache_args': 'lua_source',
            'timeout': 10.0,
            'session_id': 'create',
            'referrer': bts_live_scraper.referrer if not None else
            "https://www.google.com",
            'searchurl': bts_live_scraper.searchurl,
            'keyword': None,  # can be used in the LUA script to submit a form
            'cookies': bts_live_scraper.cookies,
            'user_agent': bts_live_scraper.user_agent,
            'splash_wait': bts_live_scraper.splash_wait
        }
        page = bts_live_scraper.browser.open('http://localhost:8050/execute',
                                             json=bts_live_scraper.splash_args,
                                             timeout=(3.0, 10.0),
                                             verify=bts_live_scraper._crawlera_ca,
                                             stream=True)
        assert type(page) == Response