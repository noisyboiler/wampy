# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
import ssl
from datetime import date

import pytest

from wampy.peers.clients import Client
from wampy.roles.callee import callee
from wampy.transports import SecureWebSocket
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

    def test_ipv4_secure_websocket_connection(self, config_path, router):
        try:
            ssl.PROTOCOL_TLSv1_2
        except AttributeError:
            pytest.skip('Python Environment does not support TLS')

        with DateService(
                router=router, transport=SecureWebSocket()
        ) as service:
            wait_for_registrations(service, 1)

            client = Client(router=router, transport=SecureWebSocket())
            with client:
                wait_for_session(client)
                result = client.rpc.get_todays_date()

        today = date.today()

        assert result == today.isoformat()
