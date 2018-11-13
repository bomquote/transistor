# -*- coding: utf-8 -*-
"""
transistor.appveyor.aquarium
~~~~~~~~~~~~
This module installs aquarium with cookiecutter on appveyor.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""
from delegator import run

if __name__ == "__main__":


    run('cookiecutter gh:TeamHG-Memex/aquarium')
    run('cd ./aquarium')
    c = run('docker-compose up')
    c.expect('folder_name')
    c.send('aquarium')
    c.expect('num_splashes')
    c.send(3)
    c.expect('auth_user')
    c.send('user')
    c.expect('auth_password')
    c.send('userpass')
    c.expect('splash_verbosity')
    c.send(1)
    c.expect('max_timeout')
    c.send(3600)
    c.expect('maxrss_mb')
    c.send(3000)
    c.expect('splash_slots')
    c.send(5)
    c.expect('stats_enabled')
    c.send(1)
    c.expect('stats_auth')
    c.send('admin:adminpass')
    c.expect('tor')
    c.send(1)
    exit(code=0)

