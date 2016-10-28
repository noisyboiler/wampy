wampy
=====

.. pull-quote ::

    WAMP RPC and Pub/Sub for your Python apps and microservices

.. image:: https://travis-ci.org/noisyboiler/wampy.svg?branch=master
    :target: https://travis-ci.org/noisyboiler/wampy

With **wampy** you can quickly and easily create your own WAMP clients, whether this is in a web app, a microservice, a script or just in a Python shell.

WAMP
----

The `WAMP Protocol`_ connects Clients via RPC or Pub/Sub over a Router.

WAMP is most commonly a WebSocket subprotocol (runs on top of WebSocket) that uses JSON as message serialization format. However, the protocol can also run with MsgPack as serialization, run over raw TCP or in fact any message based, bidirectional, reliable transport - but **wampy** runs over websockets only.

.. include :: ./docs/quickstart.rst

Check out the full documentation at ReadTheDocs_.

Build the docs
~~~~~~~~~~~~~~

::

    $ pip install -r docs_requirements.txt
    $ sphinx-build -E -b html ./docs/ ./docs/_build/

.. _Crossbar.io docs: http://crossbar.io/docs/Quick-Start/
.. _ReadTheDocs: http://wampy.readthedocs.io/en/latest/
.. _WAMP Protocol: http://wamp-proto.org/
