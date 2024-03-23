import socket
import asyncio
import aiofiles

from math import e

import globals
from wlc_console import console
from peer_exchange import runPEX
from torrent_parser import read_torrent


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
    tasks = [
        asyncio.create_task(console()),
        asyncio.create_task(runPEX())
    ]
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    readconfig()
    asyncio.run(main())