# """
# transistor.appveyor.check_rabbitmq_connection
# ~~~~~~~~~~~~
# This is a script to check the rabbitmq connection works.
# It is included here to facilitate various test cases in appveyor CI.
#
# :copyright: Copyright (C) 2018 by BOM Quote Limited
# :license: The MIT License, see LICENSE for more details.
# ~~~~~~~~~~~~
# """

from kombu import Connection

# try to establish connection and check its status
try:
    connection = Connection("amqp://guest:guest@localhost:5672//")
    connection.connect()
    if connection.connected:
        print('OK - successfully connected to RabbitMQ')
    else:
        print('FAIL - did not connect to RabbitMQ')
    connection.release()
    exit(0)
except Exception as error:
  print('Error:', error.__class__.__name__)
  exit(1)