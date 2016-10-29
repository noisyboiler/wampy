import datetime

from wampy.peers import WebApplication
from wampy.roles import register_rpc


class DateService(WebApplication):

    @register_rpc
    def get_todays_date(self):
        return datetime.date.today().isoformat()
