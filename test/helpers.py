# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from wampy.backends import async_adapter


def assert_stops_raising(
        fn, exception_type=Exception, timeout=5, interval=0.1):

    with async_adapter.Timeout(timeout):
        while True:
            try:
                fn()
            except exception_type:
                pass
            else:
                return
            async_adapter.sleep(interval)
