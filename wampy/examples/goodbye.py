from wampy.logger import get_logger
from wampy.session import Session
from wampy.messages.goodbye import Goodbye as GoodbyeMessage
from wampy.messages import MESSAGE_TYPE_MAP
from wampy.protocol import register_peer
from wampy.testing.routers.crossbar import Crossbar


logger = get_logger('examples.goodbye')


class Goodbye(object):

    def send(self):
        """ Simple "GOODBYE" to Router example.

        Sent by a Peer to close a previously opened WAMP session.  Must be
        echo'ed by the receiving Peer.

        Represented as ::

            [GOODBYE, Details|dict, Reason|uri]

        """
        crossbar = Crossbar(
            host='localhost',
            config_path='./router/config.json',
            crossbar_directory='./',
        )

        register_peer(crossbar)

        session = Session(crossbar)
        session.begin()

        message = GoodbyeMessage()
        message.construct()
        response_message = session.send_and_receive(message)
        crossbar.stop()

        wamp_code, details, reason = response_message

        assert wamp_code == 6
        assert MESSAGE_TYPE_MAP[wamp_code] == 'GOODBYE'
        assert details == {}
        assert reason == GoodbyeMessage.DEFAULT_REASON  # "wamp.close.normal"

        logger.info('Goodbye sent to router: "%s"', response_message)
