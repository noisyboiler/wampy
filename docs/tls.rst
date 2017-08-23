TLS/wss Support
===============

Your Router must be configured to use TLS. For an example see the `config`_ used by the test runner along with the `TLS Router`_ setup.

To connect a Client over TLS you define this transport in the Client init. This is actually overriding the default transport of ``WebSocket``. An instance must be passed in, so you should do something like the following:

::

    In [1]: from wampy.transports import SecureWebSocket

    In [2]: websocket_with_tls = SecureWebSocket()

    In [3]: client = Client(router=router, transport=websocket_with_tls)

Note that **Crossbar.io** does not support TLS over IPV6, and you'll need to be executing as root for port 443. All of these choices are made in the **Crossbar.io** config.

.. _config: https://github.com/noisyboiler/wampy/blob/master/wampy/testing/configs/crossbar.config.ipv4.tls.json
.. _TLS Router: https://github.com/noisyboiler/wampy/blob/master/test/test_transports.py#L71
