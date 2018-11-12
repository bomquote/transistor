# -*- coding: utf-8 -*-
"""
transistor.examples.cny_exchange_rate
~~~~~~~~~~~~
This module implements a basic mechanicalsoup.StatefulBrowser web scrape example.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from mechanicalsoup import StatefulBrowser


def get_current_usd_to_cny():
    """
    Get the current China mainland bank transfer buying rate for USD to CNY.

    Casting returned objects to string can ensure they do not inadvertently contain
    a BS4 object, which presents difficulties in pickling which can be hard to debug.
    If you do use newt.db, scrape objects can be tested with newt.db.jsonpickle
    `dumps` function, to ensure that the object can be both pickled and also
    serialized to json by newt.db and indexed/saved in a PostgreSQL jsonb field.

    :return: str(): rate in CNY, str(): time string
    """
    browser = StatefulBrowser()
    browser.open('http://www.boc.cn/sourcedb/whpj/enindex.html')
    trs = browser.get_current_page().find_all("tr")
    cells = []
    for tr in trs:
        if tr.td:
            if 'USD' in tr.td.text:
                usd_row = tr.td.next_siblings
                if usd_row:
                    for cell in usd_row:
                        if '\n' not in cell:
                            cells.append(cell)
    rate = cells[0].text
    time = cells[5].text
    time = time.split()
    time = time[0] + ' ' + time[1]
    return str(rate), str(time)