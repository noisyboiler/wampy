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
from wampy.wamp.messages.register import Register


def test_register_endpoint(basic_profile_router, session):
    """ If the _Dealer_ is able to fulfill and allowing the registration, it
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
