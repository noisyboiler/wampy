import pytest
import gevent
from gevent import Greenlet
from geventwebsocket import WebSocketServer, Resource

from wampy.transports.websocket.connection import WebSocket


@pytest.fixture
def server():
    s = WebSocketServer(
        ('0.0.0.0', 8001),
        Resource([]),
        debug=False,
    )
    thread = Greenlet.spawn(s.serve_forever)
    yield s
    thread.kill()


def test_websocket_connects_to_server(server):
    websocket = WebSocket(server_url='ws://0.0.0.0:8001')
    websocket.connect()
    websocket.disconnect()


def __test_send_ping(server):
    websocket = WebSocket(server_url='ws://0.0.0.0:8000')
    websocket.connect()




