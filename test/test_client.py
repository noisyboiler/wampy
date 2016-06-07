from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES
from wampy.entrypoints import rpc
from wampy.peer import ClientBase
from wampy.registry import get_client_registry, get_registered_entrypoints
from wampy.testing.clients.callers import StandAloneClient


def test_client_connects_to_router(router):

    class MyClient(ClientBase):
        pass

    client = MyClient(
        name="my test client", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )

    assert client.running is False
    assert client.session is None

    client.start()

    assert client.running is True
    assert client.session is not None

    client.stop()

    assert client.running is False
    assert client.session is None


def test_client_registers_entrypoints_with_router(router):
    registered_peers = get_client_registry()
    registered_entrypoints = get_registered_entrypoints()

    def get_entrypoint_names():
        return [
            app_name_tuple[1] for app_name_tuple in
            registered_entrypoints.values()
        ]

    assert registered_peers == {}
    assert registered_entrypoints == {}
    assert get_entrypoint_names() == []

    class MyClient(ClientBase):
        @rpc
        def get_foo(self):
            pass

        @rpc
        def get_bar(self):
            pass

    app = MyClient(
        name="Foo Bar Service", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    app.start()
    assert app.running

    assert app.name in registered_peers
    assert "get_foo" in get_entrypoint_names()
    assert "get_bar" in get_entrypoint_names()

    app.stop()


def test_can_start_two_clients(router):
    app_one = StandAloneClient(
        name="Client One", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    app_one.start()
    assert app_one.running
    assert app_one.session.id

    app_two = StandAloneClient(
        name="Client Two", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    app_two.start()
    assert app_two.running

    app_one.stop()
    app_two.stop()

    assert app_one.running is False
    assert app_two.running is False
