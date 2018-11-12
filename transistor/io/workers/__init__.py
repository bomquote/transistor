# -*- coding: utf-8 -*-
"""
transistor.io.workers
~~~~~~~~~~~~
This module implements BaseWorker and BaseGroup classes. Classes which are
nearly fully functional but have a few abstract methods which must be finally
implemented to use, or else, methods which are highly recommended to override
in a sublcass, for customization.

Generally, an end user needs to subclass these classes and then implement
those few methods marked as abstract methods or other methods to work with
a desired data persistence model.

The BaseWorker wraps a scraper object.  The BaseGroup wraps the BaseWorker object
and provides methods to scale the BaseWorker to an arbitrary number of Workers
which can then perform scrape jobs as a coordinated Group.

This module also implements WorkGroup, a namedtuple used mainly for organization
and in composing a list of BaseGroups to pass as a parameter into a manager class.


:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from .workgroup import WorkGroup
from .baseworker import BaseWorker
from .basegroup_abc import BaseGroup
