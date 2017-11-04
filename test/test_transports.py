# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import ssl
from datetime import date

import pytest

from wampy.peers.clients import Client
from wampy.roles.callee import callee
from wampy.testing.helpers import wait_for_session, wait_for_registrations


class DateService(Client):

    @callee
    def get_todays_date(self):
        return datetime.date.today().isoformat()


class TestIP4(object):

    @pytest.fixture(scope="function")
    def config_path(self):
        return './wampy/testing/configs/crossbar.json'

    def test_ipv4_websocket_connection(self, config_path, router):
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
        return './wampy/testing/configs/crossbar.ipv6.json'

    @pytest.mark.skip(reason="Travis errors wheh swapping between IPV 4 & 6")
    def test_ipv6_websocket_connection(self, config_path, router):
        service = DateService(router=router)
        with service:
            wait_for_registrations(service, 1)

            client = Client(router=router)

            with client:
                result = client.rpc.get_todays_date()

        today = date.today()

        assert result == today.isoformat()


class TestSecureWebSocket(object):

    @pytest.fixture(scope="function")
    def config_path(self):
        return './wampy/testing/configs/crossbar.tls.json'

    def test_ipv4_secure_websocket_connection_by_router_instance(
        self, config_path, router
    ):
        try:
            ssl.PROTOCOL_TLSv1_2
        except AttributeError:
            pytest.skip('Python Environment does not support TLS')

        with DateService(router=router) as service:
            wait_for_registrations(service, 1)

            client = Client(router=router)
            with client:
                wait_for_session(client)
                result = client.rpc.get_todays_date()

        today = date.today()

        assert result == today.isoformat()

    def test_ipv4_secure_websocket_connection_by_router_url(self, router):
        assert router.url == "wss://localhost:9443"

        try:
            ssl.PROTOCOL_TLSv1_2
        except AttributeError:
            pytest.skip('Python Environment does not support TLS')

        with DateService(
            url="wss://localhost:9443",
            cert_path="./wampy/testing/keys/server_cert.pem",
        ) as service:
            wait_for_registrations(service, 1)

            client = Client(
                url="wss://localhost:9443",
                cert_path="./wampy/testing/keys/server_cert.pem",
            )
            with client:
                wait_for_session(client)
                result = client.rpc.get_todays_date()

        today = date.today()

        assert result == today.isoformat()
