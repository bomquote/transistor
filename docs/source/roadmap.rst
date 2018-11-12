---------------
Goals & Roadmap
---------------
1. Enable scraping targeted data from a wide range of websites including sites rendered with Javascript.
2. Navigate websites which present logins, custom forms, and other blockers to data collection, like captchas.
3. Provide asynchronous I/O for task execution, using `gevent <https://github.com/gevent/gevent>`_.
4. Easily integrate within a web app like `Flask <https://github.com/pallets/flask>`_, `Django <https://github.com/django/django>`_ , or other python based `web frameworks <https://github.com/vinta/awesome-python#web-frameworks>`_.
5. Provide spreadsheet based data ingest and export options, like import a list of search terms from excel, ods, csv, and export data to each as well.
6. Utilize quick and easy integrated task queues which can be automatically filled with data search terms by a simple spreadsheet import.
7. Able to integrate with more robust task queues like `Celery <https://github.com/celery/celery>`_ and also interact with `rabbitmq <https://www.rabbitmq.com/>`_ and `redis <https://redis.io/>`_ as needed.
8. Provide hooks for users to persist data via any method they choose, while also supporting our own opinionated choice which is a `PostgreSQL <https://www.postgresql.org/>`_ database along with `newt.db <https://github.com/newtdb/db>`_.
9. Contain useful abstractions, classes, and interfaces for scraping and crawling with machine learning assistance (wip, timeline tbd).
10. Further support data science use cases of the persisted data, where convenient and useful for us to provide in this library (wip, timeline tbd).
11. Provide a command line interface (low priority wip, timeline tbd).

