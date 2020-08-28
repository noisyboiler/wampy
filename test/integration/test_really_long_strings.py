from wampy.peers.clients import Client


def test_send_really_long_string(router, echo_service):
    really_long_string = "a" * 1000

    caller = Client(url=router.url)
    with caller:
        response = caller.rpc.echo(message=really_long_string)

    assert response['message'] == really_long_string
