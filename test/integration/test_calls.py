from wampy.constants import DEFAULT_REALM, DEFAULT_ROLES
from wampy.peers.clients import WampClient, RpcClient
from wampy.peers.routers import WampRouter
from wampy.rpc import rpc


class HelloService(WampClient):

    @rpc
    def say_hello(self, name):
        message = "Hello {}".format(name)
        return message

    @rpc
    def say_greeting(self, name, greeting="hola"):
        message = "{greeting} to {name}".format(
            greeting=greeting, name=name)
        return message


def test_remote_call():
    router = WampRouter(
        name="Crossbar", host="wampy.online", port=8082)

    with HelloService(
        name="Hello Service", router=router,
        realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
    ):

        caller = RpcClient(
            name="Caller", router=router,
            realm=DEFAULT_REALM, roles=DEFAULT_ROLES,
        )
        caller.start()

        response = caller.rpc.say_hello("Simon")

        assert response == "Hello Simon"

        caller.stop()
