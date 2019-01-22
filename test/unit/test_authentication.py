# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys

import pytest

from wampy.auth import compute_wcs


# deterministic only for specifc python versions
@pytest.mark.skipif(sys.version_info != (3, 6), reason="requires python3")
def test_compute_wamp_challenge_response():
    secret = 'prq7+YkJ1/KlW1X0YczMHw=='
    challenge_data = {
        "authid": "peter",
        "authrole": "wampy",
        "authmethod": "wampcra",
        "authprovider": "static",
        "session": 3071302313344522,
        "nonce": "acL4f0gAqPijddsa6ko555z5nTLF3pjWp0lO0okYDvCC4GhXt8NbTooRaeYjNwTu",  # noqa
        "timestamp": "2019-01-17T12:09:52.508Z",
    }

    expected_signature = b'bn55LVCWcn68Zrqifsn8Dh0YZMfhmnyeRd0Hrllqlg4='

    assert compute_wcs(secret, str(challenge_data)) == expected_signature
