from wampy.peers.clients import DefaultClient as Client


def test_client_connects_to_router(router):

    class MyClient(Client):
        pass

    client = MyClient()

    assert client.session.id is None

    client.start()

    session = client.session
    assert session.id is not None
    assert session.client is client

    client.stop()

    assert client.session.id is None


def test_can_start_two_clients(router):

    class MyClient(Client):
        pass

    app_one = MyClient()
    app_one.start()
    assert app_one.session.id

    app_two = MyClient()
    app_two.start()
    assert app_two.session.id

    app_one.stop()
    app_two.stop()

    assert app_one.session.id is None
    assert app_two.session.id is None
