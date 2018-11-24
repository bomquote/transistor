# -*- coding: utf-8 -*-
"""
transistor.workers.workgroup
~~~~~~~~~~~~
This module implements WorkGroup.
See transistor.workers.__init__ for more notes on this module.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
from typing import NamedTuple, Type
from transistor.workers.basegroup_abc import BaseGroup


class WorkGroup(NamedTuple):
    """
    A container class to use when starting up a WorkGroupManager.  Intended use
    is, like below:

    >>> groups = [
    >>>          WorkGroup(class_=MouseKeyGroup, workers=2, name='mousekey.cn',
    >>>          kwargs={'china':True, 'timeout': (3.0, 3.0)}),
    >>>
    >>>          WorkGroup(class_=MouseKeyGroup, workers=2, name='mousekey.com',
    >>>          kwargs={'timeout':(3.0, 3.0)})
    >>>          ]
    >>> manager = WorkGroupManager('part_number_job_1', book, groups=groups, pool=5)

    :param class: the <WorkerGroup> class object
    :param class: the number of workers to spawn
    :param class: the workgroup name,
    where name == tracker name == worker name == scraper name, must all be same
    :param class: kwargs to use for each <Worker> instance in the group
    """
    class_: Type[BaseGroup]
    workers: int
    name: str
    kwargs: dict
