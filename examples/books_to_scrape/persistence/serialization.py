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
from transistor.persistence import SplashScraperItems
from transistor.persistence.loader import ItemLoader


def serialize_price(value):
    """
    A serializer used in BookScraperItems to ensure USD is prefixed on the
    `price` Field, for the data returned in the scrape.
    :param value: the scraped value for the `price` Field
    """
    if value:
        return f"UK {str(value)}"


class BookItems(newt.db.Persistent, SplashScraperItems):
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
    price = Field()  # the self.price attribute
    stock = Field()  # the self.stock attribute


class BookItemsLoader(ItemLoader):

    def write(self):
        """
        Write your scraper's exported custom data attributes to the
        BookScraperItems class which will be persisted in the database.

        Call super() to also capture attributes built-in from the Base classes.

        Last, ensure you assign the attributes to `self.items` and also finally
        you must return self.items in this method!
        """

        # now, define your custom items
        self.items['book_title'] = self.spider.book_title
        self.items['stock'] = self.spider.stock
        # set the value with self.serialize_field(field, name, value) as needed,
        # for example, `serialize_price` below turns '£50.10' into 'UK £50.10'
        # the '£50.10' is the original scraped value from the website stored in
        # self.scraper.price, but we think it is more clear as 'UK £50.10'
        self.items['price'] = self.serialize_field(
            field=Field(serializer=serialize_price),
            name='price',
            value=self.spider.price)

        # call super() to write the built-in Items from BaseItemExporter
        super().write()

        return self.items