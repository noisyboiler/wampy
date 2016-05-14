from mock import ANY
from mock import Mock

from wampy.networking.connections.http import HttpConnection
from wampy.networking.connections.websocket import (
    WebsocketConnection)
from wampy.networking.connections.wamp import WampConnection
from wampy.session import Session


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


def test_wamp_session(router):
    client = Mock(name="test client")
    session = Session(router, client)
    assert session.id is None

    session.begin()
    assert session.alive is True

    session.end()
    assert session.alive is False
