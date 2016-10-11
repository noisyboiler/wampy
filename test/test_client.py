from wampy.peers.clients import StandAlone as Client


def test_client_connects_to_router(router):

    class MyClient(Client):
        pass

    client = MyClient(name="my test client")

    assert client.session is None

    client.start()

    session = client.session
    assert session.id is not None
    assert session.client is client
    assert session.router is client.host

    client.stop()

    assert client.session is None


def test_can_start_two_clients(router):

    class MyClient(Client):
        pass

    app_one = MyClient(name="my test client")
    app_one.start()
    assert app_one.session.id

    app_two = MyClient(name="Client Two")
    app_two.start()
    assert app_two.session.id

    app_one.stop()
    app_two.stop()

    assert app_one.session is None
    assert app_two.session is None
