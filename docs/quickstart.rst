Quickstart: wampy from a Python console.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before any messaging can happen you need a Router. Messages are then routed between Clients over an administritive domain called a “realm”.

For a quickstart I suggest that you use Crossbar.io and start it up on the default **host** and **port** with the default **realm** and **roles**. See the `Crossbar.io docs`_ for the instructions of this or alternatively run with wampy's testing setup:

::

    $ pip install -r test_requirements.txt

    $ crossbar start --config ./test/crossbar.config.json

By default, a client connects to this endpoint, but this is configurable on initialisation.

Now open a Python console and we'll create a simple service that takes a decimal number and returns the binary representation of it.

::

    In [1]: from wampy.peers import Client

    In [2]: from wampy.roles.callee import rpc

    In [3]: class BinaryNumberService(Client):

                @rpc
                def get_binary_number(self, number):
                    return bin(number)

    In [4]: service = BinaryNumberService(name="Binary Number Service")

The preferred usage of a wampy client is as a context manager which handles connections for you, but for demonstration purposes we'll explicitly start and stop the service.

::

    In [5]: service.start()

    In [6]: service.session.id
    Out[6]: 3941615218422338

    In [7]: service.registration_map['get_binary_number']
    Out[7]: 8205738934160840

Now open another Python shell.

::

    In [1]: from wampy.peers.clients import RpcClient

    In [2]: with RpcClient(name="wampy") as client:
                result = client.rpc.get_binary_number(number=100)

    In [3]: result
    Out[3]: u'0b1100100'


If you don’t context-manage your client, then you do have to explicitly call ``stop`` in order to gracefully disassociate yourself from the router, but also to tidy up the green threads and connections.

::

    In [8]: client.stop()

You can also publish to and subscribe to topics. This is most fun when you open a second terminal!

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.entrypoints import subscribe

    In [3]: class NewsReader(Client):

                def __init__(self, *args, **kwargs):
                    super(NewsReader, self).__init__(*args, **kwargs)
                    self.messages = []

                @subscribe(topic="news")
                def handle_news(self, *args, **kwargs):
                    headlines = kwargs['headlines']
                    for headline in headlines:
                        self.messages.append(headline)

    In [5]: reader = NewsReader(name="News Reader")

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
                    "probably best to use wampy in your next project!",
                ])

News will print out in your second terminal!

That’s about it so far.

::

    exit()

.. _Crossbar.io docs: http://crossbar.io/docs/Quick-Start/