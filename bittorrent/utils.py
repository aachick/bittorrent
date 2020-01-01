import ipaddress
import os

__all__ = ['is_valid_ip_address', 'is_valid_torrent_meta', 'read']


def is_valid_ip_address(address):
    """This method verifies if the address parameter is
    a valid IPv4 or IPv6 address.

    Parameters
    ----------
    address : str
        An IPv4 or IPv6 address.

    Returns
    -------
    bool
        True if the address parameter is a valid IPv4 or IPv6
        address; False otherwise.
    """
    is_valid = True
    try:
        ipaddress.ip_address(address)
    except ValueError:
        is_valid = False

    return is_valid


def is_valid_torrent_meta(torrent_contents):
    """This method is designed to validate the structure of a
    decoded torrent file.

    Parameters
    ----------
    torrent_contents : dict, OrderedDict
        The decoded torrent contents of a .torrent file.

    Returns
    -------
    bool
        Returns True if the torrent contents are valid, False
        otherwise.

    Notes
    -----
    This method performs a superficial validation scheme as it only
    verifies that the mandatory fields of a torrent metainformation
    file are present as opposed to also verifying the type of the key
    contents.
    """
    if b'announce' not in torrent_contents:
        return False
    if not isinstance(torrent_contents[b'announce'], bytes):
        return False

    if b'info' not in torrent_contents:
        return False

    common_keys = {b'piece length', b'pieces'}
    if common_keys.difference(torrent_contents[b'info'].keys()) != set():
        return False

    if b'length' in torrent_contents[b'info']:
        # All mandatory keys have been found in the single file mode
        # torrent file.
        return True
    else:
        if b'files' not in torrent_contents[b'info']:
            return False
        for f in torrent_contents[b'info'][b'files']:
            if b'length' not in f or b'path' not in f:
                return False

    return True


def read(path):
    """This method is designed to read .torrent files into bytes.

    Parameters
    ----------
    path : str
        The file path of a .torrent file.

    Returns
    -------
    bytes
        A bytes object corresponding to the raw content of the
        torrent file.

    Raises
    ------
    FileNotFoundError
        A FileNotFoundError is raised if the path parameter is None or
        if it does not correspond to an existing file.
    ValueError
        A ValueError is raised if the file was found but is not a .torrent
        file.
    """
    if path is None or not os.path.exists(path):
        raise FileNotFoundError('Could not find "{}"'.format(path))
    if os.path.splitext(path)[1].lower() != '.torrent':
        raise ValueError('Incorrect file path supplied.')

    byte_str = b''
    with open(path, 'rb') as f:
        byte = f.read(1)
        while byte:
            byte_str += byte
            byte = f.read(1)

    return byte_str


if __name__ == "__main__":
    pass
