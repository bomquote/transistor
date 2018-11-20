# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.workgroup
~~~~~~~~~~~~
This module implements a working example of a BaseWorker and BaseGroup.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
import gevent
from transistor import BaseWorker, BaseGroup
from examples.books_to_scrape.scraper import BooksToScrapeScraper
from examples.books_to_scrape.persistence import BookDataExporter, ndb
from transistor.persistence.newt_db.collections import ScrapeList


class BooksWorker(BaseWorker):
    """
    A Worker wraps the custom Scraper object and the custom DataExtractor objects.
    Then, the Worker can be combined into a Group of an arbitrary number of Workers,
    to facilitate gevent based concurrency.

    First, inherit from BaseWorker and then implement the get_scraper,
    get_scraper_extractor, and save_to_db methods, as shown below.

    Also, add any extra class attributes as needed to support your custom
    Scraper and ScraperDataExtractor.
    """

    def result(self, scraper, task):
        """
        I'm only overriding this method to return a few extra print messages and
        also call out, this is a good hook place for your further customization.

        Use whatever complex logic between save_to_db() and
        gevent.sleep() as per your own customized requirement.

        Also, if you don't want to use newt.db at all, you should override the
        self.save_to_db method.

        """
        self.events.append(scraper)
        self.save_to_db(scraper, task)
        #  /start CUSTOM LOGIC
        print(f'{self.name} has {scraper.stock} inventory status.')
        print(f'pricing: {scraper.price}')
        print(f'Worker {self.name}-{self.number} finished task {task}')
        # /end CUSTOM LOGIC
        gevent.sleep(0)

    def get_scraper(self, task, **kwargs):
        """
        Return an instance of the custom Scraper object. Specifically, note
        how `task` is passed here, as the `book_title` parameter.

        The book titles are read from the excel spreadsheet, and each title then
        loaded into a work queue, where it becomes a task to be assigned by the
        manager for completion.  Here, we pass in the task.
        """
        scraper = self.scraper(task, name=self.name, number=self.number,
                               **kwargs)
        return scraper

    def get_scraper_exporter(self, scraper):
        """
        Use this method to pass in the scraper which has already returned from
        the scrape job, into your own custom data exporter/serializer.
        :param scraper: this will be the executed scraper object (i.e. BookScraper())
        :return: a custom ScraperExporter instance
        """
        return BookDataExporter(scraper)

    def save_to_db(self, scraper, task):
        """
        Save the container of the completed Scraper object to newt.db, using the
        middle-layer serialization helper class, BookDataExporter.

        :param scraper: the scraper object (i.e. MouseKeyScraper())
        :param task: just passing through the item for printing.
        :return: commit to newt db and return a print statement.
        """
        if self.job_id is not 'NONE':
            try:
                # create the list with the job name if it doesnt already exist
                ndb.root.scrapes.add(self.job_id, ScrapeList())
                print(f'Worker {self.name}-{self.number} created a new scrape_list for '
                      f'{self.job_id}')
            except KeyError:
                # will be raised if there is already a list with the same job_name
                pass
            # export the data object to be persisted, with the export.write() method
            items = self.get_scraper_exporter(scraper).write()
            ndb.root.scrapes[self.job_id].add(items)
            ndb.commit()
            print(f'Worker {self.name}-{self.number} saved {items.__repr__()} to '
                  f'scrape_list "{self.job_id}" for task {task}.')
        else:
            # if job_id is NONE then we'll skip saving the objects
            print(f'Worker {self.name}-{self.number} said job_name is {self.job_id} '
                  f'so will not save it.')


class BooksToScrapeGroup(BaseGroup):
    """
    Organize a group of Workers for the Manager class to assign tasks and monitor
    results.

    All WorkerGroups should inherit from BaseGroup. Then, create the
    Worker instance in `hired_worker` method using the custom scraper object.

    Note how, in this case, the `BooksToScrapeScraper` is assigned in the
    `hired_worker` method.
    """

    def hired_worker(self):
        """
        Encapsulate your custom scraper, inside of a Worker object. This will
        eventually allow us to run an arbitrary amount of Scraper objects.

        Creates the number of workers given in `staff` (see BaseGroup.__init__()).
        Setting the http_session for the Worker is also handled here.
        Last, this is a good place to ensure any custom class attributes you must
        have on the worker are set here.

        :returns <Worker>, the worker object which will go into a Workgroup
        """
        worker = BooksWorker(job_id=self.job_id, scraper=BooksToScrapeScraper,
                             http_session={'url': self.url, 'timeout': self.timeout},
                             **self.kwargs)

        # NOTE: assign custom class attrs on your workers here, as needed.
        # You pretty much always need to assign worker.name here, but you
        # may need others as well. For example, if our scraper depended
        # on china=True to scrape .com.cn domain. Set:
        # worker.china = self.china

        worker.name = self.name

        return worker
