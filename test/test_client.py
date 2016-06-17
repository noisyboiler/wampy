from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES
from wampy.rpc import rpc
from wampy.peers.clients import Client
from wampy.registry import get_client_registry, get_registered_entrypoints


def test_client_connects_to_router(router):

    class MyClient(Client):
        pass

    client = MyClient(
        name="my test client", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )

    assert client.session is None

    client.start()

    session = client.session
    assert session.id is not None
    assert session.client is client
    assert session.router is router

    client.stop()

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

    class MyClient(Client):
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

    assert app.name in registered_peers
    assert "get_foo" in get_entrypoint_names()
    assert "get_bar" in get_entrypoint_names()

    app.stop()


def test_can_start_two_clients(router):

    class MyClient(Client):
        pass

    app_one = MyClient(
        name="my test client", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    app_one.start()
    assert app_one.session.id

    app_two = MyClient(
        name="Client Two", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    app_two.start()
    assert app_two.session.id

    app_one.stop()
    app_two.stop()

    assert app_one.session is None
    assert app_two.session is None
