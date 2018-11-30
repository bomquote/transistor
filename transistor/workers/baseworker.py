# -*- coding: utf-8 -*-
"""
transistor.workers.baseworker
~~~~~~~~~~~~
This module implements BaseWorker. See transistor.workers.__init__
for more notes on this module.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
import gevent
from gevent.queue import Queue, Empty


class BaseWorker:
    """
    A class that performs actions on a returned Spider object (Scraper or Crawler)
    and can itself be scaled up to an arbitrary number of instances in a BaseGroup.
    """

    tasks = Queue(maxsize=1)
    number = None
    events = []

    def __init__(self, job_id:str, spider, http_session=None, **kwargs):
        """
        :param job_id: will be the name of the list which the worker
        appends the finished spider object to in newt.db, for example, if the
        job_name is 'testing' then the jobs will be added to the `testing` scrape_list.

        :param spider: the Scraper or Crawler class object like `BooksToScrapeScraper`

        ::param http_session: dict(), specialized session args. Example,
        some spider implementation may require to define a custom landing page
        url and also need fine control over the timeouts. So the http_session would
        look like http_session={'url': <landing page url>, 'timeout' : (3.05, 1200.05)}

        :param kwargs: generally only needed to support customized spider
        implementations. For example, if your spider logic depends on some flag,
        like china=True, which might define whether or not a .com.cn domain is
        scraped, instead of just the .com domain. Use kwargs as needed here, to
        execute based on your customized spider logic.

        :param kwargs: qtimeout: to adjust the queue timeout like {"qtimeout":5} which
        you should probably never adjust this. But, if you do adjust this, ensure that
        the worker's qtimeout is less than the manager's qtimeout.

        """
        self.job_id = job_id
        self.spider = spider
        self.http_session = http_session
        if http_session is None:
            self.http_session = {}
        self.name = kwargs.get('name', None)
        self.items = kwargs.get('items', None)
        self.loader = kwargs.get('loader', None)
        self.exporters = kwargs.get('exporters', None)
        # a note for clarity about qtimeout, it is the self.tasks.get(timeout=int)
        # `timeout`, not the http_session `timeout`
        # this worker qtimeout must be longer than manager's qtimeout or else
        # the worker will quit early as it runs out of work waiting for the manager
        self.qtimeout = kwargs.get('qtimeout', 1)

    def __repr__(self):
        return f"<Worker(job_id='{self.job_id}', name='{self.name}-{self.number}')>"

    def spawn_spider(self, **kwargs):
        """
        Start and execute.
        """
        try:
            while True:
                task = self.tasks.get(timeout=self.qtimeout)  # decrements queue by 1
                print(f'Worker {self.name}-{self.number} got task {task}')
                spider = self.get_spider(task, **kwargs)
                spider.start_http_session(**self.http_session)
                # OK, right here is where we wait for the spider to return a result.
                self.result(spider, task)
        except Empty:
            print(f'Quitting time for worker {self.name}-{self.number}!')

    def result(self, spider, task):
        """
        At this point, we finally received a result from the spider, and this
        is where the spider object itself can be finally processed. We define
        a process_exports method along with a `pre` and `post` method as hooks
        for signals or other custom logic.

        :param spider: the returned custom modified spider object, which end
        user must initially create from a subclassed SplashSpider object.
        :param task: passing through the task from spawn_spider method.
        """

        self.pre_process_exports(spider, task)
        self.process_exports(spider, task)
        self.post_process_exports(spider, task)
        gevent.sleep(0)

    def pre_process_exports(self, spider, task):
        """
        A hook point which executes just before process_exports in
        the self.results method.

        :param spider: the returned custom modified spider object, which end
        user must initially create from a subclassed SplashSpider object.
        :param task: passing through the task from spawn_spider method.
        """
        pass

    def process_exports(self, spider, task):
        """
        Process the spider exports.

        :param spider: the spider object (i.e. MouseKeyScraper())
        :param task: just passing through the item.
        :return: commit to newt db and return a print statement.
        """
        items = self.load_items(spider)
        for exporter in self.get_spider_exporters():
           exporter.export_item(items)


    def post_process_exports(self, spider, task):
        """
        A hook point which executes just after process_exports has completed in
        the self.results method.

        :param spider: the returned custom modified spider object, which end
        user must initially create from a subclassed SplashSpider object.
        :param task: passing through the task from spawn_spider method.
        """
        pass

    def get_spider(self, task, **kwargs):
        """
        Return an instance of a custom Spider object with parameters that you need.
        Specifically, note how `task` is passed here.

        In our examples/books_to_scrape, task is passed to the `book_title`
        parameter. The book titles are read from the excel spreadsheet, and each
        title is then loaded into a work queue, where it becomes a task to be
        assigned by the manager for completion.  Here, is where task is passed in.

        :return: self.spider(task, name=self.name, number=self.number, **kwargs)
        """
        spider = self.spider(task, name=self.name, number=self.number,
                             **kwargs)
        return spider

    def get_spider_items(self):
        """
        Return an instance of a class that subclasses from Item. For example,
        SplashSpiderItem from transistor.persistence.containers.
        """
        return self.items()

    def load_items(self, spider):
        """
        Start with ItemLoader instance subclassed from the
        transistor.persistence.loader ItemLoader class. But, return
        a data loaded Item class object.
        :return: Type[Item]
        """
        # at this point, self.loader will be # Type[ItemLoader], if load_items()
        # has not yet been called. After calling, it will be Type[Item].
        # This is tricky and so it kinda sucks. Requires a special `written` attr
        # flag on both the Item class and the ItemLoader class. Needs refactored.
        if not self.loader.written:
            self.loader = self.loader()
            self.loader.items = self.get_spider_items()
            self.loader.spider = spider
            self.loader = self.loader.write()  # .write returns Type[Item]
        return self.loader  # careful, this is Type[Item] not Type[ItemLoader]

    def get_spider_exporters(self) -> list:
        """
        Return a list of exporters. If exporters were defined in the WorkGroup
        then just return them. Otherwise, can override this method and provide
        the exporters here.
        """
        return self.exporters
