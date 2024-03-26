import asyncio
import netifaces

shpath:str = "shared"
pcpath:str = "pieces"
host = ""
peers = {} # format: Address : [Last time heard, Resource list]
resource_list = []
resetPEX = asyncio.Event()
resetAnnouncementsPEX = asyncio.Event()
run = True

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