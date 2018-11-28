# -*- coding: utf-8 -*-
"""
transistor.workers.basegroup
~~~~~~~~~~~~
This module implements BaseGroup. See transistor.workers.__init__ for
more notes on this module.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""


class BaseGroup:
    """
    Inherit this class to create a Group of Worker objects. It allows to
    easily index and combine groups of workers. For example, this class
    enables class WorkerGroup<#>(BaseGroup) to be combined like:

    WorkerGroup3 = WorkerGroup1 + WorkerGroup2
    """

    def __init__(self, staff: int, job_id: str, timeout: tuple = None, **kwargs):
        """
        :param staff: an integer number which represents how many workers to
        spin up for scraping.  It can be an arbitrary number.
        :param job_id: str(), the name
        :param timeout: tuple for python-requests timeout like (3.0, 700.0).
        You should not need to adjust the first number. But you may need to
        adjust the 2nd timeout number.  Definitely, if you use Crawlera. When using
        Crawlera, the 2nd timeout number is dependent on the website and
        optimization of the LUA SOURCE script to filter links that do not need
        followed in order to get the data that you are targeting.
        :param kwargs: name::str(): a name attribute which will be passed down to
        the worker and spider.
        :param: url::str(): the starting URL which will be passed down to the worker
        and spider.
        """
        self.staff = staff
        self.job_id = job_id
        self.timeout = timeout
        if self.timeout is None:
            self.timeout = (3.05, 700.00)
        self.worker_list = None
        self.name = kwargs.get('name', None)
        self.items = kwargs.get('items', None)
        self.loader = kwargs.get('loader', None)
        self.exporter = kwargs.get('exporter', None)
        self.worker = kwargs.get('worker', None)
        self.spider = kwargs.pop('spider', None)
        self.url = kwargs.get('url', None)
        self.kwargs = kwargs

    def __repr__(self):
        return f"<WorkerGroup(job_id='{self.job_id}', group_name='{self.name}')>"

    def __getitem__(self, index):
        """
        Enable the class to function like a list.
        :param index: an index
        """
        return self.worker_list[index]

    def __add__(self, other):
        """
        Enable to add two classes that inherit from this BaseGroup class,
        together.  It should function the same as adding two lists together.
        :param other: another object which inherits from BaseGroup
        """
        total_workers = []
        if self.worker_list:
            total_workers = self.worker_list + other.worker_list
        return total_workers

    def init_workers(self):
        """
        Create the number of workers in staff count.
        :returns list, the staff of workers
        """
        worker_list = []
        for number in range(0, self.staff):
            worker = self.hired_worker()
            worker.job_id = self.job_id
            worker.number = number + 1  # I don't want a zero index worker number
            worker.items = self.items
            worker.loader = self.loader
            worker.exporter = self.exporter
            worker_list.append(worker)
        self.worker_list = worker_list
        return worker_list

    @property
    def workers(self):
        """return a list of all individual workers in the workgroup"""

        return self.worker_list

    def hired_worker(self):
        """
        Encapsulates the custom spider, inside of a Worker object. This helps
        enable running an arbitrary amount of Spider objects.

        Creates the number of workers given in `staff` (see BaseGroup.__init__()).
        Setting the http_session for the Worker is also handled here.
        Last, this is a good place to ensure any custom class attributes you must
        have on the worker are set here.

        :returns <Worker>, the worker object
        """
        worker = self.worker(job_id=self.job_id, spider=self.spider,
                             http_session={'url': self.url, 'timeout': self.timeout},
                             **self.kwargs)

        return worker