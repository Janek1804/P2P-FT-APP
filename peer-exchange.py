# TODO: Figure out how to get the proper broadcast and host ip addr., as 255.255.255.255 can fail (Much fun)

from asyncio import wait_for, get_running_loop, open_connection
from asyncio import sleep as as_sleep
import asyncio
import socket
import time

bcast_timer = 90
dead_timer = 200
host = socket.gethostbyname(socket.gethostname())
msg_list = []

peers = {} # format: Address : Last time heard

async def listenPEX(bcast: str, PEX_queue: asyncio.queue)-> None:
    # TODO: Verify whether bcast is even needed
    """[!] Listens for PEX messages, WARNING: this function expects to be run on a separate thread
        INPUT:
        - bcast (string) - broadcast ip address in string format
        - PEX_queue (queue) - asyncio queue to put received PEX messages
        RETURNS NOTHING"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 6771))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(False)
    while True:
        data, addr = await get_running_loop().sock_recv(sock, 1024)
        PEX_queue.put((addr, data.decode(), time.time()))
        await as_sleep(0) # yielding control just in case something else is on the same thread

async def handlePEX(PEX_queue: asyncio.queue):
    """ Handles received PEX messages
        INPUT:
        - PEX_queue (queue) - asyncio queue of received PEX messages"""
    while True():
        msg = await PEX_queue.get()
        peers[msg[0]] = msg[2]
        # TODO: Add resource list handling
        PEX_queue.task_done()


async def advertise(resources: list, bcast: str) -> None:
    """Broadcasts its presence to other peers on LAN
        INPUT:
        - resources (list) - list of resources to be broadcast
        - bcast (string) - broadcast ip address in string format
        RETURNS NOTHING"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 6771))
    sock.connect((bcast, 6771))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setblocking(False)
    loop = get_running_loop()
    msg = f"PEX-PEER:{host};RESOURCES:{','.join(resources)}".encode()
    while True:
        next_bcast = time.time() + bcast_timer # next_bcast as specific time
        await loop.sock_sendall(sock, msg)
        next_bcast = next_bcast - time.time() # next_bcast as delay
        if next_bcast >= 0:
            await as_sleep(next_bcast)


async def verifyPeersLife() -> None:
    """Verifies each peer once per broadcast cycle
        INPUT ABSENT
        RETURNS NOTHING"""
    while True:
        for entry in peers.keys():
            if time.time() - peers[entry] > dead_timer:
                peers.pop(entry)
        await as_sleep(bcast_timer)


async def obtainFromPeer(resource: str, peer: str, port: int = 6771) -> bytes:
    """Attempts to obtain specified resource from specified peer.
        INPUT:
        - resource (string) - resource to be requested
        - peer (string) - peer's ip address in string format
        - port (int) [default: 6771] - destination port in int format
        RETURNS:
        - piece (bytes) - containing obtaines piece from peer, in the event of failure returns empty bytes object"""
    reader, writer = await open_connection(peer, port=port)
    writer.write(f"REQUEST:{resource}".encode())
    await writer.drain()
    try:
        piece = await wait_for(reader.read(-1), timeout = 60)
    except TimeoutError:
        piece = b""
    writer.close()
    await writer.wait_closed()
    return piece

if __name__ == "__main__":
    print("Running network self-test.")
    res_list = ["TESTING", "TEST"]
    bcast = "192.168.2.255"
    try:
        wait_for(asyncio.run(advertise(res_list, bcast)), timeout = 60)            
    except TimeoutError:
            print("Ended advertising test")