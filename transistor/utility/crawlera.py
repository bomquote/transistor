# -*- coding: utf-8 -*-
"""
transistor.utility.crawlera
~~~~~~~~~~~~
This module implements various helper functions for working with the
scrapinghub.com Crawlera 'smart proxy' service.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
import os
import json
import requests
import gevent
from transistor.exceptions import Unauthorized

# If you use crawlera, set an environment variable with a comma separated
# string of regions, which must already be setup at the scrapinghub.com website.
# The environment variable should be formatted similar to below:
# CRAWLERA_REGIONS = CRAWLERA_ALL,CRAWLERA_USA,CRAWLERA_CN

CRAWLERA_REGIONS = os.environ.get('CRAWLERA_REGIONS').split(',')


def get_crawlera_sessions(region:str):
    """
    Get all the sessions in region.  Thanks to the awesome tool at
     https://curl.trillworks.com/ to help get this figured out quickly.

    :param region: First, you must have environment variables setup for any Crawlera
    region you have created, in the scrapinghub.com website.
    :return: A python-requests response object. You should use this function like:
    response = get_crawlera_sessions(YOUR_REGION).content

    """
    auth = None
    if region in CRAWLERA_REGIONS:
        auth = os.environ.get(region, None)

    response = requests.get(
        'http://proxy.crawlera.com:8010/sessions',
        auth=(f'{auth}', ''))

    return response


def delete_crawlera_sessions(region:str):
    """
    Delete ALL the sessions in a region. This may or may not be what you want.
    :param region: A region name that matches your environment variable.
    :return: list(Response()), a list of python request response objects.
    """
    import requests
    auth = None
    if region in CRAWLERA_REGIONS:
        auth = os.environ.get(region, None)

    sessions = get_crawlera_sessions(region)
    if sessions.status_code == 401:
        raise Unauthorized("""You probably supplied the wrong credentials.""")

    sessions = sessions.content.decode('utf-8')

    keys = None
    if sessions:
        sessions = json.loads(sessions)
        keys = [key for key in sessions.keys()]

    def fetch(key):
        response = requests.delete(f'http://proxy.crawlera.com:8010/sessions/{key}',
                                auth=(f'{auth}', ''))
        return response

    if keys:
        threads = [gevent.spawn(fetch, key) for key in keys]
        gevent.joinall(threads)
    try:
        return f'Deleted {len(threads)} sessions in region {region}.'
    except UnboundLocalError:
        return f'No sessions to delete in region {region}.'
