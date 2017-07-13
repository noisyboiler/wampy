Exception Handling
==================

When calling a remote procedure an ``Exception`` might be raised by the remote application. It this happens the *Callee's* ``Exception`` will be wrapped in a wampy ``RemoteError`` and will contain the name of the remote procedure that raised the error, the ``request_id``, the exception type and any message.

::

    from wampy.errors import RemoteError
    from wampy.peers.clients import Client


    try:
        with Client() as client:
            response = client.rpc.some_unreliable_procedure()
    except RemoteError as rmt_err:
        # do stuff here to recover from the error
