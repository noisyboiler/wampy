# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

try:
    from urlparse import urlsplit
except ImportError:
    from urllib.parse import urlsplit


class ParseUrlMixin(object):
    def parse_url(self):
        """ Parses a URL of the form:

        - ws://host[:port][path]
        - wss://host[:port][path]
        - ws+unix:///path/to/my.socket

        """
        self.scheme = None
        self.resource = None
        self.host = None
        self.port = None

        if self.url is None:
            return

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
                self.port = 8080
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
