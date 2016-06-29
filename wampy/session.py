import logging


logger = logging.getLogger('wampy.wamp.session')


class Session(object):
    """ A WAMP Session.

    A Session is a transient conversation between two roles attached to a
    Realm and running over a Transport.

    WAMP Sessions are established over a WAMP Connection.

    A WAMP Session is joined to a Realm on a Router.

    """

    def __init__(self, client, router, session_id):
        self.id = session_id
        self.client = client
        self.router = router
