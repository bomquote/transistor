
.. image:: https://raw.githubusercontent.com/bmjjr/transistor/master/img/transistor_logo.png?token=AAgJc9an2d8HwNRHty-6vMZ94VfUGGSIks5b8VHbwA%3D%3D

**Web data collection and storage for intelligent use cases.**

.. image:: https://img.shields.io/badge/Python-3.6%20%7C%203.7-blue.svg
  :target: https://github.com/bomquote/transistor
.. image:: https://img.shields.io/badge/pypi%20package-0.1.1-blue.svg
  :target: https://pypi.org/project/transistor/0.1.1/
.. image:: https://img.shields.io/badge/Status-Beta-blue.svg
  :target: https://github.com/bomquote/transistor
.. image:: https://ci.appveyor.com/api/projects/status/xfg2yedwyrbyxysy/branch/master?svg=true
    :target: https://ci.appveyor.com/project/bomquote/transistor
.. image:: https://pyup.io/repos/github/bomquote/transistor/shield.svg?t=1542037265283
    :target: https://pyup.io/account/repos/github/bomquote/transistor/
    :alt: Updates
.. image:: https://api.codeclimate.com/v1/badges/0c34950c38db4f38aea6/maintainability
   :target: https://codeclimate.com/github/bomquote/transistor/maintainability
   :alt: Maintainability
.. image:: https://codecov.io/gh/bomquote/transistor/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/bomquote/transistor


=============
*transistor*
=============

About
-----

The web is full of data. Transistor is a lightweight framework for collecting, storing, and using targeted data from structured web pages.

Transistor's current strengths are in being able to:
    - provide an interface to use `Splash <https://github.com/scrapinghub/splash>`_ headless browser / javascript rendering service.
    - includes *optional* support for using the scrapinghub.com `Crawlera <https://scrapinghub.com/crawlera>`_  'smart' proxy service.
    - ingest keyword search data from a spreadsheet and automatically transform keywords into a queue of tasks.
    - scale one worker into an arbitrary number of workers combined into a ``WorkGroup``.
    - coordinate an arbitary number of ``WorkGroup`` objects searching an arbitrary number of websites, into one scrape job with a ``WorkGroupManager``.
    - send out all the ``WorkGroups`` concurrently, using gevent based asynchronous I/O.
    - return data from each website for each search term 'task' in our list, for easy website-to-website comparison.

Suitable use cases include:
    - comparing attributes like stock status and price, for a list of ``book titles`` or ``part numbers``, across multiple websites.

Development of Transistor is sponsored by `BOM Quote Manufacturing <https://www.bomquote.com>`_.

**Primary goals**:

1. Enable scraping targeted data from a wide range of websites including sites rendered with Javascript.
2. Navigate websites which present logins, custom forms, and other blockers to data collection, like captchas.
3. Provide asynchronous I/O for task execution, using `gevent <https://github.com/gevent/gevent>`_.
4. Easily integrate within a web app like `Flask <https://github.com/pallets/flask>`_, `Django <https://github.com/django/django>`_ , or other python based `web frameworks <https://github.com/vinta/awesome-python#web-frameworks>`_.
5. Provide spreadsheet based data ingest and export options, like import a list of search terms from excel, ods, csv, and export data to each as well.
6. Utilize quick and easy integrated task queues which can be automatically filled with data search terms by a simple spreadsheet import.
7. Able to integrate with more robust task queues like `Celery <https://github.com/celery/celery>`_ and also interact with `rabbitmq <https://www.rabbitmq.com/>`_ and `redis <https://redis.io/>`_ as needed.
8. Provide hooks for users to persist data via any method they choose, while also supporting our own opinionated choice which is a `PostgreSQL <https://www.postgresql.org/>`_ database along with `newt.db <https://github.com/newtdb/db>`_.
9. Contain useful abstractions, classes, and interfaces for scraping and crawling with machine learning assistance (wip, timeline tbd).
10. Further support data science use cases of the persisted data, where convenient and useful for us to provide in this library (wip, timeline tbd).
11. Provide a command line interface (low priority wip, timeline tbd).


Architecture Summary
--------------------

Transistor provides useful layers and objects in the following categories:

**Layers & Services**

1. **javascript rendering service / headless browser layer**:

- Transistor uses `Splash <https://github.com/scrapinghub/splash>`_ implemented with `Aquarium <https://github.com/TeamHG-Memex/aquarium>`_ cookicutter docker template.
- Splash provides a programmable headless browser to render javascript and Aquarium provides robust concurrency with multiple Splash instances that are load balanced with `HAProxy <http://www.haproxy.org/>`_ .
- Transistor provides integration with Splash through our ``SplashBrowser`` class found in ``transistor/browsers/splash_browser.py``.

2. **smart proxy service**:

- Transistor supports use of `Crawlera <https://scrapinghub.com/crawlera>`_ , which is a paid *smart proxy service* providing robust protection against getting our own ip banned while scraping sites that actively present challenges to web data collection.
- Crawlera use is optional. It has a minimum monthly cost of $25 USD for starter package and next level up is currently $100 USD/month.
- in using Crawlera, the concurrency provided by gevent for asynchronous I/O along with Splash running with Aquarium, is absolutely required, because a single request with Splash + Crawlera is quite slow, taking up to **15 minutes** or more to successfully return a result.

**Scraping**

1. **browsers**

- see: ``transistor/browsers``
- wrap `python-requests <https://github.com/requests/requests>`_ and `beautifulsoup4 <https://www.crummy.com/software/BeautifulSoup/bs4/doc/>`_ libraries to serve our various scraping browser needs.
- browser API is generally created by subclassing and overriding the well known `mechanicalsoup <https://github.com/MechanicalSoup/MechanicalSoup>`_ library to work with Splash and/or Splash + Crawlera.
- if Javascript support is not needed for a simple scrape, it is nice to just use mechanicalsoup's ``StatefulBrowser`` class directly, like as shown in ``examples/cny_exchange_rate.py`` .
- a ``Browser`` object is generally instantiated inside of a ``Scraper`` object, where it handles items like fetching the page, parsing headers, creating a ``self.page`` object to parse with beautifulsoup4, handling failures with automatic retries, and setting class attributes accessible to our ``Scraper`` object.

2. **scrapers**

- see ``transistor/scrapers``
- instantiates a browser to grab the ``page`` object, implements various html filter methods on ``page`` to return the target data, can use Splash headless browser/javascript rendering service to navigate links, fill out forms, and submit data.
- for a Splash or Splash + Crawlera based scraper, the ``SplashScraper`` base class provides a minimal required Lua script and all required connection logic. However, more complex use cases will require providing your own custom modified Lua script.
- the scraper design is built around gevent based asynchronous I/O, and this design allows to send out an arbitrarily large number of scraper workers, with each scraper worker assigned a specific scrape task to complete.
- the current core design, in allowing to send out an arbitrarily large number of scraper workers, is not necessarily an optimal design to 'crawl' pages in search of targeted data. Where it shines is when you need to use a webpage search function on an arbitrarily large list of search tasks, await the search results for each task, and finally return a scraped result for each task.

3. **spiders** (wip, on the to-do list)

- see ``transistor/spiders`` (not yet implemented)
- while it is straightforward to use the current Transistor design to do basic crawling (see ``examples/books_to_scrape/scraper.py`` for an example) the current way to do this with Transistor is not always optimal for crawling. So we'll implement modified designs for crawling spiders.
- specifics TBD, may be fully custom or else may reuse some good architecture parts of `scrapy <https://github.com/scrapy/scrapy>`_, although if we do that, it will be done so we don't need a scrapy dependency and further it will be using gevent for asynchronous I/O.


**Program I/O**

1. **books**:

- see ``transistor/io/books``
- a ``StatefulBook`` object provides an interface to work with spreadsheet based data.
- for example, a book facilitates importing a column of keyword search term data, like 'book titles' or 'electronic component part numbers', from a designated column in an .xlsx file.
- after importing the keyword search terms, the book will transform each search term into a task contained in a ``TaskTracker`` object
- each ``TaskTracker`` will contain a queue of tasks to be assigned by the ``WorkGroupManager``, and will ultimately allow an arbitrarily large number of ``WorkGroups`` of ``BaseWorkers`` to execute the tasks, concurrently.

2. **workers**:

- a ``BaseWorker`` object encapsulates a ``SplashScraper`` object, which has been customized by the end user to navigate and extract the targeted data from a structured web page.
- a ``WorkGroup`` object can then be created, to encapsulate the ``BaseWorker`` object which contains the ``SplashScraper`` object.
- The purpose of this ``WorkGroup`` object is to enable concurrency and scale by being able to spin up an arbitrarily large number of ``BaseWorker`` objects, each assigned a different scrape task for execution.
- the ``WorkGroup`` object can then receive tasks to execute, like individual book titles or electronic component part numbers to search, delegated by a ``WorkGroupManager`` class.
- each ``BaseWorker`` in the ``WorkGroup`` also processes web request results, as they are returned from it's wrapped ``SplashScraper`` object.  ``BaseWorker`` methods include hooks for saving data to the db of your choice.

3. **managers**:

- the overall purpose of the ``WorkGroupManager`` object is to provide yet more scale and concurrency through asynchronous I/O.
- The ``WorkGroupManager`` can spin up an arbitrarily large number of ``WorkGroup`` objects while assigning each ``BaseWorker/SplashScraper`` in each of the ``WorkGroup`` objects, individual scrape tasks.
- This design approach is most useful when you have a finite pipeline of scrape tasks which you want to search and compare the same terms, across multiple different websites, with each website targeted by one ``WorkGroup``.
- for example, we may have a list of 50 electronic component part numbers, which we want to search each part number in ten different regional websites. The ``WorkGroupManager`` can spin up a ``WorkGroup`` for each of the 10 websites, assign 50 workers to each ``WorkGroup``, and send out 500 ``BaseWorkers`` each with 1 task to fill, concurrently.
- to further describe the ``WorkGroupManager``, it is a middle-layer between ``StatefulBook`` and ``BaseGroup``. It ingests ``TaskTracker`` objects from the ``StatefulBook`` object. It is also involved to switch states for ``TaskTracker`` objects, useful to track the task state like completed, in progress, or failed (this last detail is a work-in-progress).

**Persistent Object Storage, Search, and Retreival**

Transistor can be used with the whichever data persistence model you choose to implement. But, it will offer some open-source code in support of the below data model:

1. **object-relational database** using `PostgreSQL <https://www.postgresql.org/>`_ with `newt.db <https://github.com/newtdb/db>`_.

- persist and store your custom python objects containing your web scraped data, directly in a PostgreSQL database, while also converting your python objects to JSON, *automatically* indexing them for super-quick searches, and making it available to be used from within your application or externally.
- leverage PostgreSQL's strong JSON support as a document database while also enabling "ease of working with your data as ordinary objects in memory".
- this is accomplished with `newt.db <https://github.com/newtdb/db>`_ which turns `PostgreSQL <https://www.postgresql.org/>`_ into an object-relational database while leveraging PostgreSQL's well integrated JSON support.
- newt.db is itself a wrapper built over the battle tested `ZODB <http://www.zodb.org/en/latest/>`_ python object database and `RelStorage <https://relstorage.readthedocs.io/en/latest/>`_ which integrates ZODB with PostgreSQL.
- more on newt.db here [1]_ and here [2]_

.. [1] `Why Postgres Should Be Your Document Database (blog.jetbrains.com) <https://blog.jetbrains.com/pycharm/2017/03/interview-with-jim-fulton-for-why-postgres-should-be-your-document-database-webinar/>`_
.. [2] `Newt DB, the amphibious database (newtdb.org) <http://www.newtdb.org/en/latest/>`_.

Quickstart
----------


First, install from pypi:

.. code-block:: python

    pip install transistor

Next, setup Splash, following the Quickstart instructions. Finally, follow the minimal abbreviated Quickstart example ``books_to_scrape`` as detailed below.

This example is explained in more detail in the source code found in the ``examples/books_to_scrape`` folder, including fully implementing object persistence with ``newt.db``.

Quickstart: Setup Splash
-------------------------
Successfully scraping is now a complex affair. Most websites with useuful data will rate limit, inspect headers, present captchas, and use javascript that must be rendered to get the data you want.

This rules out using simple python requests scripts for most serious use. So, setup becomes much more complicated.

To deal with this, we are going to use `Splash <https://github.com/scrapinghub/splash>`_,
"A Lightweight, scriptable browser as a service with an HTTP API".

Transistor also supports the **optional** use of a *smart proxy service* from `scrapinghub <https://scrapinghub.com/>`_ called `Crawlera <https://scrapinghub.com/crawlera>`_.
The crawlera smart proxy service helps us:

- avoid getting our own server IP banned
- enable regional browsing which is important to us, because data can differ per region on the websites we want to scrape, and we are interested in those differences

The minimum monthly cost for the smallest size crawlera `C10` plan is $25 USD/month. This level is useful but can easily be overly restrictive.  The next level up is $100/month.

The easiest way to get setup with Splash is to use `Aquarium <https://github.com/TeamHG-Memex/aquarium>`_ and that is what we are going to do. Using Aquarium requires Docker and Docker Compose.

**Windows Setup**

On Windows, the easiest way to get started with Docker is to use `Chocolately <https://chocolatey.org/>`_ to install docker-for-windows. Using Chocolately requires
`installing Chocolately <https://chocolatey.org/install>`_.

Then, to install Docker-for-windows with Chocolately:

.. code-block:: rest

    C:\> choco install docker-for-windows

You will likely need to restart your Windows box after installing docker-for-windows, even if it doesn't tell you to do so.

**All Platforms**

Install Docker for your platform. For Aquarium, follow the `installation instructions <https://github.com/TeamHG-Memex/aquarium#usage>`_.

After setting up Splash with Aquarium, ensure you set the following environment variables:

.. code-block:: python

    SPLASH_USERNAME = '<username you set during Aquarium setup>'
    SPLASH_PASSWORD = '<password you set during Aquarium setup>'

Finally, to run Splash service, cd to the Aquarium repo on your hard drive, and then run ``docker-compose up`` in your command prompt.

**Troubleshooting Aquarium and Splash service**:

1. Ensure you are in the ``aquarium`` folder when you run the ``docker-compose up`` command.
2. You may have some initial problem if you did not share your hard drive with Docker.
3. Share your hard drive with docker (google is your friend to figure out how to do this).
4. Try to run the ``docker-compose up`` command again.
5. Note, upon computer/server restart, you need to ensure the Splash service is started, either daemonized or with ``docker-compose up``.

At this point, you should have a splash service running in your command prompt.

**Crawlera**

Using crawlera is optional and not required for this ``books_to_scrape`` quickstart.

But, if you want to use Crawlera with Transistor, first, register for the service and buy a subscription at `scrapinghub.com <https://scrapinghub.com>`_.

After registering for Crawlera, create accounts in scrapinghub.com for each region you would like to present a proxied ip address from. For our case, we are setup to handle three regions, ALL for global, China, and USA.

Finally, you should set environment variables on your computer/server with the api key for each region you need, like below:

.. code-block:: python

    CRAWLERA_ALL = '<your crawlera account api key for ALL regions>'
    CRAWLERA_CN = '<your crawlera account api key for China region>'
    CRAWLERA_USA = '<your crawlera account api key for USA region>'

Quickstart: ``books_to_scrape`` example
---------------------------------------

See ``examples/books_to_scrape`` for a fully working example with more detailed notes in the source code.  We'll go through an abbreviated setup here, without many of the longer notes and database/persistence parts that you can find in the ``examples`` folder souce code.

The ``books_to_scrape`` example assumes we have a column of 20 book titles in an excel file, with a column heading *item*.  We plan to scrape the domain ``books.toscrape.com`` to find the book titles. For the book titles we find, we will scrape the sale price and stock status.

First, let's setup a custom scraper by subclassing ``SplashScraper``. This will enable it to use the Splash headless browser.

Next, create a few custom methods to parse the html in the ``self.page`` objects with beautifulsoup4.

.. code-block:: python

    from transistor.scrapers import SplashScraper

    class BooksToScrapeScraper(SplashScraper):
        """
        Given a book title, scrape books.toscrape.com/index.html
        for the book cost and stock status.
        """

        def __init__(self, book_title: str, script=None, **kwargs):
            """
            Create the instance with a few custom attributes and
            set the baseurl
            """
            super().__init__(script=script, **kwargs)
            self.baseurl = 'http://books.toscrape.com/'
            self.book_title = book_title
            self.price = None
            self.stock = None

        def start_http_session(self, url=None, timeout=(3.05, 10.05)):
            """
            Starts the scrape session. Normally, you can just call
            super().start_http_session(). In this case, we also want to start out
            with a call to self._find_title() to kickoff the crawl.
            """
            super().start_http_session(url=url, timeout=timeout)
            return self._find_title()

        # now, define your custom books.toscrape.com scraper logic below

        def _find_title(self):
            """
            Search for the book title in the current page. If it isn't found, crawl
            to the next page.
            """
            if self.page:
                title = self.page.find("a", title=self.book_title)
                if title:
                    return self._find_price_and_stock(title)
                else:
                    return self._crawl()
            return None

        def _next_page(self):
            """
            Find the url to the next page from the pagination link.
            """
            if self.page:
                next_page = self.page.find('li', class_='next').find('a')
                if next_page:
                    if next_page['href'].startswith('catalogue'):
                        return self.baseurl + next_page['href']
                    else:
                        return self.baseurl + '/catalogue/' + next_page['href']
            return None

        def _crawl(self):
            """
            Navigate to the next url page using the SplashScraper.open() method and
            then call find_title again, to see if we found our tasked title.
            """
            if self._next_page():
                self.open(url=self._next_page())
                return self._find_title()
            return print(f'Crawled all pages. Title not found.')

        def _find_price_and_stock(self, title):
            """
            The tasked title has been found and so now find the price and stock and
            assign them to class attributes self.price and self.stock for now.
            """
            price_div = title.find_parent(
                "h3").find_next_sibling(
                'div', class_='product_price')

            self.price = price_div.find('p', class_='price_color').text
            self.stock = price_div.find('p', class_='instock availability').text.translate(
                {ord(c): None for c in '\n\t\r'}).strip()
            print('Found the Title, Price, and Stock.')


Now, let's setup a ``BaseGroup`` object, in which a ``BaseWorker`` object wraps our ``BooksToScrapeScraper``.

This ultimately allows us to scale up the number of ``BooksToScrapeScraper`` objects by an arbitrary amount, using gevent.

Setting up a ``BaseGroup`` is all that is required for the minimal example.

.. code-block:: python

    import gevent
    from transistor import BaseWorker, BaseGroup
    from examples.books_to_scrape.scraper import BooksToScrapeScraper

    class BooksToScrapeGroup(BaseGroup):
    """
    A BaseGroup enables us to organize a Group of Workers from a single BaseWorker.
    Note how, the `BooksToScrapeScraper` is assigned in the `hired_worker` method.
    """

    def hired_worker(self):
        """
        Encapsulate your custom scraper, inside of a Worker object. This will
        eventually allow us to run an arbitrary number of Scrapers in a Group.

        :returns <Worker>, the worker object which will go into a WorkGroup
        """
        worker = BaseWorker(job_id=self.job_id, scraper=BooksToScrapeScraper,
                             http_session={'url': self.url, 'timeout': self.timeout},
                             **self.kwargs)

        # NOTE: assign custom class attrs on your workers here, as needed.  You pretty
        # much always need to assign worker.name here, but you may need others as well.
        # For example, if our scraper logic depended on china=True as a flag directing
        # it to scrape the books.toscrape.com.cn domain, we should set that flag here.

        # worker.china = self.china
        worker.name = self.name

        return worker

A more robust use case will also first subclass the ``BaseWorker`` class. Because, it provides several methods as hooks for data persistence and post-scrape manipulation.

Refer to the full example in the ``examples/books_to_scrape/workgroup.py`` file for an example of customizing ``BaseWorker`` methods to fit your data persistence needs.

So, at this point, we've:

1. Setup a custom scraper ``BooksToScrapeScraper`` by subclassing ``SplashScraper``.
2. Decided not to set up a database or object persistence model just yet, which would require explicitly subclassing the ``BaseWorker`` class and customizing a few methods.
3. Due to #2 above, we can just use the standard ``BaseWorker`` class to encapsulate our custom ``BooksToScrapeScraper`` and get on with our first scrape.
4. We setup a custom ``BooksToScrapeGroup`` by subclassing ``BaseGroup``.

Next, we are ready to setup a ``main.py`` file as an entry point to run our first scrape.

The first thing we need to do is perform some imports.

.. code-block:: python

    #  -*- coding: utf-8 -*-
    # in main.py, monkey patching for gevent must be done first
    from gevent import monkey
    monkey.patch_all()
    # next, import other need objects to launch the scrape job
    from transistor import StatefulBook, WorkGroup
    from examples.books_to_scrape.workgroup import BooksToScrapeGroup
    from examples.books_to_scrape.manager import BooksWorkGroupManager

Second, setup a ``StatefulBook`` which will read the ``book_titles.xlsx`` file and transform the book titles from the spreadsheet "titles" column into task queues for our ``WorkGroups``.

.. code-block:: python

    filepath = 'your/path/to/book_titles.xlsx'
    trackers = ['books.toscrape.com']
    stateful_book = StatefulBook(filepath, trackers, keywords="titles")

Third, setup the ``WorkGroup`` in a list we'll call *groups*. We use a list here because you can setup as many ``WorkGroup`` objects with unique target websites and as many individual workers, as you need:

.. code-block:: python

    groups = [
    WorkGroup(
        class_=BooksToScrapeGroup,
        workers=20,  # this creates 20 scrapers and assigns each a unique book title as a task
        name='books.toscrape.com',
        kwargs={'url': 'http://books.toscrape.com/', 'timeout': (3.0, 20.0)})
    ]

Last, setup the ``WorkGroupManager`` and prepare the file to call the ``manager.main()`` method to start the scrape job:

.. code-block:: python

    # Ensure the pool is marginally larger than the sum of the total number of workers
    # assigned in the list of WorkGroup objects.
    manager = BooksWorkGroupManager(job_id='books_scrape', book=stateful_book, groups=groups, pool=25)

    if __name__ == "__main__":
        manager.main()  # call manager.main() to start the job.

Finally, run ``python main.py`` and then **profit**.

To summarize what we did in ``main.py``:

We setup a ``WorkGroupManager``, wrapped our ``BooksToScrapeGroup`` inside a ``WorkGroup`` and then passed a list called *groups* containing the ``WorkGroup`` to the ``WorkGroupManager``.

- Wrapping the ``BooksToScrapeGroup`` inside a ``WorkGroup`` allows the  ``WorkGroupManager`` to run multiple ``BaseGroup`` objects with different website targets, concurrently.
- In this simple example, we are only scraping ``books.toscrape.com``, but if we wanted to also scrape ``books.toscrape.com.cn``, then we'd setup two ``BaseGroup`` objects and wrap them each in their own ``WorkGroup``. One ``WorkGroup`` for each domain.

NOTE: If you do try to follow the more detailed example  in ``examples/books_to_scrape``, including data persistence with postgresql and newt.db, you may need to set the environment variable:

.. code-block:: python

    TRANSISTOR_DEBUG = 1

Whether or not you actually need to set this ``TRANSISTOR_DEBUG`` environment variable will depend on how you setup your settings.py and newt_db.py files.
If you copy the files verbatim as shown in the ``examples/books_to_scrape`` folder, then you will need to set it.

Directly Using A SplashScraper
--------------------------------

Perhaps you just want to do a quick one-off scrape?

It is possible to just use your custom scraper sublcassed from ``SplashScraper`` directly, without going through all the work to setup a ``StatefulBook``, ``BaseWorker``, ``BaseGroup``, ``WorkGroup``, and ``WorkGroupManager``.

Just fire it up in a python repl like below and ensure the ``start_http_session`` method is run, which can generally be done by setting ``autorun=True``.

.. code-block:: python

    from my_custom_scrapers.component.mousekey import MouseKeyScraper

    ms = MouseKeyScraper(part_number='C1210C106K4RACTU', autorun=True)

After the scrape completes, various methods and attributes from ``SplashScraper`` and ``SplashBrowser`` are available, plus your custom attributes and methods from your own subclassed scraper, are available:

.. code-block:: python

    >>> print(ms.stock())
    '4,000'
    >>> print(ms.pricing())
    '{"1" : "USD $0.379", "10" : "USD $0.349"}'


Database Setup
---------------
Transistor maintainers prefer to use PostgreSQL with newt.db. Below is a quick setup walkthrough.

After you have a valid PostgreSQL installation, you should install newt.db:

.. code-block:: rest

    pip install newt.db

After installation of newt.db you need to provide a URI connection string for newt.db to connect to PostgreSQL. An example setup might use two files for this, with a URI as shown
in ``examples/books_to_scrape/settings.py`` and a second file to setup newt.db as shown in ``examples/books_to_scrape/newt_db.py`` as shown below:

1. ``examples/books_to_scrape/settings.py``

- not recreated here, check the source file

2. ``examples/books_to_scrape/newt_db.py``:

.. code-block:: python

    import os
    import newt.db
    from transistor.settings import DevConfig, ProdConfig, TestConfig
    from transistor.utility.utils import get_debug_flag

    def get_config():
        if 'APPVEYOR' in os.environ:
            return TestConfig
        return DevConfig if get_debug_flag() else ProdConfig

    CONFIG = get_config()
    ndb = newt.db.connection(CONFIG.NEWT_DB_URI)

Next, we need to store our first two python objects in newt.db, which are:

1. A list collection object, so we have a place to store our scrapes.
2. An object to hold our list collection object, so that we can have a list of lists

.. code-block:: python

    from transistor.persistence.newt_db.collections import ScrapeList, ScrapeLists

Now, from your python repl:

.. code-block:: python

    from transistor.newt_db import ndb

    >>> ndb.root.scrapes = ScrapeLists()  # Assigning ScrapeLists() is only required during initial seup. Or else, when/if you change the ScrapeLists() object, for example, to provide more functionality to the class.
    >>> ndb.root.scrapes.add('first-scrape', ScrapeList())  # You will add a new ScrapeList() anytime you need a new list container. Like, every single scrape you save.  See ``save_to_db`` method in ``examples/books_to_scrape/workgroup.py``.
    >>> ndb.commit() # you must explicitly commit() after each change to newt.db.

At this point, you are ready-to-go with newt.db and PostgreSQL.

Later, when you have a scraper object instance, such as ``BooksToScrapeScraper()`` which has finished it's web scrape cycle, it will be stored in the ``ScrapeList()`` named ``first-scrape`` like such:

.. code-block:: python

        >>> ndb.root.scrapes['first-scrape'].add(BooksToScrapeScraper(name="books.toscrape.com", book_title="Soumission"))


More on StatefulBook
--------------------

Practical use requires multiple methods of input and output.  ``StatefulBook`` provides a method for reading an excel file
with one column of search terms, *part numbers* in the below example, which we would like to search and scrape data from multiple websites which sell such components:

.. code-block:: python

    >>> from transistor import StatefulBook

    >>> filepath = '/path/to/your/file.xlsx'
    >>> trackers = ['mousekey.cn', 'mousekey.com', 'digidog.com.cn', 'digidog.com']

This will create four separate task trackers for each of the four websites to search with the part numbers:

.. code-block:: python

    >>> book = StatefulBook(filepath, trackers, keywords="part_numbers")

    >>> book.to_do()

Output:

.. code-block:: python

    deque([<TaskTracker(name=mousekey.cn)>, <TaskTracker(name=mousekey.com)>, <TaskTracker(name=digidog.com.cn)>, <TaskTracker(name=digidog.com)>])

So now, each website we intend to scrape, has it's own task queue.  To work with an individual tracker and see what is in it's individual to_do work queue:

.. code-block:: python

    >>> for tracker in book.to_do():
    >>> if tracker.name == 'mousekey.cn':
    >>>     ms_tracker = tracker

    >>> print(ms_tracker)

        <TaskTracker(name=mousekey.cn)>

    >>> ms_tracker.to_do()

        deque(['050R30-76B', '1050170001', '12401598E4#2A', '525591052', '687710152002', 'ZL38063LDG1'])



Testing
-------------

The easiest way to test your scraper logic is to download the webpage html and then pass in the html file with a test dict.
Below is an example:

.. code-block:: python

    from pathlib import Path
    data_folder = Path("c:/Users/<your-username>/repos/<your-repo-name>/tests/scrapers/component/mousekey")
    file_to_open = data_folder / "mousekey.cn.html"
    f = open(file_to_open, encoding='utf-8')
    page = f.read()
    test_dict = {"_test_true": True, "_test_page_text": page, "_test_status_code": 200, "autostart": True}

    from my_custom_scrapers.component.mousekey import MouseKeyScraper

    ms = MouseKeyScraper(part_number='GRM1555C1H180JA01D', **test_dict)

    assert ms.stock() == '17,090'
    assert ms.pricing() == '{"1": "CNY ¥0.7888", "10": "CNY ¥0.25984", "100": "CNY ¥0.1102", ' \
               '"500": "CNY ¥0.07888", "10,000": "CNY ¥0.03944"}'