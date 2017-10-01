TLS/wss Support
===============

Your Router must be configured to use TLS. For an example see the `config`_ used by the test runner along with the `TLS Router`_ setup.

To connect a Client over TLS you must provide a connection URL using the ``wss`` protocol and your **Router** probably will require you to provide a certificate for authorisation.

::

    In [1]: from wampy.peers import Client

    In [2]: client = Client(url="wss://...", cert_path="./...")

.. _config: https://github.com/noisyboiler/wampy/blob/master/wampy/testing/configs/crossbar.config.ipv4.tls.json
.. _TLS Router: https://github.com/noisyboiler/wampy/blob/master/test/test_transports.py#L71
