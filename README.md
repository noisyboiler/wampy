![Travis](https://travis-ci.org/noisyboiler/wampy.svg?branch=master)
![Python35](https://img.shields.io/badge/python-3.5-blue.svg)
![Python36](https://img.shields.io/badge/python-3.6-blue.svg)
![Python37](https://img.shields.io/badge/python-3.7.3-blue.svg)
![Python38](https://img.shields.io/badge/python-3.8-blue.svg)

![image](https://coveralls.io/repos/github/noisyboiler/wampy/badge.svg?branch=master)

wampy
=====

*[whomp-ee]*

For a background as to what WAMP is, please see
[here](https://medium.com/@noisyboiler/the-web-application-messaging-protocol-d8efe95aeb67).

This is a Python implementation of
[WAMP](http://wamp-proto.org/static/rfc/draft-oberstet-hybi-crossbar-wamp.html)
using [Gevent](http://www.gevent.org/), but you can also configure
**wampy** to use [eventlet](http://eventlet.net/), if that is how your
application does async. **Wampy** is is a light-weight alternative to
[autobahn](https://github.com/crossbario/autobahn-python).

With **wampy**, you can quickly and easily create your own **WAMP**
clients, whether this is in a web app, a microservice, a script or just
in a Python shell. You can integrate **wampy** into your existing
applications without having to re-write or re-design anything.

**wampy** tries to provide an intuitive API for your **WAMP** messaging.

See [ReadTheDocs](http://wampy.readthedocs.io/en/latest/) for more
detailed documentation, but the README here is detailed enough to get
going.

wampy features
--------------

-   Remote Procedure Calls over websockets
-   Publish and Subscribe over websockets
-   Open Source and Open *Thoughts* - see
    [internals](https://github.com/noisyboiler/wampy/wiki/Internal-Architecture)
    and then the entire WIKI
-   Use **wampy** as a microservice/app, or in your Flask or nameko
    apps, or in scripts.... or just in a Python shell!
-   Client Authentication (Ticket and WCA)
-   Transport Layer Security
-   CLI for easy and rapid development
-   Pytest fixtures to use when testing your projects, including a
    Crossbar.io fixture that tears down between each test
-   [nameko](https://github.com/nameko) integration with
    [namekowwamp](https://github.com/noisyboiler/nameko-wamp)
-   [Flask](https://github.com/pallets/flask) integration with
    [flaskwwamp](https://github.com/noisyboiler/flask-wamp)
-   Compatible with gevent, eventlet and asyncio
-   Alpha features (see below)

QuickStart - Connect and Go!
----------------------------

If you've already got access to a running **Router** which has other
**Peers** connected, then stay here. If not, jump to the next section.
If you're still here...

    pip install wampy

...and then open a Python shell.

The example here assumes a **Peer** connected to a **Router** on
`localhost`, port `8080`, that has registered a remote procedure called
`get_foobar`, and you want to *call* that procedure.

    from wampy.peers import Client

    with Client() as client:
        response = client.rpc.get_foobar()

    # do something with the response here

The same example here, but the **Router** is on a *remote* host.

    from wampy.peers import Client

    with Client(url="ws://example.com:8080") as client:
        response = client.rpc.get_foobar()

    # do something with the response here

The WAMP Session is "context managed", meaning it begins as you enter,
and ends as you exit the scope of the client instance.

See [ReadTheDocs](http://wampy.readthedocs.io/en/latest/) for much more
detail on this.

Running and Calling a wampy Application
---------------------------------------

Before any messaging can happen you need a **Router**. Messages are then
routed between **Clients** over an administrative domain on the
**Router** called a **Realm**.

For the quickest of starts I suggest that you use **Crossbar.io** and
start it up on the default host and port, and with the default **realm**
and **roles**. See the [Crossbar.io
docs](http://crossbar.io/docs/Quick-Start/) for the instructions on this
or alternatively run with **wampy's** testing setup.

Note, if you already have Crossbar installed and running you do *not*
need these steps, because the dev requirements also include Crossbar.

    $ make dev-install

    $ crossbar start --config ./wampy/testing/configs/crossbar.json

wampy RPC
---------

Now open your preferred text editor and we'll write a few lines of
Python constructing a simple **WAMP** service that takes a decimal
number and returns the binary representation of it - wowzers!

    from wampy.peers.clients import Client
    from wampy.roles import callee

    class BinaryNumberService(Client):

        @callee
        def get_binary_number(self, number):
            return bin(number)

Save this module somewhere on your Python path and we'll use a **wampy**
command line interface tool to start the service.

    $ wampy run path.to.your.module.including.module_name:BinaryNumberService

For example, running one of the **wampy** example applications against
the Router suggested previously:

    $ wampy run docs.examples.services:DateService --config ./wampy/testing/configs/crossbar.json

Actually - no need to panic! The `BinaryNumberService` example already
exists in the **wampy** examples so put that text editor away if you
like. Just execute from the command line:

    $ wampy run docs.examples.services:BinaryNumberService --config ./wampy/testing/configs/crossbar.json

Now, open a Python console in a new terminal, allowing the
`BinaryNumberService` to run uninterupted in your original terminal (but
once you're done with it `Ctrl-C` is required).

    In [1]: from wampy.peers.clients import Client

    In [2]: with Client(url="ws://localhost:8080") as client:
                result = client.rpc.get_binary_number(number=100)

    In [3]: result
    Out[3]: u'0b1100100'

wampy RPC for Crossbar.io
-------------------------

The RPC pattern above was inspired by the
[nameko](https://github.com/nameko) project, but this pattern may not
feel intuitive for those familiar with **Crossbar.io**, the primary
Router used by **wampy**.

For this reason there also exists the `CallProxy` object which
implements the `call` API by more loosely wrapping **wampy's** `Call`
Message. In this pattern, applications and their endpoints are
identified by dot delimented strings rather than a single API name, e.g.

    "com.example.endpoint"

Just like the `rpc` API, the `call` API is directly available on every
**wampy** client. Lets look at the two examples side by side.

    >>> client.rpc.get_foo_bar(eggs, foo=bar, spam=ham)
    >>> client.call("get_foo_bar", eggs, foo=bar, spam=ham)

Noted these are very similar and achieve the same, but the intention
here is for the `call` API to behave more like a classic **Crossbar.io**
application and the `rpc` to be used in
[namekowwamp](https://github.com/noisyboiler/nameko-wamp).

The `call` API however does allow calls of the form...

    >>> client.call("com.myapp.foo.bar", eggs, foo=bar, spam=ham) 

...which you will not be able to do with the `rpc` API.

Publishing and Subscribing is equally as simple
-----------------------------------------------

To demonstrate, first of all you need a **Subscriber**. You can either
create one yourself in a Python module (as a subclass of a **wampy**
`Client`) or use the example `Client` already for you in
`docs.examples.services`.

Here we use the said example service, but all a **Subscriber** is is a
**wampy** `Client` with a method decorated by `subscribe`. Take a look
and see for yourself in the
[examples](https://github.com/noisyboiler/wampy/blob/master/docs/examples/services.py#L26).

Let's start up that example service.

    $ wampy run docs.examples.services:SubscribingService --config ./wampy/testing/configs/crossbar.json

Now we have a service running that subscribes to the topic "foo".

In another terminal, with a **wampy** virtualenv, you can create a
**Publisher** - which is no different to any other **wampy** Client.

    In [1]: from wampy.peers import Client

    In [2]: with Client() as client:
                result = client.publish(topic="foo", message="spam")

Hopefully you'll see any message you send printed to the screen where
the example service is running. You'll also see the meta data that
**wampy** chooses to send.

Please note. **wampy** believes in explicit `kwargs` and not bare
`args`, so you can only publish keyword arguments. Bare arguments don't
tell readers enough about the call, so even though **WAMP** supports
them, **wampy** does not.

It doesn't matter what the `kwargs` are they will be published, but you
might find a call like this is not supported by subscribers of other
**WAMP** implementations (sorry) e.g.

    In [1]: from wampy.peers import Client

    In [2]: with Client() as client:
                client.publish(
                    topic="foo",
                    ham="spam",
                    birds={'foo_bird': 1, 'bar_bird': 2},
                    message="hello world",
                )

Notice `topic` is *always* first, followed by `kwargs`. Happy to explore
how implementations like
[autobahn](https://github.com/crossbario/autobahn-python) can be
supported here.

See [ReadTheDocs](http://wampy.readthedocs.io/en/latest/) for more
detailed documentation.

Have Fun With Wampy
===================

You can simply import a wampy client into a Python shell and start
creating WAMP apps. Open a few shells and start clients running! Or
start an example app and open a shell and start calling it. Don't forget
to start Crossbar first though!

    $ make install

    $ crossbar start --config ./wampy/testing/configs/crossbar.json

Extensions
==========

Wampy is a "simple" WAMP client and so it can easily be integrated with
other frameworks. The current extensions are:

> -   [Flask-WAMP](https://github.com/noisyboiler/flask-wamp)
> -   [nameko-wamp](https://github.com/noisyboiler/nameko-wamp)

Extensions for other Python Frameworks are encouraged!

Async Networking
================

The default backend for async networking is **gevent**, but you can
switch this to **eventlet** if that is what your applications already
use.

    $ export WAMPY_ASYNC_NAME=eventlet

Swapping back is easy.

    $ export WAMPY_ASYNC_NAME=gevent


Gevent is officially supported bu eventlet no longer is, sorry.

Async.io would require a complete re-write, and if you're already using
the standard library and want to use **wampy** that is *not* a problem -
just roll with the default gevent - as the two event loops can run side
by side.

Why does wampy support both eventlet and gevent? Because wampy is not a
framework like Flask or nameko, and wampy tries to make as few
assumptions about the process it is running in as possible. Wampy is
intended to be integrated into existing Python apps as an easy way to
send and receive WAMP messages, and if your app is already committed to
a paritcular async architecture, then wampy may not be usable unless he
can switch between them freely. And do remember: both options are
compatible with the core asyncio library, so don't be put off if your
app uses this.

Alpha Features
==============

WebSocket Client -\> Server Pings
---------------------------------

Disabled by default, but by setting the environment variable
**DEFAULT\_HEARTBEAT\_SECONDS** you can tell wampy to start Pinging the
Router/Broker, i.e. Crossbar.

    $ export DEFAULT_HEARTBEAT_SECONDS=5

There is also **HEARTBEAT\_TIMEOUT\_SECONDS** (defaults to 2 seconds)
which on missed will incrmeent a missed Pong counter. That's it for now;
WIP.

WAMP Call TimeOuts
------------------

WAMP advacned protocol describes an RPC timeout which **wampy**
implements but Crossbar as yet does not. See
<https://github.com/crossbario/crossbar/issues/299>. wampy does pass
your preferred value to the Router/Broker in the Call Message, but the
actual timeout is implemented by wampy, simply cutting the request off
at the head. Sadly this does mean the server still may return a value
for you and your app will have to handle this. We send the Cancel
Message too, but there are issues here as well: Work In Progress.

Running the tests
=================

    $ pip install --editable .[dev]
    $ py.test ./test -v

Build the docs
==============

    $ pip install -r rtd_requirements.txt
    $ sphinx-build -E -b html ./docs/ ./docs/_build/

**If you like this project, then Thank You, and you're welcome to get
involved.**

Contributing
============

Firstly. thank you everyone who does. And *everyone* is welcome to. And
thanks for reading the
[CONTRIBUTING](https://github.com/noisyboiler/wampy/blob/master/CONTRIBUTING.md)
guidelines. And for adding yourselves to the
[CONTRIBUTORS](https://github.com/noisyboiler/wampy/blob/master/CONTRIBUTORS.txt)
list on your PR - you should! Many thanks. It's also great to hear how
everyone uses wampy, so please do share how with me on your PR in
comments.

Then, please read about the
[internals](https://github.com/noisyboiler/wampy/wiki/Internal-Architecture).

Finally.... get coding!!

Thanks!

#### TroubleShooting

Crossbar.io is used by the test runner and has many dependencies.

##### Mac OS

`snappy/snappymodule.cc:31:10: fatal error: 'snappy-c.h' file not found   #include <snappy-c.h>`

Fix by brew install snappy
