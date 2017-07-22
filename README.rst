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

*[whomp-ee]*

.. pull-quote ::

    WAMP RPC and Pub/Sub for your Python apps and microservices

This is a Python implementation of `WAMP`_ not requiring `Twisted`_ or asyncio, enabling use within classic blocking Python applications. It is a light-weight alternative to `autobahn`_.

With **wampy** you can quickly and easily create your own **WAMP** clients, whether this is in a web app, a microservice, a script or just in a Python shell.

**wampy** tries to provide an intuitive API for your **WAMP** messaging.

See `ReadTheDocs`_ for more detailed documentation.

wampy features
~~~~~~~~~~~~~~

- Remote Procedure Calls over websockets
- Publish and Subscribe over websockets
- Client Authentication
- Transport Layer Security
- Pytest fixtures to use when testing your projects
- nameko_ integration with nameko_wamp_

Quickstart: wampy from the command line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before any messaging can happen you need a **Router**. Messages are then routed between **Clients** over an administrative domain on the **Router** called a **Realm**.

For the quickest of starts I suggest that you use **Crossbar.io** and start it up on the default host and port, and with the default **realm** and **roles**. See the `Crossbar.io docs`_ for the instructions on this or alternatively run with **wampy's** testing setup.

::

    $ pip install --editable .[dev]

    $ crossbar start --config ./wampy/testing/configs/crossbar.json

wampy RPC
~~~~~~~~~

Now open your preferred text editor and we'll write a few lines of Python constructing a simple **WAMP** service that takes a decimal number and returns the binary representation of it - wowzers!

::

    from wampy.peers.clients import Client
    from wampy.roles import callee

    class BinaryNumberService(Client):

        @callee
        def get_binary_number(self, number):
            return bin(number)

Save this module somewhere on your Python path and we'll use a **wampy** command line interface tool to start the service.

::

    $ wampy run path.to.your.module.including.module_name:BinaryNumberService

For example, running one of the **wampy** example applications against the Router suggested previously:

::

    $ wampy run docs.examples.services:DateService --config ./wampy/testing/configs/crossbar.json

Actually - no need to panic! The ``BinaryNumberService`` example already exists in the **wampy** examples so put that text editor away if you like. Just execute from the command line:

::

    $ wampy run docs.examples.services:BinaryNumberService --config ./wampy/testing/configs/crossbar.json


Now, open a Python console in a new terminal, allowing the ``BinaryNumberService`` to run uninterupted in your original terminal (but once you're done with it ``Ctrl-C`` is required).

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.peers.routers import Crossbar

    In [3]: router = Crossbar(config_path='./wampy/testing/configs/crossbar.json')

    In [4]: with Client(router=router) as client:
                result = client.rpc.get_binary_number(number=100)

    In [5]: result
    Out[5]: u'0b1100100'

Note here that a ``Client`` takes a ``router`` argument which defaults to Crossbar. Crossbar then defaults to ``realm1`` on ``localhost:8080``. To use different values you'll need to configure and pass in the router object to the client yourself. This isn't hard, but when you're developing locally these defaults are there to help you get up and running quickly.

In fact, the ``router`` was just there in this example to make it clear that a ``Client`` takes a ``router`` parameter. Developing locally, this is all you need:

::

    In [1]: from wampy.peers.clients import Client

    In [2]: with Client() as client:
                result = client.rpc.get_binary_number(number=100)


wampy RPC for Crossbar.io
~~~~~~~~~~~~~~~~~~~~~~~~~

The RPC pattern above was inspired by the nameko_ project, but this pattern may not feel intuitive for those familiar with **Crossbar.io**, the primary Router used by **wampy**.

For this reason there also exists the ``CallProxy`` object which implements the ``call`` API by more loosely wrapping **wampy's** ``Call`` Message. In this pattern, applications and their endpoints are identified by dot delimented strings rather than a single API name, e.g.

::

    "com.example.endpoint"

Just like the ``rpc`` API, the ``call`` API is directly available on every **wampy** client. Lets look at the two examples side by side.

::

    >>> client.rpc.get_foo_bar(eggs, foo=bar, spam=ham)
    >>> client.call("get_foo_bar", eggs, foo=bar, spam=ham)

Noted these are very similar and achieve the same, but the intention here is for the ``call`` API to behave more like a classic **Crossbar.io** application and the ``rpc`` to be used in nameko_wamp_.

The ``call`` API however does allow calls of the form...

::

    >>> client.call("com.myapp.foo.bar", eggs, foo=bar, spam=ham) 

...which you will not be able to do with the ``rpc`` API.


Publishing and Subscribing is equally as simple
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To demonstrate, first of all you need a **Subscriber**. You can either create one yourself in a Python module (as a subclass of a **wampy** ``Client``) or use the example ``Client`` already for you in ``docs.examples.services``.

Here we use the said example service, but all a **Subscriber** is is a **wampy** ``Client`` with a method decorated by ``subscribe``. Take a look and see for yourself in the examples_.

Let's start up that example service.

::
    
    $ wampy run docs.examples.services:SubscribingService --config './wampy/testing/configs/crossbar.config.ipv4.json'

Now we have a service running that subscribes to the topic "foo".

In another terminal, with a **wampy** virtualenv, you can create a **Publisher** - which is no different to any other **wampy** Client.

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.peers.routers import Crossbar

    In [3]: with Client(router=Crossbar()) as client:
                result = client.publish(topic="foo", message="spam")

Hopefully you'll see any message you send printed to the screen where the example service is running. You'll also see the meta data that **wampy** chooses to send.

See `ReadTheDocs`_ for more detailed documentation.


Running the tests
~~~~~~~~~~~~~~~~~

::

    $ pip install --editable .[dev]
    $ py.test ./test -v


Build the docs
~~~~~~~~~~~~~~

::

    $ pip install -r rtd_requirements.txt
    $ sphinx-build -E -b html ./docs/ ./docs/_build/

If you like this project, then Thank You, and you're welcome to get involved.

.. _Crossbar.io docs: http://crossbar.io/docs/Quick-Start/
.. _ReadTheDocs: http://wampy.readthedocs.io/en/latest/
.. _WAMP Protocol: http://wamp-proto.org/
.. _examples: https://github.com/noisyboiler/wampy/blob/master/docs/examples/services.py#L26
.. _autobahn: http://autobahn.ws/python/
.. _nameko: https://github.com/nameko
.. _nameko_wamp: https://github.com/noisyboiler/nameko-wamp
.. _nameko: https://github.com/nameko/nameko
.. _Twisted: https://twistedmatrix.com/trac/
.. _WAMP: http://wamp-proto.org/static/rfc/draft-oberstet-hybi-crossbar-wamp.html
