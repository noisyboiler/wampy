import logging

from . tcp import TCPConnection


logger = logging.getLogger(__name__)


class HttpConnection(TCPConnection):
    type_ = 'http'

    def __init__(self, host, port):
        super(HttpConnection, self).__init__(host, port)

    def _upgrade(self):
        headers = self._get_handshake_headers()
        handshake = '\r\n'.join(headers) + "\r\n\r\n"
        self.send(handshake)
        self.status, self.headers = self._read_handshake_response()
        logger.info('HTTP Connection status: "%s"', self.status)

    def _get_handshake_headers(self):
        headers = []
        headers.append("GET / HTTP/1.1")
        return headers

    def _read_handshake_response(self):
        logger.info('reading handshake')
        status = None
        headers = {}

        while True:
            line = self._recv_handshake_response_by_line()

            try:
                line = line.decode('utf-8')
            except:
                line = u'{}'.format(line)

            logger.warning(line)
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

        return status, headers

    def _recv_handshake_response_by_line(self):
        logger.info('reading handshake by line')
        received_bytes = bytearray()

        while True:
            bytes = self.socket.recv(bufsize=1)

            if not bytes:
                break

            received_bytes.append(bytes)

            if bytes == "\n" or bytes == "\r\n":
                # a complete line has been received
                logger.info('complete line read')
                break

        return received_bytes
