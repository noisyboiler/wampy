from mock import ANY

from wampy.networking.connection import WampConnection


def test_remote_host_wamp_connection():
    connection = WampConnection(host='wampy.online', port=8082)
    connection.connect()

    assert connection.status == 101
    assert connection.headers == {
        'status': 101,
        'upgrade': 'websocket',
        'sec-websocket-accept': ANY,
        'x-powered-by': 'autobahnpython/0.13.1',
        'sec-websocket-protocol': 'wamp.2.json',
        'server': 'crossbar/0.13.2',
        'connection': 'upgrade',
        'status_info': [
            'HTTP/1.1', '101', 'Switching Protocols'
        ]
    }
