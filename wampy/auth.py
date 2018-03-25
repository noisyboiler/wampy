# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import binascii
import hmac
import hashlib
from struct import Struct
from operator import xor
from itertools import starmap

try:
    from itertools import izip as zip
except ImportError:
    pass

_pack_int = Struct('>I').pack


def pbkdf2(data, salt, iterations=1000, keylen=32, hashfunc=None):
    """Returns a binary digest for the PBKDF2 hash algorithm of `data`
    with the given `salt`.  It iterates `iterations` time and produces a
    key of `keylen` bytes.
    """
    def _pseudorandom(x, mac):
        h = mac.copy()
        h.update(x)
        return map(ord, h.digest())

    hashfunc = hashfunc or hashlib.sha256
    mac = hmac.new(data, None, hashfunc)
    buf = []
    for block in range(1, -(-keylen // mac.digest_size) + 1):
        rv = u = _pseudorandom(salt + _pack_int(block), mac)
        for i in range(iterations - 1):
            u = _pseudorandom(''.join(map(chr, u)), mac)
            rv = starmap(xor, zip(rv, u))
        buf.extend(rv)
    return ''.join(map(chr, buf))[:keylen]


def derive_key(secret, salt, iterations=1000, keylen=32):
    secret = secret.encode('utf8')
    salt = salt.encode('utf8')
    key = pbkdf2(secret, salt, iterations, keylen)
    return binascii.b2a_base64(key).strip()


def compute_wcs(key, challenge):
    """
    Compute an WAMP-CRA authentication signature from an authentication
    challenge and a (derived) key.

    :param key: The key derived (via PBKDF2) from the secret.
    :type key: bytes
    :param challenge: The authentication challenge to sign.
    :type challenge: bytes

    :return: The authentication signature.
    :rtype: bytes
    """
    key = key.encode('utf8')
    challenge = challenge.encode('utf8')
    sig = hmac.new(key, challenge, hashlib.sha256).digest()
    return binascii.b2a_base64(sig).strip()
