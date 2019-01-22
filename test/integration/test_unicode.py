# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from wampy.peers.clients import Client
from wampy.testing.helpers import wait_for_session


def test_client_sending_unicode_does_not_raise(router, echo_service):
    class MyClient(Client):
        pass

    client = MyClient(url=router.url)

    client.start()
    wait_for_session(client)

    response = client.rpc.echo(weird_text="100éfa")

    assert response is not None
