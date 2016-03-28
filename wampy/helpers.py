import yaml

from . constants import CONFIG_PATH


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]


def collect_configuration():
    with open(CONFIG_PATH, 'r') as fh:
        docs = yaml.load(fh)

    return docs
