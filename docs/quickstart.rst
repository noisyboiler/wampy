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
