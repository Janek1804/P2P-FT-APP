from asyncio import open_connection
from scapy.all import Packet
from scapy.fields import *
from scapy.sendrecv import AsyncSniffer
async def listenPEX()-> None:
    sniffer = AsyncSniffer(filter="udp dst port 6771")
    sniffer.start()

async def advertise(resources:list,bcast:str) -> None: 
    reader, writer = await open_connection(bcast,port=6771)

class PEX(Packet):
    name ="Peer Exchange"
    fields_desc= [IPField(name="peer_address",default="127.0.0.1"),
    IntField(name="port",default=6771),
    StrField(name="Resources")
    ]