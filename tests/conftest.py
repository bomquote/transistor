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
from os.path import dirname as d
from os.path import abspath, join
from unittest.mock import Mock, patch
from requests.adapters import HTTPAdapter
from transistor import SplashBrowser
from transistor.persistence.newt_db.collections import ScrapeList
from examples.books_to_scrape.workgroup import BooksWorker, BooksToScrapeGroup
from examples.books_to_scrape.scraper import BooksToScrapeScraper
from examples.books_to_scrape.persistence.newt_db import ndb

root_dir = d(d(abspath(__file__)))


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
    Create a BooksWorker which saves jobs to ndb.root._scrapes, where ._scrapes uses
    the _ScrapeListsTesting fixture.
    """
    class _BooksWorker(BooksWorker):
        """
        A _BooksWorker instance which overrides the save_to_db method to
        make it useful for testing.
        """

        def save_to_db(self, scraper, task):
            if self.job_id is not 'NONE':
                try:
                    # create the list with the job name if it doesnt already exist
                    ndb.root._scrapes.add(self.job_id, ScrapeList())
                    print(
                        f'Worker {self.name}-{self.number} created a new scrape_list '
                        f'for {self.job_id}.')
                except KeyError:
                    # will be raised if there is already a list with the same job_name
                    pass
                # extract the data object to be persisted, with the
                # extractor.write() method
                container = self.get_scraper_extractor(scraper).write()
                ndb.root._scrapes[self.job_id].add(container)
                ndb.commit()
                print(f'Worker {self.name}-{self.number} saved {container.__repr__()} to '
                      f'scrape_list "{self.job_id}" for task {task}.')
            else:
                # if job_id is NONE then we'll skip saving the objects
                print(
                    f'Worker {self.name}-{self.number} said job_name is {self.job_id} '
                    f'so will not save it.')

    return _BooksWorker


@pytest.fixture(scope='function')
def _BooksToScrapeGroup(_BooksWorker):
    """
    Create an Group for testing which uses the _BooksWorker
    """
    class _BookstoScrapeGroup(BooksToScrapeGroup):
        """
        A _BooksWorker instance which overrides the save_to_db method to
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
            worker.name = self.name
            return worker

    return _BookstoScrapeGroup


@pytest.fixture(scope='function')
def splash_browser():
    """
    A SplashBrowser instance for the unit tests.
    :return:
    """
    browser = SplashBrowser(
    soup_config = {'features': 'lxml'},
    requests_adapters = {'http://': HTTPAdapter(max_retries=5)})

    return browser


def get_job_results(job_id):
    """
    A ndb helper method that manipulates the _scraper object.
    """
    return ndb.root._scrapes.lists[job_id].results


def delete_job(job_id):
    """
    A ndb helper method that manipulates the _scraper object.
    """
    try:
        del ndb.root._scrapes.lists[job_id]
        ndb.commit()
    except KeyError:
        pass