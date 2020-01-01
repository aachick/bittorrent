import struct

import bittorrent.exceptions as exceptions
from . import message as msg


class MessageDecoder(object):

    _MESSAGE_CLASS = {
        0: msg.Choke,
        1: msg.Unchoke,
        2: msg.Interested,
        3: msg.NotInterested,
        4: msg.Have,
        5: msg.Bitfield,
        6: msg.Request,
        7: msg.Piece,
        8: msg.Cancel,
        9: msg.Port
    }

    @staticmethod
    def decode_message(payload: bytes):
        """This method is designed to decode a byte string corresponding
        to a message's payload into an object whose class implements the
        BaseMessage abstract class.

        Parameters
        ----------
        payload : bytes
            A message's payload as a byte string.

        Returns
        -------
        <T> inherits bittorrent.messages.BaseMessage
            The payload as a message object.

        Raises
        ------
        bittorrent.exceptions.InvalidMessageStructure
            An InvalidMessageStructure is raised if the payload
            parameter does not conform to the BitTorrent message
            standard or has an ID attribute value that is unknown.
        """
        if not isinstance(payload, bytes):
            raise exceptions.InvalidMessageStructure(
                'Valid messages must be in bytes format to be decoded.'
            )

        if len(payload) < 4:
            raise exceptions.InvalidMessageStructure(
                'Valid messages must be at least 4 bytes in length.'
            )

        if len(payload) == 4:
            return msg.KeepAlive()

        if payload[0] == 19:
            # Check if payload is a handshake by testing the first byte
            return msg.Handshake.from_bytes(payload)

        try:
            msg_id, = struct.unpack('>B', payload[4:5])
        except struct.error:
            raise exceptions.InvalidMessageStructure(
                'Valid messages must have their 5th byte correspond to their ID.'
            )

        try:
            bt_msg = MessageDecoder._MESSAGE_CLASS[msg_id].from_bytes(
                payload
            )
        except KeyError:
            raise exceptions.InvalidMessageStructure(
                'Unknown message ID.'
            )

        return bt_msg


def decode_message(payload: bytes):
    """This method is designed to decode a byte string corresponding
    to a message's payload into an object whose class implements the
    BaseMessage abstract class.

    Parameters
    ----------
    payload : bytes
        A message's payload as a byte string.

    Returns
    -------
    <T> inherits bittorrent.messages.BaseMessage
        The payload as a message object.

    Raises
    ------
    bittorrent.exceptions.InvalidMessageStructure
        An InvalidMessageStructure is raised if the payload
        parameter does not conform to the BitTorrent message
        standard or has an ID attribute value that is unknown.
    """
    return MessageDecoder.decode_message(payload)


if __name__ == "__main__":
    pass
