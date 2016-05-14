
class Registry:
    client_registry = {}
    registration_map = {}
    request_map = {}

    @classmethod
    def clear(cls):
        cls.client_registry = {}
        cls.registration_map = {}
        cls.request_map = {}


def get_client_registry():
    return Registry.client_registry


def get_registered_entrypoints():
    return Registry.registration_map
