import socket
import asyncio

shpath:str = "shared"
pcpath:str = "pieces"
host = socket.gethostbyname(socket.gethostname())
peers = {} # format: Address : [Last time heard, Resource list]
resource_list = []
resetPEX = asyncio.Event()