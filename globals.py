import asyncio
import netifaces

shpath:str = "shared"
pcpath:str = "pieces"
host = netifaces.ifaddresses(netifaces.gateways()['default'][netifaces.AF_INET][1])[netifaces.AF_INET][0]['addr']
peers = {} # format: Address : [Last time heard, Resource list]
resource_list = []
resetPEX = asyncio.Event()
resetAnnouncementsPEX = asyncio.Event()
run = True