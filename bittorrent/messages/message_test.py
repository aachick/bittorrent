import random
import string
import unittest

import bittorrent.messages.message as bt_msg


class TestMessage(unittest.TestCase):

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

    def test_message_conversion(self):
        print('\n| ', end='')
        for msg in self.messages:
            print(type(msg).__name__, end=' | ')
            msg_as_bytes = msg.to_bytes()
            msg_from_bytes = type(msg).from_bytes(msg_as_bytes)

            self.assertTrue(msg == msg_from_bytes)
        print()


if __name__ == "__main__":
    unittest.main()
