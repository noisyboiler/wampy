# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import json

from wampy.backends import async_adapter
from wampy.message_handler import MessageHandler

TIMEOUT = 5


def wait_for_subscriptions(client, number_of_subscriptions):
    with async_adapter.Timeout(TIMEOUT):
        while (
            len(client.session.subscription_map.keys())
            < number_of_subscriptions
        ):
            async_adapter.sleep(0.01)


def wait_for_registrations(client, number_of_registrations):
    with async_adapter.Timeout(TIMEOUT):
        while (
            len(client.session.registration_map.keys())
            < number_of_registrations
        ):
            async_adapter.sleep(0.01)


def wait_for_session(client):
    with async_adapter.Timeout(TIMEOUT):
        while client.session.id is None:
            async_adapter.sleep(0.01)


def wait_for_messages(client, number_of_messages):
    messages_received = (
        client.session.message_handler.messages_received)

    with async_adapter.Timeout(TIMEOUT):
        while len(messages_received) < number_of_messages:
            async_adapter.sleep(0.01)

    return messages_received


class CollectingMessageHandler(MessageHandler):

    def __init__(self):
        super(CollectingMessageHandler, self).__init__()
        self.messages_received = []

    def handle_message(self, message, client):
        self.messages_received.append(json.loads(message))
        super(CollectingMessageHandler, self).handle_message(
            message, client
        )
