import struct
import urllib.parse
import urllib.request

import bittorrent.bencoding as bencoding
import bittorrent.torrent as torrent
import bittorrent.utils


class Tracker(object):
    """The Tracker class is designed to provide utility methods for the
    BitTorrent client in its communication with a tracker. Currently, the
    Tracker class is designed to get peers from a tracker for a given torrent.

    TODO: Add method to send a 'completed' event message to the tracker
    TODO: Add method to send a 'stopped' event message to the tracker
    """

    def __init__(self, peer_id: bytes, port, torrent):
        self.peer_id = peer_id
        self.port = port
        self.torrent = torrent

        self.tracker_addr = torrent.announce_url
        self.peers = []

        self.interval = -1
        self.min_interval = -1

        self.tracker_id = b''
        # Number of peers with the entire file (seeders)
        self.complete = -1
        # Number of peers with only parts of the file (leechers)
        self.incomplete = -1

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '\n'.join([
            'Tracker ID: {}'.format(self.tracker_id.decode()),
            'Tracker IP: {}'.format(self.tracker_addr),
            '\tRequest interval: {}s (min interval: {}s)'.format(
                self.interval, self.min_interval
            ),
            '\t'
        ])

    def _build_url(self, event='', uploaded=0, downloaded=0, left=0, compact=1, no_peer_id=0):
        params = {
            'info_hash': self.torrent.info_hash,
            'peer_id': self.peer_id,
            'port': self.port,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': left,
            'compact': compact,
            'event': event
        }

        if compact == 0 and no_peer_id == 1:
            params['no_peer_id'] = 1

        url_params = urllib.parse.urlencode(params)
        url = '{}?{}'.format(self.tracker_addr, url_params)

        return url

    def _update_tracker_info(self, tracker_res):
        if b'interval' in tracker_res:
            self.interval = tracker_res[b'interval']
        if b'min interval' in tracker_res:
            self.min_interval = tracker_res[b'min interval']
        if b'tracker id' in tracker_res:
            self.tracker_id = tracker_res[b'tracker id']
        if b'complete' in tracker_res:
            self.complete = tracker_res[b'complete']
        if b'incomplete' in tracker_res:
            self.incomplete = tracker_res[b'incomplete']

    def _parse_peers(self, peers, compact):
        peer_list = []

        if compact == 1:
            for i in range(0, len(peers), 6):
                peer_ip = peers[i:i+4]
                peer_port = peers[i+4:i+6]

                peer_ip = struct.unpack('>BBBB', peer_ip)
                peer_ip = '.'.join(str(dec) for dec in peer_ip)

                peer_port = struct.unpack('>H', peer_port)[0]

                peer_list.append((peer_ip, peer_port, ''))
        else:
            for peer in peers[b'peers']:
                peer_ip = peer[b'ip'].decode()
                peer_port = peer[b'port'].decode()
                peer_id = peer[b'peer id'].decode()

                peer_list.append((peer_ip, peer_port, peer_id))

        return peer_list

    def can_scrape(self):
        """This method is designed to indicate whether a tracker has adopted
        the scrape convention or not. For more information on this, see the
        following forum post:
        https://groups.yahoo.com/neo/groups/BitTorrent/conversations/topics/3275

        Returns
        -------
        bool
            True if the tracker has adopted the scrape convention; False
            otherwise.
        """
        print(self.tracker_addr)
        slash_idx = self.tracker_addr.rfind('/')
        print(self.tracker_addr[slash_idx:])
        if slash_idx == -1:
            raise ValueError('Invalid tracker address.')

        target = 'announce'
        if target == self.tracker_addr[slash_idx+1:slash_idx+1+len(target)]:
            return True
        else:
            return False

    def get_peers(self):
        """This method is designed to obtain a list of peers for a torrent
        from a tracker. The list elements correspond to 3-tuples whose elements
        correspond to the peer's IP address, port, and ID, respectively. If
        the compact parameter is set to 1, peer IDs will be empty.

        Returns
        -------
        list of tuple of str, int, str
            A list of 3-tuples corresponding to the peers' IP addresses, ports,
            and IDs.
        """
        url = self._build_url('started', 0, 0, self.torrent.file_size, 1, 0)

        with urllib.request.urlopen(url) as response:
            response_content = response.read()
            decoded_content = bencoding.decode(response_content)

            self._update_tracker_info(decoded_content)

            peers = self._parse_peers(decoded_content[b'peers'], 1)

            return peers

    def scrape(self):
        if not self.can_scrape():
            return

        url = self._build_url('', 0, 0, self.torrent.file_size, 1, 0)
        slash_idx = url.rfind('/')
        url = '{}{}'.format(
            url[:slash_idx], url[slash_idx:].replace('announce', 'scrape', 1)
        )

        with urllib.request.urlopen(url) as response:
            content = response.read()
            decoded_content = bencoding.decode(content)

            self._update_tracker_info(decoded_content)


if __name__ == "__main__":
    pass
