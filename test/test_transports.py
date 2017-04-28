import datetime
import ssl
from datetime import date

import pytest

from wampy.peers.clients import Client
from wampy.peers.routers import Crossbar
from wampy.roles.callee import callee
from wampy.testing.helpers import wait_for_session, wait_for_registrations


class DateService(Client):

    @callee
    def get_todays_date(self):
        return datetime.date.today().isoformat()


class TestIP4(object):

    @pytest.fixture(scope="function")
    def config_path(self):
        return './wampy/testing/configs/crossbar.config.ipv4.json'

    def test_ipv4_websocket_connection(self, config_path, router):
        with router:
            service = DateService(router=router)
            with service:
                wait_for_registrations(service, 1)

                client = Client(router=router)

                with client:
                    result = client.rpc.get_todays_date()

            today = date.today()

            assert result == today.isoformat()


class TestIP6(object):

    @pytest.fixture(scope="function")
    def config_path(self):
        return './wampy/testing/configs/crossbar.config.ipv6.json'

    def test_ipv6_websocket_connection(self, config_path, router):
        with router:
            service = DateService(router=router)
            with service:
                wait_for_registrations(service, 1)

                client = Client(router=router)

                with client:
                    result = client.rpc.get_todays_date()

            today = date.today()

            assert result == today.isoformat()


def test_ipv4_secure_websocket_connection():
    try:
        ssl.PROTOCOL_TLSv1_2
    except AttributeError:
        pytest.skip('Python Environment does not support TLS')

    # note that TLS not supported by crossbar on ipv6
    crossbar = Crossbar(
        config_path='./wampy/testing/configs/crossbar.config.ipv4.tls.json',
        crossbar_directory='./',
    )

    with crossbar as router:
        with DateService(router=router, use_tls=True) as service:
            wait_for_registrations(service, 1)

            client = Client(router=router, use_tls=True)
            with client:
                wait_for_session(client)
                result = client.rpc.get_todays_date()

        today = date.today()

        assert result == today.isoformat()
