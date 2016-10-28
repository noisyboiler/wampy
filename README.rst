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

Quickstart: wampy from a Python shell
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before any messaging can happen you need a Router. Messages are then routed between Clients over an administritive domain called a “realm”.

For a quickstart I suggest that you use Crossbar.io and start it up on the default **host** and **port** with the default **realm** and **roles**. See the `Crossbar.io docs`_ for the instructions of this or alternatively run with wampy's testing setup:

::

    $ pip install -r test_requirements.txt

    $ crossbar start --config ./test/crossbar.config.json

By default, a client connects to this endpoint, but this is configurable on initialisation.


Now open your favourite text editor and we'll create a simple service that takes a decimal number and returns the binary representation of it.

::

    from wampy.peers import WebApplication
    from wampy.roles import register_rpc

    class BinaryNumberService(WebApplication):

        @register_rpc
        def get_binary_number(self, number):
            return bin(number)

Save this module somewhere on your Python path and we'll use a ``wampy`` command lime interface tool to start the service.

::

    $ wampy run path.to.your.module.including.module_name:BinaryNumberService

For example, running a ``wampy`` example application.

::

    $ wampy run docs.examples.services:DateService

Now open a Python console.

::

    In [1]: from wampy import WebClient

    In [2]: with WebClient(name="wampy") as client:
                result = client.rpc.get_binary_number(number=100)

    In [3]: result
    Out[3]: u'0b1100100'

Check out the full documentation at ReadTheDocs_.

Build the docs
~~~~~~~~~~~~~~

::

    $ pip install -r docs_requirements.txt
    $ sphinx-build -E -b html ./docs/ ./docs/_build/

.. _Crossbar.io docs: http://crossbar.io/docs/Quick-Start/
.. _ReadTheDocs: http://wampy.readthedocs.io/en/latest/
.. _WAMP Protocol: http://wamp-proto.org/
