import datetime
from datetime import date

from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES
from wampy.entrypoints import rpc
from wampy.peers import Client


class DateService(Client):
    """ A service that tells you todays date """

    @property
    def name(self):
        return 'Date Service'

    @rpc
    def get_todays_date(self):
        return datetime.date.today().isoformat()


def test_call_with_no_args_or_kwargs(router):
    callee = DateService(
        name="Date Service", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    callee.start()

    caller = Client(
        name="Caller", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    caller.start()

    response = caller.make_rpc(procedure="get_todays_date")
    today = date.today()

    assert response == today.isoformat()

    callee.stop()
    caller.stop()
