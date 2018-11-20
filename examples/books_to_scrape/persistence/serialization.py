# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.persistence.serialization
~~~~~~~~~~~~
This module contains classes to serialize the data from a scrape object
after a scrape in a format that is able to be pickled and persisted in
a postgresql database with newt.db. and also exported to excel.

The attributes in the container object to be saved must match up to the
exporter class `write` methods.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

import newt.db
from transistor.persistence.item import Field
from transistor.persistence import BaseItemExporter, SplashScraperItems


def serialize_price(value):
    """
    A serializer used in BookScraperItems to ensure USD is prefixed on the
    `price` Field, for the data returned in the scrape.
    :param value: the scraped value for the `price` Field
    """
    return f'UK {str(value)}'


class BookScraperItems(newt.db.Persistent, SplashScraperItems):
    """
    A class object which will encapsulate the data from the scraper
    object. It will itself be persisted in PostgreSQL and also
    further serialized to a JSONB field, which is automatically
    indexed for fast search queries.  The caveat is, the data encapsulated
    in this class object must all be pickleable. The main items we deal
    with which are not pickleable are beautifulsoup4 objects.

    Don't try to persist a beautifulsoup4 object in postgres with newt.db.
    To avoid issues, ensure that the result from a beautifulsoup4 object
    is cast to string. Wrapping it with str() will avoid issues.
    """

    # -- names of your customized scraper class attributes go here -- #

    book_title = Field()  # str() # the book_title which we searched
    price = Field(serializer=serialize_price)  # the self.price attribute
    stock = Field()  # the self.stock attribute


class BookDataExporter(BaseItemExporter):
    """
    A worker tool to extract the data from the BookScraper object and pass the
    data into BookScraperContainer, a class which can be pickled.
    """

    def __init__(self, scraper, items=BookScraperItems):
        super().__init__(scraper=scraper, items=items)

    def write(self):
        """
        Write your scraper's exported custom data attributes to the
        BookScraperItems class which will be persisted in the database.

        Call super() to also capture attributes built-in from the Base classes.

        Last, ensure you assign the attributes to `self.items` and also finally
        you must return self.items in this method!
        """
        super().write()
        self.items['book_title'] = self.scraper.book_title
        self.items['price'] = self.serialize_field(
            field=Field(serializer=serialize_price),
            name='price',
            value=self.scraper.price)
        self.items['stock'] = self.scraper.stock

        return self.items