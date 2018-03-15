# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import array
import logging
import json
import os
from struct import pack, unpack_from

from wampy.errors import (
    WampyError, WebsocktProtocolError, IncompleteFrameError
)


logger = logging.getLogger('wampy.networking.frames')


class Frame(object):
    """ The framing is what distinguishes the connection from a raw TCP
    one - it's part of the websocket protocol.

    """
    #    ws-frame      = frame-fin           ; 1 bit in length
    #                    frame-rsv1          ; 1 bit in length
    #                    frame-rsv2          ; 1 bit in length
    #                    frame-rsv3          ; 1 bit in length
    #                    frame-opcode        ; 4 bits in length
    #                    frame-masked        ; 1 bit in length
    #                    frame-payload-length    ; either 7, 7+16,
    #                                            ; or 7+64 bits in
    #                                            ; length
    #                    [ frame-masking-key ]   ; 32 bits in length
    #                    frame-payload-data      ; n*8 bits in
    #                                            ; length, where
    #
    #                                            ; n >= 0

    # protocol constants are represented in base16/hexidecimal.

    # always use "text" as the type of data to send
    TEXT = 0x01  # 1, 00000001

    # always send an entire message as one frame
    FIN = 0x80  # 128

    # opcodes indicate what the frame represents e.g. a ping, a pong,
    # a acontinuation data from last or a termination, et all.

    OPCODE_BINARY = 0x2
    OPCODE_CONT = 0x0
    OPCODE_CLOSE = 0x8
    OPCODE_PING = 0x9
    OPCODE_PONG = 0xa
    OPCODE_TEXT = 0x1
    OPCODES = (
        OPCODE_BINARY, OPCODE_CONT, OPCODE_CLOSE,
        OPCODE_PING, OPCODE_PONG, OPCODE_TEXT,
    )

    CONTROL_FRAMES = [OPCODE_PING, ]

    # Frame Length

    # The WebSocket protocol has a frame-size limit of 2^63 octets, but
    # a WebSocket message can be composed of an unlimited number of frames.

    # websocket frames come in 3 length brackets: 7bit, 16bit and 64bit.
    # this does mean that there is more than one way to represent the
    # length of the payload.... but the spec insiste you only use the
    # shortest bracket available. clear?

    # i.e. inspect bits 9-15 to determine the payload length or what bits
    # to inspect to *actually* determine the payload length.

    # 9-15: 0-125   means the payload is that long
    #       126     means the length is actually determined by bits
    #               16 through 31, i.e. the next bracket size up
    #       127     means the length is actually determined by bits 16
    #               through 79, i.e. the largest bracket

    LENGTH_7 = 0x7e  # 0x7e, 126, 01111110
    LENGTH_16 = 1 << 16  # 0x10000, 65536, 10000000000000000
    MAX_LENGTH = 1 << 63  # 1 x 2**63

    def __init__(self, bytes, payload=None):
        self.bytes = bytes
        self.opcode = bytes[0] & 0xf
        # this is just the payload, i.e. the bytes that the application cares
        # about
        self.payload = payload or Frame.generate_payload(bytes)

    def __len__(self):
        try:
            unicode_body = self.payload.decode("utf-8")
        except UnicodeError:
            unicode_body = self.payload
        except AttributeError:
            # already decoded, hence no "decode" attribute
            unicode_body = self.payload

        return len(unicode_body)

    def __str__(self):
        return self.payload

    @classmethod
    def generate_payload(cls, bytes):
        if not bytes:
            raise IncompleteFrameError(required_bytes=1)

        # Parse the first two bytes of header.
        fin = bytes[0] >> 7

        if fin == 0:
            logger.exception("Multiple Frames Returned: %s", bytes)
            raise WampyError(
                'Multiple framed responses not yet supported: {}'.format(bytes)
            )

        try:
            payload_length_indicator = bytes[1] & 0b1111111
        except Exception:
            raise IncompleteFrameError(required_bytes=1)

        available_bytes_for_body = bytes[2:]

        if not available_bytes_for_body:
            return None

        available_bytes_for_body = bytes[2:]

        try:
            available_bytes_for_body[1]
        except IndexError:
            raise IncompleteFrameError(required_bytes=payload_length_indicator)

        # unpack the buffered bytes into an integer
        body_length = unpack_from(">h", available_bytes_for_body)[0]

        if payload_length_indicator < 126:
            # then we have enough knowlege about the payload length as it's
            # contained within the 2nd byte of the header - because the
            # trailing 7 bits of the 2 bytes tells us exactly how long the
            # payload is
            body_candidate = available_bytes_for_body
            # in this case body length is represented by the indicator
            body_length = payload_length_indicator

        elif payload_length_indicator == 126:
            # then we don't have enough knowledge yet.
            # and actually the following two bytes indicate the payload length.
            # get all buffered bytes beyond the header and the excluded 2 bytes
            body_candidate = available_bytes_for_body[2:]  # require >= 2 bytes

        else:
            # actually, the following eight bytes indicate the payload length.
            # so check we have at least as much as we need, else exit.
            body_candidate = available_bytes_for_body[6:]  # require >= 8 bytes

        if len(body_candidate) < body_length:
            required_bytes = body_length - len(body_candidate)
            logger.debug("missing %s bytes", required_bytes)
            raise IncompleteFrameError(
                required_bytes=required_bytes
            )

        try:
            # decode required before loading JSON for python 2 only
            payload = json.loads(body_candidate.decode('utf-8'))
        except Exception:
            raise WebsocktProtocolError(
                'Failed to load JSON object from: "%s"', body_candidate
            )

        return payload

    @property
    def frame(self):
        return self.bytes


class FrameFactory(object):

    @classmethod
    def from_bytes(cls, bytes):
        payload = Frame.generate_payload(bytes)
        logger.info('got a frame: %s', bytes)
        if payload is None:
            opcode = bytes[0] & 0xf
            if opcode == Frame.OPCODE_BINARY:
                # binary - the handshake response?
                return Frame(bytes=bytes, payload=None)

            if opcode in Frame.CONTROL_FRAMES:
                if opcode == Frame.OPCODE_PING:
                    return Ping()

            raise IncompleteFrameError(required_bytes=1)

        return Frame(bytes=bytes, payload=payload)


class ClientFrame(Frame):
    """ Represent outgoing Client -> Server messages.

    Takes a paylod and wraps it in a WebSocket frame.

    """

    def __init__(self, message):
        """

        :Parameters:
            message : str
                The data to be sent to the server. Tbis will form the
                "payload" segments of the WebSocket frame(s).

        """
        self.fin_bit = 1
        self.opcode = Frame.OPCODE_TEXT
        self.payload = message
        self.bytes = self.generate_frame(message)

    def data_to_bytes(self, data):
        return bytearray(data, 'utf-8')

    def generate_mask(self, mask_key, data):
        """ Mask data.

        :Parameters:
            mask_key: byte string
                4 byte string(byte), e.g. '\x10\xc6\xc4\x16'
            data: str
                data to mask

        """
        # Masking of WebSocket traffic from client to server is required
        # because of the unlikely chance that malicious code could cause
        # some broken proxies to do the wrong thing and use this as an
        # attack of some kind. Nobody has proved that this could actually
        # happen, but since the fact that it could happen was reason enough
        # for browser vendors to get twitchy, masking was added to remove
        # the possibility of it being used as an attack.
        if data is None:
            data = ""

        data_bytes = self.data_to_bytes(data)

        _m = array.array("B", mask_key)
        _d = array.array("B", data_bytes)

        for i in range(len(_d)):
            _d[i] ^= _m[i % 4]

        return _d.tostring()

    def generate_frame(self, message):
        """ Format data to string (bytes) to send to server.
        """
        # the first byte contains the FIN bit, the 3 RSV bits and the
        # 4 opcode bits and for a client will *always* be 1000 0001 (or 129).
        # so we want the first byte to look like...
        #
        #  1 0 0 0 0 0 0 1   (1 is a text frame)
        # +-+-+-+-+-------+
        # |F|R|R|R| opcode|
        # |I|S|S|S|       |
        # |N|V|V|V|       |
        # | |1|2|3|       |
        # +-+-+-+-+-------+
        # note that because all RSV bits are zero, we can ignore them
        fin_bit = 1

        # this shifts each bit into position and bitwise ORs them together,
        # using the struct module to pack them as incoming network bytes
        payload = pack(
            '!B', (
                (fin_bit << 7) |
                self.opcode
            )
        )  # which is '\x81' as a raw byte repr

        # the second byte - and maybe the 7 after this, we'll use to tell
        # the server how long our payload is.

        #                 +-+-------------+-------------------------------+
        #                 |M| Payload len |    Extended payload length    |
        #                 |A|     (7)     |             (16/63)           |
        #                 |S|             |   (if payload len==126/127)   |
        #                 |K|             |                               |
        # +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
        # |     Extended payload length continued, if payload len == 127  |
        # + - - - - - - - - - - - - - - - +-------------------------------+

        # the mask is always included with client -> server, so the first bit
        # of the second byte is always 1 which flags that the data is masked,
        # i.e. encoded
        mask_bit = 1 << 7
        # next we have to | this bit with the payload length, if not too long!
        length = len(self)
        if length >= self.MAX_LENGTH:
            raise WebsocktProtocolError("data is too long")

        # the second byte contains the payload length and mask
        if length < self.LENGTH_7:
            # we can simply represent payload length with first 7 bits
            payload += pack('!B', (mask_bit | length))
        elif length < self.LENGTH_16:
            payload += pack('!B', (mask_bit | 126)) + pack('!H', length)
        else:
            payload += pack('!B', (mask_bit | 127)) + pack('!Q', length)

        # we always mask frames from the client to server
        # use a string of n random bytes for the mask
        mask_key = os.urandom(4)
        mask_data = self.generate_mask(mask_key=mask_key, data=message)
        mask = mask_key + mask_data
        payload += mask

        # this is a bytes string being returned here
        return payload


class Ping(Frame):

    def __init__(self, message=''):
        """

        :Parameters:
            message : str
                An optional message to send along with the PING,
                e.g. "hello". Forms the ``payload`` of the WebSocket
                message.

        """
        # PING is a Control Frame denoted by the opcode 9
        # this modelsa PING from the Server -> Client, and as such does
        # not mask.
        self.fin_bit = 1
        self.opcode = Frame.OPCODE_PING
        self.bytes = self.generate_frame()

    def generate_frame(self):
        # This is long hand for documentation purposes

        # the first byte contains the FIN bit, the 3 RSV bits and the
        # 4 opcode bits, so we are looking for

        #  1 0 0 0 0 1 0 1   Opcode 9 for a Ping Frame
        # +-+-+-+-+-------+
        # |F|R|R|R| opcode|
        # |I|S|S|S|       |
        # |N|V|V|V|       |
        # | |1|2|3|       |
        # +-+-+-+-+-------+

        # this shifts each bit into position and bitwise ORs them together,
        # using the struct module to pack them as incoming network bytes
        b0 = pack(
            '!B', (
                (self.fin_bit << 7) |
                self.opcode
            )
        )  # which is '\x81' as a raw byte repr

        # frame-masked              ; 1 bit in length
        # frame-payload-length      ; either 7, 7+16,
        #                           ; or 7+64 bits in length

        # second byte, payload len bytes and mask, so we are looking for

        #  0 0 0 0 0 0 0 0
        # +-+-+-+-+-------+
        # |M| payload len |
        # |A|             |
        # |S|             |
        # |K|             |
        # +-+-+-+-+-------+

        b1 = 0
        # as implemented here, the Client could not send this as it is not
        # masking
        mask_bit = 0 << 7
        # next we have to | this bit with the payload length,
        # if not too long!
        b1 = pack('!B', (mask_bit | 0))

        bytes = b''.join([b0, b1])

        first_byte = bytes[0]
        assert self.opcode == first_byte & 0xf

        # we could append payload data such as a HELLO here...
        # then we'd have to update the 2nd byte with the new length

        return bytes  # this is b'\x89\x00'


class PongFrame(Frame):

    def __init__(self, payload=''):
        self.fin_bit = 1
        self.opcode = Frame.OPCODE_PONG
        self.bytes = self.generate_frame()

    def generate_frame(self):
        b0 = pack(
            '!B', (
                (self.fin_bit << 7) |
                self.opcode
            )
        )

        b1 = 0
        mask_bit = 1 << 7  # masked, as the Client is sending
        b1 = pack('!B', (mask_bit | 0))
        bytes = b''.join([b0, b1])

        first_byte = bytes[0]
        assert self.opcode == first_byte & 0xf

        return bytes  # this is b'\x8a\x00'
