import logging
import socket
import ssl
import uuid
from base64 import encodestring
from urlparse import urlsplit
from socket import error as socket_error

import eventlet

from wampy.constants import WEBSOCKET_SUBPROTOCOLS, WEBSOCKET_VERSION
from wampy.errors import (
    IncompleteFrameError, ConnectionError, WampProtocolError, WampyError)

from . frames import ClientFrame, ServerFrame

logger = logging.getLogger(__name__)


class WampWebSocket(object):

    def __init__(self, router):
        self.url = router.url

        self.host = None
        self.port = None
        self.ipv = router.ipv
        self.resource = None

        self._parse_url()
        self.websocket_location = self.resource
        self.key = encodestring(uuid.uuid4().bytes).decode('utf-8').strip()
        self.socket = None

    def _parse_url(self):
        """
        Parses a URL which must have one of the following forms:

        - ws://host[:port][path]
        - wss://host[:port][path]
        - ws+unix:///path/to/my.socket

        In the first two cases, the ``host`` and ``port``
        attributes will be set to the parsed values. If no port
        is explicitely provided, it will be either 80 or 443
        based on the scheme. Also, the ``resource`` attribute is
        set to the path segment of the URL (alongside any querystring).

        In addition, if the scheme is ``ws+unix``, the
        ``unix_socket_path`` attribute is set to the path to
        the Unix socket while the ``resource`` attribute is
        set to ``/``.
        """
        # Python 2.6.1 and below don't parse ws or wss urls properly.
        # netloc is empty.
        # See: https://github.com/Lawouach/WebSocket-for-Python/issues/59
        scheme, url = self.url.split(":", 1)

        parsed = urlsplit(url, scheme="http")
        if parsed.hostname:
            self.host = parsed.hostname
        elif '+unix' in scheme:
            self.host = 'localhost'
        else:
            raise ValueError("Invalid hostname from: %s", self.url)

        if parsed.port:
            self.port = parsed.port

        if scheme == "ws":
            if not self.port:
                self.port = 80
        elif scheme == "wss":
            if not self.port:
                self.port = 443
        elif scheme in ('ws+unix', 'wss+unix'):
            pass
        else:
            raise ValueError("Invalid scheme: %s" % scheme)

        if parsed.path:
            resource = parsed.path
        else:
            resource = "/"

        if '+unix' in scheme:
            self.unix_socket_path = resource
            resource = '/'

        if parsed.query:
            resource += "?" + parsed.query

        self.scheme = scheme
        self.resource = resource

    def _connect(self):
        if self.ipv == 4:
            _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                _socket.connect((self.host, self.port))
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

    def _upgrade(self):
        handshake_headers = self._get_handshake_headers()
        handshake = '\r\n'.join(handshake_headers) + "\r\n\r\n"

        self.socket.send(handshake)

        try:
            with eventlet.Timeout(5):
                self.status, self.headers = self._read_handshake_response()
        except eventlet.Timeout:
            raise WampyError(
                'No response after handshake "{}"'.format(handshake)
            )

        logger.debug("WAMP Connection reply: %s", self.headers)

    def _get_handshake_headers(self):
        """ Do an HTTP upgrade handshake with the server.

        Websockets upgrade from HTTP rather than TCP largely because it was
        assumed that servers which provide websockets will always be talking to
        a browser. Maybe a reasonable assumption once upon a time...

        The headers here will go a little further and also agree the
        WAMP websocket JSON subprotocols.

        """
        headers = []
        # https://tools.ietf.org/html/rfc6455
        headers.append("GET /{} HTTP/1.1".format(self.websocket_location))
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
        headers.append("Sec-WebSocket-Protocol: {}".format(
            WEBSOCKET_SUBPROTOCOLS))
        logger.info(headers)
        return headers

    def _read_handshake_response(self):
        status = None
        headers = {}

        while True:
            # we need this to guarantee we can context switch back to the
            # Timeout.
            eventlet.sleep()

            line = self._recv_handshake_response_by_line()

            try:
                line = line.decode('utf-8')
            except:
                line = u'{}'.format(line)

            if line == "\r\n" or line == "\n":
                break

            line = line.strip()
            if line == '':
                continue

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

        return status, headers

    def _recv_handshake_response_by_line(self):
        received_bytes = bytearray()

        while True:
            bytes = self.socket.recv(1)

            if not bytes:
                break

            received_bytes.append(bytes)

            if bytes == "\n" or bytes == "\r\n":
                # a complete line has been received
                break

        return received_bytes

    def connect(self):
        self._connect()
        self._upgrade()

    def read_websocket_frame(self, bufsize=1):
        frame = None
        received_bytes = bytearray()

        while True:
            logger.debug("waiting for %s bytes", bufsize)

            try:
                bytes = self.socket.recv(bufsize)
            except eventlet.greenlet.GreenletExit as exc:
                raise ConnectionError('Connection closed: "{}"'.format(exc))
            except socket.timeout as e:
                message = str(e)
                raise ConnectionError('timeout: "{}"'.format(message))
            except Exception as exc:
                raise ConnectionError('error: "{}"'.format(exc))

            if not bytes:
                break

            logger.debug("received %s bytes", bufsize)
            received_bytes.extend(bytes)

            try:
                frame = ServerFrame(received_bytes)
            except IncompleteFrameError as exc:
                bufsize = exc.required_bytes
            else:
                break

        if frame is None:
            raise WampProtocolError("No frame returned")

        return frame

    def send_websocket_frame(self, message):
        frame = ClientFrame(message)
        self.socket.sendall(frame.payload)


class TLSWampWebSocket(WampWebSocket):
    def __init__(self, router):
        super(TLSWampWebSocket, self).__init__(router)

        self.ipv = router.ipv
        self.ssl_version = ssl.PROTOCOL_TLSv1_2
        self.certificate = router.certificate

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
