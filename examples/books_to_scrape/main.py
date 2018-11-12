# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.main
~~~~~~~~~~~~
Entry point to run the books_to_scrape example.

Note: The example highlighted here, employs a "crawl" mechanism inside each
of the scraper objects. This is not really showcasing the optimal use case for
a Transistor SplashScraper with Manager/WorkGroups, per the current design.

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
one worker to crawl each page and collect mutliple results per page as they are found,
would have crawled a lot less pages in total, bringing some potential net benefit. Even
if the benefit is just reducing the risk of irritating the target server webmaster.

The primary use case where the current Transistor design shines, is when you need to
scrape websites which have a search functionality. These are generally non-paginated
websites, which you need to enter a search term, and then scrape the page which is
given by the server in response.

For the search term use case, this design is good. You can send an arbitrary number
of workers to the search page. Each worker has one task issued, a task to execute the
search for the term it has been assigned, and return to us with the response.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
# monkey patching for gevent must be done first
from gevent import monkey
monkey.patch_all()
# used to find the excel file, this can probably be simplified
from os.path import dirname as d
from pathlib import Path
from os.path import abspath
# finally, the core of what we need to launch the scrape job
from transistor.io.workers import WorkGroup
from transistor.io.books import StatefulBook
from examples.books_to_scrape.workgroup import BooksToScrapeGroup
from examples.books_to_scrape.manager import BooksWorkGroupManager


# 1) get the excel file path which has the book_titles we are interested to scrape
def get_file_path(filename):
    """
    Find the book_title excel file path.
    """
    root_dir = d(d(abspath(__file__)))
    root = Path(root_dir)
    filepath = root / 'books_to_scrape' / filename
    return r'{}'.format(filepath)


# 2) Create a StatefulBook instance to read the excel file and load the work queue.
# Set a list of tracker names, with one tracker name for each WorkGroup you create
# in step three. Ensure the tracker name matches the WorkGroup.name in step three.
file = get_file_path('book_titles.xlsx')
trackers = ['books.toscrape.com']
stateful_book = StatefulBook(file, trackers, autorun=True)


# 3) Setup the WorkGroup. You can setup an arbitrary number of WorkGroups in a list.
# For example, if there are three different domains which you want to search for
# the book titles from the excel file. To, scrape the price and stock data on
# each of the three different websites for each book title. You could setup three
# different WorkGroups here. Last, the WorkGroup.name should match the tracker name.
groups = [
    WorkGroup(
        class_=BooksToScrapeGroup,
        workers=20,  # this creates 20 scrapers and assigns each a book as a task
        name='books.toscrape.com',
        kwargs={'url': 'http://books.toscrape.com/', 'timeout': (3.0, 20.0)})
    ]

# 4) Last, setup the Manager. Ensure the pool is marginally larger than the number of
# total workers assigned in groups in step #3 above.
manager = BooksWorkGroupManager('books_scrape', stateful_book, groups=groups, pool=25)


if __name__ == "__main__":
    manager.main()  # call manager.main() to start the job.

    # below shows an example of navigating your persisted data after the scrape
    from examples.books_to_scrape.persistence.newt_crud import (get_job_results,
                                                                delete_job)

    result = get_job_results('books_scrape')

    for r in result:
        print(f'{r.book_title}, {r.price}, {r.stock}')

    delete_job('books_scrape')
