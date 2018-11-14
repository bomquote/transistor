# -*- coding: utf-8 -*-
"""
transistor.browsers.mixin
~~~~~~~~~~~~
This module implements a mixin to for SplashBrowser properties and methods
that will be useful in multiple classes.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
import json


class SplashBrowserMixin:
    """
    Property mixin. It doesn't include raw_content and status. You will need to
    provide that in the receiving class.
    """

    @property
    def encoding(self):
        return 'UTF-8'

    @property
    def ucontent(self):
        print(f'this is self.raw_content -> {self.raw_content}')
        return self.raw_content.decode(self.encoding)

    @property
    def resp_content(self):
        """The lua script is returning application/json"""
        if self._test_true:
            return json.loads(b'{}')
        return json.loads(self.ucontent)

    @property
    def resp_headers(self):
        return self.resp_content.get('headers', None)

    @property
    def har(self):
        """
        Return the har format data.
        https://splash.readthedocs.io/en/stable/scripting-ref.html#splash-har
        """
        return self.resp_content.get('har', None)

    @property
    def png(self):
        """
        Return the png bytestring
        :return:
        """
        return self.resp_content.get('png', None)

    @property
    def endpoint_status(self):
        """This status from the actual endpoint website"""
        return self.resp_content.get('http_status', None)

    @property
    def crawlera_session(self):
        """
        Extract the crawlera session number. This is helpful if we
        receive 503 banned multiple times we should request a new crawlera session
        (tbd how to actually do that).
        """
        if self.resp_headers:
            try:
                return [d['value'] for d in self.resp_headers if
                        'X-Crawlera-Session' in d['name']][0]
            except IndexError:
                # IndexError: list index out of range
                return None
        return None

    @property
    def resp_content_type_header(self):
        """This is the endpoint header from the json response."""
        if self.resp_headers:
            return [d['value'] for d in self.resp_headers if
                    'content-type' in d['name'].lower()][0]
        return None

    @property
    def html(self):
        return self.resp_content.get('html', None)
