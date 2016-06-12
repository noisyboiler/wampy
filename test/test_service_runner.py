import datetime
from wampy.constants import (
    DEFAULT_HOST, DEFAULT_REALM, DEFAULT_ROLES)
from wampy.entrypoints import rpc
from wampy.registry import get_client_registry, get_registered_entrypoints
from wampy.clients import Client
from wampy.services import ServiceRunner
from wampy.testing.routers.crossbar import Crossbar


class DateService(Client):
    """ A service that tells you todays date """

    @property
    def name(self):
        return 'Date Service'

    @rpc
    def get_todays_date(self):
        return datetime.date.today().isoformat()


def test_start_service_runner():
    # must execute without error or hanging
    crossbar = Crossbar(
        host=DEFAULT_HOST,
        config_path='./wampy/testing/routers/config.json',
        crossbar_directory='./',
    )
    crossbar.start()

    runner = ServiceRunner(
        router=crossbar, realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )

    runner.start()
    runner.stop()


def test_service_runner_register_endpoint(service_runner):
    registered_peers = get_client_registry()
    registered_entrypoints = get_registered_entrypoints()

    def get_entrypoint_names():
        return [
            app_name_tuple[1] for app_name_tuple in
            registered_entrypoints.values()
        ]

    app = DateService(
        name="Date Service", router=None,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    assert app.name not in registered_peers
    assert "get_todays_date" not in get_entrypoint_names()

    service_runner.register_client(app)

    assert app.name in registered_peers
    assert "get_todays_date" in get_entrypoint_names()
