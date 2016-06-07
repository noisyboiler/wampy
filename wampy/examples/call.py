""" The message flow between Callers, a Dealer and Callees for
calling procedures and invoking endpoints involves the following
messages:

1.  "CALL"
2.  "RESULT"
3.  "INVOCATION"
4.  "YIELD"
5.  "ERROR"

"""
from wampy.exceptions import WampProtocolError
from wampy.logger import get_logger
from wampy.messages import Message, MESSAGE_TYPE_MAP
from wampy.protocol import register_peer
from wampy.testing.routers.crossbar import Crossbar

from . peers.clients.callee import CalleeApplication
from . peers.clients.caller import CallerApplication

logger = get_logger('examples.call')


class Call(object):
    """ A Peer makes a CALL to a Dealer naming a registered procedure.

    If the Dealer is able to mediate the call - and it allows the call -
    it sends a "INVOCATION" message to the respective Callee implementing
    the procedure ::

        [
            CALL, Request|id, Options|dict, Procedure|uri, Arguments|list,
            ArgumentsKw|dict
        ]

    "Request" is a random, ephemeral ID chosen by the _Caller_ and
    used to correlate the Dealer's response with the request.

    "Options" is a dictionary that allows to provide additional call
    request details in an extensible way.  This is described further
    below.

    "Procedure" is the URI of the procedure to be called.

    "Arguments" is a list of positional call arguments (each of
    arbitrary type).  The list may be of zero length.

    "ArgumentsKw" is a dictionary of keyword call arguments (each of
    arbitrary type).  The dictionary may be empty.

    """
    def run(self):
        crossbar = Crossbar(
            host='localhost',
            config_path='./router/config.json',
            crossbar_directory='./',
        )
        callee_client = CalleeApplication()

        register_peer(crossbar)
        register_peer(callee_client)

        caller = CallerApplication(crossbar)
        caller.call(procedure="foo")
        logger.info('rpc call made to "foo"')

        resp_message = caller.wait_for_message()
        logger.info('wamp response: "%s"', resp_message)
        crossbar.stop()

        wamp_code, original_request_id, details, result_args = resp_message

        assert wamp_code == Message.RESULT

        result = result_args[0]
        assert result == 'FOO SUCCESS'

        logger.info('rpc result received: "%s"', result)


class CallWithError(object):
    """ Invocation ERROR.

    [ERROR, INVOCATION, INVOCATION.Request|id, Details|dict,
    Error|uri, Arguments|list, ArgumentsKw|dict]

    "INVOCATION.Request" is the ID from the original "INVOCATION"
    equest previously sent by the Dealer to the Callee.

    "Details" is a dictionary with additional error details.

    "Error" is an URI that identifies the error of why the request
    could not be fulfilled.

    "Arguments" is a list containing arbitrary, application defined,
    positional error information.  This will be forwarded by the
    Dealer to the Caller that initiated the call.

    "ArgumentsKw" is a dictionary containing arbitrary, application
    defined, keyword-based error information.  This will be forwarded
    by the Dealer to the Caller that initiated the call.

    """
    def __init__(self):
        pass


class CallToWriteProtectedObjectError(CallWithError):
    """ A Peer makes a CALL to a Dealer naming a registered procedure but
    can not invocate the call on the Callee.

    The Dealer is unable to mediate this request and returns an error ::

        [
            8, 68, 6131533, {}, "com.myapp.error.object_write_protected",
            ["Object is write protected."], {"severity": 3}
        ]

    """


class ProcedureAlreadyRegisteredError(CallWithError):
    """ A Peer makes a CALL to a Dealer naming a registered procedure but
    that procedure has already been registerd.

    The Dealer is unable to mediate this request and returns an error ::

        [
            8,64,10000,{},"wamp.error.procedure_already_exists",
            ["register for already registered procedure 'foo.spam'"]
        ]

    """


class CallToNoSuchProcedureError(CallWithError):
    """ When a peer makes a CALL to a procedure that has not been
    registered by a Callee then an ERROR messgae is returned by the
    Dealer. ::

        [
            8, 48, 6131533, {}, "wamp.error.no_such_procedure",
            ["no callee registered for procedure..."]
        ]

    """
    def run(self):
        crossbar = Crossbar(
            host='localhost',
            config_path='./router/config.json',
            crossbar_directory='./',
        )
        callee_client = CalleeApplication()

        register_peer(crossbar)
        register_peer(callee_client)

        caller = CallerApplication(crossbar)
        logger.info('making rpc call made to "foo.bar.spam"')

        try:
            caller.call(procedure="foo.bar.spam")
        except WampProtocolError as exc:
            logger.error(str(exc))

        resp = caller.wait_for_message()
        crossbar.stop()

        (message_code, originating_message_code, details,
            originating_request_id, error_uri, args) = resp

        assert message_code == 8
        assert MESSAGE_TYPE_MAP[8] == 'ERROR'

        assert originating_message_code == 48
        assert MESSAGE_TYPE_MAP[48] == 'CALL'

        assert error_uri == 'wamp.error.no_such_procedure'

        assert len(args) == 1

        assert "no callee registered for procedure" in args[0]
        assert "foo.bar.spam" in args[0]

        print args[0]
