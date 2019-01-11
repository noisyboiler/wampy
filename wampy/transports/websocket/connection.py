# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import sched
import socket
import ssl
import uuid
from base64 import encodestring
from socket import error as socket_error
from time import time

from wampy.backends import async_adapter
from wampy.backends.errors import WampyTimeOut
from wampy.config.defaults import heartbeat, heartbeat_timeout
from wampy.constants import (
    WEBSOCKET_SUBPROTOCOLS, WEBSOCKET_VERSION,
)
from wampy.errors import (
    IncompleteFrameError, ConnectionError, WampProtocolError, WampyError,
)
from wampy.interfaces import Transport
from wampy.mixins import ParseUrlMixin
from wampy.serializers import json_serialize

from . frames import FrameFactory, Ping, Pong, Text

logger = logging.getLogger(__name__)


class WebSocket(Transport, ParseUrlMixin):

    def __init__(self, server_url, ipv=4):

        self.url = server_url
        self.ipv = ipv

        self.host = None
        self.port = None
        self.resource = None

        self.parse_url()
        self.websocket_location = self.resource
        self.key = encodestring(uuid.uuid4().bytes).decode('utf-8').strip()
        self.socket = None
        self.connected = False

        self._first_pinged_at = None
        self._pinged_at = None
        self._pong_pointer = None

        self.pongs = async_adapter.queue()
        self.missed_pongs = 0
        self.is_pinging = False

    def connect(self, upgrade=True):
        # TCP connection
        self._connect()
        self._handshake(upgrade=upgrade)

        if heartbeat > 0:
            self.start_pinging()
        return self

    def disconnect(self):
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except socket.error:
                pass

            self.socket.close()

    def send(self, message):
        frame = Text(payload=json_serialize(message))
        websocket_message = frame.frame
        self._send_raw(websocket_message)

    def _send_raw(self, websocket_message):
        logger.debug('send raw: %s', websocket_message)
        self.socket.sendall(websocket_message)

    def receive(self, bufsize=1):
        frame = None
        received_bytes = bytearray()

        while True:
            try:
                bytes_ = self.socket.recv(bufsize)
            except socket.timeout as e:
                message = str(e)
                raise ConnectionError('timeout: "{}"'.format(message))
            except Exception as exc:
                raise ConnectionError('Connection lost: "{}"'.format(exc))
            if not bytes_:
                break

            received_bytes.extend(bytes_)

            try:
                frame = FrameFactory.from_bytes(received_bytes)
            except IncompleteFrameError as exc:
                bufsize = exc.required_bytes
            else:
                if frame.opcode == frame.OPCODE_PING:
                    # Opcode 0x9 marks a ping frame. It does not contain wamp
                    # data, so the frame is not returned.
                    # Still it must be handled or the server will close the
                    # connection.
                    async_adapter.spawn(self.handle_ping(ping_frame=frame))
                    received_bytes = bytearray()
                    continue
                if frame.opcode == frame.OPCODE_PONG:
                    self.handle_pong(pong_frame=frame)
                    received_bytes = bytearray()
                    continue
                if frame.opcode == frame.OPCODE_BINARY:
                    break
                if frame.opcode == frame.OPCODE_CLOSE:
                    self.handle_close(close_frame=frame)

                break

        if frame is None:
            raise WampProtocolError("No frame returned")

        return frame

    def _connect(self):
        if self.ipv == 4:
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                _socket.connect((self.host.encode(), self.port))
            except socket_error as exc:
                if exc.errno == 61:
                    logger.error(
                        'unable to connect to %s:%s (IPV%s)',
                        self.host, self.port, self.ipv
                    )

                raise

        elif self.ipv == 6:
            _socket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

            try:
                _socket.connect(("::", self.port))
            except socket_error as exc:
                if exc.errno == 61:
                    logger.error(
                        'unable to connect to %s:%s (IPV%s)',
                        self.host, self.port, self.ipv
                    )

                raise

        else:
            raise WampyError(
                "unknown IPV: {}".format(self.ipv)
            )

        self.socket = _socket
        logger.debug("socket connected")

    def _handshake(self, upgrade):
        handshake_headers = self._get_handshake_headers(upgrade=upgrade)
        handshake = '\r\n'.join(handshake_headers) + "\r\n\r\n"

        self.socket.send(handshake.encode())

        try:
            with async_adapter.Timeout(5):
                self.status, self.headers = self._read_handshake_response()
        except WampyTimeOut:
            raise WampyError(
                'No response after handshake "{}"'.format(handshake)
            )

        logger.debug("connection upgraded")

    def _get_handshake_headers(self, upgrade):
        """ Do an HTTP upgrade handshake with the server.

        Websockets upgrade from HTTP rather than TCP largely because it was
        assumed that servers which provide websockets will always be talking to
        a browser. Maybe a reasonable assumption once upon a time...

        The headers here will go a little further and also agree the
        WAMP websocket JSON subprotocols.

        """
        headers = []
        # https://tools.ietf.org/html/rfc6455
        headers.append("GET {} HTTP/1.1".format(self.websocket_location))
        headers.append("Host: {}:{}".format(self.host, self.port))
        headers.append("Upgrade: websocket")
        headers.append("Connection: Upgrade")
        # Sec-WebSocket-Key header containing base64-encoded random bytes,
        # and the server replies with a hash of the key in the
        # Sec-WebSocket-Accept header. This is intended to prevent a caching
        # proxy from re-sending a previous WebSocket conversation and does not
        # provide any authentication, privacy or integrity
        headers.append("Sec-WebSocket-Key: {}".format(self.key))
        headers.append("Origin: ws://{}:{}".format(self.host, self.port))
        headers.append("Sec-WebSocket-Version: {}".format(WEBSOCKET_VERSION))

        if upgrade:
            headers.append("Sec-WebSocket-Protocol: {}".format(
                WEBSOCKET_SUBPROTOCOLS)
            )

        logger.debug("connection headers: %s", headers)

        return headers

    def _read_handshake_response(self):
        # each header ends with \r\n and there's an extra \r\n after the last
        # one
        status = None
        headers = {}

        def read_line():
            bytes_cache = []
            received_bytes = None
            while received_bytes not in [b'\r\n', b'\n', b'\n\r']:
                received_bytes = self.socket.recv(1)
                bytes_cache.append(received_bytes)
            return b''.join(bytes_cache)

        while True:
            received_bytes = read_line()
            if received_bytes == b'\r\n':
                # end of the response
                break

            bytes_as_str = received_bytes.decode()
            line = bytes_as_str.strip()

            if not status:
                status_info = line.split(" ", 2)
                try:
                    status = int(status_info[1])
                except IndexError:
                    logger.warning('unexpected handshake resposne')
                    logger.error('%s', status_info)
                    raise

                headers['status_info'] = status_info
                headers['status'] = status
                continue

            kv = line.split(":", 1)
            if len(kv) != 2:
                raise Exception(
                    'Invalid header: "{}"'.format(line)
                )

            key, value = kv
            headers[key.lower()] = value.strip().lower()

        logger.info("handshake complete: %s : %s", status, headers)
        self.connected = True
        return status, headers

    def start_pinging(self):

        def websocket_ping_thread(socket):
            s = sched.scheduler(time, async_adapter.sleep)

            def send_ping_and_expect_pong():
                payload = 'wampy::' + str(uuid.uuid4())
                # we send a Ping with a unique payload, and we expect
                # a Pong back echoing the same payload - but within the
                # deadline of ``heartbeat_timeout_seconds``.
                ping = Ping(payload=payload, mask_payload=True)

                try:
                    socket.sendall(bytes(ping.frame))
                except OSError:
                    # connection closed by parent thread, or wampy
                    # has been disconnected from server...
                    # either way, this gthread will be killed as
                    # soon if the Close message is received else
                    # schedule another Ping
                    logger.info('ping failed')
                    pass
                except BrokenPipeError:
                    logger.info('server ripped out from under us!')
                    pass

                pong = None

                with async_adapter.Timeout(
                    heartbeat_timeout, raise_after=False
                ):
                    while pong is None:
                        # required for Hub to implelent TimeOut
                        async_adapter.sleep()

                        try:
                            maybe_my_pong = self.pongs.get(block=False)
                        except async_adapter.QueueEmpty:
                            continue

                        if maybe_my_pong:
                            if maybe_my_pong.payload == payload:
                                pong = maybe_my_pong
                            else:
                                # possibly Pinging faster than the server is
                                # Ponging, else Hub hasn't scheduled the right
                                # gthread yet.
                                logger.error('Pongs out of order?')
                                self.pongs.put(maybe_my_pong)

                if pong is None:
                    logger.info('missed a Pong from the server')
                    self.missed_pongs += 1

            def pinger(sc):
                # do i need to spawn here???
                async_adapter.spawn(send_ping_and_expect_pong)
                s.enter(heartbeat, 1, pinger, (sc,))

            s.enter(heartbeat, 1, pinger, (s,))

            # the first Ping will be emitted after the first "hearbeat"
            # seconds, i.e. *not* immediatly
            s.run()

        self.pinger_thread = async_adapter.spawn(
            websocket_ping_thread, self.socket
        )
        self.is_pinging = True

    def handle_ping(self, ping_frame):
        pong_frame = Pong(payload=ping_frame.payload)
        bytes_ = pong_frame.frame
        self._send_raw(bytes_)

    def handle_pong(self, pong_frame):
        self.pongs.put(pong_frame)

    def handle_close(self, close_frame):
        logger.warning(
            'server closed connection: %s', close_frame.payload,
        )
        self.stop_pinging()
        self.disconnect()

    def stop_pinging(self):
        try:
            self.pinger_thread.kill()
        except AttributeError:
            pass
        self.is_pinging = False


class SecureWebSocket(WebSocket):
    def __init__(self, server_url, certificate_path, ipv=4):
        super(SecureWebSocket, self).__init__(server_url=server_url, ipv=ipv)

        # PROTOCOL_TLSv1_1 and PROTOCOL_TLSv1_2 are only available if Python is
        # linked with OpenSSL 1.0.1 or later.
        try:
            self.ssl_version = ssl.PROTOCOL_TLSv1_2
        except AttributeError:
            raise WampyError("Your Python Environment does not support TLS")

        self.certificate = certificate_path

    def _connect(self):
        _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        wrapped_socket = ssl.wrap_socket(
            _socket,
            ssl_version=self.ssl_version,
            ciphers="ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:\
            DH+AES:ECDH+3DES:DH+3DES:RSA+AES:RSA+3DES:!ADH:!AECDH:!MD5:!DSS",
            cert_reqs=ssl.CERT_REQUIRED,
            ca_certs=self.certificate,
        )

        try:
            wrapped_socket.connect((self.host, self.port))
        except socket_error as exc:
            if exc.errno == 61:
                logger.error(
                    'unable to connect to %s:%s', self.host, self.port
                )

            raise

        self.socket = wrapped_socket
