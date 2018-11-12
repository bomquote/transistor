# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.scraper
~~~~~~~~~~~~
This module implements an example scraper, created by inheriting from
SplashScraper and defining a few custom class methods, using beautifulsoup4
to navigate the html tree. This example does not use Crawlera.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from transistor import SplashScraper


class BooksToScrapeScraper(SplashScraper):
    """
    Given a book title, scrape books.toscrape.com/index.html for
    the book cost and stock status.
    """

    def __init__(self, book_title: str, script=None, **kwargs):
        """
        Create the instance.  Customize it with your book_title which will be the
        target term for your scrape.  Also, in many cases you will want to explicitly
        set the self.baseurl and self.referrer.
        """
        super().__init__(script=script, **kwargs)
        self.baseurl = 'http://books.toscrape.com/'
        self.book_title = book_title
        self.price = None
        self.stock = None

    def start_http_session(self, url=None, timeout=(3.05, 10.05)):
        """It is advised to just set this url parameter here to be filled later during
        startup, with a kwarg. This is useful, for example, if your scraper can handle
        both a .com domain and an alternate geographic site, like com.cn domain. You
        may want to spin up separate WorkGroups per region, and set the domain
        at runtime."""
        super().start_http_session(url=url, timeout=timeout)
        return self._find_title()

    # now, define your scrape logic

    def _find_title(self):
        """
        Search for the book title in the current page.
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
        Navigate to the next url page using the open() method and then
        call find_title again.
        """
        if self._next_page():
            self.open(url=self._next_page())
            return self._find_title()
        return print(f'Crawled all pages. Title not found.')

    def _find_price_and_stock(self, title):
        """
        The title has been found and so now find the price and stock and assign
        them to attributes.
        """
        price_div = title.find_parent(
            "h3").find_next_sibling(
            'div', class_='product_price')

        self.price = price_div.find('p', class_='price_color').text
        self.stock = price_div.find('p', class_='instock availability').text.translate(
            {ord(c): None for c in '\n\t\r'}).strip()
        print('Found the Title, Price, and Stock.')