import sys
if sys.version_info[0] < 3:
    import SocketServer as socketserver
else:
    import socketserver

from wampy.mixins import ParseUrlMixin


class WebSocketHandler(socketserver.BaseRequestHandler):
    # taken from Python docs
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())


class WebsocketServer(socketserver.TCPServer, ParseUrlMixin):

    def __init__(self, url, ipv=4):
        self.url = url
        self.host = None
        self.port = None
        self.parse_url()

        super(
            socketserver.TCPServer, self
        ).__init__((self.host, self.port), WebSocketHandler)
