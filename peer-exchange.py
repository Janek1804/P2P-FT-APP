from asyncio import Timeout, open_connection
from asyncio import sleep as as_sleep
from asyncio import timeout
from asyncio.windows_events import NULL
from scapy.all import Packet
from scapy.fields import *
from scapy.sendrecv import AsyncSniffer
from scapy.all import get_if_addr
from scapy.layers.inet import IP

bcast_timer = 90
dead_timer = 200
host = get_if_addr(conf.iface)

peers = {} # format: Address : Last time heard


async def listenPEX(bcast: str)-> None:
    """[!] Listens for PEX messages and handles adding peers, WARNING: this function expects to be run on a separate thread
        INPUT:
        - bcast (string) - broadcast ip address in string format
        RETURNS NOTHING"""
    msg_list = []
    sniffer = AsyncSniffer(filter=f"(udp dst port 6771) && (dst host {host} || dst net {bcast})", prn=lambda x: msg_list.append(x), store = False)
    sniffer.start()
    while True:
        for msg in msg_list:
            if PEX in msg:
                peers[msg[PEX].peer_address] = time.time()
            msg_list.remove(msg)


async def advertise(resources: list, bcast: str) -> None:
    """Broadcasts its presence to other peers on LAN
        INPUT:
        - resources (list) - list of resources to be broadcast
        - bcast (string) - broadcast ip address in string format
        RETURNS NOTHING"""
    reader, writer = await open_connection(bcast,port=6771)
    while True:
        writer.write(PEX(peer_address = host, Resources = resources))
        next_bcast = time.time() + bcast_timer # next_bcast as specific time
        await writer.drain()
        next_bcast = next_bcast - time.time() # next_bcast as delay
        if next_bcast > 0:
            await as_sleep(next_bcast-time.time())


async def verifyPeersLife() -> None:
    """Verifies each peer once per broadcast cycle
        INPUT ABSENT
        RETURNS NOTHING"""
    while True:
        for entry in peers.keys():
            if time.time() - peers[entry] > dead_timer:
                peers.pop(entry)
        await as_sleep(bcast_timer)


async def obtainFromPeer(resource: str, peer: str, port: int = 6771) -> list[bytes]:
    """Attempts to obtain specified resource from specified peer.
        INPUT:
        - resource (string) - resource to be requested
        - peer (string) - peer's ip address in string format
        - port (int) - destination port in string format
        RETURNS:
        - pieces (list[bytes]) - containing obtaines pieces from peer, in the event of failure returns empty list"""
    reader, writer = await open_connection(peer, port=port)
    writer.write(f"Request:{resource}".encode()) # TODO: This seems a bit silly...
    pieces = []
    await writer.drain()
    try:
        while True:
            async with timeout(10):
                line = await reader.readline()
                if not line:
                    break
            # TODO: Figure out the format and add translation from line to pieces
    except TimeoutError:
        pass
    writer.close()
    await writer.wait_closed()
    return pieces


class PEX(Packet):
    """Defines PEX packet based on scapy"""
    name ="Peer Exchange"
    fields_desc= [IPField(name="peer_address",default="127.0.0.1"),
    IntField(name="port",default=6771),
    StrField(name="Resources")
    ]