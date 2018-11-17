# -*- coding: utf-8 -*-
"""
transistor.io.workers.basegroup_abc
~~~~~~~~~~~~
This module implements BaseGroup. See transistor.io.workers.__init__ for
more notes on this module.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
from abc import ABC, abstractmethod


class BaseGroup(ABC):
    """
    Inherit this class to create a WorkGroup. It allows to index and combine
    groups of workers. For example, this class enables WorkGroups to be combined like:

    workgroup3 = workgroup1 + workgroup2

    It should be inherited to form a WorkGroup, where WorkGroup is a group of
    individual scraper workers.
    """
    name = None

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

        """
        self.staff = staff
        self.job_id = job_id
        self.timeout = timeout
        if self.timeout is None:
            self.timeout = (3.05, 700.00)
        self.worker_list = None
        self.name = kwargs.get('name', None)
        self.url = kwargs.get('url', None)
        self.kwargs = kwargs

    def __repr__(self):
        return f"<WorkGroup(job_id='{self.job_id}', group_name='{self.name}')>"

    def __getitem__(self, index):
        """
        We want the class to be able to work like a list.
        :param index: an index
        """
        return self.worker_list[index]

    def __add__(self, other):
        """
        Let's be able to add two worker lists together.
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
            worker_list.append(worker)
        self.worker_list = worker_list
        return worker_list

    @property
    def workers(self):
        """return a list of all individual workers in the workgroup"""

        return self.worker_list

    @abstractmethod
    def hired_worker(self):
        raise NotImplementedError("You must define a hired_worker method")