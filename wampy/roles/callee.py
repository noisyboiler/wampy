# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import logging
import types
from functools import partial


logger = logging.getLogger(__name__)


class RegisterProcedureDecorator(object):

    def __init__(self, *args, **kwargs):
        self.invocation_policy = kwargs.get("invocation_policy", "single")

    @classmethod
    def decorator(cls, *args, **kwargs):

        def registering_decorator(fn, args, kwargs):
            invocation_policy = kwargs.get("invocation_policy", "single")
            fn.callee = True
            fn.invocation_policy = invocation_policy
            return fn

        if len(args) == 1 and isinstance(args[0], types.FunctionType):
            # usage without arguments to the decorator:
            return registering_decorator(args[0], args=(), kwargs={})
        else:
            # usage with arguments to the decorator:
            return partial(registering_decorator, args=args, kwargs=kwargs)


callee = RegisterProcedureDecorator.decorator
