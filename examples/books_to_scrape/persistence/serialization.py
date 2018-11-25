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
from transistor.persistence import SplashScraperItems, CsvItemExporter


def serialize_price(value):
    """
    A serializer used in BookScraperItems to ensure USD is prefixed on the
    `price` Field, for the data returned in the scrape.
    :param value: the scraped value for the `price` Field
    """
    if value:
        return f"UK {str(value)}"

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
    price = Field()  # the self.price attribute
    stock = Field()  # the self.stock attribute


class BookDataExporter(CsvItemExporter):
    """
    A worker tool to extract the data from the BookScraper object and pass the
    data into BookScraperContainer, a class which can be pickled.

    Define any custom serializers on a per-field basis here, by calling
    self.serialize_field(field, name, value).  See the example below
    for 'price'.
    """

    def __init__(self, scraper, items=BookScraperItems, **kwargs):
        super().__init__(scraper=scraper, items=items, **kwargs)

    def write(self):
        """
        Write your scraper's exported custom data attributes to the
        BookScraperItems class which will be persisted in the database.

        Call super() to also capture attributes built-in from the Base classes.

        Last, ensure you assign the attributes to `self.items` and also finally
        you must return self.items in this method!
        """
        # first call super() to write the built-in Items from BaseItemExporter
        super().write()

        # now, define your custom items
        self.items['book_title'] = self.scraper.book_title
        self.items['stock'] = self.scraper.stock
        # set the value with self.serialize_field(field, name, value) as needed,
        # for example, `serialize_price` below turns '£50.10' into 'UK £50.10'
        # the '£50.10' is the original scraped value from the website stored in
        # self.scraper.price, but we think it is more clear as 'UK £50.10'
        self.items['price'] = self.serialize_field(
            field=Field(serializer=serialize_price),
            name='price',
            value=self.scraper.price)

        # finally, ensure you return self.items
        return self.items

    def export_item(self, item):
        """
        Override to set a globals `_headers_not_written` variable. We must
        do this because we are utilizing multiple Worker objects that are
        each encapsulating a unique class::Exporter instance. While, we are
        writing to the same global csv file. So, to avoid re-writing the header
        on each exporter's write the the csv file, we can refer to a globally
        scoped variable, to write the header on the first write, and then check
        if the header has already been written on the subsequent writes.
        """
        if globals().get('_headers_not_written', True):
            globals()['_headers_not_written'] = False
            self._write_headers_and_set_fields_to_export(item)

        fields = self._get_serialized_fields(item, default_value='',
                                             include_empty=True)
        values = list(self._build_row(x for _, x in fields))

        self.csv_writer.writerow(values)