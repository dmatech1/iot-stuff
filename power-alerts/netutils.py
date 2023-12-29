import socket
import fcntl
import struct
import requests
import requests.adapters
import urllib3.poolmanager

SO_BINDTODEVICE = 25
SIOCGIFADDR = 0x8915

class AlternateInterfaceAdapter(requests.adapters.HTTPAdapter):
    """
    Simple adapter that uses the specified IPv4 network interface for requests.
    The idea and implementation are based on SocketOptionsAdapter and
    SourceAddressAdapter in the "requests_toolbelt" package.

    This is currently specific to Linux and IPv4.  Extending this to Windows
    might require using the IP_UNICAST_IF or IPV6_UNICAST_IF socket options
    instead of SO_BINDTODEVICE.  Plus, the interface management functions are
    totally different.  But since I'm only using IPv4 on a Raspberry Pi 4
    for this project, this isn't necessary.
    """

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

        # This is specific to Linux.  I've only seen it used in "curl".  If you
        # use "ip rule" and "ip route" correctly, this step is unnecessary.
        # See: https://github.com/curl/curl/blob/2683de3078eadc86d9b182e7417f4ee75a247e2c/lib/cf-socket.c#L448-L469
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
