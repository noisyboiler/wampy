# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from wampy.peers.clients import Client
from wampy.roles.callee import callee
from wampy.testing.helpers import wait_for_registrations, wait_for_session


@pytest.fixture
def config_path():
    return './wampy/testing/configs/crossbar.json'


class EchoService(Client):

    @callee
    def echo(self, **kwargs):
        return kwargs


@pytest.yield_fixture
def echo_service(router):
    with EchoService(url=router.url) as svc:
        wait_for_session(svc)
        wait_for_registrations(svc, 1)
        yield
