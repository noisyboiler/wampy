# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

from wampy.errors import WampProtocolError


def json_serialize(message_obj):
    try:
        return json.dumps(
            message_obj.message, separators=(',', ':'), ensure_ascii=False,
        )
    except TypeError as exc:
        raise WampProtocolError(
            "Message not serialized: {} - {}".format(
                message_obj.message, str(exc)
            )
        )
