import pytest

from wampy.peers.clients import Client


@pytest.fixture(autouse=True)
def config_path():
    return './wampy/testing/configs/crossbar.config.ipv4.json'


@pytest.yield_fixture
def client(router):
    with Client(router=router) as client:
        yield client
