import copy
import hashlib
import math
import pprint

import bittorrent.bencoding as bencoding
from bittorrent import utils


class Torrent(object):
    """The Torrent class is designed to contain the metainformation
    found inside a .torrent file. This class enables users to use utility
    functions such as obtaining the announce's URL, the file size, the
    info hash of the metainformation's info dictionary, and the pieces
    of the metainformation file.

    The default constructor of this class assumes that the torrent_meta
    parameter is the decoded version of the .torrent file. As such, the
    Torrent.from_bytes, and Torrent.from_path class methods provide a
    convenient way to instantiate an object.
    """

    def __init__(self, torrent_meta):
        if not utils.is_valid_torrent_meta(torrent_meta):
            raise ValueError(
                'The torrent_meta constructor parameter is not a valid '
                'torrent metainformation file.'
            )

        self._path = ''
        self._meta_info = torrent_meta

        self._info_hash = None
        self._announce_list = []

    def __getitem__(self, item):
        if item not in self._meta_info:
            return None

        return self._meta_info[item]

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        d = dict(copy.deepcopy(self._meta_info))
        d[b'info'] = dict(d[b'info'])
        d[b'info'][b'pieces'] = d[b'info'][b'pieces'][:30] + b' ...'

        return pprint.pformat(d)

    @classmethod
    def from_bytes(cls, torrent_contents: bytes) ->:
        """This method is designed to return a Torrent instance
        given a bytes string that corresponds to the contents of
        a .torrent file.

        Parameters
        ----------
        torrent_contents : bytes
            A bytes string corresponding to the contents of .torrent
            file.

        Returns
        -------
        Torrent
            A Torrent instance containing the .torrent data
        """
        torrent_meta = bencoding.decode(torrent_contents)

        torrent = cls(torrent_meta)

        return torrent

    @classmethod
    def from_path(cls, torrent_fpath: str) -> str:
        """This method is designed to return a Torrent instance
        given the file path of a .torrent file.

        Parameters
        ----------
        torrent_fpath : str
            A string corresponding to the file path of a .torrent
            file.

        Returns
        -------
        Torrent
            A Torrent instance containing the .torrent data

        Raises
        ------
        FileNotFoundError
            A FileNotFoundError is raised if the file path parameter
            is invalid.
        """
        contents = utils.read(torrent_fpath)
        torrent_meta = bencoding.decode(contents)

        torrent = cls(torrent_meta)
        torrent._path = torrent_fpath

        return torrent

    @property
    def announce_list(self) -> list:
        if not self._announce_list:
            if self[b'announce-list'] is None:
                return []
            self._announce_list = [
                item for sublist in self[b'announce-list'] for item in sublist
            ]
            self._announce_list = [
                announce.decode() for announce in self._announce_list
            ]

        return self._announce_list

    @property
    def announce_url(self) -> str:
        """Returns the announce's URL as a UTF-8 encoded string."""
        return self[b'announce'].decode('utf-8')

    @property
    def created_by(self) -> str:
        """Returns the torrent's creator name if it exists."""
        return self[b'created by'].decode()

    @property
    def info_hash(self) -> bytes:
        """Returns the bencoded info dictionary's SHA1 hash as a bytes string.
        """
        if not self._info_hash:
            self._info_hash = hashlib.sha1(
                bencoding.encode(self[b'info'])
            ).digest()
        return self._info_hash

    @property
    def file_size(self) -> int:
        """Returns the lengths, in bytes, of the file or files
        in the metainfo file.
        """
        if b'length' in self[b'info']:
            return int(self[b'info'][b'length'])
        else:
            return sum([int(f[b'length']) for f in self[b'info'][b'files']])

    @property
    def file_count(self) -> int:
        """Returns the number of files in the metainfo file."""
        if b'length' in self[b'info']:
            return 1
        else:
            return len(self[b'info'][b'files'])

    @property
    def file_name(self) -> str:
        """Returns the torrent's name."""
        return self[b'info'][b'name'].decode()

    @property
    def piece_length(self) -> int:
        return self[b'info'][b'piece length']

    @property
    def pieces_total_length(self) -> int:
        if b'files' not in self[b'info']:
            return self[b'info'][b'length']
        total_length = 0
        for file_ in self[b'info'][b'files']:
            self.total_length += file_[b'length']
        return total_length

    @property
    def pieces(self) -> list:
        """Returns the pieces as a list of 20-byte hash digests."""
        n = 20
        pieces = self[b'info'][b'pieces']
        return [pieces[i:i+n] for i in range(0, len(pieces), n)]

    @property
    def pieces_count(self) -> int:
        """Returns the number of pieces in the torrent file."""
        return math.ceil(self.pieces_total_length / self.piece_length)


if __name__ == "__main__":
    pass
