wampy
=====

.. pull-quote ::

    WAMP RPC and Pub/Sub for your Python apps and microservices

.. image:: https://travis-ci.org/noisyboiler/wampy.svg?branch=master
    :target: https://travis-ci.org/noisyboiler/wampy

With **wampy** you can quickly and easily create your own WAMP clients, whether this is in a web app, a microservice, a script or just in a Python shell.

WAMP
----

The `WAMP Protocol`_ is a powerful tool for your web applications and microservices - else just for your free time, fun and games!

**WAMP** facilitates communication between independent applications over a common "router". An actor in this process is called a **Peer**, and a **Peer** is either a **Client** or the **Router**.

**WAMP** messaging occurs between **Clients** over the **Router** via **Remote Procedure Call (RPC)** or the **Publish/Subscribe** pattern. As long as your **Client** knows how to connect to a **Router** it does not then need to know anything further about other connected **Peers** beyond a shared string name for an endpoint or topic, i.e. it does not care where a **Client** application is, how many of them there might be, how they might be written or how to identify them. This is more simple than other messaging protocols, such as AMQP for example, where you also need to consider exchanges and queues in order to explicitly connect to actors from your applications.

**WAMP** is most commonly a WebSocket subprotocol (runs on top of WebSocket) that uses JSON as message serialization format. However, the protocol can also run with MsgPack as serialization, run over raw TCP or in fact any message based, bidirectional, reliable transport - but **wampy** (currently) runs over websockets only.

At a high level **WAMP** is a very simple and powerful protocol which will allow you to use buzz words like "real time", "de-coupled" and "scaleable" in no time at all. At a lower level you can quickly get bogged down in the complexities of the transports - but hey, that's what **wampy** is here to abstract away from you! **wampy** tries to provide an intuitive API for your **WAMP** messaging.

For further reading please see some of the popular blog posts on WAMP such as http://tavendo.com/blog/post/is-crossbar-the-future-of-python-web-apps/.

Quickstart: wampy from the command line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Save this module somewhere on your Python path and we'll use a ``wampy`` command line interface tool to start the service.

::

    $ wampy run path.to.your.module.including.module_name:BinaryNumberService

For example, running a ``wampy`` example application.

::

    $ wampy run docs.examples.services:DateService

or

::

    $ wampy run docs.examples.services:DateService --router http://wampy.online:8082

Now, open a Python console in a new terminal, allowing the ``BinaryNumberService`` to run uninterupted in your original terminal (but once you're done with it ``Ctrl-C`` is required).

::

    In [1]: from wampy.peers import WebClient

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
