Exception Handling
==================

When calling a remote procedure an ``Exception`` might be raised by the remote application. It this happens the *Callee's* ``Exception`` will be wrapped in a wampy ``RemoteException`` and will contain the name of the remote procedure that raised the error, the ``request_id``, the exception type and any message.
