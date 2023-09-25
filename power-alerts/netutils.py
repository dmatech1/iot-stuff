import socket
import fcntl
import struct
import requests
import requests.adapters
import urllib3.poolmanager

SO_BINDTODEVICE = 25
SIOCGIFADDR = 0x8915

class AlternateInterfaceAdapter(requests.adapters.HTTPAdapter):
    """Simple adapter that uses the specified network interface for requests."""

    def __init__(self, if_name: str, **kwargs):
        self.if_name = if_name
        super(AlternateInterfaceAdapter, self).__init__(**kwargs)
        
    def init_poolmanager(self, connections, maxsize, block=False):
        if_name_bytes = bytes(self.if_name[:15], 'utf-8')

        # Get the IPv4 address for the requested interface.
        # See: https://stackoverflow.com/a/24196955/7077511
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            addr = socket.inet_ntoa(fcntl.ioctl(s.fileno(), SIOCGIFADDR, struct.pack('256s', if_name_bytes))[20:24])
            print(addr)

        # This is specific to Linux.  I've only seen it used in "curl".
        socket_options = [
            (socket.SOL_SOCKET, SO_BINDTODEVICE, if_name_bytes + b'\x00')
        ]

        # Create the PoolManager.
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            socket_options=socket_options,
            source_address=(addr, 0))
