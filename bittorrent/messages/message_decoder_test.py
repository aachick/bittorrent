import random
import string
import unittest

import bittorrent.messages.message as bt_msg
import bittorrent.messages.message_decoder as decode


class MessageDecoderTest(unittest.TestCase):

    def setUp(self):
        self.peer_id = ''.join(
            random.choice(string.ascii_letters + string.digits) for i in range(20)
        ).encode()
        self.info_hash = bytearray(random.getrandbits(1) for _ in range(20))
        self.piece_index = 0
        self.block_index = 0
        self.length = 520
        self.port = 50000

        self.messages = [
            bt_msg.Handshake(self.info_hash, self.peer_id),
            bt_msg.KeepAlive(),
            bt_msg.Choke(),
            bt_msg.Unchoke(),
            bt_msg.Interested(),
            bt_msg.NotInterested(),
            bt_msg.Have(self.piece_index),
            bt_msg.Bitfield(b'somerandombitfield'),
            bt_msg.Request(self.piece_index, self.block_index, self.length),
            bt_msg.Piece(self.piece_index, self.block_index, b'foobarbaz'),
            bt_msg.Cancel(self.piece_index, self.block_index, self.length),
            bt_msg.Port(self.port)
        ]

        self.incorrect_message = b'foobar'

    def test_message_decoding(self):
        print('\n| ', end='')
        for msg in self.messages:
            print(msg.__class__.__name__, end=' | ')
            msg_as_bytes = msg.to_bytes()

            decoded_msg = decode.decode_message(msg_as_bytes)

            self.assertEqual(msg, decoded_msg)
        print()


if __name__ == "__main__":
    pass
