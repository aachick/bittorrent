import collections

from bittorrent.exceptions.exceptions import InvalidBencodeDataType


class Encoder(object):
    """The Encoder class is designed to encode Python data types in
    bencoded format. Supported data types for bencoding are the following:
        str, bytes : These data types will be bencoded as strings. Bytes
        are expected to be utf-8 encoded.

        int, bool : These data types will be bencoded as integers. Bool
        types will be treated as 1 if true; 0 otherwise.

        list, tuple : These data types will be bencoded as lists.

        dict : This data type will be bencoded as a dictionary.
    """

    def __init__(self, data):
        self._data = data
        self._bencoded = []

        self._encode_func = {
            int: self._encode_int,
            bool: self._encode_bool,
            str: self._encode_str,
            bytes: self._encode_bytes,
            list: self._encode_list,
            tuple: self._encode_list,
            dict: self._encode_dict,
            collections.OrderedDict: self._encode_dict
        }

    def encode(self):
        """This method encodes Python objects into a bencoded byte string.
        Supported data types are: int, str, bool, bytes, tuple, list, and dict.
        For more information on the specification, see the following:
        https://wiki.theory.org/index.php/BitTorrentSpecification#Bencoding

        Returns
        -------
        bytes
            A utf-8 encoded byte string corresponding to the bencoded
            Python objects.

        Raises
        ------
        InvalidBencodeDataType
            An InvalidBencodeDataType exception is raised if a non-supported
            data type is found or if a byte is not utf-8 encoded.
        """
        try:
            self._encode_func[type(self._data)](self._data)
        except UnicodeDecodeError:
            raise InvalidBencodeDataType(
                'Could not decode a byte sequence. Bytes should be '
                'encoded in UTF-8.'
            )
        except KeyError as e:
            raise InvalidBencodeDataType(
                'Could not encode the following data type:\n{}'.format(str(e))
            )

        return b''.join(self._bencoded)

    def _encode_int(self, i):
        encoded_int = b'i' + str(i).encode() + b'e'

        self._bencoded.append(encoded_int)

    def _encode_bool(self, b):
        if b:
            self._encode_int(1)
        else:
            self._encode_int(0)

    def _encode_str(self, s):
        encoded_str = str(len(s)).encode() + b':' + s.encode()

        self._bencoded.append(encoded_str)

    def _encode_bytes(self, b):
        encoded_bytes = str(len(b)).encode() + b':' + b

        self._bencoded.append(encoded_bytes)

    def _encode_list(self, lst):
        self._bencoded.append(b'l')

        for el in lst:
            self._encode_func[type(el)](el)

        self._bencoded.append(b'e')

    def _encode_dict(self, d):
        self._bencoded.append(b'd')

        for k, v in d.items():
            self._encode_func[type(k)](k)
            self._encode_func[type(v)](v)

        self._bencoded.append(b'e')


def encode(data: bytes):
    """This method encodes Python objects into a bencoded byte string.
    Supported data types are: int, str, bool, bytes, tuple, list, and dict.
    For more information on the specification, see the following:
    https://wiki.theory.org/index.php/BitTorrentSpecification#Bencoding

    Returns
    -------
    bytes
        A utf-8 encoded byte string corresponding to the bencoded
        Python objects.

    Raises
    ------
    InvalidBencodeDataType
        An InvalidBencodeDataType exception is raised if a non-supported
        data type is found or if a byte is not utf-8 encoded.
    """
    encoder = Encoder(data)

    return encoder.encode()


if __name__ == "__main__":
    pass
