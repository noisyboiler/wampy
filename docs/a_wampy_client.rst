A wampy Client
==============

If you're working from a Python shell or script you have the convieiance of using the wampy client directly without having to start up an application.

::

    from wampy.peers import Client
    from wampy.peers.routers import Crossbar

    with Client(router=Crossbar()) as client:
        result = client.call("example.app.com")
        client.publish(topic="foo", message=result)


Note that the Crossbar router does require a path to an expected ``config,.yaml``, but here a default value is used. The default for Crossbar is ``"./crossbar/config.json"``.
