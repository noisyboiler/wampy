import datetime

from ... entrypoints import rpc
from ... logger import get_logger

from ... peer import ClientBase


logger = get_logger('wampy.testing.clients.callees.date_service')


class DateService(ClientBase):
    """ A service that tells you todays date """

    @property
    def name(self):
        return 'Date Service'

    @rpc
    def get_todays_date(self):
        logger.info('getting todays date')
        return datetime.date.today().isoformat()
