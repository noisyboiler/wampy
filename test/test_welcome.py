import pytest

from wampy.peers.clients import Client
from wampy.roles.callee import rpc


@pytest.fixture
def service(router):
    class Service(Client):
        @rpc
        def foo(self):
            pass
    foo_service = Service(name="foo service")
    foo_service._connect_to_router()
    return foo_service


def test_welcome_message(service):
    message = service._say_hello_to_router()
    assert message[0] == 2  # WELCOME

    details = message[2]
    assert details['realm'] == 'realm1'

    roles = details['roles']
    assert sorted(roles.keys()) == ['broker', 'dealer']

    # look at subscriptions
    assert roles['dealer'] == {
        'features': {
            'payload_encryption_cryptobox': True,
            'payload_transparency': True,
            'pattern_based_registration': True,
            'registration_revocation': True,
            'shared_registration': True,
            'caller_identification': True,
            'session_meta_api': True,
            'registration_meta_api': True,
            'progressive_call_results': True,
        }
    }

    # and registrations
    assert roles['broker'] == {
        'features': {
            'publisher_identification': True,
            'pattern_based_subscription': True,
            'subscription_meta_api': True,
            'payload_encryption_cryptobox': True,
            'payload_transparency': True,
            'subscriber_blackwhite_listing': True,
            'session_meta_api': True,
            'publisher_exclusion': True,
            'subscription_revocation': True,
        }
    }
