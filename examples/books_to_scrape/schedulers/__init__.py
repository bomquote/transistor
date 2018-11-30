# -*- coding: utf-8 -*-
"""
transistor.examples.books_to_scrape.schedulers
~~~~~~~~~~~~
This module implements a few different methods of assigning
and managing task ingest/distribution.

The `stateful_book` folder shows an example of ingesting
data from a spreadsheet and passing that to the WorkGroupManager
for worker task assignment.

The `rabbitmq` folder shows an example of using RabbitMQ to
serve as an Exchange. In this case, the scenerio would be
we have a consumer (Worker) awaiting some producer to send
tasks, Exchange routing the tasks to the consumer as needed
in the WorkGroupManager class.

:copyright: Copyright (C) 2018 by BOM Quote Limited
:license: The MIT License, see LICENSE for more details.
~~~~~~~~~~~~
"""