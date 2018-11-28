# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.workgroup
~~~~~~~~~~~~
This module implements a working example of a BaseWorker and BaseGroup.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from transistor import BaseWorker
from examples.books_to_scrape.persistence import ndb
from transistor.persistence.newt_db.collections import SpiderList


class BooksWorker(BaseWorker):
    """
    A Worker wraps the custom Spider object and processes it after returning
    data from a scrape or crawl. The Worker can be combined into a Group of
    an arbitrary number of Workers, to enable gevent based asynchronous I/O.

    First, inherit from BaseWorker and then implement the pre_process_exports
    and/or post_process_exports methods, as shown below. Other methods
    that could be easily overriden include get_spider, get_spider_extractor, and
    even process_exports could be overriden if needed.

    Also, add any extra class attributes as needed here, to support your custom
    Spider and Exporters.
    """

    def pre_process_exports(self, spider, task):
        """
        A hook point for customization before process_exports method is
        called.

        In this example, we use this method to save our spider data to
        postgresql using newt.db.

        :param spider: the Scraper or Crawler object (i.e. MouseKeyScraper())
        :param task: just passing through the task item for printing.
        """
        if self.job_id is not 'NONE':
            try:
                # create the list with the job name if it doesnt already exist
                ndb.root.spiders.add(self.job_id, SpiderList())
                print(f'Worker {self.name}-{self.number} created a new scrape_list for '
                      f'{self.job_id}')
            except KeyError:
                # will be raised if there is already a list with the same job_name
                pass
            # export the scraper data to the items object
            items = self.load_items(spider)
            # save the items object to newt.db
            ndb.root.spiders[self.job_id].add(items)
            ndb.commit()
            print(f'Worker {self.name}-{self.number} saved {items.__repr__()} to '
                  f'scrape_list "{self.job_id}" for task {task}.')
        else:
            # if job_id is NONE then we'll skip saving the objects
            print(f'Worker {self.name}-{self.number} said job_name is {self.job_id} '
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
