# -*- coding: utf-8 -*-
"""
transistor.books.taskstate
~~~~~~~~~~~~
This module creates task tracking objects, used to assign and monitor task state on
a per WorkGroup basis.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from collections import deque
from abc import ABC, abstractmethod


class _TaskState:
    """
    Store the state of task items for each website WorkGroup/Worker/Scraper set.

    For example, lets suppose we have a list of 100 different manufacturing part
     numbers for electronic components. We want to search each part number on six
     different website domains. After searching, we're going to scrape the result.
     So, we need to do 600 searches, 100 different searches on each of six websites.

      WEBSITE                Scrape Tasks
    - mousekey.com.cn           x 100
    - mousekey.com              x 100
    - digidog.com.cn            x 100
    - digidog.com               x 100
    - electricfuture.cn         x 100
    - electricfuture.com        x 100

    From a messaging queuing and task assignment point of view, the structure
    of the required solution is called `Fanout`.  We have some `producer` that
    creates the initial 100 different manufacturing part numbers (mpn's). Then,
    we deliver those mpn's to an `exchange` (the StatefulBook class). The
    StatefulBook class creates a `queue` for each of the workers which will
    scrape the website, containing the same 100 mpns.

    Further, we ultimately want to track the state of each of the 100 part number
    searches on each website. So we can have conversations like, "Do we have results
    for part number xyz1 on website 'mousekey.com' and 'digifuture.com'? How do
    they compare? Darn it, the search on 'digifuture.com' failed. We need to
    retry it or else investigate why the search failed."

    trackers = ['mousekey.com.cn', 'mousekey.com', 'digidog.com.cn', 'digidog.com',
    'electricfuture.cn', 'electricfuture.com']

    We want to keep track of the task status state of each part number search, for
    each website we scrape.
    """

    def __init__(self, to_do=None, in_proc=None,
                 done=None, failed=None):
        """
        :param records: a list of OrderedDict ingest from the items tab
        :param sheet: pyexcel.sheet.Sheet of the items tab
        :param to_do: track items not yet started
        :param in_proc: track currently in process items
        :param done: track sucessfully completed items
        :param failed: track failed items
        """
        self.to_do = to_do
        self.in_proc = in_proc
        self.done = done
        self.failed = failed


class TaskTracker:
    """
    Track the items task status for each type of crawler job.
    For example, we want to track the part number status for:

    - mousekey.com.cn
    - mousekey.com
    - digidog.com.cn
    - digidog.com
    - electricfuture.cn
    - electricfuture.com

    So we need to keep track of the state of each part number task, for each
    of the websites we want to scrape.

    """

    def __init__(self, name:str, to_do=None):
        """
        Create the tracker.
        :param name: a string name for this tracker
        :param to_do: a deque of starting to_do
        """
        self.__state = _TaskState()
        self.name = name
        self._build_queues(to_do)

    def __repr__(self):
        return f'<TaskTracker(name={self.name})>'

    def _build_queues(self, pns):
        """
        Parse the item records and build the initial job queues.
        :param records: a deque of starting items

        :return: all the queues

        self.to_do = to_do
        self.in_proc = in_proc
        self.done = done
        self.failed = failed
        """

        to_do = pns
        # build the other empty queues
        in_proc = deque()
        done = deque()
        failed = deque()

        self.__state = _TaskState(to_do=to_do, in_proc=in_proc,
                                done=done, failed=failed)

        return to_do, in_proc, done, failed

    def to_do(self):
        """
        Return the item queue.
        :return:
        """
        return self.__state.to_do

    def in_proc(self):
        """
        Return the in_proc queue

        :return:
        """
        return self.__state.in_proc

    def done(self):
        """
        Return the in_proc queue

        :return:
        """
        return self.__state.done

    def failed(self):
        """
        Return the failed queue

        :return:
        """
        return self.__state.failed
