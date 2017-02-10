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

    $ pip install --editable .[dev]

    $ crossbar start --config ./wampy/testing/configs/crossbar.config.json

By default a **wampy** ``WebClient`` connects to localhost on port 8080, but this is of course configurable, and is done so on client initialisation.

Now open your preferred text editor and we'll write a few lies of Python constructing a simple WAMP service that takes a decimal number and returns the binary representation of it - fantastic stuff!

Wampy RPC
~~~~~~~~~

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.roles import register_rpc

    In [3]: class BinaryNumberService(Client):

                @register_rpc
                def get_binary_number(self, number):
                    return bin(number)

Save this module somewhere on your Python path and we'll use a ``wampy`` command line interface tool to start the service.

::

    $ wampy run path.to.your.module.including.module_name:BinaryNumberService

For example, running one of the ``wampy`` example applications.

::

    $ wampy run docs.examples.services:DateService --router http://localhost:8080

Okay, no need to write any code: execute this:

::

    $ wampy run docs.examples.services:BinaryNumberService --router http://localhost:8080


Now, open a Python console in a new terminal, allowing the ``BinaryNumberService`` to run uninterupted in your original terminal (but once you're done with it ``Ctrl-C`` is required).

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.peers.routers import Crossbar

    In [3]: with Client(router=Crossbar()) as client:
                result = client.rpc.get_binary_number(number=100)

    In [4]: result
    Out[4]: u'0b1100100'

Note that the `Client` here is connecting to `localhost` and `8080`, but you could also have done:

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.peers.routers import Crossbar

    In [3]: with Client(router=Crossbar()) as client:
                result = client.rpc.get_binary_number(number=100)


Publishing and Subscribing is equally as simple
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To demonstrate, first of all you need a ``Subscriber``. You can either create one yourself in a Python module (as a subclass of a wampy ``Client``, ready to run using ``wampy run....``) or use the example ``Client`` already for you in ``docs.examples.services``.

Here we use the said example service, but all a Subscriber is is a wampy ``Client`` with a method decorated by ``subscribe``. Take a look and see for yourself in the ``examples``, assuming you're running Crossbar.io on your own machine.

Let's start up that example service.

::
    
    $ wampy run docs.examples.services:SubscribingService --router http://localhost:8080

Now we have a service running that subscribes to the topic "foo".

In another terminal, with a wampy virtualenv, you can create a ``Publisher`` - which is no different to any other Client.

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.peers.routers import Crossbar

    In [3]: with Client(router=Crossbar()) as client:
                client.publish(topic="foo", message="spam")

Hopefully you'll see any message you send printed to the screen where the example service is running. You'll also see the meta data that wampy chooses to send.

TLS Support (alpha)
~~~~~~~~~~~~~~~~~~

This feature is only experimental....

When you instantiate your Router, pass in a path to the server certificate along with the host and port that it operates on, e.g.

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.peers.routers import Crossbar

    In [3]: router = Crossbar(
                host="example.com", port=8080, certificate="path.to.certificate")

    In [4]: client = Client(router=router)

Your certificate must also be configured in your Crossbar.io config. For an example see ``crossbar.config.tls.json`` in the `testing` namespace. Also see ``test.test_transports.py``.

There are many undocumented features of this project and lots of new features to add.... Remember, you can help!

If you like this, then Thank You.

Testing
~~~~~~~

wampy provides some ``pytest`` fixtures and helpers for you to run a crossbar server. These are ``router``, ``tls_router`` and ``session_maker``.


Running the tests
~~~~~~~~~~~~~~~~~

::

    $ pip install --editable .[dev]
    $ py.test ./test -v


Build the docs
~~~~~~~~~~~~~~

::

    $ pip install -r docs_requirements.txt
    $ sphinx-build -E -b html ./docs/ ./docs/_build/

.. _Crossbar.io docs: http://crossbar.io/docs/Quick-Start/
.. _ReadTheDocs: http://wampy.readthedocs.io/en/latest/
.. _WAMP Protocol: http://wamp-proto.org/
