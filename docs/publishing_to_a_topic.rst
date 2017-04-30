Publishing to a Topic
=====================

To publish to a topic you simply call the ``publish`` API on any wampy client with the topic name and message to deliver.

::

    from wampy.peers.clients import Client
    from wampy.peers.routers import Crossbar

    with Client(router=Crossbar()) as client:
        client.publish(topic="foo", message={'foo': 'bar'})


The message can be whatever JSON serializable object you choose.

Note that the Crossbar router does require a path to an expected ``config,.yaml``, but here a default value is used. The default for Crossbar is ``"./crossbar/config.json"``.
