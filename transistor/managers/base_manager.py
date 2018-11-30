# -*- coding: utf-8 -*-
"""
transistor.managers.base_manager
~~~~~~~~~~~~
This module implements BaseWorkGroupManager as a fully functional base class
which can assign tasks and conduct a scrape job across an
arbitrary number of WorkGroups. Each WorkGroup can contain an arbitrary number of
Worker/Scrapers.

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
from kombu import Connection
from kombu.mixins import ConsumerMixin
from transistor.schedulers.books.bookstate import StatefulBook
from transistor.schedulers.brokers.queues import ExchangeQueue
from transistor.workers.workgroup import WorkGroup
from transistor.exceptions import IncompatibleTasks
from kombu.log import get_logger
from kombu.utils.functional import reprcall
logger = get_logger(__name__)
debug, info, warn, error = logger.debug, logger.info, logger.warn, logger.error


class BaseWorkGroupManager(ConsumerMixin):
    """
    Base class for a WorkGroupManager.
    """
    __attrs__ = [
        'book', 'exporter', 'job_id', 'wgroups', 'trackers', 'pool', 'qitems',
        'workgroups',
    ]

    def __init__(self, job_id, tasks: Type[Union[Type[StatefulBook],
                                                 Type[ExchangeQueue]]],
                 workgroups: List[WorkGroup], pool: int=20,
                 connection: Connection = None, should_stop=False):
        """

        Create the instance.

        :param job_id: will save the result of the workers Scrapes to `job_id` list.
        If this job_id is "NONE" then it will pass on the save.
        :param tasks:  a StatefulBook instance or other class which passes
        an object which can be turned into a task queue in _init_tasks() method.
        :param pool: size of the greenlets pool. If you want to utilize all the
        workers concurrently, it should be at least the total number
        of all workers + 1 for the manager. Otherwise, the pool is useful to
        constrain concurrency to help stay within Crawlera subscription limits.
        :param groups: a list of class: `WorkGroup()` objects.
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
        self._init_tasks()
        self.connection = connection
        self.kombu = False
        self.manager_should_stop = should_stop

    def _init_tasks(self):
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

        self._init_workers()

    def _init_workers(self):
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

                    # add the name to group.kwargs dict so it can be passed down
                    # to the group/worker/spider and assigned as an attr
                    group.kwargs['name'] = name
                    group.kwargs['url'] = group.url
                    group.kwargs['spider'] = group.spider
                    group.kwargs['worker'] = group.worker
                    group.kwargs['items'] = group.items
                    group.kwargs['loader'] = group.loader
                    # exporters is a list of exporter instances
                    group.kwargs['exporters'] = group.exporters
                    workergroup = group.group(
                        staff=group.workers, job_id=self.job_id, **group.kwargs)
                    # now that attrs assigned, init the workers on the workgroup
                    workergroup.init_workers()
                    # lastly, after calling init_workers, assign the workgroup
                    # instance to the workgroups dict with key = `name`
                    self.workgroups[name] = workergroup

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
        """
        keywords = body['keywords']
        logger.info(f'Got task: {reprcall(keywords)}')
        try:
            kwds = json.loads(keywords)
            for key in self.qitems.keys():
                self.qitems[key] = Queue(items=kwds)
            self.manage()
        except Exception as exc:
            # logger.error('task raised exception: %r', exc)
            print(f'task raised exception: {exc}')
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

        spawn_run = []
        if self.kombu:
            spawn_run = [self.pool.spawn(self.run)]

        spawn_list = spawn_run + \
                     [self.pool.spawn(self.monitor, worker) for work_group in
                      workgroups for worker in work_group]

        # we get a blocking error if we spawn the manager first, so spawn it last
        spawn_list.append(self.pool.spawn(self.manage))

        return spawn_list

    def monitor(self, target):
        """
        This method actually spawns the spider and then the purpose is to allow
        some additional final actions to be performed on the spider object after
        the worker completes the spider's job, but before it shuts down and the
        object instance is lost.

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
                                one_task = q.get(timeout=0.5)
                                worker.tasks.put(one_task)
                gevent.sleep(0)
        except Empty:
            print(f'Assigned all {name} work!')
            if self.manager_should_stop:
                self.should_stop = True

    def main(self):
        spawny = self.spawn_list()
        gevent.pool.joinall(spawny)
        gevent.sleep(0)
