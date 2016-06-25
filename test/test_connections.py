from mock import ANY

from wampy.networking.connections.tcp import TCPConnection
from wampy.networking.connections.http import HttpConnection
from wampy.networking.connections.websocket import (
    WebsocketConnection)
from wampy.networking.connections.wamp import WampConnection


def test_http_connection(http_pong_server):
    connection = HttpConnection(host='localhost', port=8080)
    connection.connect()

    assert connection.status == 200
    assert connection.headers == {
        'status': 200,
        'date': ANY,
        'status_info': ['HTTP/1.1', '200', 'OK'],
        'content-type': 'text/plain', 'content-length': '7',
    }


def test_websocket_connection(http_pong_server):
    connection = WebsocketConnection(host='localhost', port=8080)
    connection.connect()

    assert connection.status == 200
    assert connection.headers == {
        'status': 200,
        'date': ANY,
        'status_info': ['HTTP/1.1', '200', 'OK'],
        'content-type': 'text/plain', 'content-length': '7',
    }


def test_wamp_connection(router):
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
