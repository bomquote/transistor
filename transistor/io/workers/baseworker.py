# -*- coding: utf-8 -*-
"""
transistor.io.workers.baseworker_abc
~~~~~~~~~~~~
This module implements BaseWorker. See transistor.io.workers.__init__
for more notes on this module.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
import gevent
from gevent.queue import Queue, Empty


class BaseWorker:

    tasks = Queue(maxsize=1)
    name = None
    number = None
    events = []

    def __init__(self, job_id:str, scraper, http_session=None, **kwargs):
        """
        :param job_id: will be the name of the list which the worker
        appends the finished scraper object to in newt.db, for example, if the
        job_name is 'testing' then the jobs will be added to the `testing` scrape_list.

        :param scraper: the Scraper class object like `BooksToScrapeScraper`

        ::param http_session: dict(), specialized session args. Example,
        some scraper implementation may require to define a custom landing page
        url and also need fine control over the timeouts. So the http_session would
        look like http_session={'url': <landing page url>, 'timeout' : (3.05, 1200.05)}

        :param kwargs: generally only needed to support customized scraper
        implementations. For example, if your scraper logic depends on some flag,
        like china=True, which might define whether or not a .com.cn domain is
        scraped, instead of just the .com domain. Use kwargs as needed here, to
        execute based on your customized scraper logic.

        :param kwargs: qtimeout: to adjust the queue timeout like {"qtimeout":5} which
        you should probably never adjust this. But, if you do adjust this, ensure that
        the worker's qtimeout is less than the manager's qtimeout.

        """
        self.job_id = job_id
        self.scraper = scraper
        self.http_session = http_session
        if http_session is None:
            self.http_session = {}
        self.number = self.number
        # a note for clarity about qtimeout, it is the self.tasks.get(timeout=int)
        # `timeout`, not the http_session `timeout`
        # this worker qtimeout must be longer than manager's qtimeout or else
        # the worker will quit early as it runs out of work waiting for the manager
        self.qtimeout = kwargs.get('qtimeout', 1)

    def __repr__(self):
        return f"<Worker(job_id='{self.job_id}', name='{self.name}-{self.number}')>"

    def spawn_scraper(self, **kwargs):
        """
        Start and execute.
        """
        try:
            while True:
                task = self.tasks.get(timeout=self.qtimeout)  # decrements queue by 1
                print(f'Worker {self.name}-{self.number} got task {task}')
                scr = self.get_scraper(task, **kwargs)
                scr.start_http_session(**self.http_session)
                # OK, right here is where we wait for the scraper to return a result.
                self.result(scr, task)
        except Empty:
            print(f'Quitting time for worker {self.name}-{self.number}!')


    def result(self, scraper, task):
        """
        At this point, we finally received a result from the scraper, and this
        is where the scraper object itself can be finally processed.

        This is designated as an abstract method, for the user to implement in
        a subclass. It can be used as-is by creating a result method in the subclass
        and calling super().result() in the subclass result method.

        :param scraper: the returned custom modified scraper object, which end
        user must initially create from a subclassed SplashScraper object.
        :param task: passing through the task from spawn_scraper method.
        """
        self.events.append(scraper)
        self.save_to_db(scraper, task)
        print(f'Worker {self.name}-{self.number} finished task {task}')
        gevent.sleep(0)


    def save_to_db(self, scraper, task):
        """
        Here is where you can implement some custom logic to persist your data.
        Check the examples/books_to_scrape folder for a fully working example
        which saves python objects to a PostgreSQL database, while also serializing
        them to a postgres jsonb field, using newt.db. Some support for newt.db is
        offered in the transistor.persistence.newt_db folder for this option.

        :param scraper: the scraper object (i.e. BookScraper())
        :param task: just passing through the item task .
        :return: pass or commit to your db and return a print statement.
        """
        raise NotImplementedError('You must implement save_to_db, even if just `pass`.')

    def get_scraper(self, task, **kwargs):
        """
        Return an instance of a custom Scraper object with parameters that you need.

        :return: self.scraper(task, name=self.name, number=self.number, **kwargs)
        """
        scraper = self.scraper(task, name=self.name, number=self.number,
                               **kwargs)
        return scraper


    def get_scraper_extractor(self, scraper):
        """
        This is a hook point for any serialization you may want to do depending on
        your data persistence model.  In `examples/books_to_scrape` we show a method
        for using PostgreSQL with newt.db to store python objects in a postrgres db
        while also automatically serializing the object to a postgres jsonb field.

        :param scraper: the scraper object (i.e. BooksToScrapeScraper())
        :return: a custom ScraperExtractor instance like:
        SplashComponentScraperExtractor(scraper)
        """
        raise NotImplementedError('You must return a custom ScraperExtractor.')