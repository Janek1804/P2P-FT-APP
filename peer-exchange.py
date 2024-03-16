from asyncio import open_connection
from asyncio import sleep as as_sleep
from networkx import is_empty
from scapy.all import Packet
from scapy.fields import *
from scapy.sendrecv import AsyncSniffer
from scapy.all import get_if_addr

bcast_timer = 90
dead_timer = 200
host = get_if_addr(conf.iface)

peers = {} # format: Address : Last time heard
msg_list = []


async def listenPEX(bcast:str)-> None:
    """Listens for PEX messages and forwards them for processing"""
    sniffer = AsyncSniffer(filter=f"(udp dst port 6771) && (dst host {host} || dst net {bcast})", prn=lambda x: msg_list.append(x))
    sniffer.start()

async def advertise(resources:list,bcast:str) -> None:
    """Broadcasts its presence to other peers on LAN"""
    reader, writer = await open_connection(bcast,port=6771)
    while True:
        writer.write(PEX(peer_address = host, Resources = resources))
        next_bcast = time.time() + bcast_timer # next_bcast as specific time
        await writer.drain()
        next_bcast = next_bcast - time.time() # next_bcast as delay
        if next_bcast > 0:
            await as_sleep(next_bcast-time.time())

async def verifyPeersLife() -> None:
    """Verifies each peer once per broadcast cycle"""
    for entry in peers.keys():
        if time.time() - peers[entry] > dead_timer:
            peers.pop(entry)
    await as_sleep(bcast_timer)


class PEX(Packet):
    """Defines PEX packet based on scapy"""
    name ="Peer Exchange"
    fields_desc= [IPField(name="peer_address",default="127.0.0.1"),
    IntField(name="port",default=6771),
    StrField(name="Resources")
    ]