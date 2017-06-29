Testing wampy apps
==================

To test any WAMP application you are going to need a Peer acting as a Router.

**wampy** provides a ``pytest`` fixture for this: ``router`` which must be installed via ``$ pip install --editable .[dev]``. Usage is then simple.

For example

::

    def test_my_wampy_applications(router):
        # do stuff here


The router is **Crossbar.io** and will be started and shutdown between each test.

It has a default configuration which you can override in your tests by creating a ``config_path`` fixture in your own ``conftest`` or test module.

For example

::

    import pytest


    @pytest.fixture
    def config_path():
        return './path/to/my/preferred/crossbar.json'


Now any test using ``router`` will be a Crossbar.io server configured yourself.

For example

::

    def test_my_app(router):
        # this router's configuration has been overridden!


If you require even more control you can import the router itself from ``wampy.peers.routers`` and setup your tests however you need to.

**wampy** also provides a ``pytest`` fixture for a WAMP client.

Here is an example testing a wampy ``HelloService`` application.

::

    import pytest

    from wampy.roles.callee import callee
    from wampy.peers.clients import Client
    from wampy.testing import wait_for_registrations

    class HelloService(Client):

        @callee
        def say_hello(self, name):
            message = "Hello {}".format(name)
            return message


    @pytest.yield_fixture
    def hello_service(router):
        with HelloService(router=router) as service:
            wait_for_registrations(service, 1)
            yield


    def test_get_hello_message(hello_service, router, client):
        response = client.rpc.say_hello(name="wampy")

        assert response == "Hello wampy"


Notice the use of ``wait_for_registrations``. All wampy actions are asynchronous, and so it's easy to get confused when setting up tests wondering why an application hasn't registered Callees or subscribed to Topics, or a Session even opened yet.

So to help you setup your tests and avoid race conditions there are some helpers that you can execute to wait for async certain actions to perform before you start actually running test cases. These are:

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

For far more examples, see the wampy test suite.
