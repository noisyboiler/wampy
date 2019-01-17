# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import binascii
import hmac
import hashlib


def compute_wcs(key, challenge):
    """
    Compute an WAMP-CRA authentication signature from an authentication
    challenge and a (derived) key.

    :param key: The key derived (via PBKDF2) from the secret.
    :type key: str/bytes
    :param challenge: The authentication challenge to sign.
    :type challenge: str/bytes

    :return: The authentication signature.
    :rtype: bytes
    """
    key = key.encode('utf8')
    challenge = challenge.encode('utf8')
    sig = hmac.new(key, challenge, hashlib.sha256).digest()
    return binascii.b2a_base64(sig).strip()
