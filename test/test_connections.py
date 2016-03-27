from wampy.constants import (
    DEFAULT_WEB_SERVER_HOST, DEFAULT_WEB_SERVER_PORT)
from wampy.networking.connections.http import HttpConnection
from wampy.networking.connections.websocket import (
    WebsocketConnection)
from wampy.networking.connections.wamp import WampConnection


def test_http_connection(http_pong_server):
    connection = HttpConnection(
        host=DEFAULT_WEB_SERVER_HOST, port=DEFAULT_WEB_SERVER_PORT)
    connection.connect()

    assert connection.status == 200

    # TODO: assert headers


def test_websocket_connection(http_pong_server):
    connection = WebsocketConnection(
        host=DEFAULT_WEB_SERVER_HOST, port=DEFAULT_WEB_SERVER_PORT)
    connection.connect()

    assert connection.status == 200


def test_wamp_connection(basic_profile_router):
    connection = WampConnection(host='127.0.0.1', port=8080)
    connection.connect()

    # it's the same as a websocket, but other hoops have been jumped through
    assert connection.status == 101
