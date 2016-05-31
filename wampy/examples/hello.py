from wampy.constants import DEFAULT_HOST, DEFAULT_PORT
from wampy.logger import get_logger
from wampy.messages import Message
from wampy.messages.hello import Hello as HelloMessage
from wampy.networking.connections.wamp import WampConnection
from wampy.testing.routers.crossbar import Crossbar


logger = get_logger('wampy.examples.hello')


class Hello(object):
    """ After the underlying transport has been established, the opening of a
    WAMP session is initiated by the Client sending a "HELLO" message to the
    Router.

    """
    def send(self):
        """ Simple "HELLO" to Router example.

        Sent by a Client to initiate opening of a WAMP session to a Router
        attaching to a Realm.

        Represented as ::

            [HELLO, Realm|uri, Details|dict]

        Once a WAMP connection is established betweeen a Client and a
        Router we can send a HELLO message, which if accepted, will begin a
        WAMP Session between the two Peers. This is a prerequisite for all
        other WAMP messaging.

        A WAMP connection is an upgraded websocket connection. See
        :class:`~wampy.networking.connections.wamp` for more details.

        The Client here is a thin wrapper around a WAMP connection.

        The Router is Crossbar.io, which is a dependency of wampy.

        The HELLO message is a constructed instance of
        :meth:`~wampy.messages.hello.Hello`.


        :Parameters:
            realm : str
                a string identifying the realm this session should attach to.
            roles : dict
                a dictionary providing details of the roles the Client
                supports, any of: publisher, subscriber, caller, callee,
                e.g. ::

                    [1, "somerealm", {
                         "roles": {
                             "publisher": {},
                             "subscriber": {}
                         }
                    }]

        """
        # start the built-in wampy Router Peer.
        crossbar = Crossbar(
            host='localhost',
            # configured to default host and port
            config_path='./wampy/testing/routers/config.json',
            crossbar_directory='./',
        )

        crossbar.start()

        # this is slightly crass, but crossbar starts in a subprocess, which
        # should be managed in event of unexpected failures.
        try:
            # create a Client with an established WAMP connection to the
            # router. note that a WAMP connection is not good enough to send
            # messages, the next step is to start a Session with the Router
            # over the Connection by sending a HELLO message.
            class Client(object):
                def __init__(self):
                    self.connection = WampConnection(
                        host=DEFAULT_HOST, port=DEFAULT_PORT)
                    self.connection.connect()

            client = Client()
            assert client.connection.connected is True

            # Construct a HELLO message using defauly realm and roles values.
            # A Realm is defined by the Router in its configuration, see
            # ./wampy/testing/routers/config.json
            # Routing occurs only between WAMP Sessions that have joined the
            # same Realm.
            # A Client must announce the Roles it supports. Here, all are
            # supported, but I omit any further details of these roles for
            # simplicity.
            realm = 'realm1'
            roles = {
                'roles': {
                    'subscriber': {},
                    'publisher': {},
                    'callee': {},
                    'caller': {},
                },
            }

            message = HelloMessage(realm, roles)
            message.construct()
            message = message.serialize()

            client.connection.send(str(message))

            data = None
            while True:
                try:
                    data = client.connection.recv()
                    if data:
                        break
                except (SystemExit, KeyboardInterrupt):
                    break

            assert data

            # wampy wraps network traffic into websocket Frames.
            # see wampy.networking.frames for more details.
            response_message = data.payload

            welcome_or_challenge, session_id, dealer_roles = response_message

            assert welcome_or_challenge == Message.WELCOME
            assert session_id

            assert dealer_roles['realm'] == 'realm1'
            assert dealer_roles['roles']['broker']
            assert dealer_roles['roles']['broker']['features'] == {
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

            assert dealer_roles['roles']['dealer']
            assert dealer_roles['roles']['dealer']['features'] == {
                'payload_encryption_cryptobox': True,
                'payload_transparency': True,
                'pattern_based_registration': True,
                'registration_revocation': True,
                'shared_registration': True,
                'caller_identification': True,
                'session_meta_api': True,
                'registration_meta_api': True,
            }

        except Exception:
            logger.exception('HELLO example failed')

        crossbar.stop()
