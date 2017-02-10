import datetime
from datetime import date

from wampy.peers.clients import Client
from wampy.roles.callee import rpc


class DateService(Client):

    @rpc
    def get_todays_date(self):
        return datetime.date.today().isoformat()


def test_connection(router):
    service = DateService(router=router, transport="ws")
    with service:

        client = Client(router=router, transport="ws")

        with client:
            result = client.rpc.get_todays_date()

    today = date.today()

    assert result == today.isoformat()


def test_secure_connection(tls_router):
    service = DateService(router=tls_router, transport="ws")
    with service:

        client = Client(router=tls_router, transport="ws")

        with client:
            result = client.rpc.get_todays_date()

    today = date.today()

    assert result == today.isoformat()
