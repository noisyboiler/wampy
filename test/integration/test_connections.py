from mock import ANY

from wampy.networking.connections.tcp import TCPConnection
from wampy.networking.connections.http import HttpConnection
from wampy.networking.connections.wamp import WampConnection


def test_remote_tcp_crossbar_connection():
    connection = TCPConnection(host='wampy.online', port=8082)
    connection.connect()


def test_remote_http_crossbar_connection():
    connection = HttpConnection(host='wampy.online', port=8082)
    connection.connect()

    assert connection.status == 404  # yes, this is the expected behaviour!
    assert connection.headers == {
        'status': 404,
        'content-length': ANY,
        'server': 'crossbar/0.13.2',
        'date': ANY,
        'status_info': [
            'HTTP/1.1', '404', 'Not Found'
        ],
        'content-type': 'text/html'
    }


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
