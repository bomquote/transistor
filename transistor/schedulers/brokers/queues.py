# -*- coding: utf-8 -*-
"""
transistor.schedulers.brokers.queues
~~~~~~~~~~~~
Exchange and task queue with support for using different queues for each
tracker. Works with RabbitMQ or Redis acting as a broker.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
from kombu import Exchange, Queue
from typing import List


class ExchangeQueue:
    """
    Setup an Exchange and a separate Queue for each named tracker in
    the `trackers` parameter.  Note: best practice is to explicitly
    declare the queues when using this. It would probably look like:
    >>> for queue in tasks.task_queues:
    >>>     queue(broker_connection).declare()
    """
    def __init__(self, trackers: List[str], exchange_name: str='transistor',
                 exchange_type: str='direct'):
        self.trackers = trackers
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.task_exchange = Exchange(self.exchange_name, type=self.exchange_type)
        self.task_queues = []
        self._init_task_queues()

    def _init_task_queues(self):
        """
        Assuming we init with parameter `trackers = ['mousekey.com', 'digidog.com',
        'futuredigi.com']`
        then this should set self.task_queues as below:

        self.task_queues = [
           Queue('mousekey.com', task_exchange, routing_key='mousekey.com'),
           Queue('digidog.com', task_exchange, routing_key='digidog.com'),
           Queue('futuredigi.com', task_exchange, routing_key='futuredigi.com')]
        """
        for tracker_name in self.trackers:
            queue = Queue(tracker_name, self.task_exchange, routing_key=tracker_name)
            self.task_queues.append(queue)
