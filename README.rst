.. -*- mode: rst -*-

|Travis|_ |Python27|_ |Python33|_ |Python34|_ |Python35|_ |Python36|_ 

.. |Travis| image:: https://travis-ci.org/noisyboiler/wampy.svg?branch=master
.. _Travis: https://travis-ci.org/noisyboiler/wampy

.. |Python27| image:: https://img.shields.io/badge/python-2.7-blue.svg
.. _Python27: https://pypi.python.org/pypi/wampy/

.. |Python33| image:: https://img.shields.io/badge/python-3.3-blue.svg
.. _Python33: https://pypi.python.org/pypi/wampy/

.. |Python34| image:: https://img.shields.io/badge/python-3.4-blue.svg
.. _Python34: https://pypi.python.org/pypi/wampy/

.. |Python35| image:: https://img.shields.io/badge/python-3.5-blue.svg
.. _Python35: https://pypi.python.org/pypi/wampy/

.. |Python36| image:: https://img.shields.io/badge/python-3.6-blue.svg
.. _Python36: https://pypi.python.org/pypi/wampy/

wampy
=====

.. pull-quote ::

    WAMP RPC and Pub/Sub for your Python apps and microservices

This is a Python implementation of **WAMP** not requiring Twisted or asyncio, enabling use within classic blocking Python applications. It is a light-weight alternative to `autobahn`_.

With **wampy** you can quickly and easily create your own **WAMP** clients, whether this is in a web app, a microservice, a script or just in a Python shell.

**wampy** tries to provide an intuitive API for your **WAMP** messaging.

WAMP
----

The `WAMP Protocol`_ is a powerful tool for your web applications and microservices - else just for your free time, fun and games!

**WAMP** facilitates communication between independent applications over a common "router". An actor in this process is called a **Peer**, and a **Peer** is either a **Client** or the **Router**.

**WAMP** messaging occurs between **Clients** over the **Router** via **Remote Procedure Call (RPC)** or the **Publish/Subscribe** pattern. As long as your **Client** knows how to connect to a **Router** it does not then need to know anything further about other connected **Peers** beyond a shared string name for an endpoint or **Topic**, i.e. it does not care where another **Client** application is, how many of them there might be, how they might be written or how to identify them. This is more simple than other messaging protocols, such as AMQP for example, where you also need to consider exchanges and queues in order to explicitly connect to other actors from your applications.

**WAMP** is most commonly a WebSocket subprotocol (runs on top of WebSocket) that uses JSON as message serialization format. However, the protocol can also run with MsgPack as serialization, run over raw TCP or in fact any message based, bidirectional, reliable transport - but **wampy** (currently) runs over websockets only.

For further reading please see some of the popular blog posts on WAMP such as http://tavendo.com/blog/post/is-crossbar-the-future-of-python-web-apps/.

Quickstart: wampy from the command line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before any messaging can happen you do need that **Router** I mentioned. Messages are then routed between **Clients** over an administrative domain on the **Router** called a **Realm**.

For the quickest of starts I suggest that you use **Crossbar.io** and start it up on the default host and port, and with the default **realm** and **roles**. See the `Crossbar.io docs`_ for the instructions on this or alternatively run with **wampy's** testing setup.

::

    $ pip install --editable .[dev]

    $ crossbar start --config ./wampy/testing/configs/crossbar.config.ipv4.json

By default a **wampy** client connects to localhost on port 8080, but this is of course configurable, and is done so on client initialisation.

The wampy Client
~~~~~~~~~~~~~~~~

**wampy** was originally written to provide a simple client to send a WAMP message.

When a **wampy** client starts up it will send the **HELLO** message for you and begin a **Session**. Once you have the **Session** you can construct and send a **WAMP** message yourself, if you so choose. But **wampy** has the ``publish`` and ``rpc`` APIs so you don't have to.

But if you did want to do it yourself, here's an example how to...

Given a **Crossbar.io** server running on localhost on port 8080, a **realm** of "realm1", and a remote procedure "foobar", send a **CALL** message with **wampy** as follows:

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.peers.routers import Crossbar

    In [3]: from wampy.messages.call import Call

    In [4]: router = Crossbar(config_path="./crossbar/config.json")

    In [5]: client = Client(router=router)

    In [6]: message = Call(procedure="foobar", args=(), kwargs={})

    In [7]: with client:
                client.send_message(message)

This is quite verbose an unnecessary with the core **wampy** API. With **wampy** you don't actually have to manually craft any messages. And of course, without another **Peer** having registered "foobar" on the same **realm**, this example will achieve little.

In the example, as you leave the context managed function call, the client will send a **GOODBYE** message and your **Session** will end.

The above can essentially be replaced with:

::

    In [X]: client.rpc.foobar(*args, **kwargs)

wampy RPC
~~~~~~~~~

Now open your preferred text editor and we'll write a few lines of Python constructing a simple **WAMP** service that takes a decimal number and returns the binary representation of it - wowzers!

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.roles import callee

    In [3]: class BinaryNumberService(Client):

                @callee
                def get_binary_number(self, number):
                    return bin(number)

Save this module somewhere on your Python path and we'll use a **wampy** command line interface tool to start the service.

::

    $ wampy run path.to.your.module.including.module_name:BinaryNumberService

For example, running one of the **wampy** example applications.

::

    $ wampy run docs.examples.services:DateService --config './path/to/crossbar.config.json'

Okay, no need to write any code: execute this:

::

    $ wampy run docs.examples.services:BinaryNumberService --config './wampy/testing/configs/crossbar.config.ipv4.json'


Now, open a Python console in a new terminal, allowing the ``BinaryNumberService`` to run uninterupted in your original terminal (but once you're done with it ``Ctrl-C`` is required).

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.peers.routers import Crossbar

    In [3]: with Client(router=Crossbar("./crossbar/config.json")) as client:
                result = client.rpc.get_binary_number(number=100)

    In [4]: result
    Out[4]: u'0b1100100'

Publishing and Subscribing is equally as simple
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To demonstrate, first of all you need a **Subscriber**. You can either create one yourself in a Python module (as a subclass of a **wampy** ``Client``, ready to run using ``wampy run....``) or use the example ``Client`` already for you in ``docs.examples.services``.

Here we use the said example service, but all a **Subscriber** is is a **wampy** ``Client`` with a method decorated by ``subscribe``. Take a look and see for yourself in the examples_.

Let's start up that example service.

::
    
    $ wampy run docs.examples.services:SubscribingService --config './wampy/testing/configs/crossbar.config.ipv4.json'

Now we have a service running that subscribes to the topic "foo".

In another terminal, with a **wampy** virtualenv, you can create a **Publisher** - which is no different to any other **wampy** Client.

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.peers.routers import Crossbar

    In [3]: with Client(router=Crossbar("./crossbar/config.json")) as client:
                result = client.publish(topic="foo", message="spam")

Hopefully you'll see any message you send printed to the screen where the example service is running. You'll also see the meta data that **wampy** chooses to send.

TLS/wss Support
~~~~~~~~~~~~~~~

When you instantiate your Router, pass in a path to the server certificate along with the host and port that it operates on, e.g.

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.peers.routers import Crossbar

    In [3]: router = Crossbar('./crossbar/config.json', certificate="path.to.certificate")

Your Router must be configured to use TLS. For an example see the `config`_ used by the test runner along with the `TLS Router`_ setup.

To connect a Client over TLS pass the ``use_tls=True`` parameter on initialisation.

::

    In [4]: client = Client(router=router, use_tls=True)

Note that **Crossbar.io** does not support TLS over IPV6 and you'll need to be executing as root for port 443. All of these choices are made in the Crossbar.io config.

Testing
~~~~~~~

**wampy** provides some ``pytest`` fixtures and helpers for you to run a crossbar server. These are ``router`` and ``session_maker``. 

The router is **Crossbar.io** and will be started and shutdown between each test. It has a default configuration which you can override in your tests by creating a ``config_path`` fixture in your own ``conftest`` - see *wampy's* ``conftest`` for an example. If you require even more control you can import the router itself from ``wampy.peers.routers`` and setup your tests however you need to.

To help you setup your test there are also some helpers that you can execute to wait for async certain actions to perform before you start actually running test code. These are:

::

    # execute with the client you're waiting for as the only argument
    from wampy.testing import wait_for_session
    # e.g. ```wait_for_session(client)```

    # wait for a specific number of registrations on a client
    from wampy.testing import wait_for_registrations
    # e.g. ``wait_for_registrations(client, number_of_registrations=5)

    # wait for a specific number of subscriptions on a client
    from wampy.testing import wait_for_subscriptions
    # e.g. ``wait_for_subscriptions(client, number_of_subscriptions=7)

    # provied a function that raises until the test passes
    from test.helpers import assert_stops_raising
    # e.g. assert_stops_raising(my_func_that_raises_until_condition_met)


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

If you like this project, then Thank You, and you're welcome to get involved.

.. _Crossbar.io docs: http://crossbar.io/docs/Quick-Start/
.. _ReadTheDocs: http://wampy.readthedocs.io/en/latest/
.. _WAMP Protocol: http://wamp-proto.org/
.. _examples: https://github.com/noisyboiler/wampy/blob/master/docs/examples/services.py#L26
.. _config: https://github.com/noisyboiler/wampy/blob/master/wampy/testing/configs/crossbar.config.tls.json
.. _TLS Router: https://github.com/noisyboiler/wampy/blob/master/wampy/testing/pytest_plugin.py#L49
.. _autobahn: http://autobahn.ws/python/
