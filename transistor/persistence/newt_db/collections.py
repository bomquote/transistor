# -*- coding: utf-8 -*-
"""
transistor.persistence.newt_db.collections
~~~~~~~~~~~~
This module implements container classes for storing python objects in newt.db.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
import newt.db


class ScrapeList(newt.db.Persistent):
    """
    A list container object to encapsulate worker scrape objects in newt.db after the
    scrapes have been run.
    """

    def __init__(self):
        self.results = newt.db.List()

    def add(self, scraper):
        return self.results.append(scraper)

    def remove(self, scraper):
        return self.results.remove(scraper)


class ScrapeLists(newt.db.Persistent):
    """
    http://www.newtdb.org/en/latest/getting-started.html#collections

    A collections list container object to encapsulate lists of worker scrape
    objects in newt.db after the scrapes have been run.

    Rather than supporting a single scrape list, this object actually supports
    an endless collection of lists of scrape lists.

    We can persist each created scrape job, and the actual scrape objects created
    at job time, as a record of the total scrape.

    This allows us to further develop against the scraped pages, for example,
    to extract more data from the html if we want, at a future date.

    Of course, the page data will get stale over time. Prices change. Stock changes.
    So, can update as needed on a schedule, like with a celery cron job.

    You should only have to setup ScrapeLists() when you change it. It should be included
    in the seed_db script. Then, append a ScrapeList to ScrapeLists() whenever you
    create a new list of scrapes. Finally, add the Scraper() object to
    ScrapeList() after the scrape.

    >>> ndb.root.scrapes = ScrapeLists()  # ONLY DURING SETUP.
    >>> ndb.root.scrapes.add('testing', ScrapeList())  # ANYTIME YOU NEED A NEW LIST
    >>> ndb.root.scrapes['testing'].add(
    ...     MouseKeyScraper(name="mousekey.cn", part_number="TPA2012D2RTJR"))
    >>> ndb.commit() # AFTER EVERY SCRAPE FOR EACH UPDATE.
    """

    def __init__(self):
        self.lists = newt.db.BTree()

    def add(self, name, list):
        """
        Add a list to this list container. Anytime you need a new list.

        ndb.root.scrapes.add('testing', ScrapeList())

        :param name: the list to add
        :param list: the list object like ScrapeList()
        """
        if name in self.lists:
            raise KeyError("There's already a list named", name)
        self.lists[name] = list

    def remove(self, name):
        """
        Remove a list from this list container. Anytime you want to remove crud.

        ndb.root.scrapes.remove('testing')
        :param name: the list to remove
        """
        del self.lists[name]

    def rename(self, current, new):
        """
        Rename a list from a `current` name to a `new` name.

        I think maybe the only way to do this is to move all the items
        into an intermediate list. Then, delete current and create
        new. Then, update the new list.

        :param current: The current list name to be changed
        :param new: The new list name
        :return: get it done (not yet tested)
        """
        intermediate = []
        for item in self.lists[current]:
            intermediate.append(item)
        del self.lists[current]
        self.add(new, ScrapeList())
        for item in intermediate:
            self.lists[new].add(item)

    def __getitem__(self, name):
        """
        This will get a list by name.
        :param name: the list you are trying to retrieve.
        :return: the list
        """
        return self.lists[name]
