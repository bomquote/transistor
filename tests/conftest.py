# -*- coding: utf-8 -*-
"""
transistor.tests.conftest
~~~~~~~~~~~~
This module defines pytest fixtures and other constants available to all tests.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

import pytest
from kombu import Connection
from kombu.pools import producers
from pathlib import Path
from os.path import dirname as d
from os.path import abspath
from requests.adapters import HTTPAdapter
from transistor import SplashBrowser
from transistor import BaseGroup
from transistor.persistence.newt_db.collections import SpiderList
from examples.books_to_scrape.workgroup import BooksWorker
from examples.books_to_scrape.persistence.newt_db import ndb
from transistor.schedulers.brokers.queues import ExchangeQueue
from transistor import StatefulBook, WorkGroup
from transistor.persistence.exporters.exporters import CsvItemExporter
from transistor.persistence.newt_db.collections import SpiderLists
from examples.books_to_scrape.scraper import BooksToScrapeScraper
from examples.books_to_scrape.manager import BooksWorkGroupManager
from examples.books_to_scrape.persistence.serialization import (
    BookItems, BookItemsLoader)

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
    Find the book_titles excel file path.
    """
    root = Path(root_dir)
    filepath = root / 'tests' / 'books_toscrape' / filename
    return r'{}'.format(filepath)


@pytest.fixture(scope='function')
def test_dict():
    """
    Need to set dict[_test_page_text] = get_html()
    :return dict
    """
    return {"_test_true": True, "_test_page_text": '', "_test_status_code": 200,
            "autostart": True}


@pytest.fixture(scope='function')
def _BooksWorker():
    """
    Create a BooksWorker which saves jobs to ndb.root._spiders.
    """
    class _BooksWorker(BooksWorker):
        """
        A _BooksWorker instance which overrides the process_exports method to
        make it useful for testing.
        """

        def pre_process_exports(self, spider, task):
            if self.job_id is not 'NONE':
                try:
                    # create the list with the job name if it doesnt already exist
                    ndb.root._spiders.add(self.job_id, SpiderList())
                    print(
                        f'Worker {self.name}-{self.number} created a new scrape_list '
                        f'for {self.job_id}')
                except KeyError:
                    # will be raised if there is already a list with the same job_name
                    pass
                # export the scraper data to the items object
                items = self.load_items(spider)
                # save the items object to newt.db
                ndb.root._spiders[self.job_id].add(items)
                ndb.commit()
                print(f'Worker {self.name}-{self.number} saved {items.__repr__()} to '
                      f'scrape_list "{self.job_id}" for task {task}.')
            else:
                # if job_id is NONE then we'll skip saving the objects
                print(
                    f'Worker {self.name}-{self.number} said job_name is {self.job_id} '
                    f'so will not save it.')

        def post_process_exports(self, spider, task):
            """
            A hook point for customization after process_exports.

            In this example, we append the returned scraper object to a
            class attribute called `events`.

            """
            self.events.append(spider)
            print(f'{self.name} has {spider.stock} inventory status.')
            print(f'pricing: {spider.price}')
            print(f'Worker {self.name}-{self.number} finished task {task}')

    return _BooksWorker


@pytest.fixture(scope='function')
def _BooksToScrapeGroup(_BooksWorker):
    """
    Create an Group for testing which uses the _BooksWorker
    """
    class _BookstoScrapeGroup(BaseGroup):
        """
        A _BooksWorker instance which overrides the process_exports method to
        make it useful for testing.
        """
        def hired_worker(self):
            """
            Encapsulate your custom scraper, inside of a Worker object. This will
            eventually allow us to run an arbitrary amount of Scraper objects.

            :returns <Worker>, the worker object which will go into a Workgroup
            """
            worker = _BooksWorker(job_id=self.job_id, scraper=BooksToScrapeScraper,
                                 http_session={'url': self.url,
                                               'timeout': self.timeout},
                                 **self.kwargs)
            return worker

    return _BookstoScrapeGroup


@pytest.fixture(scope='function')
def splash_browser():
    """
    A SplashBrowser instance for the unit tests.
    :return:
    """
    browser = SplashBrowser(
        soup_config={'features': 'lxml'},
        requests_adapters={'http://': HTTPAdapter(max_retries=5)})

    return browser


def get_job_results(job_id):
    """
    A ndb helper method that manipulates the _scraper object.
    """
    return ndb.root._spiders.lists[job_id].results


def delete_job(job_id):
    """
    A ndb helper method that manipulates the _scraper object.
    """
    try:
        del ndb.root._spiders.lists[job_id]
        ndb.commit()
    except KeyError:
        pass


@pytest.fixture(scope='function')
def bts_static_scraper(test_dict):
    """
    A BooksToScrapeScraper static test fixture.
    """
    book_title = 'Soumission'
    page = get_html("tests/books_toscrape/books_toscrape_index.html")
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
    # first, setup newt.db for testing
    ndb.root._spiders = SpiderLists()
    ndb.commit()

    # ensure to open this file in binary mode
    book_data_file = open('c:/temp/book_data.csv', 'a+b')
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

    yield manager

    # teardown
    delete_job('books_scrape')
    del ndb.root._spiders
    ndb.commit()


@pytest.fixture(scope='function')
def broker_tasks(broker_conn):
    trackers = ['books.toscrape.com']
    tasks = ExchangeQueue(trackers)

    # explicitly declare the queues
    for queue in tasks.task_queues:
        queue(broker_conn).declare()

    return tasks


@pytest.fixture(scope='function')
def broker_conn():
    """
    A Kombu connection object. Connect with RabbitMQ or Redis.
    """
    connection = Connection("pyamqp://guest:guest@localhost:5672//")
    # connection = Connection("redis://127.0.0.1:6379")
    return connection


@pytest.fixture(scope='function')
def bts_broker_manager(_BooksToScrapeGroup, _BooksWorker, broker_tasks, broker_conn):
    """
    A BooksToScrape Manager test fixture for live network call.
    Here, we use a broker (RabbitMQ) to test.
    """
    # setup newt.db for testing
    ndb.root._spiders = SpiderLists()
    ndb.commit()

    # ensure to open this file in binary mode
    book_data_file = open('c:/temp/broker_data.csv', 'a+b')
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
                                    workgroups=groups, pool=5, connection=broker_conn)

    yield manager

    # teardown newt.db
    delete_job('books_broker_scrape')
    del ndb.root._spiders
    ndb.commit()