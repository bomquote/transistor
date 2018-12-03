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
import time
from requests import Response
from bs4 import BeautifulSoup
from pkgutil import get_data
from pathlib import Path
from os.path import dirname as d
from os.path import abspath
from kombu import Connection
from transistor.schedulers.brokers.queues import ExchangeQueue
from transistor import StatefulBook, WorkGroup
from transistor.persistence.newt_db.collections import SpiderLists
from transistor.persistence.exporters.exporters import CsvItemExporter
from ..conftest import get_job_results, delete_job
from examples.books_to_scrape.persistence.newt_db import ndb
from examples.books_to_scrape.scraper import BooksToScrapeScraper
from examples.books_to_scrape.manager import BooksWorkGroupManager
from examples.books_to_scrape.persistence.serialization import (
    BookItems, BookItemsLoader)
from examples.books_to_scrape.schedulers.brokers.client_main import send_as_task

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
def bts_book_manager(_BooksToScrapeGroup, _BooksWorker):
    """
    A BooksToScrape Manager test fixture for live network call.
    Here, we are spinning up two workers, while we have three
    tasks. It is important to test this as such, in spinning up
    a less number of workers vs total tasks.  There are plenty
    of ways to break this test when refactoring. One likely
    source would be the BaseWorker class method `load_items`.
    It took me half-a-day to track down a bug in that method
    which resulted in this test only working if the # workers
    was equal to the number of tasks. That was the previous
    default way to run this test, so the bug went un-found.
    """
    # ensure to open this file in binary mode
    book_data_file = open('c:/tmp/book_data.csv', 'a+b')
    exporters = [
        CsvItemExporter(
            fields_to_export=['book_title', 'stock', 'price'],
            file=book_data_file,
            encoding='utf_8_sig'
        )
    ]

    file = get_file_path('book_titles.xlsx')
    trackers = ['books.toscrape.com']
    tasks = StatefulBook(file, trackers, keywords='titles', autorun=True)

    groups = [
        WorkGroup(
            name='books.toscrape.com',
            url='http://books.toscrape.com/',
            spider=BooksToScrapeScraper,
            worker=_BooksWorker,
            items=BookItems,
            loader=BookItemsLoader,
            exporters=exporters,
            workers=2,  # this creates 2 scrapers and assigns each a book as a task
            kwargs={'timeout': (3.0, 20.0)})
    ]
    manager = BooksWorkGroupManager('books_scrape', tasks, workgroups=groups, pool=5)

    return manager


@pytest.fixture(scope='function')
def broker_tasks():
    trackers = ['books.toscrape.com']
    tasks = ExchangeQueue(trackers)
    return tasks


@pytest.fixture(scope='function')
def rabbit_conn():
    """
    A Kombu connection object with RabbitMQ URI.
    """
    connection = Connection("pyamqp://guest:guest@localhost:5672//")
    return connection


@pytest.fixture(scope='function')
def bts_broker_manager(_BooksToScrapeGroup, _BooksWorker, broker_tasks,
                       rabbit_conn):
    """
    A BooksToScrape Manager test fixture for live network call.
    Here, we use a broker (RabbitMQ) to test.
    """
    # ensure to open this file in binary mode
    book_data_file = open('c:/tmp/broker_data.csv', 'a+b')
    exporters = [
        CsvItemExporter(
            fields_to_export=['book_title', 'stock', 'price'],
            file=book_data_file,
            encoding='utf_8_sig'
        )
    ]

    groups = [
        WorkGroup(
            name='books.toscrape.com',
            url='http://books.toscrape.com/',
            spider=BooksToScrapeScraper,
            worker=_BooksWorker,
            items=BookItems,
            loader=BookItemsLoader,
            exporters=exporters,
            workers=2,  # this creates 2 scrapers and assigns each a book as a task
            kwargs={'timeout': (3.0, 20.0)})
    ]
    manager = BooksWorkGroupManager('books_broker_scrape', broker_tasks,
                                    workgroups=groups, pool=5, connection=rabbit_conn)

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

    def test_live_book_scheduled_manager(self, bts_book_manager):
        """
        Test a live scrape using an excel workbook and the StatefulBook
        class scheduler.
        """

        # todo: move this to a setup fixture
        # first, setup newt.db for testing
        ndb.root._spiders = SpiderLists()
        ndb.commit()

        # now, perform the scrape
        bts_book_manager.main()

        # when the scrape is completed then check the results

        result = get_job_results('books_scrape')

        book_titles = []
        prices = []
        stocks = []
        for r in result:
            book_titles.append(r['book_title'])
            prices.append(r['price'])
            stocks.append(r['stock'])

        assert len(book_titles) == 3
        assert len(prices) == 3
        assert len(stocks) == 3

        assert 'Soumission' in book_titles
        assert 'Rip it Up and Start Again' in book_titles
        assert 'Black Dust' in book_titles
        assert 'UK £50.10' in prices
        assert 'In stock' in stocks
        assert None not in prices
        assert None not in stocks

        assert result[0]['har']['log']['browser']['comment'] == 'PyQt 5.9, Qt 5.9.1'
        assert result[0]['png']

        # the below should currently return None if not using Crawlera
        assert result[0]['endpoint_status'] is None
        assert result[0]['crawlera_session'] is None
        assert result[0]['resp_content_type_header'] is None

        # todo: move this to a teardown fixture
        delete_job('books_scrape')
        del ndb.root._spiders
        ndb.commit()

    def test_live_broker_scheduled_manager(self, bts_broker_manager, rabbit_conn,
                                           broker_tasks):
        """
        Test a live scrape using RabbitMQ broker and the ExchangeQueue
        class passed to the Manager tasks parameter.
        """

        # first, use a producer to send the tasks to RabbitMQ
        keyword_1 = '["Soumission"]'
        keyword_2 = '["Rip it Up and Start Again"]'
        keywords = '["Black Dust", "When We Collided"]'

        send_as_task(rabbit_conn, keywords=keyword_1, routing_key='books.toscrape.com',
                     exchange=broker_tasks.task_exchange, kwargs={})
        send_as_task(rabbit_conn, keywords=keyword_2, routing_key='books.toscrape.com',
                     exchange=broker_tasks.task_exchange, kwargs={})
        send_as_task(rabbit_conn, keywords=keywords, routing_key='books.toscrape.com',
                     exchange=broker_tasks.task_exchange, kwargs={})
        # give it a few seconds to ensure the tasks are registered in RabbitMQ
        time.sleep(3)

        # setup newt.db for testing
        ndb.root._spiders = SpiderLists()
        ndb.commit()
        time.sleep(2)

        # now, perform the scrape
        bts_broker_manager.main()

        # when the scrape is completed then check the results

        result = get_job_results('books_broker_scrape')

        book_titles = []
        prices = []
        stocks = []
        for r in result:
            book_titles.append(r['book_title'])
            prices.append(r['price'])
            stocks.append(r['stock'])

        assert len(book_titles) == 4
        assert len(prices) == 4
        assert len(stocks) == 4

        assert 'Soumission' in book_titles
        assert 'Rip it Up and Start Again' in book_titles
        assert 'Black Dust' in book_titles
        assert 'When We Collided' in book_titles
        assert 'UK £50.10' in prices
        assert 'In stock' in stocks
        assert None not in prices
        assert None not in stocks

        assert result[0]['har']['log']['browser']['comment'] == 'PyQt 5.9, Qt 5.9.1'
        assert result[0]['png']

        # the below should currently return None if not using Crawlera
        assert result[0]['endpoint_status'] is None
        assert result[0]['crawlera_session'] is None
        assert result[0]['resp_content_type_header'] is None

        delete_job('books_broker_scrape')
        del ndb.root._spiders
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
            'splash_wait': bts_live_scraper.splash_wait,
            'js_source': ";" if not bts_live_scraper.js_source else
            bts_live_scraper.js_source,
            'script': 0 if not bts_live_scraper.js_source else 1
        }
        page = bts_live_scraper.browser.open('http://localhost:8050/execute',
                                             json=bts_live_scraper.splash_args,
                                             timeout=(3.0, 10.0),
                                             verify=bts_live_scraper._crawlera_ca,
                                             stream=True)
        assert type(page) == Response