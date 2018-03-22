import os

from wampy.constants import GEVENT
from . async import async_adapter  # noqa

async_name = os.environ.get('WAMPY_ASYNC_NAME', GEVENT)
