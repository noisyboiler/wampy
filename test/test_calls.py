import datetime
from datetime import date

from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES
from wampy.rpc import rpc
from wampy.peers.clients import WampClient, RpcClient


class DateService(WampClient):
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

    caller = RpcClient(
        name="Caller", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    )
    caller.start()

    response = caller.rpc.get_todays_date()
    today = date.today()

    assert response == today.isoformat()

    callee.stop()
    caller.stop()
