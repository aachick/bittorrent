import collections

from bittorrent.exceptions.exceptions import InvalidTorrentFileBencoding


class Decoder(object):
    """The Decoder class is designed to decoded bencoded byte strings.

    Attributes
    ----------
    bytes : _data
        Corresponds to a torrent file's bencoded content.
    int : _curr_index
        Corresponds to the index at which the instance is at
        in the bencoding process.

    Raises
    ------
    TypeError
        Raises a TypeError if the data constructor parameter is not
        a bytes string.
    """

    def __init__(self, data: bytes):
        if data is None or not data or not isinstance(data, bytes):
            raise TypeError('Metainfo file data must be in bytes form')

        self._data = data
        self._curr_index = 0

        self._bdecode = {
            b'l': self._decode_list,
            b'd': self._decode_dict,
            b'i': self._decode_int,
            b'0': self._decode_str,
            b'1': self._decode_str,
            b'2': self._decode_str,
            b'3': self._decode_str,
            b'4': self._decode_str,
            b'5': self._decode_str,
            b'6': self._decode_str,
            b'7': self._decode_str,
            b'8': self._decode_str,
            b'9': self._decode_str,
        }

    def decode(self) -> bytes:
        """This method is designed to decode a bencoded byte string.
        The returned result can be a byte string, an integer, a list,
        or a dictionary depending on the contents of the bencoded byte
        string. Lists and dictionaries may contain nested lists and
        dictionaries.

        Returns
        -------
        str, int, list, or dict
            Returns the decoded bencoded contents.

        Raises
        ------
        InvalidTorrentFileBencoding
            This method raises an InvalidTorrentFileBencoding exception
            if the contents of the bencoded byte string are not valid.
            See the following page for bencoding specifications:
            https://wiki.theory.org/index.php/BitTorrentSpecification#Bencoding
        """
        self._curr_index = 0

        curr_byte = bytes([self._data[self._curr_index]])

        res = self._bdecode[curr_byte]()

        if self._curr_index != len(self._data):
            raise InvalidTorrentFileBencoding(
                'The number of decoded bytes does not match '
                'the number of total bytes.'
            )

        return res

    def _decode_str(self):
        """This method decodes bencoded strings. Bencoded strings are
        represented in the following format: "<len>:<string>", where
        <len> corresponds to the string's length, and <string> corresponds
        to the string.
        """
        colon_index = self._data.find(b':', self._curr_index)
        if colon_index == -1:
            raise InvalidTorrentFileBencoding(
                'Expected to find a colon after string\'s length. '
                'Error occured at {}.'.format(self._curr_index)
            )

        try:
            str_length = int(self._data[self._curr_index:colon_index])
        except ValueError:
            raise InvalidTorrentFileBencoding(
                'Expected a valid integer to indicate the string length. '
                'Obtained "{}" at {}.'.format(
                    self._data[self._curr_index:colon_index], self._curr_index
                )
            )

        decoded_str = self._data[colon_index+1:colon_index+1+str_length]
        decoded_str = decoded_str

        self._curr_index = colon_index + 1 + str_length

        return decoded_str

    def _decode_int(self):
        """This method decodes bencoded integers. Bencoded integers are
        represented in the following format: "i<integer>e", where <integer>
        corresponds to the bencoded integer.
        """
        self._curr_index += 1
        int_end = self._data.find(b'e', self._curr_index)
        if int_end == -1:
            raise InvalidTorrentFileBencoding(
                'Expected to find an "e" to delimit the integer. '
                'Error occured at {}.'.format(self._curr_index)
            )

        i = self._data[self._curr_index:int_end]

        if len(i) > 1:
            if bytes([i[0]]) == b'0' or (bytes([i[0]]) == b'-' and bytes([i[1]]) == b'0'):
                raise InvalidTorrentFileBencoding((
                    'Integers may not be represented with leading 0s. '
                    'Error occured at {}.'.format(self._curr_index)
                ))

        try:
            i = int(i)
        except ValueError:
            raise InvalidTorrentFileBencoding(
                'Could not coerce the following byte string to an integer: '
                '{}. Error occured at {}'.format(i, self._curr_index)
            )

        self._curr_index = int_end + 1

        return i

    def _decode_list(self):
        """This method decodes bencoded lists. Bencoded lists are
        represented in the following format: "l<elements>e", where
        <element> corresponds to the list's elements. These can be
        strings, integers, lists or dictionaries.
        """
        lst = []
        self._curr_index += 1

        while self._curr_index < len(self._data) and bytes([self._data[self._curr_index]]) != b'e':
            curr_byte = bytes([self._data[self._curr_index]])

            element = self._bdecode[curr_byte]()
            lst.append(element)

        self._curr_index += 1

        return lst

    def _decode_dict(self):
        """This method decodes bencoded dictionaries. Bencoded dictionaries
        are represented in the following format: "d<key><value>e",
        where <key> corresponds to a bencoded string, and where
        <value> corresponds to the key's value. Values can be strings,
        integers, lists, or dictionaries.
        """
        d = collections.OrderedDict()
        self._curr_index += 1

        while self._curr_index < len(self._data) and bytes([self._data[self._curr_index]]) != b'e':
            curr_byte = bytes([self._data[self._curr_index]])
            key = self._decode_str()

            curr_byte = bytes([self._data[self._curr_index]])
            val = self._bdecode[curr_byte]()

            d[key] = val

        self._curr_index += 1

        return d


def decode(data: bytes) -> dict:
    """This method decodes a bencoded byte string and returns its
    contents in the form of a string, integer, list, or dictionary.
    Lists and dictionaries can contain nested lists and dictionaries.

    Returns
    -------
    dict
        Returns the decoded bencoded contents.

    Raises
    ------
    TypeError
        A TypeError is raised if the data parameter is not an instance
        of the bytes class.
    InvalidTorrentFileBencoding
        This method raises an InvalidTorrentFileBencoding exception
        if the contents of the bencoded byte string are not valid.
        See the following page for bencoding specifications:
        https://wiki.theory.org/index.php/BitTorrentSpecification#Bencoding
    """
    decoder = Decoder(data)

    return decoder.decode()


if __name__ == "__main__":
    pass
