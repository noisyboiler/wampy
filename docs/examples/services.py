import datetime

from wampy.peers import WebApplication
from wampy.roles import register_rpc


class DateService(WebApplication):
    """ A web service that returns the current date.

    usage ::

        $ wampy run docs.examples.services:DateService --router http://example.com:port

    This service can then be called as such ::

        In [1]: from wampy.peers import WebClient

        In [2]: with WebClient(name="wampy", host="examaple.com", port=port) as client:
           ...:     date = client.rpc.get_todays_date()

        In [3]: date
        Out[3]: u'2016-11-26'

    """
    @register_rpc
    def get_todays_date(self):
        return datetime.date.today().isoformat()
