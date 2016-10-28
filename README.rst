wampy
=====

.. pull-quote ::

    WAMP RPC and Pub/Sub for your Python apps and microservices

.. image:: https://travis-ci.org/noisyboiler/wampy.svg?branch=master
    :target: https://travis-ci.org/noisyboiler/wampy

With **wampy** you can quickly and easily create your own WAMP clients, whether this is in a web app, a microservice, a script or just in a Python shell.

WAMP
----

The `WAMP Protocol`_ is a powerful tool for your web applications, microservices or free time fun and games.

The **WAMP Protocol** facilitates communication between independent applications over a common "router".

An actor in this process is called a **Peer**.

And a **Peer** is either a **Client** or a **Router**.

WAMP messaging occurs between **Clients** over a **Router** via a **Remote Procedure Call (RPC)** or the **Publish/Subscribe** pattern. As long as your **Client** knows how to connect to a **Router** it does not then need to know anything further about other connected **Peers** beyond a shared string name for an endpoint, i.e. it does not care where a **Client** application is, how many of them there might be, how they might be written or how to identify them. This is unlike other protocols, such as AMQP for example, where you also need to consider exchanges and queues in order to explicitly connect actors from your applications.

WAMP is most commonly a WebSocket subprotocol (runs on top of WebSocket) that uses JSON as message serialization format. However, the protocol can also run with MsgPack as serialization, run over raw TCP or in fact any message based, bidirectional, reliable transport - but **wampy** (currently) runs over websockets only.

At a high level **WAMP** is very simple and powerful protocol which will allow you to use buzz words like "real time", "de-coupled" and "scaleable" in no time at all. At a lower level you can get bogged down in the complexities of hte transports - but hey, that's what **wampy** is here to abstract for you! For further reading please see some of the popular blog posts on WAMP such as http://tavendo.com/blog/post/is-crossbar-the-future-of-python-web-apps/.

Quickstart: wampy from a Python shell
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before any messaging can happen you do need that **Router** I mentioned. Messages are then routed between **Clients** over an administritive domain on the Router called a **Realm**.

For the quickeststart I suggest that you use Crossbar.io and start it up on the default **host** and **port** with the default **realm** and **roles**. See the `Crossbar.io docs`_ for the instructions of this or alternatively run with wampy's testing setup:

::

    $ pip install -r test_requirements.txt

    $ crossbar start --config ./test/crossbar.config.json

By default a **wampy** ``WebClient`` connects to this endpoint, but this is configurable on initialisation for your particular use case.

Now open your preferred text editor and we'll write a few lies of Python constructing a simple WAMP service that takes a decimal number and returns the binary representation of it - fantastic!

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

Now open a Python console in a new terminal, allowing the DateService to run uninterupted in your original terminal.

::

    In [1]: from wampy import WebClient

    In [2]: with WebClient(name="wampy") as client:
                result = client.rpc.get_binary_number(number=100)

    In [3]: result
    Out[3]: u'0b1100100'


Please check out the full documentation at ReadTheDocs_ for more patterns.

Thank you.

Build the docs
~~~~~~~~~~~~~~

::

    $ pip install -r docs_requirements.txt
    $ sphinx-build -E -b html ./docs/ ./docs/_build/

.. _Crossbar.io docs: http://crossbar.io/docs/Quick-Start/
.. _ReadTheDocs: http://wampy.readthedocs.io/en/latest/
.. _WAMP Protocol: http://wamp-proto.org/
