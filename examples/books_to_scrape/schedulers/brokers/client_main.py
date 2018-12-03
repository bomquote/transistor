# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.schedulers.brokers.client_main
~~~~~~~~~~~~
This module implements a client producer for testing
and example.

To run this example, first run:

>>> python client_worker.py

This will start the worker and await the task. Then, in a separate
command prompt, to simulate a message sent to the broker queue, run:

>>> python client_main.py

The result should be the worker will process the `keywords` tasks.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
import time
from kombu import Connection
from kombu.pools import producers
from transistor.schedulers.brokers.queues import ExchangeQueue
from transistor.utility.logging import logger
# from examples.books_to_scrape.schedulers.brokers.worker_main import tasks

trackers = ['books.toscrape.com']
tasks = ExchangeQueue(trackers)
connection = Connection("pyamqp://guest:guest@localhost:5672//")

def _publish(producer, payload, routing_key, exchange):
    """

    :param producer: example ->
        >>> with producers[connection].acquire(block=True) as producer:
    :param payload: example ->
        >>> payload = {'keywords': keywords, 'kwargs': kwargs}
    :param routing_key: Type[str]: 'books.toscrape.com'
    :param exchange: a kombu Type[Exchange] class object
    :return:
    """
    producer.publish(payload,
                     serializer='json',
                     exchange=exchange,
                     routing_key=routing_key,
                     declare=[exchange],
                     retry=True,
                     retry_policy={
                         'interval_start': 0,  # First retry immediately,
                         'interval_step': 2,  # then increase by 2s for every retry.
                         'interval_max': 5,  # don't exceed 5s between retries.
                         'max_retries': 3,  # give up after 3 tries.
                     })


def send_as_task(connection, keywords, routing_key, exchange, kwargs={}):
    payload = {'keywords': keywords, 'kwargs': kwargs}

    with producers[connection].acquire(block=True) as producer:
        # for tracker in tasks.trackers:
        #    publish(producer=producer, payload=payload, routing_key=tracker)
        producer.publish(payload,
                         serializer='json',
                         # if there is more than one tracker, use something like
                         # the _publish above, with a for loop for each tracker
                         routing_key=routing_key,
                         exchange=exchange,
                         declare=[exchange],
                         )


if __name__ == '__main__':

    from kombu import Connection
    from kombu.utils.debug import setup_logging

    # setup root logger
    setup_logging(loglevel='INFO', loggers=[''])

    keyword_1 = '["Soumission"]'
    keyword_2 = '["Rip it Up and Start Again"]'
    keywords = '["Black Dust", "When We Collided"]'

    with Connection("pyamqp://guest:guest@localhost:5672//") as conn:
        send_as_task(conn, keywords=keyword_1, routing_key='books.toscrape.com',
                     exchange= tasks.task_exchange, kwargs={})
        logger.info(f'sent task {keyword_1}')
        send_as_task(conn, keywords=keyword_2, routing_key='books.toscrape.com',
                     exchange= tasks.task_exchange, kwargs={})
        logger.info(f'sent task {keyword_2}')
        send_as_task(conn, keywords=keywords, routing_key='books.toscrape.com',
                     exchange= tasks.task_exchange, kwargs={})
        logger.info(f'sent task {keywords}')
