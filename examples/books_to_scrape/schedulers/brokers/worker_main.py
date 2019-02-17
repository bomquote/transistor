# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.main
~~~~~~~~~~~~
Entry point to run the books_to_scrape example.

To run this example, first run:

>>> python client_main.py

This will start the producer and send the tasks to the broker Exchange queue.
Then, in a separate command prompt, run:

>>> python client_worker.py

The result should be the worker will process the `keywords` tasks.

Note:

The primary use case where the current Transistor design shines, is when you need to
scrape websites which have a search functionality. These are generally non-paginated
websites, which you need to enter a search term, and then scrape the page which is
given by the server in response.

For the search term use case, this design is good. You can send an arbitrary number
of workers to the search page. Each worker has one task issued, a task to execute the
search for the term it has been assigned, and return to us with the response.

The example highlighted here in `books_to_scrape`, employs a "crawl" mechanism
inside each of the scraper objects. This is not really showcasing the optimal
use case for a Transistor SplashScraper with Manager/WorkGroups, per the
current design.

The reason is, in this example, we send out 20 workers at once. Each worker
crawls through EACH PAGE on the books.toscrape.com website, until the worker finds
the book title it has been dispatched to find.  There are only 50 pages on the
books.toscrape.com website. Meanwhile, this design we've used here, results in us
crawling hundreds of pages, considering each page that each of 20 workers will crawl.

It gets the job done. But, this design results in a comparatively heavy load on
the target server. Versus, an alternative design, which could use only one worker
to crawl each web page, searching each page for a book_title which matches a
book title in it's work queue, gathering the data for each matched book title, as it
crawls from page to next-page.

The total crawl time would be about the same. But, the alternative design using only
one worker to crawl each page and collect multiple results per page as they are found,
would have crawled a lot less pages in total, bringing some potential net benefit. Even
if the benefit is just reducing the risk of irritating the target server webmaster.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
# monkey patching for gevent must be done first
from gevent import monkey
monkey.patch_all()
# used to establish a connection to RabbitMQ server
from kombu import Connection
# used for postgresql and newt.db persistence
from transistor.persistence.newt_db import get_job_results, delete_job
from examples.books_to_scrape.persistence.newt_db import ndb
# finally, the core of what we need to launch the scrape job
from transistor import WorkGroup
from transistor.schedulers.brokers.queues import ExchangeQueue
from transistor.persistence.exporters import CsvItemExporter
from transistor.persistence.exporters.json import JsonLinesItemExporter
from examples.books_to_scrape.workgroup import BooksWorker
from examples.books_to_scrape.scraper import BooksToScrapeScraper
from examples.books_to_scrape.manager import BooksWorkGroupManager
from examples.books_to_scrape.persistence.serialization import (
    BookItems, BookItemsLoader)
from transistor.utility.logging import logger


# 1) Create an ExchangeQueue instance and connection object to prepare
# to use RabbitMQ message broker.
# Set a list of tracker names, with one tracker name for each WorkGroup you create
# in step three. Ensure the tracker name matches the WorkGroup.name in step four.

trackers = ['books.toscrape.com']
tasks = ExchangeQueue(trackers)
connection = Connection("pyamqp://guest:guest@localhost:5672//")

# 2) Setup a list of exporters which than then be passed to whichever WorkGroup
# objects you want to use them with. In this case, we are just going to use the
# built-in CsvItemExporter but we could also use additional exporters to do
# multiple exports at the same time, if desired.

exporters = [CsvItemExporter(
                fields_to_export=['book_title', 'stock', 'price'],
                file=open('c:/temp/book_data.csv', 'a+b'),
                encoding='utf_8_sig'),
             JsonLinesItemExporter(
                fields_to_export=['book_title', 'stock', 'price'],
                file=open('c:/temp/book_data.json', 'a+b'),
                encoding='utf_8_sig')]

# 3) Setup the WorkGroups. You can create an arbitrary number of WorkGroups in a list.
# For example, if there are three different domains which you want to search for
# the book titles from the excel file. If you wanted to scrape the price and stock data
# on each of the three different websites for each book title. You could setup three
# different WorkGroups here. Last, the WorkGroup.name should match the tracker name.

groups = [
    WorkGroup(
        name='books.toscrape.com',
        url='http://books.toscrape.com/',
        spider=BooksToScrapeScraper,
        worker=BooksWorker,
        items=BookItems,
        loader=BookItemsLoader,
        exporters=exporters,
        workers=2,  # this creates x scrapers and assigns each a book as a task
        kwargs={'timeout': (3.0, 20.0)})
    ]

# 4) Last, setup the Manager. You can constrain the number of workers actually
# deployed, through the `pool` parameter. For example, this is useful
# when using a Crawlera 'C10' plan which limits concurrency to 10. To deploy all
# the workers concurrently, set the pool to be marginally larger than the number
# of total workers assigned in groups in step #3 above.
manager = BooksWorkGroupManager('books_scrape', tasks, workgroups=groups, pool=10,
                                connection=connection)

if __name__ == "__main__":

    from kombu.utils.debug import setup_logging
    # setup root logger
    setup_logging(loglevel='INFO', loggers=[''])
    with Connection('amqp://guest:guest@localhost:5672//') as conn:
        try:

            manager.main()  # call manager.main() to start the job.
        except KeyboardInterrupt:
            print('bye bye')
    # below shows an example of navigating your persisted data after the scrape

    result = get_job_results(ndb, 'books_scrape')
    logger.info(f'Printing: books_scrape result =>')
    if result:
        for r in result:
            logger.info(f"{r['book_title']}, {r['price']}, {r['stock']}")
        delete_job(ndb, 'books_scrape')
