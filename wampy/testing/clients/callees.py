import datetime

from ... constants import CALLEE
from ... entrypoints import rpc
from ... logger import get_logger
from ... mixins import HandleMessageMixin
from ... roles import Callee


logger = get_logger('wampy.testing.clients.callees.date_service')


class DateService(HandleMessageMixin, Callee):
    """ A service that tells you todays date """

    def __init__(self, router=None):
        self._router = router

    @property
    def name(self):
        return 'Date Service'

    @property
    def role(self):
        return CALLEE

    @property
    def config(self):
        return {}

    @property
    def router(self):
        return self._router

    @rpc
    def get_todays_date(self):
        logger.info('getting todays date')
        return datetime.date.today().isoformat()
