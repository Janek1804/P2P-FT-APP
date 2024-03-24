import socket
import asyncio
import aiofiles

import globals

from wlc_console import console
from peer_exchange import runPEX
from file_sharing import updateLocalResources


def readconfig(path:str="FT.conf") -> None:
    """Reads configuration file
        INPUT:
        - path (string) - local path to configuration file
        RETURNS NOTHING"""
    with open(path,'r') as file:
        entries:list[str] =  file.readlines()
        #print(entries)
        for entry in entries:
            if entry[0] == "#":
                continue
            if entry.find("shared") != -1:
                globals.shpath = entry.strip().split("=",1)[1]
            elif entry.find("pieces") != -1:
                globals.pcpath = entry.strip().split("=",1)[1]


async def main():
    tasks = []
    try:
        tasks = [
            asyncio.create_task(console()),
            asyncio.create_task(runPEX()),
            asyncio.create_task(updateLocalResources())
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    except asyncio.CancelledError:
        for task in tasks:
            task.cancel()


if __name__ == "__main__":
    readconfig()
    asyncio.run(main())