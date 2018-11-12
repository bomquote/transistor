# -*- coding: utf-8 -*-
"""
transistor.utility.browsercookie
~~~~~~~~~~~~
The browsercookie module loads cookies used by your web browser into a cookiejar object.
This can be useful if you want to use python to download the same content you see in
the web browser without needing to login.

Originally from browsercookie==0.7.5 (https://pypi.org/project/browsercookie/)
LICENCE: LGPL 2.1, see:
https://bitbucket.org/richardpenman/browsercookie/src/default/LICENSE.txt

But it requires pycrypto and that is hard to build on Windows. Pycryptodome is a
replacement for pycrypto which is more easily compatible with Windows. So, we
require pycryptodome and include the browsercookie library here.

https://bitbucket.org/richardpenman/browsercookie/src/default/__init__.py
https://bitbucket.org/richardpenman/browsercookie/src/default/LICENSE.txt

:copyright: Original browswercookie==0.7.5 are Copyright by it's authors and further
changes or contributions here are Copyright (C) 2018 by BOM Quote Limited.
:license: Original browsercookie==0.7.5 code is LGPL 2.1 and further changes or
contributions here are licensed under The MIT License, see LICENSE for more details.
"""

__doc__ = 'Load browser cookies into a cookiejar'

import os
import sys
import time
import glob

try:
    import cookielib
except ImportError:
    import http.cookiejar as cookielib
from contextlib import contextmanager
import tempfile

try:
    import json
except ImportError:
    import simplejson as json
try:
    import ConfigParser as configparser
except ImportError:
    import configparser

try:
    # should use pysqlite2 to read the cookies.sqlite on Windows
    # otherwise will raise the "sqlite3.DatabaseError: file is encrypted or is not a database" exception
    from pysqlite2 import dbapi2 as sqlite3
except ImportError:
    import sqlite3

import lz4.block
import keyring
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES


class BrowserCookieError(Exception):
    pass


@contextmanager
def create_local_copy(cookie_file):
    """Make a local copy of the sqlite cookie database and return the new filename.
    This is necessary in case this database is still being written to while the user browses
    to avoid sqlite locking errors.
    """
    # check if cookie file exists
    if os.path.exists(cookie_file):
        # copy to random name in tmp folder
        tmp_cookie_file = tempfile.NamedTemporaryFile(suffix='.sqlite').name
        open(tmp_cookie_file, 'wb').write(open(cookie_file, 'rb').read())
        yield tmp_cookie_file
    else:
        raise BrowserCookieError('Can not find cookie file at: ' + cookie_file)

    os.remove(tmp_cookie_file)


class BrowserCookieLoader(object):
    def __init__(self, cookie_files=None):
        cookie_files = cookie_files or self.find_cookie_files()
        self.cookie_files = list(cookie_files)

    def find_cookie_files(self):
        '''Return a list of cookie file locations valid for this loader'''
        raise NotImplementedError

    def get_cookies(self):
        '''Return all cookies (May include duplicates from different sources)'''
        raise NotImplementedError

    def load(self):
        '''Load cookies into a cookiejar'''
        cookie_jar = cookielib.CookieJar()
        for cookie in self.get_cookies():
            cookie_jar.set_cookie(cookie)
        return cookie_jar


class Chrome(BrowserCookieLoader):
    def __str__(self):
        return 'chrome'

    def find_cookie_files(self):
        for pattern in [
            os.path.expanduser(
                '~/Library/Application Support/Google/Chrome/Default/Cookies'),
            os.path.expanduser('~/Library/Application Support/Vivaldi/Default/Cookies'),
            os.path.expanduser('~/.config/chromium/Default/Cookies'),
            os.path.expanduser('~/.config/chromium/Profile */Cookies'),
            os.path.expanduser('~/.config/google-chrome/Default/Cookies'),
            os.path.expanduser('~/.config/google-chrome/Profile */Cookies'),
            os.path.expanduser('~/.config/vivaldi/Default/Cookies'),
            os.path.join(os.getenv('APPDATA', ''),
                         r'..\Local\Google\Chrome\User Data\Default\Cookies'),
            os.path.join(os.getenv('APPDATA', ''),
                         r'..\Local\Vivaldi\User Data\Default\Cookies'),
        ]:
            for result in glob.glob(pattern):
                yield result

    def _darwin_key(self, salt, length):
        """
        return key if sys.platform == 'darwin'
        :return: PBKDF2 instance
        """
        # running Chrome on OSX
        my_pass = keyring.get_password('Chrome Safe Storage', 'Chrome')
        my_pass = my_pass.encode('utf8')
        iterations = 1003
        key = PBKDF2(my_pass, salt, length, iterations)
        return key

    def _linux_key(self, salt, length):
        """
        return key if sys.platform == 'darwin'
        :return: PBKDF2 instance
        """
        # running Chrome on Linux
        my_pass = 'peanuts'.encode('utf8')
        iterations = 1
        key = PBKDF2(my_pass, salt, length, iterations)
        return key

    def _connect_cursor(self, key, tmp_cookie_file):
        con = sqlite3.connect(tmp_cookie_file)
        cur = con.cursor()
        cur.execute('SELECT value FROM meta WHERE key = "version";')
        version = int(cur.fetchone()[0])
        query = 'SELECT host_key, path, is_secure, expires_utc, name, value, encrypted_value FROM cookies;'
        if version < 10:
            query = query.replace('is_', '')
        cur.execute(query)
        for item in cur.fetchall():
            host, path, secure, expires, name = item[:5]
            value = self._decrypt(item[5], item[6], key=key)
            yield create_cookie(host, path, secure, expires, name, value)
        con.close()


    def get_cookies(self):
        salt = b'saltysalt'
        length = 16
        if sys.platform == 'darwin':
            key = self._darwin_key(salt, length)
        elif sys.platform.startswith('linux'):
            key = self._linux_key(salt, length)
        elif sys.platform == 'win32':
            key = None
        else:
            raise BrowserCookieError('Unsupported operating system: ' + sys.platform)

        for cookie_file in self.cookie_files:
            with create_local_copy(cookie_file) as tmp_cookie_file:
                self._connect_cursor(key, tmp_cookie_file)

    def _decrypt(self, value, encrypted_value, key):
        """Decrypt encoded cookies
        """
        if (sys.platform == 'darwin') or sys.platform.startswith('linux'):
            if value or (encrypted_value[:3] != b'v10'):
                return value

            # Encrypted cookies should be prefixed with 'v10' according to the
            # Chromium code. Strip it off.
            encrypted_value = encrypted_value[3:]

            # Strip padding by taking off number indicated by padding
            # eg if last is '\x0e' then ord('\x0e') == 14, so take off 14.
            def clean(x):
                last = x[-1]
                if isinstance(last, int):
                    return x[:-last].decode('utf8')
                else:
                    return x[:-ord(last)].decode('utf8')

            iv = b' ' * 16
            cipher = AES.new(key, AES.MODE_CBC, IV=iv)
            decrypted = cipher.decrypt(encrypted_value)
            return clean(decrypted)
        else:
            # Must be win32 (on win32, all chrome cookies are encrypted)
            try:
                import win32crypt
            except ImportError:
                raise BrowserCookieError(
                    'win32crypt must be available to decrypt Chrome cookie on Windows')
            return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[
                1].decode("utf-8")


class Firefox(BrowserCookieLoader):
    def __str__(self):
        return 'firefox'

    def parse_profile(self, profile):
        cp = configparser.ConfigParser()
        cp.read(profile)
        path = None
        for section in cp.sections():
            try:
                if cp.getboolean(section, 'IsRelative'):
                    path = os.path.dirname(profile) + '/' + cp.get(section, 'Path')
                else:
                    path = cp.get(section, 'Path')
                if cp.has_option(section, 'Default'):
                    return os.path.abspath(os.path.expanduser(path))
            except configparser.NoOptionError:
                pass
        if path:
            return os.path.abspath(os.path.expanduser(path))
        raise BrowserCookieError('No default Firefox profile found')

    def find_default_profile(self):
        if sys.platform == 'darwin':
            return glob.glob(os.path.expanduser(
                '~/Library/Application Support/Firefox/profiles.ini'))
        elif sys.platform.startswith('linux'):
            return glob.glob(os.path.expanduser('~/.mozilla/firefox/profiles.ini'))
        elif sys.platform == 'win32':
            return glob.glob(
                os.path.join(os.getenv('APPDATA', ''), 'Mozilla/Firefox/profiles.ini'))
        else:
            raise BrowserCookieError('Unsupported operating system: ' + sys.platform)

    def find_cookie_files(self):
        profile = self.find_default_profile()
        if not profile:
            raise BrowserCookieError('Could not find default Firefox profile')
        path = self.parse_profile(profile[0])
        if not path:
            raise BrowserCookieError('Could not find path to default Firefox profile')
        cookie_files = glob.glob(os.path.expanduser(path + '/cookies.sqlite'))
        if cookie_files:
            return cookie_files
        else:
            raise BrowserCookieError('Failed to find Firefox cookies')

    def get_cookies(self):
        for cookie_file in self.cookie_files:
            with create_local_copy(cookie_file) as tmp_cookie_file:
                con = sqlite3.connect(tmp_cookie_file)
                cur = con.cursor()
                cur.execute(
                    'select host, path, isSecure, expiry, name, value from moz_cookies')

                for item in cur.fetchall():
                    yield create_cookie(*item)
                con.close()

                # current sessions are saved in sessionstore.js/recovery.json/recovery.jsonlz4
                session_files = (
                os.path.join(os.path.dirname(cookie_file), 'sessionstore.js'),
                os.path.join(os.path.dirname(cookie_file), 'sessionstore-backups',
                             'recovery.json'),
                os.path.join(os.path.dirname(cookie_file), 'sessionstore-backups',
                             'recovery.jsonlz4'))
                for file_path in session_files:
                    if os.path.exists(file_path):
                        if file_path.endswith('4'):
                            try:
                                session_file = open(file_path, 'rb')
                                # skip the first 8 bytes to avoid decompress failure (custom Mozilla header)
                                session_file.seek(8)
                                json_data = json.loads(
                                    lz4.block.decompress(session_file.read()).decode())
                            except IOError as e:
                                print('Could not read file:', str(e))
                            except ValueError as e:
                                print('Error parsing Firefox session file:', str(e))
                        else:
                            try:
                                json_data = json.loads(
                                    open(file_path, 'rb').read().decode('utf-8'))
                            except IOError as e:
                                print('Could not read file:', str(e))
                            except ValueError as e:
                                print('Error parsing firefox session JSON:', str(e))

                if 'json_data' in locals():
                    expires = str(int(time.time()) + 3600 * 24 * 7)
                    for window in json_data.get('windows', []):
                        for cookie in window.get('cookies', []):
                            yield create_cookie(cookie.get('host', ''),
                                                cookie.get('path', ''), False, expires,
                                                cookie.get('name', ''),
                                                cookie.get('value', ''))
                else:
                    print('Could not find any Firefox session files')


def create_cookie(host, path, secure, expires, name, value):
    """Shortcut function to create a cookie
    """
    return cookielib.Cookie(0, name, value, None, False, host, host.startswith('.'),
                            host.startswith('.'), path, True, secure, expires, False,
                            None, None, {})


def chrome(cookie_file=None):
    """Returns a cookiejar of the cookies used by Chrome
    """
    return Chrome(cookie_file).load()


def firefox(cookie_file=None):
    """Returns a cookiejar of the cookies and sessions used by Firefox
    """
    return Firefox(cookie_file).load()


def _get_cookies():
    '''Return all cookies from all browsers'''
    for klass in [Chrome, Firefox]:
        try:
            for cookie in klass().get_cookies():
                yield cookie
        except BrowserCookieError:
            pass


def load():
    """Try to load cookies from all supported browsers and return combined cookiejar
    """
    cookie_jar = cookielib.CookieJar()

    for cookie in sorted(_get_cookies(), key=lambda cookie: cookie.expires):
        cookie_jar.set_cookie(cookie)

    return cookie_jar
