# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape
~~~~~~~~~~~~
This module implements a full working example for scraping a list of book titles on
the books.toscrape.com website, with the book titles themselves ingested from a
column in the `book_titles.xlsx` workbook.

- scraper.py
    - subclasses SplashScraper to create a customized  BooksToScrapeScraper
    - see SplashScraper in transistor.scrapers.abstract.sc_scraper_abc

- workgroup.py
    - subclasses BaseWorker to create BooksWorker
    - sublcasses BaseGroup to create BooksToScrapeGroup
    - see BaseWorker and BaseGroup in transistor.io.workers.abstract

- manager.py
    - sublasses BaseWorkGroupManager to create BooksWorkGroupManager
    - see BaseWorkGroupManager in transistor.io.managers.manager_abc

- main.py
    - Entry point to run the books_to_scrape example

- settings.py
    - An example application configuration, for database URI's and other attributes

- persistence/serialization.py
    - classes to serialize data from a scrape object in a suitable format for newt.db

- persistence/newt_db.py
    - an example of setting up a newt.db connection, which we name ndb

- persistence/newt_crud.py
    - some crud convenience functions to work with objects in lists stored in newt.db


:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""