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

    def __init__(self, bytes):
        self.body = bytes

    def __len__(self):
        # UTF-8 is an unicode encoding which uses more than one byte for
        # special characters. calculating the length needs consideration.
        try:
            unicode_body = self.body.decode("utf-8")
        except UnicodeError:
            unicode_body = self.body
        except AttributeError:
            # already decoded, hence no "decode" attribute
            unicode_body = self.body

        return len(unicode_body.encode('utf-8'))

    def __str__(self):
        return self.body


class ClientFrame(Frame):
    """ Represent outgoing Client -> Server messages
    """

    def __init__(self, bytes):
        super(ClientFrame, self).__init__(bytes)

        self.fin_bit = 1
        self.rsv1_bit = 0
        self.rsv2_bit = 0
        self.rsv3_bit = 0
        self.opcode = self.OPCODE_TEXT
        self.payload = self.generate_payload()

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

    def generate_payload(self):
        """ Format data to string (bytes) to send to server.
        """
        # the first byte contains the FIN bit, the 3 RSV bits and the
        # 4 opcode bits and for a client will *always* be 1000 0001 (or 129).
        # so we want the first byte to look like...
        #
        #  1 0 0 0 0 0 0 1
        # +-+-+-+-+-------+
        # |F|R|R|R| opcode|
        # |I|S|S|S|  (4)  |
        # |N|V|V|V|       |
        # | |1|2|3|       |
        # +-+-+-+-+-------+

        # this shifts each bit into position and bitwise ORs them together,
        # using the struct module to pack them as incoming network bytes
        payload = pack(
            '!B', (
                (self.fin_bit << 7) |
                self.opcode
            )
        )  # which is '\x81' as a raw byte repr

        # note that because all RSV bits are zero, we can ignore them

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

        mask_data = self.generate_mask(mask_key=mask_key, data=self.body)
        mask = mask_key + mask_data
        payload += mask

        # this is a bytes string being returned here
        return payload

class PongFrame(ClientFrame):
    def __init__(self, *args):
        super(PongFrame, self).__init__(*args)
        self.opcode = 0xa
        self.payload = self.generate_payload()

    def data_to_bytes(self, data):
        return data

class ServerFrame(Frame):
    """ Represent incoming Server -> Client messages
    """

    def __init__(self, bytes):
        super(ServerFrame, self).__init__(bytes)

        if not bytes:
            return

        try:
            self.payload_length_indicator = bytes[1] & 0b1111111
        except Exception:
            raise IncompleteFrameError(required_bytes=1)

        # if this doesn't raise, all the above will receive a value
        self.ensure_complete_frame(bytes)

        # server must not mask the payload
        mask = bytes[1] >> 7
        assert mask == 0

        self.buffered_bytes = bytes

        self.len = 0
        # Parse the first two bytes of header.
        self.fin = bytes[0] >> 7

        if self.fin == 0:
            logger.exception("Multiple Frames Returned: %s", bytes)
            raise WampyError(
                'Multiple framed responses not yet supported: {}'.format(bytes)
            )

        self.opcode = bytes[0] & 0b1111

        if self.opcode != 9:
            # Wamp data frames contain a json-encoded payload.
            # The other kind of frame we handle (opcode 0x9) is a ping and it has a non-json payload
            try:
                # decode required before loading JSON for python 2 only
                self.payload = json.loads(self.body.decode('utf-8'))
            except Exception:
                raise WebsocktProtocolError(
                    'Failed to load JSON object from: "%s"', self.body
                )
        else:
            self.payload = self.body

    def ensure_complete_frame(self, buffered_bytes):
        # we need a minimum of 2 bytes to determine the payload length and
        # hence whether this is a complete frame or not.
        if len(buffered_bytes) < 2:
            # there are more bytes to receive.
            raise IncompleteFrameError(required_bytes=1)

        payload_length_indicator = buffered_bytes[1] & 0b1111111
        available_bytes_for_body = buffered_bytes[2:]

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

        self.body = body_candidate
        self.payload_length_indicator = payload_length_indicator
