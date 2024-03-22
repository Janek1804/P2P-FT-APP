from math import e
from torrent_parser import read_torrent
import aiofiles
import asyncio
shpath:str ="shared"
pcpath:str = "pieces"
def readconfig(path:str="FT.conf") -> None:
    with open(path,'r') as file:
        entries:list[str] =  file.readlines()
        print(entries)
        for entry in entries:
            if entry[0] == "#":
                continue
            if entry.find("shared") != -1:
                global shpath
                shpath = entry.strip().split("=",1)[1]
            elif entry.find("pieces") != -1:
                global pcpath
                pcpath = entry.strip().split("=",1)[1]
if __name__ == "__main__":
    readconfig()
    print(shpath)
    print(pcpath)