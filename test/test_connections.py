from mock import ANY

from wampy.networking.connection import WampWebConnection


def test_local_wamp_connection(router):
    connection = WampWebConnection(host='localhost', port=8080)
    connection.connect()

    # it's the same as a websocket, but other hoops have been jumped through
    assert connection.status == 101
    assert connection.headers == {
        'connection': 'upgrade',
        'sec-websocket-accept': ANY,
        'sec-websocket-protocol': 'wamp.2.json',
        'server': 'crossbar',
        'status': 101,
        'status_info': ['HTTP/1.1', '101', 'Switching Protocols'],
        'upgrade': 'websocket',
    }
