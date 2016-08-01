from wampy.messages.call import Call
from wampy import Peer
from wampy.registry import Registry
from wampy.entrypoints import rpc


class DateService(Peer):

    @rpc
    def get_date(self):
        return "2016-01-01"


def test_registration_and_goodbye(router):
    client = Peer(name="Caller")
    client.start()

    message = Call(
        procedure="wamp.registration.list",
    )

    client.send_message(message)
    response = client.recv_message()

    # e.g. [
    #     50, 3892220001, {},
    #     [{u'prefix': [], u'exact': [427621208574865], u'wildcard': []}]
    # ]
    wamp_code, _, _, registrations = response
    assert wamp_code == 50  # result

    registered = registrations[0]['exact']
    assert len(registered) == 0

    # Now fire up a service
    service = DateService(name="Date Service")
    service.start()

    client.send_message(message)
    response = client.recv_message()

    wamp_code, _, _, registrations = response
    assert wamp_code == 50  # result

    registered = registrations[0]['exact']
    assert len(registered) == 1

    date_service_id = registered[0]
    assert date_service_id in Registry.registration_map.keys()

    # get the meta data on this registration
    metadata_call_message = Call(
        procedure="wamp.registration.get",
        args=[date_service_id],
    )

    client.send_message(metadata_call_message)
    response = client.recv_message()

    wamp_code, registered_id, _, data_list = response
    assert wamp_code == 50  # result
    assert len(data_list) == 1

    metadata = data_list[0]
    assert metadata['id'] == date_service_id
    assert metadata['match'] == 'exact'
    assert metadata['uri'] == 'get_date'

    # Now stop the service
    service.stop()

    client.send_message(message)
    response = client.recv_message()
    wamp_code, _, _, registrations = response
    assert wamp_code == 50  # result

    registered = registrations[0]['exact']
    assert len(registered) == 0

    client.stop()
