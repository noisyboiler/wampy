import json

import yaml

from . constants import CONFIG_PATH, DEFAULT_HOST
from . exceptions import ConfigurationError
from . logger import get_logger


logger = get_logger('wampy.helpesr')


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]


def collect_configuration():
    config = {}

    try:
        with open(CONFIG_PATH, 'r') as fh:
            config = yaml.load(fh)
    except IOError:
        logger.warning(
            'You should create a ```config.yaml``` defining some '
            'Peers and their roles - see ```config.example.yaml``` '
            'for guideance.'
        )

    return config


def load_router_configuration(peer_name, global_config):
    if peer_name not in ['Crossbar']:
        raise ConfigurationError(
            'Router not supported: "{}"'.format(peer_name)
        )

    for peer_config in global_config['peers'].values():
        if peer_config['name'] == peer_name:
            peer_config = peer_config
            break
    else:
        raise ConfigurationError(
            'no config for peer: "{}"'.format(peer_name)
        )

    local_config_path = peer_config['local_configuration']

    with open(local_config_path) as data_file:
        data = json.load(data_file)

    config = {
        'host': peer_config.get('host', DEFAULT_HOST),
        'port': data['workers'][0]['transports'][0]['endpoint']['port'],
        'realm': data['workers'][0]['realms'][0]['name'],
        'roles': data['workers'][0]['realms'][0]['roles'][0],
    }

    global_config['router'] = config
