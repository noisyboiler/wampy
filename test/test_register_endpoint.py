""" Registering and Unregistering

The message flow between _Callees_ and a _Dealer_ for registering and
unregistering endpoints to be called over RPC involves the following
messages:
1. "REGISTER"
2. "REGISTERED"
3. "UNREGISTER"
4. "UNREGISTERED"
5. "ERROR"
"""
from datetime import date
from wampy.messages.call import Call
from wampy.registry import get_client_registry, get_registered_entrypoints

from wampy.testing.clients.callers import StandAloneClient
from wampy.testing.clients.callees import DateService


def test_application_register_endpoint_with_router_running(router):
    registered_peers = get_client_registry()
    registered_entrypoints = get_registered_entrypoints()

    def get_entrypoint_names():
        return [
            app_name_tuple[1] for app_name_tuple in
            registered_entrypoints.values()
        ]

    app = DateService(router)
    assert app.name not in registered_peers
    assert "get_todays_date" not in get_entrypoint_names()

    assert not app.started

    app.start()
    assert app.started

    assert app.name in registered_peers
    assert "get_todays_date" in get_entrypoint_names()

    client = StandAloneClient(router=router)
    assert client.started

    message = Call(procedure="get_todays_date")
    message.construct()

    client.send(message)
    response = client.wait_for_response()

    today = date.today()

    assert response == today.isoformat()

    client.stop()
    app.stop()


def test_service_runner_register_endpoint(service_runner):
    registered_peers = get_client_registry()
    registered_entrypoints = get_registered_entrypoints()

    def get_entrypoint_names():
        return [
            app_name_tuple[1] for app_name_tuple in
            registered_entrypoints.values()
        ]

    app = DateService()
    assert app.name not in registered_peers
    assert "get_todays_date" not in get_entrypoint_names()

    service_runner.register_client(app)

    assert app.name in registered_peers
    assert "get_todays_date" in get_entrypoint_names()
