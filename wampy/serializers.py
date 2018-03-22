# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import simplejson as json
from wampy.errors import WampProtocolError


def json_serialize(message):
    # WAMP serialization insists on UTF-8 encoded Unicode
    try:
        data = json.dumps(
            message, separators=(',', ':'), ensure_ascii=False,
            encoding='utf-8',
        )
    except TypeError as exc:
        raise WampProtocolError(
            "Message not serialized: {} - {}".format(
                message, str(exc)
            )
        )

    return data
