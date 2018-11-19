# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.persistence.newt_crud
~~~~~~~~~~~~
This module contains some convenience functions to create, read, update, delete,
objects from newt.db scrape lists.

Be sure to checkout the transistor source files in transistor/persistence/newt_db
and particularly the collections.py file. The ScrapeList and ScrapeLists classes
in that file are examples of containers which must be defined and are ultimately
used to encapsulate your objects stored in PostgreSQL with newt.db.

The containers in transistor/persistence/newt_db/collections.py will be updated
periodically and further developed, as we find a need. So, we will maintain
them in the core Transistor library.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

# you must set ndb like `from .newt_db import ndb`
ndb = None


def get_job_ids(ndb):
    """
    Return a simple list of all the current lists in scrape_lists.lists

    :param ndb: an instance of ndb. Please refer to
    examples/books_to_scrape/persistence/newt_db.py for an example.

    :return: list() of str(list_name)
    """
    return [list for list in ndb.root.scrapes.lists]


def get_job_results(ndb, job_id:str=None):
    """
    Return a list of results of a job_id.

    :param ndb: an instance of ndb. Please refer to
    examples/books_to_scrape/persistence/newt_db.py for an example.

    :param job_id: the `job_id` assigned to the WorkerManager during the scrape. This
    is then used as the list name to save resulting objects to in newt.db.

    :return: [<SplashScraperData(('books.toscrape.com', 'soulsearcher'))>, ...]
    """
    return ndb.root.scrapes.lists[job_id].results


def delete_job(ndb, job_id:str=None):
    """
    CAUTION: there is no going back from a delete.

    So if you have a list `ndb.root.scrape_lists.lists['job_id_1'] with a
    6 hour run of 50 scrape jobs in there. This will delete it entirely.

    So you may want to save the scrapes you want to keep. Move them to
    another list.

    In referring to `job_name` it is just an alias for a newt scrapes.list name.

    When a WorkerManager is initiated with a `job_name`, it will
    either create a new scrapes.list name or else just add all the
    jobs to the existing list if it matches the `job_name`.

    It turns out, deleting in newt is not straightforward.  You can remove
    the class but the data remains in postgresql until the database is `packed`.

    `Packing` the database should be done periodically in production,
    based on a celery task cron job or similar method.  To pack the database,
    all you need to do is run ndb.db().pack(days=<int()>). Usually, I use 3 days,
    ndb.db().pack(days=3).

    :param ndb: an instance of ndb. Please refer to
    examples/books_to_scrape/persistence/newt_db.py for an example.

    :return: a print statement
    """
    try:
        del ndb.root.scrapes.lists[job_id]
        ndb.commit()
        return print(f'Deleted {job_id}')
    except KeyError:
        print(f'Job-ID {job_id} does not exist.')


def update_newt_container(ndb):
    """
    Update the newt.db container containing the newt.db persisted objects.

    NOTE: IF YOU DO THIS WRONG IT CAN BE COMPLETELY DESTRUCTIVE for objects in the
    container.If you need to keep objects in the containers, you should copy the objects
    into another intermediate list or take some similar precautions. Then, you can move
    them back into the new container after it has been upgraded.

    :param ndb: an instance of ndb. Please refer to
    examples/books_to_scrape/persistence/newt_db.py for an example.

    :return:
    """
    raise NotImplementedError