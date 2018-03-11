from collections import OrderedDict

import pytest
import gevent
from gevent import Greenlet
from geventwebsocket import (
    WebSocketApplication, WebSocketServer, Resource,
)
from mock import patch

from wampy.transports.websocket.connection import WebSocket
from wampy.transports.websocket.frames import Ping


class TestApplication(WebSocketApplication):
    pass


@pytest.fixture
def server():
    s = WebSocketServer(
        ('0.0.0.0', 8001),
        Resource(OrderedDict([('/', TestApplication)]))
    )
    s.start()
    thread = Greenlet.spawn(s.serve_forever)
    yield s
    s.stop()
    thread.kill()


def test_websocket_connects_to_server(server):
    websocket = WebSocket(server_url='ws://0.0.0.0:8001')

    assert not hasattr(server, 'socket')

    websocket.connect()
    assert hasattr(server, 'socket')
    assert server.clients

    websocket.disconnect()


def test_send_ping(server):
    websocket = WebSocket(server_url='ws://0.0.0.0:8001')
    connection = websocket.connect(upgrade=False)

    def connection_handler():
        while True:
            try:
                message = connection.receive()

            except Exception as exc:
                print(type(exc), exc)
                raise

        return message

    thread = gevent.spawn(connection_handler)

    with patch.object(websocket, 'handle_ping') as mock_handle:
        while not hasattr(server, 'socket'):
            gevent.sleep(0.01)

        clients = server.clients
        assert len(clients) == 1

        client_handler = list(clients.values())[0]
        socket = client_handler.ws

        frame = Ping()
        payload = frame.payload

        ping_masked_bytes = b'0x8a0x850x370xfa0x210x3d0x7f0x9f0x4d0x510x58'

        socket.send(payload)

    thread.kill()
