import os
import time
import socket
import asyncio
import aiofiles

from typing import Optional
from asyncio import sleep as as_sleep
from asyncio import CancelledError, wait_for, get_running_loop, open_connection

import globals

bcast_timer = 90
dead_timer = 200


async def listenPEX(PEX_queue: asyncio.Queue)-> None:
    """Listens for PEX messages
        INPUT:
        - PEX_queue (queue) - asyncio queue to put received PEX messages
        RETURNS NOTHING"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", 7050))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(False)
    loop = asyncio.get_running_loop()
    try:
        while globals.run:
            data = await loop.sock_recv(sock, 1024)
            PEX_queue.put_nowait((data.decode(), time.time()))
            await as_sleep(0) # yielding control just in case something else is on the same thread
    except CancelledError:
        pass
    finally:
        sock.close()


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
                    data = msg[0].partition(";")  # data[0] = f"PEX-PEER:{host}", data[2] = f"RESOURCES:{','.join(resources)}"
                    addr = data[0].replace("PEX-PEER:", "", 1)
                    if addr != globals.host:
                        globals.peers[addr] = [msg[1], data[2].replace("RESOURCES:", "", 1).split(",")]
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
            request = await wait_for(reader.read(-1), timeout = 120)
            request = request.decode()
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
        pass
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
    try:
        async with serv:
            await serv.serve_forever()
    except CancelledError:
        serv.close()


async def advertise(resources: list, bcast: str = "255.255.255.255") -> None:
    """Broadcasts its presence to other peers on LAN
        INPUT:
        - resources (list) - list of resources to be broadcast
        - bcast (string) [default: "255.255.255.255"] - broadcast ip address in string format
        RETURNS NOTHING"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((globals.host, 7050))
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.connect((bcast, 7050))
    sock.setblocking(False)
    loop = get_running_loop()
    msg = f"PEX-PEER:{globals.host};RESOURCES:{','.join(resources)}".encode()
    try:
        while globals.run:
            next_bcast = time.time() + bcast_timer # next_bcast as specific time
            await loop.sock_sendall(sock, msg)
            next_bcast = next_bcast - time.time() # next_bcast as delay
            if next_bcast >= 0:
                await as_sleep(next_bcast)
    except CancelledError:
        pass
    finally:
        sock.close()


async def verifyPeersLife() -> None:
    """Verifies each peer once per broadcast cycle
        INPUT ABSENT
        RETURNS NOTHING"""
    try:
        while globals.run:
            for entry in globals.peers.keys():
                if time.time() - globals.peers[entry] > dead_timer:
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
    except CancelledError:
        return piece
    try:
        writer.write(f"REQUEST:{resource};".encode())
        await writer.drain()
        try:
            data = await wait_for(reader.read(-1), timeout = 60)
            data = data.decode()
            if data.startswith("CONTENT:"):
                piece = data.partition(";")[2].encode()
        except TimeoutError:
            pass
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