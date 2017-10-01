A wampy Client
==============

If you're working from a Python shell or script you can connect to a Router as follows.

1. Router is running on localhost, port 8080, start and stop manually.

::

    from wampy.peers import Client

    client = Client()
    client.start()  # connects to the Router & establishes a WAMP Session
    # send some WAMP messages here
    client.stop()  # ends Session, disconnects from Router


2. Router is running on localhost, port 8080, context-manage the Session

::

    from wampy.peers import Client

    with Client() as client:
        # send some WAMP messages here

    # on exit, the Session and connection are gracefully closed

3. Router is on example.com, port 8080, context-managed client again

::

    from wampy.peers import Client

    with Client(url="ws://example.com:8080") as client:
        # send some WAMP messages here

    # exits as normal

Under the hood wampy creates an instance of a Router representaion because a Session is a managed conversation between two Peers - a Client and a Router. Because wampy treats a Session like this, there is actually also a *fourth* method of connection, as you can create the Router instance yourself and pass this into a Client directly. This is bascically only useful for test and CI environments, or local setups during development, or for fun. See the wampy tests for examples and the wampy wrapper around the Crossbar.io Router.

Sending a Message
=================

When a **wampy** client starts up it will send the **HELLO** message for you and begin a **Session**. Once you have the **Session** you can construct and send a **WAMP** message yourself, if you so choose. But **wampy** has the ``publish`` and ``rpc`` APIs so you don't have to.

But if you did want to do it yourself, here's an example how to...

Given a **Crossbar.io** server running on localhost on port 8080, a **realm** of "realm1", and a remote procedure "foobar", send a **CALL** message with **wampy** as follows:

::

    In [1]: from wampy.peers.clients import Client

    In [2]: from wampy.messages.call import Call

    In [3]: client = Client()

    In [4]: message = Call(procedure="foobar", args=(), kwargs={})

    In [5]: with client:
                client.send_message(message)

This example assumes a Router running on localhost and a second Peer attached over the same realm who hjas registered the callee "foobar"

Note that in the example, as you leave the context managed function call, the client will send a **GOODBYE** message and your **Session** will end.

wampy does not want you to waste time constructing messages by hand, so the above can be replaced with:

::

    In [1]: from wampy.peers.clients import Client

    In [2]: client = Client()

    In [5]: with client:
                client.rpc.foobar(*args, **kwargs)

Under the hood, **wampy** has the ``RpcProxy`` object that implements the ``rpc`` API.
