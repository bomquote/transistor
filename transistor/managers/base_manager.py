# -*- coding: utf-8 -*-
"""
transistor.managers.base_manager
~~~~~~~~~~~~
This module implements BaseWorkGroupManager as a fully functional base class
which can assign tasks and conduct a scrape job across an arbitrary number
of WorkGroups. Each WorkGroup can contain an arbitrary number of
Worker/Scrapers.

It's `tasks` parameter can accept a StatefulBook instance, which transforms
a spreadsheet column into keyword tasks search terms. The `tasks` parameter
can also accept an ExchangeQueue instance, which creates an AMQP compatable
exchange and queue, while BaseWorkGroupManager acts as a consumer/worker,
processing tasks from a broker like RabbitMQ or Redis.

Although this class is fully functional as-is. The monitor() method provides an
excellent hook point for post-scrape Worker manipulation. A more robust implementation
will subclass BaseManager and override the monitor method for customization.


:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

import gevent
import json
from typing import List, Type, Union
from gevent.queue import Queue, Empty
from gevent.pool import Pool
from gevent.exceptions import LoopExit
from kombu import Connection
from kombu.mixins import ConsumerMixin
from transistor.schedulers.books.bookstate import StatefulBook
from transistor.schedulers.brokers.queues import ExchangeQueue
from transistor.workers.workgroup import WorkGroup
from transistor.exceptions import IncompatibleTasks
from transistor.utility.logging import logger
from kombu.utils.functional import reprcall


class BaseWorkGroupManager(ConsumerMixin):
    """
    Base class for a WorkGroupManager.
    """
    __attrs__ = [
        'book', 'exporter', 'job_id', 'trackers', 'pool', 'qitems',
        'workgroups',
    ]

    def __init__(self, job_id, tasks: Type[Union[Type[StatefulBook],
                                                 Type[ExchangeQueue]]],
                 workgroups: List[WorkGroup], pool: int=20,
                 connection: Connection = None, should_stop=True, **kwargs):
        """

        Create the instance.

        :param job_id: will save the result of the workers Scrapes to `job_id` list.
        If this job_id is "NONE" then it will pass on the save.
        :param tasks:  a StatefulBook or ExchangeQueue instance.
        :param workgroups: a list of class: `WorkGroup()` objects.
        :param pool: size of the greenlets pool. If you want to utilize all the
        workers concurrently, it should be at least the total number
        of all workers + 1 for the manager and +1 for the broker runner in
        self.run() method. Otherwise, the pool is also useful to constrain
        concurrency to help stay within Crawlera subscription limits.
        :param connection: a kombu Connection object, should include the URI to
        connect to either RabbitMQ or Redis.
        :param should_stop: whether to run indefinitely or to stop after the
        manager queue runs empty.
        Example:
            >>> groups = [
            >>> WorkGroup(class_=MouseKeyGroup, workers=5, kwargs={"china":True}),
            >>> WorkGroup(class_=MouseKeyGroup, workers=5, kwargs={})
            >>> ]
        :param pool: number of greenlets to create
        """
        self.job_id = job_id
        self.tasks = tasks
        self.groups = workgroups
        self.pool = Pool(pool)
        self.qitems = {}
        self.workgroups = {}
        self.qtimeout = kwargs.get('qtimeout', 5)
        self.mgr_qtimeout = self.qtimeout//2 if self.qtimeout else None
        self.connection = connection
        self.kombu = False
        self.mgr_should_stop = should_stop
        self.mgr_no_work = False
        # call this last
        self._init_tasks(kwargs)

    def _init_tasks(self, kwargs):
        """
        Create individual task queues for the workers.

        If, Type[StatefulBook] is passed as the `tasks` parameter, the tracker with
        a name that matches a workgroup name, is effectively the workgroup's
        task queue. So, extract the tracker name from self.book.to_do()
        and the tracker name should match the worker name.

        Extract the tracker name and then create qitems:

        Example hint, `self.tasks.to_do()` looks like this:
        deque([<TaskTracker(name=mousekey.cn)>, <TaskTracker(name=mousekey.com)>])
        """
        if isinstance(self.tasks, StatefulBook):
            for tracker in self.tasks.to_do():
                # set the name of qitems key to tracker.name
                self.qitems[tracker.name] = Queue(items=tracker.to_do())

        elif isinstance(self.tasks, ExchangeQueue):
            for tracker in self.tasks.trackers:
               self.qitems[tracker] = Queue()
            self.kombu = True

        else:
            raise IncompatibleTasks('`task` parameter must be an instance of '
                                    'StatefulBook or ExchangeQueue')

        # if not a stateful book. The class should have some attribute which
        # presents a list-like object, where this list-like object is a
        # list of queues.

        # classes of type Type[X], where X has attributes X.name and X.to_do(),
        # where X.to_do() returns object appropriate for Queue(items=X.to_do())

        self._init_workers(kwargs)

    def _init_workers(self, kwargs):
        """
        Create the WorkGroups by tracker name and assign them by name to the
        workgroups dict.

        :return:
        """
        # first, build a list from tracker names per qitems.keys()
        names = [name for name in self.qitems.keys()]
        for name in names:
            for group in self.groups:
                # match the tracker name to the group name
                if group.name == name:
                    # assumes `group` is a WorkGroup namedtuple
                    # add attrs to group.kwargs dict so they can be passed down
                    # to the group/worker/spider and assigned as attrs
                    group.kwargs['name'] = name
                    group.kwargs['url'] = group.url
                    group.kwargs['spider'] = group.spider
                    group.kwargs['worker'] = group.worker
                    group.kwargs['items'] = group.items
                    group.kwargs['loader'] = group.loader
                    # exporters is a list of exporter instances
                    group.kwargs['exporters'] = group.exporters
                    if not group.kwargs.get('qtimeout', None):
                        group.kwargs['qtimeout'] = self.qtimeout
                    basegroup = group.group(
                        staff=group.workers, job_id=self.job_id, **group.kwargs)
                    # now that attrs assigned, init the workers in the basegroup class
                    basegroup.init_workers()
                    # lastly, after calling init_workers, assign the workgroup
                    # instance to the workgroups dict with key = `name`
                    self.workgroups[name] = basegroup

    def get_consumers(self, Consumer, channel):
        """
        Must be implemented for Kombu ConsumerMixin
        """
        return [Consumer(queues=self.tasks.task_queues,
                         accept=['json'],
                         callbacks=[self.process_task])]

    def process_task(self, body, message):
        """
        Process messages to extract the task keywords and then
        load them into a gevent Queue for each tracker.

        To customize how this Manger class works with the broker,
        this method should be a top consideration to override.

        Kwargs is not currently used. But it could be very useful
        to set logic flags for use in this method.
        """
        keywords = body['keywords']
        kwargs = body['kwargs']
        logger.info(f'Got task: {reprcall(keywords)}')
        try:
            if isinstance(keywords, str):
                keywords = json.loads(keywords)
            for key in self.qitems.keys():
                for item in keywords:
                    self.qitems[key].put(item)
            if not self.mgr_should_stop:
                if self.mgr_no_work:
                    gevent.spawn(self.manage).join()
        except Exception as exc:
            logger.error(f'task raised exception: {exc}')
        message.ack()

    def spawn_list(self):
        """"
        The spawn() method begins a new greenlet with the given arguments
        (which are passed to the greenlet constructor) and adds it to the
        collection of greenlets this group is monitoring.

        We return a list of the newly started greenlets, used in a later
        'joinall` call.

        :return: A list of the newly started greenlets.
        """

        # here, workgroups is a list of Type[BaseGroup] objects
        workgroups = [val for val in self.workgroups.values()]
        spawn_list = [self.pool.spawn(self.monitor, worker) for work_group in
                      workgroups for worker in work_group]

        # we get a blocking error if we spawn the manager first, so spawn it last
        spawn_list.append(self.pool.spawn(self.manage))

        return spawn_list

    def monitor(self, target):
        """
        This method actually spawns the spider and then the purpose is to allow
        some additional final actions to be performed the worker completes the
        spider's job, but before it shuts down and the object instance is lost.

        The simplest example which must be implemented:

        def monitor(self, target):
            '''
            The only absolute requirement is to start the spider with
            target.spawn_spider() and then call gevent.sleep(0)
            '''
            target.spawn_spider()
            gevent.sleep(0)

        A more useful example:

        def monitor(self, target):
            '''
            More useful, would be to hook in some post-scrape logic between
            spawn_spider() and gevent.sleep(0).
            '''
            target.spawn_spider()
            # /start --> YOUR POST-SCRAPE HOOK IS HERE, ADD LOGIC AS REQUIRED.
            for event in target.events:
                # .event is a simple list() as a class attribute, in the scraper object
                # we could apply some transformation to an object in event, now.
                print(f'THIS IS A MONITOR EVENT - > {event}')
            # /end --> YOUR POST SCRAPE HOOK LOGIC. Finally, call gevent.sleep()
            gevent.sleep(0)

        :param target: a worker
        :return:
        """
        target.spawn_spider()
        gevent.sleep(0)

    def manage(self):
        """"
        Manage will hand out work when the appropriate Worker is free.
        The manager timeout must be less than worker timeout, or else, the
        workers will be idled and shutdown.
        """
        try:
            while True:
                for name, workgroup in self.workgroups.items():
                    for qname, q in self.qitems.items():
                        if name == qname: # workgroup name must match tracker name
                            # a tracker with the same name as workgroup name, is...
                            # ...effectively, the workgroup's task queue, so now...
                            # assign a task to a worker from the workgroup's task queue
                            for worker in workgroup:
                                one_task = q.get(timeout=self.mgr_qtimeout)
                                worker.tasks.put(one_task)
                gevent.sleep(0)
        except Empty:
            self.mgr_no_work = True
            if self.mgr_should_stop:
                logger.info(f"Assigned all {name} work. I've been told I should stop.")
                self.should_stop = True
            else:
                logger.info(f"Assigned all {name} work. Awaiting more tasks to assign.")

    def main(self):
        spawny = self.spawn_list()
        if self.kombu:
            gevent.spawn(self.run).join()
        try:
            gevent.pool.joinall(spawny)
        except LoopExit:
            logger.error('No tasks. This operation would block forever.')
        # print([worker.get() for worker in spawny])
        gevent.sleep(0)
