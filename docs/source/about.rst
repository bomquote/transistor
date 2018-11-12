
What is Transistor?
~~~~~~~~~~~~~~~~~~~

The web is full of data. Transistor is a lightweight framework for collecting, storing,
and using targeted data from structured web pages.

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
