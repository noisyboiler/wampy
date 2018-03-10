from threading import Thread

import pytest
from geventwebsocket import WebSocketServer, Resource

from wampy.transports.websocket.connection import WebSocket


@pytest.fixture(scope='function')
def server():
    s = WebSocketServer(
        ('0.0.0.0', 8000),
        Resource([]),
        debug=False,
    )

    server_thread = Thread(target=s.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    yield s
    s.stop()


def test_websocket_connects_to_server(server):
    websocket = WebSocket(server_url='ws://0.0.0.0:8000')
    websocket.connect()
    websocket.disconnect()
