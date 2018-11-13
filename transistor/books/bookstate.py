# -*- coding: utf-8 -*-
"""
transistor.books.bookstate
~~~~~~~~~~~~
This module opens an excel workbook, reads an 'item' column to ingest an arbitrary
number of rows of search terms. It then transforms each search term into a task.
Finally, it creates work queues full of tasks, with each task being a search term.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
import pyexcel as pe
from collections import deque
from pathlib import Path
from os.path import dirname as d
from os.path import abspath
from transistor.books.taskstate import TaskTracker

root_dir = d(d(abspath(__file__)))


def get_file_path(filename):
    """
    if you refactor the file path of this file, then this needs updated
    :param filename:
    :return:
    """
    root = Path(root_dir)  # C:\Users\thisguy\repos\transistor\transistor\io
    data_folder = root / u'files'
    filepath = data_folder / filename
    return r'{}'.format(filepath)


class _BookState:
    """
    Store the state of StatefulBook attributes and methods. Like, pyexcel
    and task status states.

    """
    def __init__(self, records=None, sheet=None, to_do=None, in_proc=None,
                 done=None, failed=None):
        """
        :param records: a list of OrderedDict ingest from the items tab
        :param sheet: pyexcel.sheet.Sheet of the items tab
        :param to_do: track items not yet started.
        :param in_proc: track currently in process items
        :param done: track successfully completed items
        :param failed: track failed items
        """
        self.records = records
        self.sheet = sheet
        self.to_do = to_do
        self.in_proc = in_proc
        self.done = done
        self.failed = failed


class StatefulBook:
    """
    Read an excel sheet to ingest the items.

    Then track the item states as the scrape progresses.

    Finally, prepare the the data for export to an excel workbook.

    When you fire this up in repl:
        from transistor.io.ingest import StatefulBook
        from transistor.io.ingest import get_file_path
        file = get_file_path('clock_bom.xlsx')
        trackers = ['mouser.cn', 'mouser.com', 'digikey.com.cn', 'digikey.com',
        'futureelectronics.cn', 'futureelectronics.com']

        book = StatefulBook(file, trackers)

    """
    def __init__(self, file_name: str=None, trackers: list=None, autorun=True,  **kwargs):
        """
        Instantiate the class.

        :param file_name: "clock_bom.xlsx"
        :param tracker: a list of strings for names assigned to each TaskTracker
        :param keywords: the spreadsheet column heading name from which to load
         the tasks.  It should be set like 'keywords'='<column heading>', for example
         'keywords'='part_numbers'.  Default is 'item'.
        """
        self.file_name = file_name
        self.__state = _BookState()
        self.SOURCE = get_file_path(self.file_name)
        self.trackers = trackers
        self.keywords = kwargs.get('keywords', 'item')
        if autorun:
            self.open_book()

    def open_book(self):
        """
        Read the sheet.
        :return:
        """
        records = self._get_records()
        sheet = self._get_sheet(records)
        to_do, in_proc, done, failed = self._build_queues(records)

        self.__state = _BookState(records=records, sheet=sheet,
                                  to_do=to_do, in_proc=in_proc,
                                  done=done, failed=failed)
        return pe.free_resources()

    def _get_records(self):
        """
        Open the records as a list.
        If you use iget then it returns a generator and we can't save the state.
        pe.iget_records(file_name=self.SOURCE)

        :return:
        """
        records = pe.get_records(file_name=self.SOURCE)
        return records

    @staticmethod
    def _get_sheet(records):
        """
        Parse the item records and return a sheet.
        :return: a pyexcel.sheet.Sheet built from ->
         a_dictionary_of_one_dimensional_arrays = {"item": [1, 2, 3, 4]}
        """
        items = []
        item_col = {'item': []}
        for record in records:
            pn = record['item']
            items.append(str(pn))
        item_col['items'] = items

        return pe.get_sheet(adict=item_col)

    def _build_queues(self, records):
        """
        Parse the item records and build the initial job queues.
        :param records: instance of pyexcel.get_records(file_name="the_file_name.xlsx")
        and it should be a list of OrderedDict ingest from the items tab
        :return: all the queues

        self.to_do = to_do
        self.in_proc = in_proc
        self.done = done
        self.failed = failed
        """
        # build the to_do deque

        init_to_do = deque()
        tracker_list = []

        for record in records:
            init_to_do.append(str(record["item"]))

        for name in self.trackers:
            tracker_list.append(TaskTracker(name=name, to_do=init_to_do))

        # put each individual TaskTracker() in the todo_tasks
        todo_tasks = deque()
        for tracker in tracker_list:
            todo_tasks.append(tracker)

        inproc_tasks = deque()
        done_tasks = deque()
        failed_tasks = deque()

        return todo_tasks, inproc_tasks, done_tasks, failed_tasks

    def to_do(self):
        """
        Return the to_do queue
        :return:
        deque([<TaskTracker(name=mouser.cn)>,
           <TaskTracker(name=mouser.com)>,
           <TaskTracker(name=digikey.com.cn)>,
           <TaskTracker(name=digikey.com)>,
           <TaskTracker(name=futureelectronics.cn)>,
           <TaskTracker(name=futureelectronics.com)>])
        """
        return self.__state.to_do

    def in_proc(self):
        """
        Return the in_proc queue

        :return: a deque of <TaskTracker(name='part_number')> objects
        """
        return self.__state.in_proc

    def done(self):
        """
        Return the done queue

        :return: a deque of <TaskTracker(name='part_number')> objects
        """
        return self.__state.done

    def failed(self):
        """
        Return the failed queue

        :return: a deque of <TaskTracker(name='part_number')> objects
        """
        return self.__state.failed