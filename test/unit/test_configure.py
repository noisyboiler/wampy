import logging

from mock import patch


def test_configure_logging(caplog):
    from wampy import configure_logging
    caplog.set_level(logging.INFO)
    configure_logging()

    assert 'logging configured' in caplog.text


def test_configure_gevent_async(caplog):
    from wampy import configure_async
    caplog.set_level(logging.INFO)
    configure_async()

    assert 'gevent monkey-patched your environment' in caplog.text


def test_configure_eventlet_async(caplog):
    from wampy import configure_async
    with patch('wampy.async_name', 'eventlet'):
        configure_async()

    assert 'eventlet monkey-patched your environment' in caplog.text
