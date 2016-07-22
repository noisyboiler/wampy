
class Registry:
    client_registry = {}
    registration_map = {}
    request_map = {}
    subscription_map = {}

    @classmethod
    def clear(cls):
        cls.client_registry = {}
        cls.registration_map = {}
        cls.request_map = {}
        cls.subscription_map = {}


def get_client_registry():
    return Registry.client_registry


def get_registered_entrypoints():
    return Registry.registration_map


def get_registered_entrypoint_names():
    entrypoints = get_registered_entrypoints()
    return [
        app_name_tuple[1] for app_name_tuple in entrypoints.values()
    ]
