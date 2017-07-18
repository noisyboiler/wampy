# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from . call import Call
from . error import Error
from . event import Event
from . hello import Hello
from . invocation import Invocation
from . goodbye import Goodbye
from . message import Message
from . publish import Publish
from . register import Register
from . registered import Registered
from . result import Result
from . subscribe import Subscribe
from . subscribed import Subscribed
from . yield_ import Yield
from . welcome import Welcome


__all__ = [
    Call, Error, Event, Goodbye, Hello, Invocation, Message, Publish,
    Register, Registered, Result, Subscribe, Subscribed, Welcome, Yield
]


MESSAGE_TYPE_MAP = {
    1: 'HELLO',
    2: 'WELCOME',
    3: 'ABORT',
    6: 'GOODBYE',
    8: 'ERROR',
    16: 'PUBLISH',
    32: 'SUBSCRIBE',
    33: 'SUBSCRIBED',
    36: 'EVENT',
    48: 'CALL',
    50: 'RESULT',
    64: 'REGISTER',
    65: 'REGISTERED',
    66: 'UNREGISTER',
    67: 'UNREGISTERED',
    68: 'INVOCATION',
    70: 'YIELD',
}
