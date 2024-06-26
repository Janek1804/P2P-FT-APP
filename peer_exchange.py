import os
import time
import socket
import asyncio
import aiofiles
from aiohttp import ClientConnectionError, ClientSession, ClientTimeout 

from typing import Optional
from asyncio import sleep as as_sleep
from asyncio import CancelledError, wait_for, get_running_loop, open_connection

import globals

from globals import setupUDPSocket

bcast_timer = 90
dead_timer = 200


async def listenPEX(PEX_queue: asyncio.Queue)-> None:
    """Listens for PEX messages
        INPUT:
        - PEX_queue (queue) - asyncio queue to put received PEX messages
        RETURNS NOTHING"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except CancelledError:
        return
    except ConnectionError:
        print("ERROR: Unable to start listening for advertisements. Download unavailable")
        globals.sharing_only = True
        globals.new_issue.set()
        return
    try:
        setupUDPSocket(sock)
        sock.bind(("", 7050))
        sock.setblocking(False)
    except CancelledError:
        sock.close()
        return
    except ConnectionError:
        print("ERROR: Unable to start listening for advertisements. Download unavailable")
        globals.sharing_only = True
        globals.new_issue.set()
        return
    loop = asyncio.get_running_loop()
    try:
        while globals.run:
            data = await loop.sock_recv(sock, 1024)
            PEX_queue.put_nowait((data.decode(), time.time()))
            await as_sleep(0) # yielding control just in case something else is on the same thread
    except CancelledError:
        sock.close()
        return
    finally:
        sock.close()

async def request_resource(addr: str, port: int, file: str="")->list[str]:
    """[!] Requests resources from HTTP server, WARNING: may raise ClientConnectionError
        INPUT:
        -addr (string) - ip address of a HTTP server
        -port (int) - port on which server is listening
        -file (string) [default: ""] - name of file to request; if set to empty string requests all files
        RETURNS:
        -resource (list[string]) - list of resource strings of requested file"""
    timeout= ClientTimeout(total=10)
    async with ClientSession(timeout=timeout) as session:
        url:str = f"http://{addr}:{port}/{file}"
        print(url)
        async with session.get(url) as response:
            resource = await response.json()
            print(resource)
            return resource




async def handlePEX(PEX_queue: asyncio.Queue) -> None:
    """ Handles received PEX messages
        INPUT:
        - PEX_queue (queue) - asyncio queue of received PEX messages
        RETURNS NOTHING"""
    try:
        while globals.run:
            msg = await PEX_queue.get()
            try:
                if msg[0].startswith("PEX-PEER"):
                    data = msg[0].split(";")  # [0] PEX-PEER:{host_addr} [1] HTTP:{http_port} [2] UPDATE (may be absent)
                    addr = data[0].replace("PEX-PEER:", "", 1)
                    port = int(data[1].replace("HTTP:", "", 1))
                    if addr != globals.host:
                        if len(data) > 1:
                            if data[2] == "UPDATE": # Get all on peer
                                try:
                                    res_list = await request_resource(addr, port)
                                    res_list = list(set(res_list))
                                    async with globals.peers_lock:
                                        globals.peers[addr] = [msg[1], res_list, 1]
                                except ClientConnectionError:
                                    async with globals.peers_lock:
                                        globals.peers[addr] = [msg[1], [], 0] # Try again soon
                            else:
                                async with globals.peers_lock:
                                    if addr in globals.peers.keys():
                                        times = globals.peers[addr][2]
                                    else:
                                        times = 0
                                if times == 0 or times >= 10: # Get or update all on peer
                                    try:
                                        res_list = await request_resource(addr, port)
                                        res_list = list(set(res_list))
                                        async with globals.peers_lock:
                                            globals.peers[addr] = [msg[1], res_list, 1]
                                    except ClientConnectionError:
                                        async with globals.peers_lock:
                                            globals.peers[addr] = [msg[1], [], 1]
                                else: # Update last time heard and times heard only on peer
                                    async with globals.peers_lock:
                                        globals.peers[addr][0] = msg[1]
                                        globals.peers[addr][2] += 1
            except CancelledError:
                PEX_queue.put_nowait(msg)
            finally:
                PEX_queue.task_done()
    except CancelledError:
        return

# TODO: Add checking for number of pieces
async def getLocalFile(request: str) -> bytes:
    try:
        request_list = request.split(":", 2) # [filename, piece, total pieces]
        filepath = os.path.join(globals.pcpath, (request_list[0]+request_list[1]))
        if not os.path.isfile(filepath):
            return b""
        async with aiofiles.open(filepath, mode="br") as file:
            return await file.read()
    except CancelledError:
        return b""


async def handleRequests(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    """[!] Handles TCP requests, WARNING: this function should only be run by the TCP server
        INPUT:
        - reader (asyncio.StreamReader) - incoming message reader
        - writer (asyncio.StreamWriter) - message writer
        RETURNS NOTHING"""
    try:
        try:
            request = await wait_for(reader.readuntil(b";"), timeout = 120)
            request = request.decode().replace("REQUEST:", "").replace(";", "")
            file_contents = await getLocalFile(request)
            if file_contents == b"":
                writer.write(f"RESOURCE_MISSING:{request}".encode())
            else:
                writer.write(f"CONTENT:{request};".encode() + file_contents)
        except TimeoutError:
            writer.close()
            await writer.wait_closed()
            return        
    except CancelledError:
        writer.close()
        await writer.wait_closed()
        return
    except ConnectionError:
        return
    finally:
        await writer.drain()
        writer.close()
        await writer.wait_closed()


async def listenTCP(sock: Optional[socket.socket] = None, port: int = 7050, listen_addr:str = "") -> None:
    """Listens for TCP requests on the specified socket or port
        INPUT:
        - sock (socket) [OPTIONAL] - TCP socket to listen at, if absent port is used instead
        - port (int) [default: 7050] - TCP port number to listen at, will be used only if sock is None
        - listen_addr (string) [default: ""] - IP address of the interface to listen at
        RETURNS NOTHING"""
    try:
        if sock is None:
            serv = await asyncio.start_server(handleRequests, listen_addr, port)
        else:
            serv = await asyncio.start_server(handleRequests, sock=sock)
    except CancelledError:
        return
    except ConnectionError:
        print("WARNING: Could not start sharing server. Only downloading available.")
        globals.download_only = True
        globals.new_issue.set()
        return
    try:
        async with serv:
            await serv.serve_forever()
    except CancelledError:
        serv.close()
    except ConnectionError:
        print("ERROR: Sharing server failed unexpectedly.")
        globals.download_only = True
        globals.new_issue.set()
        return


async def advertise(resources: list, bcast: str = "255.255.255.255", http_port: int = 7051) -> None:
    """Broadcasts its presence to other peers on LAN
        INPUT:
        - resources (list) - list of resources to be broadcast
        - bcast (string) [default: "255.255.255.255"] - broadcast ip address in string format
        - http_port (int) [default: 7051] - port number of local HTTP server
        RETURNS NOTHING"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except ConnectionError:
        print("WARNING: Could not start sharing server. Only downloading available.")
        globals.download_only = True
        globals.new_issue.set()
        return
    except CancelledError:
        return
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        setupUDPSocket(sock)
        sock.bind((globals.host, 7050))
        sock.connect((bcast, 7050))
        sock.setblocking(False)
    except ConnectionError:
        print("WARNING: Could not start sharing server. Only downloading available.")
        globals.download_only = True
        globals.new_issue.set()
        return
    except CancelledError:        
        sock.close()
        return
    try:
        loop = get_running_loop()
        msg = f"PEX-PEER:{globals.host};HTTP:{http_port}".encode()
        await loop.sock_sendall(sock, msg + ";UPDATE".encode())
        next_bcast = bcast_timer
        while globals.run:
            if next_bcast >= 0:
                await as_sleep(next_bcast)
            next_bcast: float = time.time() + bcast_timer # next_bcast as specific time
            await loop.sock_sendall(sock, msg)
            next_bcast = next_bcast - time.time() # next_bcast as delay
    except CancelledError:
        sock.close()
        return
    except ConnectionError:
        return
    finally:
        sock.close()


async def verifyPeersLife() -> None:
    """Verifies each peer once per broadcast cycle
        INPUT ABSENT
        RETURNS NOTHING"""
    try:
        while globals.run:
            async with globals.peers_lock:
                for entry in globals.peers.keys():
                    if time.time() - globals.peers[entry][0] > dead_timer:
                        globals.peers.pop(entry)
            await as_sleep(bcast_timer)
    except CancelledError:
        return


async def obtainFromPeer(resource: str, peer: str, port: int = 7050) -> bytes:
    """Attempts to obtain specified resource from specified peer.
        INPUT:
        - resource (string) - resource to be requested
        - peer (string) - peer's ip address in string format
        - port (int) [default: 7050] - destination port in int format
        RETURNS:
        - piece (bytes) - containing obtaines piece from peer, in the event of failure returns empty bytes object"""
    piece = b""
    try:
        reader, writer = await open_connection(peer, port=port)
    except ConnectionError:
        return b""
    except CancelledError:
        return b""
    try:
        writer.write(f"REQUEST:{resource};".encode())
        await writer.drain()
        try:
            #er.write(f"CONTENT:{request};".encode() + file_contents)
            data = await wait_for(reader.read(-1), timeout = 60)
            if data.startswith(b"CONTENT:"):
                piece = data[data.find(b";")+1:]
        except TimeoutError:
            pass
    except ConnectionError:
        return b""
    except CancelledError:
        await writer.drain()
        writer.write(f"CANCEL_REQUEST:{resource}".encode())
    finally:
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return piece

async def selfTestOne():
    print("Running network self-test.")
    res_list = ["TESTING", "TEST"]
    tasks = [asyncio.create_task(advertise(res_list)), asyncio.create_task(listenPEX(asyncio.Queue()))]
    await asyncio.gather(*tasks, return_exceptions=True)


async def watchEvent(tasks: list[asyncio.Task], event: asyncio.Event) -> None:
    """Watches specified event and cancels all task when it is set
        INPUT:
        - tasks (list[asyncio.Task]) - list of tasks to cancel when event is set
        - event (asyncio.Event) - event to watch
        RETURNS NOTHING"""
    try:
        await event.wait()
        event.clear()
        for task in tasks:
            task.cancel()
    except CancelledError:
        return


async def runAdvert() -> None:
    """Runs advertisement function
        INPUT ABSENT
        RETURNS NOTHING"""
    advert = None
    watch = None
    try:
        while globals.run:
            advert = asyncio.create_task(advertise(globals.resource_list))
            watch = asyncio.create_task(watchEvent([advert], globals.resetAnnouncementsPEX))
            await advert
    except CancelledError:
        if watch is not None:
            watch.cancel()
        if advert is not None:
            advert.cancel()
        return


async def runOther() -> None:
    """Runs non-advertisement functions
        INPUT ABSENT
        RETURNS NOTHING"""
    tasks = []
    watch = None
    PEX_queue = asyncio.Queue()
    try:
        while globals.run:
            tasks = [
                asyncio.create_task(listenPEX(PEX_queue)),
                asyncio.create_task(handlePEX(PEX_queue)),
                asyncio.create_task(verifyPeersLife()),
                asyncio.create_task(listenTCP()),
            ]
            watch = asyncio.create_task(watchEvent(tasks, globals.resetPEX))
            await asyncio.gather(*tasks, return_exceptions=True)
    except CancelledError:
        if watch is not None:            
            watch.cancel()
        for task in tasks:
            task.cancel()
        return

async def runPEX() -> None:
    """Runs PEX functions
        INPUT ABSENT
        RETURNS NOTHING"""
    tasks = []
    try:
        tasks = [
            asyncio.create_task(runAdvert()),
            asyncio.create_task(runOther())
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    except CancelledError:
        for task in tasks:
            task.cancel()


if __name__ == "__main__":
    asyncio.run(selfTestOne())
