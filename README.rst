wampy
=====

.. pull-quote ::

    WAMP RPC and Pub/Sub for your Python apps and microservices

.. image:: https://travis-ci.org/noisyboiler/wampy.svg?branch=master
    :target: https://travis-ci.org/noisyboiler/wampy

wampy is a WAMP client that you can use in your web apps, microservices or just in a python shell.

WAMP
----

The `WAMP Protocol`_ connects Clients via RPC or Pub/Sub over a Router.

WAMP is most commonly a WebSocket subprotocol (runs on top of WebSocket) that uses JSON as message serialization format. However, the protocol can also run with MsgPack as serialization, run over raw TCP or in fact any message based, bidirectional, reliable transport - but **wampy** runs over websockets only.

With **wampy** you can quickly and easily create your own WAMP clients, whether this is in a web app, a microservice, a script or just in a Python shell.

Quickstart: wampy from a Python shell
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before any messaging can happen you need a Router. Messages are then routed between Clients over an administritive domain called a “realm”.

For a quickstart I suggest that you use Crossbar.io and start it up on the default **host** and **port** with the default **realm** and **roles**. See the `Crossbar.io docs`_ for the instructions of this or alternatively run with wampy's testing setup:

::

    $ pip install -r test_requirements.txt

    $ crossbar start --config ./test/crossbar.config.json

By default, a client connects to this endpoint, but this is configurable on initialisation.

Now open a Python console and we'll create a simple service that takes a decimal number and returns the binary representation of it.

::

    In [1]: from wampy.peers import WebApplication

    In [2]: from wampy.roles.callee import rpc

    In [3]: class BinaryNumberService(WebApplication):

                @rpc
                def get_binary_number(self, number):
                    return bin(number)

    In [4]: service = BinaryNumberService(name="Binary Number Service")

The intended usage of a wampy client is as a context manager which will handle the websocket connection for you, but for demonstration purposes we'll explicitly start and stop the service.

::

    In [5]: service.start()

    In [6]: service.session.id
    Out[6]: 3941615218422338

    In [7]: service.registration_map['get_binary_number']
    Out[7]: 8205738934160840

Now open another Python shell.

::

    In [1]: from wampy import WebClient

    In [2]: with WebClient(name="wampy") as client:
                result = client.rpc.get_binary_number(number=100)

    In [3]: result
    Out[3]: u'0b1100100'

If you don’t context-manage your client, then you do have to explicitly call ``stop`` in order to gracefully disassociate yourself from the router, but also to tidy up the green threads and connections.

::

    In [8]: client.stop()

For further documentation see ReadTheDocs_.

::

    exit()

Read The Docs
~~~~~~~~~~~~~

Check out the full documentation at ReadTheDocs_.

Build the docs
~~~~~~~~~~~~~~

::

    $ pip install -r docs_requirements.txt
    $ sphinx-build -E -b html ./docs/ ./docs/_build/

.. _Crossbar.io docs: http://crossbar.io/docs/Quick-Start/
.. _ReadTheDocs: http://wampy.readthedocs.io/en/latest/
.. _WAMP Protocol: http://wamp-proto.org/
