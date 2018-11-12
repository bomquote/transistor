============
Architecture
============

Transistor provides useful layers and objects in the following categories:

.. _Layers & Services:

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
- while it is straightforward to use the current Transistor design to do basic crawling (see ``examples/books_to_scrape/scraper.py`` for an example) the current way to do this with Transistor is always optimal for crawling. So we'll implement modified designs for crawling spiders.
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
