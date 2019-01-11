# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import array
import logging
import os
from struct import pack, unpack_from

from wampy.errors import WebsocktProtocolError, IncompleteFrameError


logger = logging.getLogger(__name__)


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
    OPCODE_PONG = 0xA
    OPCODE_TEXT = 0x1
    OPCODES = (
        OPCODE_BINARY, OPCODE_CONT, OPCODE_CLOSE,
        OPCODE_PING, OPCODE_PONG, OPCODE_TEXT,
    )

    # not intended to carry data for the application but instead for
    # protocol-level signaling,
    CONTROL_FRAMES = [OPCODE_PING, OPCODE_PONG, OPCODE_CLOSE]

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

    def __init__(self, raw_bytes):
        """ Represent a complete websocket frame """
        self.raw_bytes = bytearray(raw_bytes)
        self.fin_bit = self.raw_bytes[0] >> 7
        self.opcode = self.raw_bytes[0] & 0xf
        self.payload_length_indicator = self.raw_bytes[1] & 0b1111111

        self._raw_bytes = raw_bytes

    def __str__(self):
        return self.payload

    @property
    def frame(self):
        return self._raw_bytes

    @property
    def payload(self):
        try:
            if self.payload_length_indicator < 126:
                payload_str = self.raw_bytes[2:].decode('utf-8')
            elif self.payload_length_indicator == 126:
                payload_str = self.raw_bytes[4:].decode('utf-8')
            else:
                payload_str = self.raw_bytes[6:].decode('utf-8')
        except UnicodeDecodeError:
            logger.error('cannot decode %s', self.raw_bytes)
            raise

        return payload_str


class FrameFactory(object):

    @classmethod
    def from_bytes(cls, buffered_bytes):
        if not buffered_bytes or len(buffered_bytes) < 2:
            raise IncompleteFrameError(required_bytes=1)

        opcode = buffered_bytes[0] & 0xf
        if opcode not in Frame.OPCODES:
            raise WebsocktProtocolError('unknown opcode: %s', opcode)

        # binary data interpretation is left up to th application...
        if opcode == Frame.OPCODE_BINARY:
            return Frame(raw_bytes=buffered_bytes)

        # Parse the first two buffered_bytes of header
        fin = buffered_bytes[0] >> 7
        if fin == 0:
            logger.warning('fragmented frame received: %s', buffered_bytes)

        payload_length_indicator = buffered_bytes[1] & 0b1111111
        if payload_length_indicator == 0:
            if opcode == Frame.OPCODE_PING:
                return Ping(raw_bytes=buffered_bytes)
            elif opcode == Frame.OPCODE_CLOSE:
                return Close(raw_bytes=buffered_bytes)
            else:
                return Frame(raw_bytes=buffered_bytes)

        available_bytes_for_body = buffered_bytes[2:]
        if len(available_bytes_for_body) < 2:
            raise IncompleteFrameError(
                required_bytes=payload_length_indicator
            )

        # unpack the buffered buffered_bytes into an integer
        body_length = unpack_from(">h", available_bytes_for_body)[0]

        if payload_length_indicator < 126:
            # then we have enough knowlege about the payload length as it's
            # contained within the 2nd byte of the header - because the
            # trailing 7 bits of the 2 buffered_bytes tells us exactly how long
            # the payload is
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
            logger.debug("missing %s buffered_bytes", required_bytes)
            raise IncompleteFrameError(
                required_bytes=required_bytes
            )

        if opcode == Frame.OPCODE_PING:
            return Ping(raw_bytes=buffered_bytes)

        if opcode == Frame.OPCODE_PONG:
            return Pong(raw_bytes=buffered_bytes)

        if opcode == Frame.OPCODE_CLOSE:
            return Close(raw_bytes=buffered_bytes)

        return Frame(raw_bytes=buffered_bytes)

    @classmethod
    def generate_mask(cls, mask_key, data):
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

        data = bytearray(data, 'utf-8')

        _m = array.array("B", mask_key)
        _d = array.array("B", data)

        for i in range(len(_d)):
            _d[i] ^= _m[i % 4]

        return _d.tostring()

    @classmethod
    def generate_bytes(cls, payload, fin_bit, opcode, mask_payload):
        """ Format data to string (buffered_bytes) to send to server.
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

        # this shifts each bit into position and bitwise ORs them together,
        # using the struct module to pack them as incoming network bytes
        frame = pack(
            '!B', (
                (fin_bit << 7) | opcode
            )
        )

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
        if mask_payload:
            mask_bit = 1 << 7
        else:
            mask_bit = 0 << 7
        # next we have to | this bit with the payload length.
        # note that we ensure that the payload is utf-8 encoded before we take
        # the length because unicode characters can be >1 bytes in length and
        # lead to bugs if we just do ``len(payload)``.
        length = len(payload.encode('utf-8'))

        if length >= Frame.MAX_LENGTH:
            raise WebsocktProtocolError("data is too long")

        # the second byte contains the payload length and mask
        if length < Frame.LENGTH_7:
            # we can simply represent payload length with first 7 bits
            frame += pack('!B', (mask_bit | length))
        elif length < Frame.LENGTH_16:
            frame += pack('!B', (mask_bit | 126)) + pack('!H', length)
        else:
            frame += pack('!B', (mask_bit | 127)) + pack('!Q', length)

        if mask_payload:
            # we always mask frames from the client to server
            # use a string of n random buffered_bytes for the mask
            mask_key = os.urandom(4)
            mask_data = cls.generate_mask(mask_key=mask_key, data=payload)
            mask = mask_key + mask_data
            frame += mask
        else:
            frame += bytearray(payload, 'utf-8')

        return bytearray(frame)


class Text(Frame):

    def __init__(self, raw_bytes=None, payload=''):
        raw_bytes = raw_bytes or FrameFactory.generate_bytes(
            payload=payload,
            fin_bit=1,
            opcode=Frame.OPCODE_TEXT,
            mask_payload=True,
        )
        super(Text, self).__init__(raw_bytes=raw_bytes)


class Ping(Frame):

    def __init__(self, raw_bytes=None, payload='', mask_payload=False):
        raw_bytes = raw_bytes or FrameFactory.generate_bytes(
            payload=payload,
            fin_bit=1,
            opcode=Frame.OPCODE_PING,
            mask_payload=mask_payload,
        )
        super(Ping, self).__init__(raw_bytes=raw_bytes)


class Pong(Frame):

    def __init__(self, raw_bytes=None, payload=''):
        raw_bytes = raw_bytes or FrameFactory.generate_bytes(
            payload=payload,
            fin_bit=1,
            opcode=Frame.OPCODE_PONG,
            mask_payload=True,
        )
        super(Pong, self).__init__(raw_bytes=raw_bytes)


class Close(Frame):

    def __init__(self, raw_bytes=None, payload=''):
        raw_bytes = raw_bytes or FrameFactory.generate_bytes(
            payload=payload,
            fin_bit=1,
            opcode=Frame.OPCODE_CLOSE,
            mask_payload=False,
        )
        super(Close, self).__init__(raw_bytes=raw_bytes)
