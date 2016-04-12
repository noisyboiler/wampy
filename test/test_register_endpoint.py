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
from wampy.messages.register import Register
from wampy.entrypoints import rpc
from wampy.interfaces import Peer
from wampy.protocol import (
    register_peer, get_registered_entrypoints, get_peer_registry)


def test_register_endpoint(session):
    """ If the Dealer_is able to fulfill and allowing the registration, it
    answers by sending a "REGISTERED" message to the "Callee" ::

        [REGISTERED, REGISTER.Request|id, Registration|id]

    """
    message = Register(procedure="com.foo.bar")
    message.construct()

    response_message = session.send_and_receive(message)
    message_code, request_id, registration_id = response_message

    assert message_code == Register.REGISTERED
    assert request_id is not None
    assert registration_id is not None


def test_callee_app_register_on_startup(router):
    class CalleeApp(Peer):
        @property
        def name(self):
            return 'test app'

        @property
        def config(self):
            return {}

        @property
        def role(self):
            return 'CALLEE'

        @property
        def start(self):
            print('test app starting up')

        @property
        def stop(self):
            print('test app stopping running')

        @rpc
        def this_is_callable_over_rpc(self):
            pass

    # register a Router/Broker
    register_peer(router)

    registered_peers = get_peer_registry()
    entrypoints = get_registered_entrypoints()

    assert 'test app' not in registered_peers
    assert not entrypoints

    app = CalleeApp()
    register_peer(app)

    registered_peers = get_peer_registry()
    entrypoints = get_registered_entrypoints()

    assert 'test app' in registered_peers
    assert len(entrypoints.keys()) == 1

    registration_id, registration_source = entrypoints.items()[0]

    assert registration_id is not None

    registering_app, registered_entrypoint_name = registration_source

    assert issubclass(registering_app, CalleeApp)
    assert registered_entrypoint_name == 'this_is_callable_over_rpc'
