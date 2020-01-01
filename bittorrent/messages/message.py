import abc
import struct


BITTORRENT_PSTR_V1 = b'BitTorrent protocol'


class BaseMessage(abc.ABC):
    """The BaseMessage class is abstract and serves to provide a foundation
    for other classes that wish to represent BT messages. All BT messages
    start with a 4-byte big-endian encoded string indicating the length of
    the total message.
    """

    def __init__(self, msg_len: int):
        self._msg_len = msg_len

    def __eq__(self, other):
        if type(other) is not type(self):
            return False

        for val_other, val_self in zip(other.__dict__.values(), self.__dict__.values()):
            if val_other != val_self:
                return False

        return True

    def __hash__(self):
        h = hash(tuple(self.__dict__.values()))
        return h

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '{}: <len={:04d}>'.format(type(self).__name__, self.msg_len)

    @property
    def msg_len(self) -> int:
        """Returns the message length."""
        return self._msg_len

    @classmethod
    @abc.abstractmethod
    def from_bytes(cls, payload: bytes):
        """This method should be used to convert a byte string to its
        corresponding BT protocol message.

        Raises
        ------
        ValueError
            A ValueError should be raised if the payload argument is not
            a byte string or if the payload's length is not the expected
            length of the message.
        """
        pass

    def to_bytes(self) -> bytes:
        """This method is designed to convert a BaseMessage implementing
        object to a big-endian encoded bytes string.

        Returns
        -------
        bytes
            A big-endian encoded bytes string containing the message's
            length.
        """
        return struct.pack('>I', self.msg_len)


class Handshake(BaseMessage):
    """A handshake message initiates, if successful, further messaging
    between two BT peers. A handshake message is structured in the following
    manner:
        <pstrlen><pstr><reserved><info_hash><peer_id>

    Attributes
    ----------
    pstr_len : int
        The length of the message's protocol (pstr) represented as a string.
        This is represented as one byte. In version 1 of BT, this value is
        set to 19.
    pstr : bytes
        The name of the used protocol as a bytes string. As of version 1,
        this is set to 'BitTorrent protocol'.
    reserved : bytes
        A string of 8 empty and reserved bytes that determine the protocol's
        behavior.
    info_hash : bytes
        A 20 byte SHA1 hash of the bencoded form of the info dict of the meta-
        information file.
    peer_id : bytes
        A 20 byte string corresponding to the peer's ID. This is reported in
        tracker requests and contained in peer lists in tracker responses.
    """
    LENGTH = len(BITTORRENT_PSTR_V1) + 49
    RESERVED = b'\x00' * 8
    STRUCT = '>B19s8s20s20s'

    def __init__(self, info_hash: bytes, peer_id: bytes):
        BaseMessage.__init__(self, Handshake.LENGTH)
        self._pstr_len = len(BITTORRENT_PSTR_V1)
        self._pstr = BITTORRENT_PSTR_V1
        self._reserved = Handshake.RESERVED

        self._info_hash = info_hash
        self._peer_id = peer_id

        if len(info_hash) != 20:
            raise ValueError('The info hash must be 20 bytes long.')
        if len(peer_id) != 20:
            raise ValueError('The peer ID must be 20 bytes long.')

    def __str__(self):
        return super().__str__() + \
            '<pstrlen={}><pstr={}><reserved={}><info-hash={}><peer-id={}>'.format(
                self.pstr_len, self.pstr.decode(),
                self.reserved.decode(), self.info_hash,
                self.peer_id
            )

    @property
    def pstr_len(self) -> int:
        """Returns the handshake's protocol string length."""
        return self._pstr_len

    @property
    def pstr(self) -> bytes:
        """Returns the protocol name."""
        return self._pstr

    @property
    def reserved(self) -> bytes:
        """Returns the handshake's reserved message bytes."""
        return self._reserved

    @property
    def info_hash(self) -> bytes:
        """Returns the handshake's info hash."""
        return self._info_hash

    @property
    def peer_id(self) -> bytes:
        """Returns the handshake's peer ID."""
        return self._peer_id

    @classmethod
    def from_bytes(cls, payload: bytes):
        if not isinstance(payload, bytes):
            raise ValueError('The payload must be a byte string.')
        if len(payload) != Handshake.LENGTH:
            raise ValueError('Expected a byte string of length {}.'.format(
                Handshake.LENGTH + len(BITTORRENT_PSTR_V1)
            ))

        unpacked_bytes = struct.unpack(Handshake.STRUCT, payload)

        handshake_msg = Handshake(unpacked_bytes[-2], unpacked_bytes[-1])

        return handshake_msg

    def to_bytes(self) -> bytes:
        return struct.pack(
            Handshake.STRUCT,
            self.pstr_len,
            self.pstr,
            self.reserved,
            self.info_hash,
            self.peer_id
        )


class KeepAlive(BaseMessage):
    """The KeepAlive class should be used to signal to a peer that a
    connection should be kept alive. The KeepAlive message should be
    zero bytes in length. If no KeepAlive is sent over a certain period
    of time, the connection should be closed.
    """
    LENGTH = 0

    def __init__(self):
        BaseMessage.__init__(self, KeepAlive.LENGTH)

    @classmethod
    def from_bytes(cls, payload: bytes):
        if len(payload) != 4:
            raise ValueError('Expected a byte string of length 4.')

        return KeepAlive()


class IDMessage(BaseMessage, abc.ABC):

    def __init__(self, msg_len: int, msg_id: int):
        BaseMessage.__init__(self, msg_len)
        self._msg_id = msg_id

    def __str__(self):
        return super(IDMessage, self).__str__() + '<id={}>'.format(self.msg_id)

    @property
    def msg_id(self) -> int:
        """Returns the message's ID."""
        return self._msg_id

    def to_bytes(self) -> bytes:
        """This method is designed to convert a BT message to a bytes
        string so that it may be sent over the wire.

        Returns
        -------
        bytes
            A byte string encoded according to BT protocol.
        """
        return struct.pack('>IB', self.msg_len, self.msg_id)

    @classmethod
    def from_bytes(cls, payload: bytes):
        if len(payload) != 5:
            # Standardized check to verify if correct byte length.
            raise ValueError('Expected a byte string of length 5.')

        msg = cls()
        return msg


class Choke(IDMessage):
    """The choke message should be sent to signal to a
    peer that it is choked. It's structure is as follows:
        <len=0001><id=0>
    """
    LENGTH = 1
    ID = 0

    def __init__(self):
        IDMessage.__init__(self, Choke.LENGTH, Choke.ID)


class Unchoke(IDMessage):
    """An unchoke message is sent from one peer to the next to indicate
    that is no longer chocked. Its structure is as follows:
        <len=0001><id=1>
    """
    LENGTH = 1
    ID = 1

    def __init__(self):
        IDMessage.__init__(self, Unchoke.LENGTH, Unchoke.ID)


class Interested(IDMessage):
    """An Interested message should be sent from one peer to the next
    to indicate that they are interested in receiving data from the
    given peer. Such messages have the following structure:
        <len=0001><id=2>
    """
    LENGTH = 1
    ID = 2

    def __init__(self):
        IDMessage.__init__(self, Interested.LENGTH, Interested.ID)


class NotInterested(IDMessage):
    """A NotInterested message should be sent from one peer to the next
    to indicate that they are no longer interested in receiving data from
    the given peer. Such messages have the following structure:
        <len=0001><id=3>
    """
    LENGTH = 1
    ID = 3

    def __init__(self):
        IDMessage.__init__(self, NotInterested.LENGTH, NotInterested.ID)


class Have(IDMessage):
    """Have messages are sent to indicate from one peer to the next
    to indicate that the peer has a particular piece of a file. A have
    message is structured as follows:
        <len=0005><id=3><piece index>

    Attributes
    ----------
    piece_index : int
        The zero-based index of the piece that a peer has.
    """
    LENGTH = 5
    ID = 4
    STRUCT = '>IBI'

    def __init__(self, piece_index: int):
        IDMessage.__init__(self, Have.LENGTH, Have.ID)
        self._piece_index = piece_index

    def __str__(self):
        return super(Have, self).__str__() \
            + '<piece_index={}>'.format(self.piece_index)

    @property
    def piece_index(self) -> int:
        """Returns the piece's index."""
        return self._piece_index

    @classmethod
    def from_bytes(cls, payload: bytes):
        if len(payload) != 9:
            raise ValueError('Expected a byte string of length 9.')

        unpacked_bytes = struct.unpack(Have.STRUCT, payload)

        have_msg = Have(unpacked_bytes[2])

        return have_msg

    def to_bytes(self) -> bytes:
        return struct.pack(
            Have.STRUCT, self.msg_len, self.msg_id, self.piece_index
        )


class Bitfield(IDMessage):
    """The Bitfield message is used by one peer to the next that it does
    not may only be sent by a peer immediately after a handshaking sequence is
    completed -and before any other message is sent. The payload of a bitfield
    message represents the different pieces that have been successfully
    downloaded. The high bit in the first byte corresponds to piece index 0.
    Cleared bits indicate a missing piece. Set bits correspond to a valid and
    available piece. Spare bits at the end are set to zero.
        <len=0001+X><id=5><bitfield>

    Parameters
    ----------
    bitfield : bytes
        A byte string corresponding to the pieces that have been successfully
        downloaded by a peer.

    Notes
    -----
    A bitfield of the wrong length is considered an error. Clients should
    drop the connection if they receive bitfields that are not of the correct
    size, or if the bitfield has any of the spare bits set.
    """
    BASE_LENGTH = 1
    ID = 5
    STRUCT = '>IB{}s'

    def __init__(self, bitfield: bytes):
        IDMessage.__init__(
            self, Bitfield.BASE_LENGTH + len(bitfield), Bitfield.ID
        )
        self._bitfield = bitfield

        if not isinstance(bitfield, bytes):
            raise ValueError('The bitfield parameter must be bytes.')

    def __str__(self):
        return super(Bitfield, self).__str__() \
            + '<bitfield={}>'.format(self.bitfield)

    @property
    def bitfield(self) -> bytes:
        """Returns the message's bitfield."""
        return self._bitfield

    @classmethod
    def from_bytes(cls, payload: bytes):
        unpacked_bytes = struct.unpack(
            Bitfield.STRUCT.format(len(payload) - Bitfield.BASE_LENGTH - 4),
            payload
        )

        bitfield_msg = Bitfield(unpacked_bytes[2])

        return bitfield_msg

    def to_bytes(self) -> bytes:
        return struct.pack(
            Bitfield.STRUCT.format(len(self.bitfield)),
            self.msg_len,
            self.msg_id,
            self.bitfield
        )

    def pieces_status(self) -> list:
        """Returns a list of booleans whose values correspond to whether
        the piece at index N has been downloaded or not."""
        pieces = []
        for byte_ in self.bitfield:
            bits = bin(byte_).lstrip('0b')
            for b in bits:
                pieces.append(True if b == '1' else False)
        return pieces


class Request(IDMessage):
    """The Request message is sent by one peer to the next to request a block.
        <len=0013><id=6><index><begin><length>

    Attributes
    ----------
    index : int
        The zero-based index of the requested piece (4 bytes).
    begin : int
        The zero-based byte offset within the piece of the block (4 bytes).
    length : int
        The length of the block in bytes (4 bytes).
    """
    LENGTH = 13
    ID = 6
    STRUCT = '>IBIII'

    def __init__(self, index: int, begin: int, length: int):
        IDMessage.__init__(self, Request.LENGTH, Request.ID)
        self._index = index
        self._begin = begin
        self._length = length

    def __str__(self):
        return IDMessage.__str__(self) \
            + '<index={}><begin={}><length={}>'.format(
                self.index, self.begin, self.length
            )

    @property
    def index(self) -> int:
        """Returns the zero-based index of the piece."""
        return self._index

    @property
    def begin(self) -> int:
        """Returns the zero-based index of the piece's block."""
        return self._begin

    @property
    def length(self) -> int:
        """Returns the length, in bytes, of the piece."""
        return self._length

    @classmethod
    def from_bytes(cls, payload: bytes):
        if len(payload) != 17:
            raise ValueError('Expected a byte string of length 17.')

        unpacked_bytes = struct.unpack(Request.STRUCT, payload)

        request_msg = Request(
            unpacked_bytes[2], unpacked_bytes[3], unpacked_bytes[4]
        )

        return request_msg

    def to_bytes(self) -> bytes:
        return struct.pack(
            Request.STRUCT,
            self.msg_len,
            self.msg_id,
            self.index,
            self.begin,
            self.length
        )


class Piece(IDMessage):
    """The piece message is sent from one peer to the next to send
    a piece block.
        <len=0009+X><id=7><index><begin><block>

    Attributes
    ----------
    index : int
        The zero-based index of the requested piece (4 bytes).
    begin : int
        The zero-based byte offset within the piece of the block (4 bytes).
    block : int
        The block of data (variable length).
    """
    BASE_LENGTH = 9
    ID = 7
    STRUCT = '>IBII{}s'

    def __init__(self, index: int, begin: int, block: bytes):
        IDMessage.__init__(self, Piece.BASE_LENGTH + len(block), Piece.ID)
        self._index = index
        self._begin = begin
        self._block = block

    def __str__(self):
        return IDMessage.__str__(self) \
            + '<index={}><begin={}><block={}>'.format(
                self.index, self.begin, self.block
            )

    @property
    def index(self) -> int:
        """Returns the zero-based piece index."""
        return self._index

    @property
    def begin(self) -> int:
        """Returns the zero-based block index of the piece."""
        return self._begin

    @property
    def block(self) -> bytes:
        """Returns the piece's block."""
        return self._block

    @classmethod
    def from_bytes(cls, payload: bytes):
        str_len = len(payload)
        unpacked_bytes = struct.unpack(
            Piece.STRUCT.format(str_len - Piece.BASE_LENGTH - 4), payload
        )
        piece = cls(unpacked_bytes[2], unpacked_bytes[3], unpacked_bytes[4])

        return piece

    def to_bytes(self) -> bytes:
        return struct.pack(
            Piece.STRUCT.format(len(self.block)),
            self.msg_len,
            self.msg_id,
            self.index,
            self.begin,
            self.block
        )


class Cancel(IDMessage):
    """The cancel message is sent from one peer to the next to cancel
    a previously requested block.
        <len=0013><id=8><index><begin><length>

    Attributes
    ----------
    index : int
        The zero-based index of the requested piece (4 bytes).
    begin : int
        The zero-based byte offset within the piece of the block (4 bytes).
    length : int
        The length of the block in bytes (4 bytes).
    """
    LENGTH = 13
    ID = 8
    STRUCT = '>IBIII'

    def __init__(self, index: int, begin: int, length: int):
        IDMessage.__init__(self, Cancel.LENGTH, Cancel.ID)
        self._index = index
        self._begin = begin
        self._length = length

    def __str__(self):
        return IDMessage.__str__(self) \
            + '<index={}><begin={}><length={}>'.format(
                self.index, self.begin, self.length
            )

    @property
    def index(self) -> int:
        """Returns the zero-based index of the piece."""
        return self._index

    @property
    def begin(self) -> int:
        """Returns the zero-based index of the piece's block."""
        return self._begin

    @property
    def length(self) -> int:
        """Returns the length, in bytes, of the piece."""
        return self._length

    @classmethod
    def from_bytes(cls, payload: bytes):
        if len(payload) != 17:
            raise ValueError('Expected a byte string of length 17.')

        unpacked_bytes = struct.unpack(Cancel.STRUCT, payload)

        cancel_msg = Cancel(
            unpacked_bytes[2], unpacked_bytes[3], unpacked_bytes[4]
        )

        return cancel_msg

    def to_bytes(self) -> bytes:
        return struct.pack(
            Cancel.STRUCT,
            self.msg_len,
            self.msg_id,
            self.index,
            self.begin,
            self.length
        )


class Port(IDMessage):
    """The port message is sent to indicate on which port a peer's DHT
    is listening on.
        <len=0003><id=9><listen-port>

    Attributes
    ----------
    msg_len : int
        The message's
    """
    LENGTH = 3
    ID = 9
    STRUCT = '>IBH'

    def __init__(self, port: int):
        IDMessage.__init__(self, Port.LENGTH, Port.ID)
        self._port = port

        if not isinstance(port, int) and port < 0:
            raise ValueError('Invalid port argument.')

    def __str__(self):
        return IDMessage.__str__(self) + '<listen-port={}>'.format(self.port)

    @property
    def port(self) -> int:
        """Returns the port number."""
        return self._port

    @classmethod
    def from_bytes(cls, payload: bytes):
        if len(payload) != 7:
            raise ValueError('Expected a byte string of length 7.')

        unpacked_bytes = struct.unpack(Port.STRUCT, payload)

        port_msg = Port(unpacked_bytes[2])

        return port_msg

    def to_bytes(self) -> bytes:
        return struct.pack(
            Port.STRUCT, self.msg_len, self.msg_id, self.port
        )


if __name__ == "__main__":
    pass
