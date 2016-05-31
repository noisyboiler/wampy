""" a callee Registering an endpoint.

The message flow between Callees and a Dealer for registering and
unregistering endpoints to be called over RPC involves the following
messages:
1. "REGISTER"
2. "REGISTERED"
3. "UNREGISTER"
4. "UNREGISTERED"
5. "ERROR"
"""
from . wampy.client import Client
from . wampy.messages import MESSAGE_TYPE_MAP
from . wampy.messages.register import Register as RegisterMessage


class Register(object):
    """  A Callee announces the availability of an endpoint implementing a
    procedure with a Dealer by sending a "REGISTER" message ::

        [
            REGISTER, Request|id, Options|dict, Procedure|uri
        ]

    "Request" is a random, ephemeral ID chosen by the _Callee_ and
    used to correlate the _Dealer’s_ response with the request.

    "Options" is a dictionary that allows to provide additional
    registration request details in a extensible way.  This is
    described further below.

    "Procedure" is the procedure the _Callee_ wants to register

    If the _Dealer_ is able to fulfill and allowing the registration, it
    answers by sending a "REGISTERED" message to the "Callee" ::

        [
            REGISTERED, REGISTER.Request|id, Registration|id
        ]

    "REGISTER.Request" is the ID from the original request.

    "Registration" is an ID chosen by the _Dealer_ for the registration.

    e.g. ::

        [
            65, 25349185, 2103333224
        ]

    """
    def run(self, procedure="com.foo.bar"):
        client = Client(name="rpc_registerer")
        client.connect()
        client.begin()

        message = RegisterMessage(procedure=procedure)
        message.construct()
        response_message = client.send_and_receive(message)

        wamp_code, request_id, registration_id = response_message

        assert wamp_code == 65
        assert MESSAGE_TYPE_MAP[wamp_code] == 'REGISTERED'
