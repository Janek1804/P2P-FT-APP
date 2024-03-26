import asyncio
import netifaces

import globals

from wlc_console import console
from globals import getAddresses
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


async def main() -> None:
    """Runs the program
        INPUT ABSENT
        RETURNS NOTHING"""
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
    try:
        globals.host = netifaces.ifaddresses(netifaces.gateways()['default'][netifaces.AF_INET][1])[netifaces.AF_INET][0]['addr']
    except KeyError:
        addr = getAddresses()
        if len(addr) > 0:
            globals.host = addr[0]
    if globals.host != "":
        asyncio.run(main())
    else:
        print("Unable to launch program: No IPv4 interfaces detected!")