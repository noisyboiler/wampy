import eventlet
from eventlet import wsgi

from wampy.constants import DEFAULT_HOST, DEFAULT_PORT


def pong_server(env, start_response):
    """ return the string 'PONG' to any HTTP connection """
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return ['PONG!\r\n']


def start_pong_server():
    wsgi.server(
        eventlet.listen((DEFAULT_HOST, DEFAULT_PORT)), pong_server)
