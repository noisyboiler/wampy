Testing wampy apps
==================

**wampy** provides some ``pytest`` fixtures and helpers for you to run a crossbar server. These are ``router`` and ``session_maker``. 

The router is **Crossbar.io** and will be started and shutdown between each test. It has a default configuration which you can override in your tests by creating a ``config_path`` fixture in your own ``conftest`` - see *wampy's* ``conftest`` for an example. If you require even more control you can import the router itself from ``wampy.peers.routers`` and setup your tests however you need to.

To help you setup your test there are also some helpers that you can execute to wait for async certain actions to perform before you start actually running test code. These are:

::

    # execute with the client you're waiting for as the only argument
    from wampy.testing import wait_for_session
    # e.g. ```wait_for_session(client)```

    # wait for a specific number of registrations on a client
    from wampy.testing import wait_for_registrations
    # e.g. ``wait_for_registrations(client, number_of_registrations=5)

    # wait for a specific number of subscriptions on a client
    from wampy.testing import wait_for_subscriptions
    # e.g. ``wait_for_subscriptions(client, number_of_subscriptions=7)

    # provied a function that raises until the test passes
    from test.helpers import assert_stops_raising
    # e.g. assert_stops_raising(my_func_that_raises_until_condition_met)
