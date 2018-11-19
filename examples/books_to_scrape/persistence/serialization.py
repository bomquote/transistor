# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.persistence.serialization
~~~~~~~~~~~~
This module contains classes to serialize the data from a scrape object after a scrape
in a format that is able to be pickled and persisted in a postgresql db with newt.db.

The attributes in the container object to be saved must match up to the extractors
`extract` and `write` methods.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

import newt.db
from transistor.persistence.newt_db import ScrapedDataExtractor, SplashScraperContainer


class BookScraperContainer(newt.db.Persistent, SplashScraperContainer):
    """
    A class object which will encapsulate the data from the scraper object. It will
    itself be persisted in PostgreSQL and also further serialized to a JSONB field,
    which is automatically indexed for fast search queries.  The caveat is, the data
    encapsulated in this class object must all be pickleable. The main items we deal
    with which are not pickleable are beautifulsoup4 objects.

    Don't try to persist a beautifulsoup4 object. To avoid issues, ensure that the
    result from a beautifulsoup4 object is cast to string. Wrapping it with an str()
    will avoid save issues.
    """

    # -- names of your customized scraper class attributes go here -- #

    book_title = None  # str() # the book_title which we searched
    price = None  # the self.price attribute
    stock = None  # the self.stock attribute

    def __init__(self):
        super().__init__()

    def __repr__(self):
        return f"<BookScraperContainer({self.name, self.book_title})>"


class BookDataExtractor(ScrapedDataExtractor):
    """
    A worker tool to extract the data from the BookScraper object and pass the
    data into BookScraperContainer, a class which can be pickled.
    """

    def __init__(self, scraper, container=BookScraperContainer):
        super().__init__(scraper=scraper, container=container)

    def extract(self):
        """
        Your encapsulate your scraper custom data attributes in this extractor class.

        Call super() to also capture the attributes built-in from the Base classes.
        """
        super().extract()
        self.book_title = self.scraper.book_title
        self.price = self.scraper.price
        self.stock = self.scraper.stock

    def write(self):
        """
        Write your scraper's extracted custom data attributes to the
        BookScraperContainer class which will be persisted in the database.

        Call super() to also capture attributes built-in from the Base classes.

        Last, ensure you assign the attributes to `self.container` and also finally
        you must return self.container in this method!
        """
        super().write()
        self.container.book_title = self.book_title
        self.container.price = self.price
        self.container.stock = self.stock

        return self.container