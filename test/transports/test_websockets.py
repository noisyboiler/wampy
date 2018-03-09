import socket
from threading import Thread

import pytest
from wampy.testing.websocket_server import WebsocketServer

from wampy.transports.websocket.connection import WebSocket

HOST, PORT = "localhost", 9999

@pytest.fixture(scope='function')
def server():
    s = WebsocketServer(url="ws://localhost:9999")
    server_thread = Thread(target=s.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    yield s
    import pdb
    pdb.set_trace()
    s.server_close()


def test_websocket_connects_to_server(server):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

