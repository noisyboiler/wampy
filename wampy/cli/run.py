# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" usage

wampy run module:app

Largely experimental for now.... sorry.

"""
import errno
import logging
import os
import sys

import gevent

from wampy.peers.routers import Crossbar

logger = logging.getLogger("cli")


class CommandError(Exception):
    pass


def import_module(module_name):

    try:
        __import__(module_name)
    except ImportError:
        if module_name.endswith(".py") and os.path.exists(module_name):
            raise CommandError(
                "Failed to find module, did you mean '{}'?".format(
                    module_name[:-3].replace('/', '.')
                )
            )

        raise

    module = sys.modules[module_name]
    return module


class AppRunner(object):

    def __init__(self):
        self.apps = []

    def add_app(self, app):
        self.apps.append(app)

    def start(self):
        for app in self.apps:
            print("starting up app: %s" % app.name)
            app.start()
            print("{} is now starting up.".format(app.name))

    def stop(self):
        for app in self.apps:
            app.stop()
        print('runner stopped')
        sys.exit(0)


def run(apps, config_path=None):
    router = Crossbar(config_path=config_path)
    router_url = router.url

    print("starting up services...")
    runner = AppRunner()

    for app in apps:
        module_name, app_name = app.split(':')
        mod = import_module(module_name)
        app_class = getattr(mod, app_name)
        app = app_class(url=router_url)
        runner.add_app(app)

    runner.start()

    while True:
        try:
            gevent.sleep()
        except OSError as exc:
            if exc.errno == errno.EINTR:
                continue
            raise
        except KeyboardInterrupt:
            try:
                runner.stop()
            except KeyboardInterrupt:
                runner.stop()
        except Exception:
            logger.exception("cannot start runner")
            break


def main(args):
    if '.' not in sys.path:
        sys.path.insert(0, '.')

    app = args.application
    config_path = args.config
    run(app, config_path)


def init_parser(parser):
    parser.add_argument(
        'application', nargs='+',
        metavar='module[:application class]',
        help='python path to one wampy application class to run')

    parser.add_argument(
        '--config', default='./crossbar/config.json',
        help='Crossbar config file path')

    return parser
