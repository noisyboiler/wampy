
from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES
from wampy.messages.call import Call
from wampy.peers.clients import WampClient
from wampy.registry import Registry
from wampy.rpc import rpc


class DateService(WampClient):

    @rpc
    def get_date(self):
        return "2016-01-01"


def test_registration_and_goodbye(router):
    client = WampClient(
        name="Caller", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    client.start()

    message = Call(
        procedure="wamp.registration.list",
    )
    message.construct()
    client.send_message(message)
    response = client.receive_message()

    # e.g. [
    #     50, 3892220001, {},
    #     [{u'prefix': [], u'exact': [427621208574865], u'wildcard': []}]
    # ]
    wamp_code, _, _, registrations = response
    assert wamp_code == 50  # result

    registered = registrations[0]['exact']
    assert len(registered) == 0

    # Now fire up a service
    service = DateService(
        name="Date Service", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    service.start()

    client.send_message(message)
    response = client.receive_message()

    wamp_code, _, _, registrations = response
    assert wamp_code == 50  # result

    registered = registrations[0]['exact']
    assert len(registered) == 1

    date_service = registered[0]

    assert date_service in Registry.registration_map.keys()

    # Now stop the service
    service.stop()

    client.send_message(message)
    response = client.receive_message()
    wamp_code, _, _, registrations = response
    assert wamp_code == 50  # result

    registered = registrations[0]['exact']
    assert len(registered) == 0

    client.stop()
