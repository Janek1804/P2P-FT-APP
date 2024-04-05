import asyncio
import netifaces
import socket
import platform

shpath:str = "shared"
pcpath:str = "pieces"
host = ""
peers_lock = asyncio.Lock()
peers = {} # format: Address : [Last time heard, Resource list, Times heard counter]
resource_list_lock = asyncio.Lock()
resource_list = []
resetPEX = asyncio.Event()
resetAnnouncementsPEX = asyncio.Event()
run = True
download_only = False
sharing_only = False
new_issue = asyncio.Event()

def getAddresses()->list[str]:
    """Obtains IP addresses of all interfaces
        INPUT ABSENT
        RETURNS:
        - addresses (list[str]) - list of IP addresses of all interfaces"""
    interfaces = netifaces.interfaces()
    addresses = [] 
    for iface in interfaces:
        try:
            addresses.append(netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr'])
        except KeyError:
            pass
    return addresses

def setupUDPSocket(sock: socket.socket):
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if platform.system() != "Windows":
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1) # type: ignore
        except AttributeError:
            return sock
    return sock