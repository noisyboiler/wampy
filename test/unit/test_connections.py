from mock import ANY

from wampy.networking.connection import WampConnection


def test_local_wamp_connection(router):
    connection = WampConnection(host='localhost', port=8080)
    connection.connect()

    # it's the same as a websocket, but other hoops have been jumped through
    assert connection.status == 101
    assert connection.headers == {
        'connection': 'upgrade',
        'sec-websocket-accept': ANY,
        'sec-websocket-protocol': 'wamp.2.json',
        'server': 'crossbar/0.13.0',
        'status': 101,
        'status_info': ['HTTP/1.1', '101', 'Switching Protocols'],
        'upgrade': 'websocket',
        'x-powered-by': ANY,
    }
