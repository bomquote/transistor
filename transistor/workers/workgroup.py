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
from typing import NamedTuple, Type, Union, List
from transistor.workers.basegroup import BaseGroup
from transistor.persistence.loader import ItemLoader
from transistor.persistence.exporters.base import BaseItemExporter
from transistor.persistence.containers import Item
from transistor.scrapers.splash_scraper_abc import SplashScraper
from transistor.workers.baseworker import BaseWorker

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

    :param name: name the group
    :param tasks: an instance of StatefulBook or dict or list
    :param group: the <WorkerGroup> class object
    :param items: the number of workers to spawn
    :param loader:
    :param exporter:
    :param kwargs: to use for each <Worker> instance in the group
    """
    name: str
    # tasks: Optional[Type[Union[Type[StatefulBook], dict]]]
    spider: Type[SplashScraper]
    worker: Type[BaseWorker] = BaseWorker
    group: Type[BaseGroup] = BaseGroup
    items: Type[Item] = Item
    loader: Type[ItemLoader] = ItemLoader
    exporters: List[Type[Union[Type[BaseItemExporter]]]] = BaseItemExporter
    workers: int = 1
    kwargs: dict = {}
