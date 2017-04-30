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

When a **wampy** client starts up it will send the **HELLO** message for you and begin a **Session**. Once you have the **Session** you can construct and send a **WAMP** message yourself, if you so choose. But **wampy** has the ``publish`` and ``rpc`` APIs so you don't have to.

But if you did want to do it yourself, here's an example how to...

Given a **Crossbar.io** server running on localhost on port 8080, a **realm** of "realm1", and a remote procedure "foobar", send a **CALL** message with **wampy** as follows:

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.peers.routers import Crossbar

    In [3]: from wampy.messages.call import Call

    In [4]: router = Crossbar(config_path="./crossbar/config.json")

    In [5]: client = Client(router=router)

    In [6]: message = Call(procedure="foobar", args=(), kwargs={})

    In [7]: with client:
                client.send_message(message)

This is quite verbose and unnecessary with the core **wampy** API. With **wampy** you don't actually have to manually craft any messages. And of course, without another **Peer** having registered "foobar" on the same **realm**, this example will achieve little. And even if there were, you'd still have to do work to receive, unpack and interpret the response.

Note that in the example, as you leave the context managed function call, the client will send a **GOODBYE** message and your **Session** will end. And that ``./crossbar/config.json`` is the default value for ``config_path``.

Because the procedure name is not a dot delimeted string, the above can essentially be replaced with:

::

    In [X]: respones = client.rpc.foobar(*args, **kwargs)

Under the hood, **wampy** has the ``RpcProxy`` object that implements the ``rpc`` API.
