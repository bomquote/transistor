# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.schedulers.brokers.client_main
~~~~~~~~~~~~
This module implements a client producer for testing
and example.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from kombu.pools import producers
from examples.books_to_scrape.schedulers.brokers.worker_main import tasks

task_exchange = tasks.task_exchange


def send_as_task(connection, keywords, kwargs={}):
    payload = {'keywords': keywords, 'kwargs': kwargs}

    with producers[connection].acquire(block=True) as producer:
        producer.publish(payload,
                         serializer='json',
                         exchange=task_exchange,
                         declare=[task_exchange])


if __name__ == '__main__':

    from kombu import Connection
    keywords = '["Soumission", "Rip it Up and Start Again", "Black Dust"]'
    connection = Connection("pyamqp://guest:guest@localhost:5672//")
    send_as_task(connection, keywords=keywords, kwargs={})