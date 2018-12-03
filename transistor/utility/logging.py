# -*- coding: utf-8 -*-
"""
transistor.utility.logging
~~~~~~~~~~~~
This module implements various helper functions for logging.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""

from kombu.log import get_logger


logger = get_logger(__name__)
debug, info, warn, error = logger.debug, logger.info, logger.warn, logger.error