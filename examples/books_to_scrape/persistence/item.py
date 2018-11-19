# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.persistence.item
~~~~~~~~~~~~
This module serves as an example for how to create
Item fields. Item objects are simple containers providing
definition about scraped data, for uses like export to excel.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
from transistor import Item, Field

class Book(Item):
    """
    Define the book data fields we want available for export to spreadsheet.
    """
    book_title = Field()
    price = Field()
    stock = Field()
