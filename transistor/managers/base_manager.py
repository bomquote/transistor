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
will sublcass BaseManager and override the monitor method for customization.


:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

import gevent
from gevent.queue import Queue, Empty
from gevent.pool import Pool
from gevent.event import Event


# prepare event signal
evt = Event()


class BaseWorkGroupManager:
    """
    Base class for a WorkGroupManager.
    """
    __attrs__ = [
        'book', 'job_id', 'groups', 'trackers', 'pool', 'qitems', 'workgroups',
    ]

    def __init__(self, job_id, book, groups:list, pool:int=20):
        """

        Create the instance.

        :param job_id: will save the result of the workers Scrapes to `job_id` list.
        If this job_id is "NONE" then it will pass on the save.
        :param book:  a StatefulBook instance
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
        self.book = book
        self.groups = groups
        self.trackers = self.book.trackers
        self.pool = Pool(pool)
        self.qitems = {}
        self.workgroups = {}
        self._init_tasks()

    def _init_tasks(self):
        """
        Create individual task queues for the workers. The worker names
        should be extracted from self.book.to_do().


        Extract the tracker name and then create the items.

        items = {}
        for tracker in book.to_do():
            items.[self.tracker.name] = tracker.to_do()

        deque([<TaskTracker(name=mousekey.cn)>, <TaskTracker(name=mousekey.com)>])

        :return:
        """

        for tracker in self.book.to_do():
            # set the name of qitems key to tracker.name
            self.qitems[tracker.name] = Queue(items=tracker.to_do())

        self._init_workers()

    def _init_workers(self):
        """
        Create the WorkGroups by tracker name and assign them by name to the
        workgroups dict.

        :return:
        """
        names = [name for name in self.qitems.keys()]
        for name in names:
            for group in self.groups:
                if group[2] == name:
                    # assumes `group` is a WorkGroup namedtuple of the form:
                    # WorkGroup(class_=BooksGroup, workers=2, kwargs={'china':True,
                    # 'timeout': (3.0, 3.0)})

                    # add the name to group3 dict
                    group[3]['name'] = name
                    workgroup = group[0](
                        staff=group[1], job_id=self.job_id, **group[3])
                    # now is the time to set the name attribute on the workgroup
                    workgroup.name = name
                    # now that the name is assigned, init the workers on the workgroup
                    # this allows the encapsulated Worker to also be assigned the name
                    # don't change this without testing, Workers will lose their name
                    workgroup.init_workers()
                    # lastly, after calling init_workers, assign the workgroup instance
                    # with workers instance to the workgroups dict with key = `name`
                    self.workgroups[name] = workgroup

    def spawn_list(self):
        """"
        The spawn() method begins a new greenlet with the given arguments
        (which are passed to the greenlet constructor) and adds it to the
        collection of greenlets this group is monitoring.

        We return a list of the newly started greenlets, used in a later
        'joinall` call.

        :return: A list of the newly started greenlets.
        """

        # workgroups is a list of BaseGroup objects
        workgroups = [val for val in self.workgroups.values()]

        spawn_list = [self.pool.spawn(self.monitor, worker) for work_group in
                      workgroups for worker in work_group]

        # we get a blocking error if we spawn the manager first, so spawn it last
        spawn_list.append(self.pool.spawn(self.manage))

        return spawn_list

    def monitor(self, target):
        """
        This method actually spawns the scraper and then the purpose is to allow
        some additional final actions to be performed on the scraper object after
        the worker completes the scrape job, but before it shuts down and the object
        instance is lost (though the ScraperContainer object will exist in the db).

        The simplest example which must be implemented:

        def monitor(self, target):
            '''
            The only absolute requirement is to start the scraper with
            target.spawn_scraper() and then call gevent.sleep(0)
            '''
            target.spawn_scraper()
            gevent.sleep(0)

        A more useful example:

        def monitor(self, target):
            '''
            More useful, would be to hook in some post-scrape logic between
            spawn_scraper() and gevent.sleep(0).
            '''
            target.spawn_scraper()
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
        target.spawn_scraper()
        gevent.sleep(0)

    def manage(self):
        """"
        Manage will hand out work when  the appropriate Worker is free.
        The manager timeout must be less than worker timeout, or else, the workers
        will be idled and shutdown.
        """
        try:
            while True:
                for name, workgroup in self.workgroups.items():
                    for qname, q in self.qitems.items():
                        if name == qname: # workgroup name must match the tracker name
                            for worker in workgroup:
                                one_task = q.get(timeout=0.5)
                                worker.tasks.put(one_task)
                gevent.sleep(0)
        except Empty:
            print(f'Assigned all {name} work!')

    def main(self):
        spawny = self.spawn_list()
        gevent.pool.joinall(spawny)
        gevent.sleep(0)
