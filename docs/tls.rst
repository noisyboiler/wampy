TLS/wss Support
===============

Your Router must be configured to use TLS. For an example see the `config`_ used by the test runner along with the `TLS Router`_ setup.

To connect a Client over TLS pass the ``use_tls=True`` parameter on initialisation.

::

    In [4]: client = Client(router=router, use_tls=True)

Note that **Crossbar.io** does not support TLS over IPV6 and you'll need to be executing as root for port 443. All of these choices are made in the **Crossbar.io** config.

.. _config: https://github.com/noisyboiler/wampy/blob/master/wampy/testing/configs/crossbar.config.ipv4.tls.json
.. _TLS Router: https://github.com/noisyboiler/wampy/blob/master/test/test_transports.py#L71
