wampy
=====

An ongoing Python WAMP Implementation
-------------------------------------

The WAMP protocol connects Clients via RPC or Pub/Sub over a Router.

A Client is some kind of application that **calls** or **subscribes** to
another Client, else provides something for others to call or subscribe
to. These are “Roles” that are performed by a Client, and they are
referred to as *Caller*, *Callee*, *Publisher* and *subscribe*.

A Router is another type of application - a message broker - that is
either a *Broker* or a *Dealer*, and highly likely to be Crossbar.io.

Whatever application you’re dealing with, WAMP refers to these as a
**Peer**.

With **wampy** you can quickly and easily create Peers to implement these
WAMP roles and peers.


Quickstart: wampy from a Python console.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before any messaging can happen you need a Router. This is a Peer that
implements the Dealer or Broker roles, or both. Messages are then routed
between Clients over an administritive domain called a “realm”.

For a quickstart I suggest that you use Crossbar.io and start it up on
the default **host** and **port** with the default **realm** and
**roles**. See the `Crossbar.io docs`_ for the instructions of this or
alternatively run with wampy's testing setup ``pip install -r test_requirements.txt && crossbar start --config ./test/crossbar.config.json``. By default, a ``Peer`` connects to this
endpoint, but this is configurable on initialisation.

Then open a Python console.

::

    In [1]: from wampy import Peer

    In [2]: from wampy.entrypoints import rpc

    In [3]: class BinaryNumberService(Peer):
                @rpc
                def get_binary_number(self, number):
                    return bin(number)

    In [4]: service = BinaryNumberService()

    In [5]: service.start()

    In [6]: service.session.id
    Out[6]: 3941615218422338

If a ``Peer`` implements the *Callee* **role**, then just by starting the ``Peer`` you
instruct it to register its RPC entrypoints with the Router.

::

    In [7]]: from wampy.registry import get_registered_entrypoints

    In [8]: get_registered_entrypoints()
    Out[8]: {2010994119734585: (__main__.BinaryNumberService, 'get_binary_number')}

Any method of the ``Peer`` decorated with *rpc* will have been registered as
publically availabile over the Router.

You can launch a client to call this entrypoint in this shell or a new one 
– it really doesn't matter. You can also optionally give your ``Peer`` a name, which may help in your shell or your ELK stack.

::

    In [9]: client = Peer(name="Binary Number Caller")

The built in stand alone client knows about the entrypoints made
available by the ``DateService`` and using it you can call them
directly.

::

    In [10]: client.start()  # note that you can context-manage clients and avoid this step!

    In [11]: client.rpc.get_binary_number(100)
    Out [11]: u'0b1100100'

If you don’t context-manage your client, then you do have to explicitly
call ``stop`` in order to gracefully disassociate yourself from the
router, but also to tidy up the green threads and connections.

::

    In [12]: client.stop()

You can also publish to and subscribe to topics. This is most fun when you open a second terminal!

::

    In [1]: from wampy import Peer

    In [2]: from wampy.entrypoints import subscribe

    In [3]: class NewsReader(Peer):

                def __init__(self, *args, **kwargs):
                    super(NewsReader, self).__init__(*args, **kwargs)
                    self.messages = []

                @subscribe(topic="news")
                def handle_news(self, *args, **kwargs):
                    headlines = kwargs['headlines']
                    for headline in headlines:
                        self.messages.append(headline)

    In [5]: reader = NewsReader()

    In [6]: reader.start()

Because we're in a terminal you also need something to poll async for messages, such as...

::

    In [7]: def listen_for_news(reader):
                import eventlet()
                while True:
                    try:
                        message = reader.messages.pop()
                    except IndexError:
                        eventlet.sleep()
                    else:
                        print(message)

    In [8]: listen_for_news(reader)

Jump back to the other terminal and publish some news!

::

    In [13]: with cliient:
                client.publish(topic="news", headlines=[
                    "wampy is great!",
                    "probably best to use wampy in your next project"
                ])

News will print out in your second terminal!

That’s about it so far.

::

    exit()

.. _Crossbar.io docs: http://crossbar.io/docs/Quick-Start/
