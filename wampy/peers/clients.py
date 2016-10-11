import eventlet

from wampy.bases import Peer
from wampy.errors import WampProtocolError
from wampy.messages import Message
from wampy.roles.publisher import PublisherMixin
from wampy.roles.callee import CalleeMixin
from wampy.roles.caller import CallerMixin, RpcMixin
from wampy.roles.subscriber import SubscriberMixin


class ClientBase(Peer):

    def start(self):
        # kick off the connection and the listener of it
        self._connect_to_router()
        # then then the session over the connection
        self._say_hello_to_router()

        def wait_for_session():
            with eventlet.Timeout(5):
                while self.session is None:
                    eventlet.sleep(0)

        wait_for_session()
        self._register_entrypoints()
        self.logger.info('%s has started', self.name)

    def stop(self):
        self._say_goodbye_to_router()
        message = self._wait_for_message()
        if message[0] != Message.GOODBYE:
            raise WampProtocolError(
                "Unexpected response from router following GOODBYE: {}".format(
                    message
                )
            )

        self.managed_thread.kill()
        self.session = None
        self.subscription_map = {}
        self.logger.info('%s has stopped', self.name)

    def get_subscription_info(self, subscription_id):
        """ Retrieves information on a particular subscription. """
        return self.call("wamp.subscription.get", subscription_id)

    def get_subscription_list(self):
        """ Retrieves subscription IDs listed according to match
        policies."""
        return self.call("wamp.subscription.list")

    def get_subscription_lookup(self, topic):
        """ Obtains the subscription (if any) managing a topic,
        according to some match policy. """
        return self.call("wamp.subscription.lookup", topic)

    def get_subscription_match(self, topic):
        """ Retrieves a list of IDs of subscriptions matching a topic
        URI, irrespective of match policy. """
        return self.call("wamp.subscription.match", topic)

    def list_subscribers(self, subscription_id):
        """ Retrieves a list of session IDs for sessions currently
        attached to the subscription. """
        return self.call(
            "wamp.subscription.list_subscribers", subscription_id)

    def count_subscribers(self, subscription_id):
        """ Obtains the number of sessions currently attached to the
        subscription. """

        return self.call(
            "wamp.subscription.count_subscribers", subscription_id)

    def get_registration_list(self):
        """ Retrieves registration IDs listed according to match
        policies."""
        return self.call("wamp.registration.list")

    def get_registration_lookup(self, procedure_name):
        """ Obtains the registration (if any) managing a procedure,
        according to some match policy."""
        return self.call("wamp.registration.lookup", procedure_name)

    def get_registration_match(self, procedure_name):
        """ Obtains the registration best matching a given procedure
        URI."""
        return self.call("wamp.registration.match", procedure_name)

    def get_registration(self, registration_id):
        """ Retrieves information on a particular registration. """
        return self.call("wamp.registration.get", registration_id)

    def list_callees(self, registration_id):
        """ Retrieves a list of session IDs for sessions currently
        attached to the registration. """
        return self.call(
            "wamp.registration.list_callees", registration_id)

    def count_callees(self, registration_id):
        """ Obtains the number of sessions currently attached to a
        registration. """
        return self.call(
            "wamp.registration.count_callees", registration_id)


class StandAlone(
        ClientBase, CallerMixin, CalleeMixin, PublisherMixin, SubscriberMixin):
    """ A WAMP Client for use in Python applications, scripts and shells.
    """


class RpcClient(ClientBase, RpcMixin):
    """ A simple client to call remote procedures by name """


class ServiceBase(
        ClientBase, RpcMixin, CalleeMixin, PublisherMixin, SubscriberMixin):
    """ A WAMP Client for use in microservices.
    """
