# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.manager
~~~~~~~~~~~~
This module implements a customized subclass of the BaseWorkGroupManager.
It shows how to assign scrape tasks with the Manager, which provides gevent based
concurrency, and ability to scale an arbitrary number of Scraper WorkGroups.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
import gevent
from transistor import BaseWorkGroupManager
from transistor.utility.logging import logger

class BooksWorkGroupManager(BaseWorkGroupManager):
    """
    Create a manager to assign tasks and direct an arbitrary number of WorkGroups.
    Inherit the BaseWorkGroupManager and implement a monitor method which calls
    target.spawn_scraper() at some point.  This is generally all that is required.
    """

    def monitor(self, target):
        """
        This method actually spawns the scrapers and then it generally just serves
        as a hook point, where it allows some additional final actions to be
        performed on the scraper object after the worker completes the scrape job,
        but before it shuts down and the original object instance is lost.

        Here, we have access to the scrape results, and could do some final
        transformations or data checking. For example to to see the
        result and then update some results list. Or even, implement some other
        persistence method, if you don't want to use postgresql with newt.db.

        :param target: the target parameter here is a <Worker()> class object and
        you must call target.spawn_scraper() to start the Worker.
        """
        logger.info(f'spawning {target}')
        target.spawn_spider()  # this must be called. It is, required.
        # Calling spawn_scraper() above instructs the Worker object to start
        # the scrape.So there will be some wait period at this point for each
        # worker to actually run out of work and quit with a graceful shutdown.
        # Therefore, A GOOD SPOT TO HOOK SOME POST-SCRAPE LOGIC ON YOUR WORKERS
        # RESULTS, IS RIGHT HERE. For example, I've simply set `events = []` as a
        # class attribute on the BaseWorker <Worker> object and then appended
        # `self` to `events` after each scrape returns, as completed by the Worker.
        for event in target.events:
            # here, event represents returned scraper objects which the worker has
            # completed. We can iterate through the event objects and, for example,
            # apply some data transformation, delete failed scrapes, or save data
            logger.info(f'THIS IS A MONITOR EVENT - > {event}')
        # This last line is required, ensure the below gevent.sleep(0) remains.
        gevent.sleep(0)


