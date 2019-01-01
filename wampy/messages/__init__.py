# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from . abort import Abort
from . authenticate import Authenticate
from . call import Call
from . cancel import Cancel
from . challenge import Challenge
from . error import Error
from . event import Event
from . hello import Hello
from . invocation import Invocation
from . goodbye import Goodbye
from . publish import Publish
from . register import Register
from . registered import Registered
from . result import Result
from . subscribe import Subscribe
from . subscribed import Subscribed
from . yield_ import Yield
from . welcome import Welcome


__all__ = [
    Abort, Authenticate, Call, Challenge, Error, Event, Goodbye, Hello,
    Invocation, Publish, Register, Registered, Result, Subscribe,
    Subscribed, Welcome, Yield
]


MESSAGE_TYPE_MAP = {
    1: Hello,
    2: Welcome,
    3: Abort,
    4: Challenge,
    5: Authenticate,
    6: Goodbye,
    8: Error,
    16: Publish,
    32: Subscribe,
    33: Subscribed,
    36: Event,
    48: Call,
    49: Cancel,
    50: Result,
    64: Register,
    65: Registered,
    68: Invocation,
    70: Yield,
}
