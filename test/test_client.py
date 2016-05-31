from wampy.peer import ClientBase


def test_client_connects_to_router(router):

    class MyClient(ClientBase):
        pass

    client = MyClient(name="my test client", router=router)
    assert client.running is False
    assert client.session is None

    client.start()

    assert client.running is True
    assert client.session is not None

    client.stop()

    assert client.running is False
    assert client.session is None
