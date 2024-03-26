import asyncio
import aiofiles

from os import scandir

import globals

from peer_exchange import obtainFromPeer
from globals import peers, resource_list, shpath, pcpath, resetAnnouncementsPEX


async def shdir(path:str='shared',num_pieces:int=512,target:str='pieces') -> None:
    """Prepares all the files from specified directory to be transferred
        INPUT:
        -path (string) - path to directory to be shared
        -num_pieces (int) - number of pieces to divide file into
        -target (string) - path to directory storing the pieces
        RETURNS NOTHING"""
    tmp = scandir(path)
    for file in tmp:
        if file.is_file():
            for peer in peers.keys():
                try:
                    for i in peers[peer]:
                        if i.find(file.name) != -1:
                            continue
                except KeyError:
                    continue
            pieces:list[bytes]= await create_pieces(f'{path}/{file.name}',num_pieces)
            await store_pieces(pieces,f'{target}/{file.name}')
        elif file.is_dir():
            await shdir(f'{path}/{file.name}',num_pieces,target)

async def create_pieces(filepath:str,num_pieces:int)->list[bytes]:
    """Creates pieces from specified file
        INPUT:
        -filepath (string) - path to file
        -num_pieces (int) - quantity of pieces to divide the file
        RETURNS:
        -pieces (list[bytes]) - pieces of the file ready to be transferred"""
    async with aiofiles.open(filepath,'rb') as file:
        content:bytes = await file.read()
        filesize:int = len(content)
        name:str = filepath.split("/")[-1]
        print(filesize)
        piecesize:int = filesize//num_pieces
        print(piecesize)
        pieces:list[bytes] = [] 
        for i in range(0,filesize,piecesize):
            current_piece = f"{name}:{i/piecesize+1}:{num_pieces}"
            if current_piece in resource_list:
                continue
            resource_list.append(current_piece)
            pieces.append(content[i:i+piecesize])
        if filesize % num_pieces != 0:
            pieces.append(content[piecesize*(num_pieces-1):])
        return pieces
async def store_pieces(pieces:list[bytes],path:str)->None:
    """Writes given pieces to a file
        INPUT:
        -pieces (list[bytes]) - pieces to be written
        -path (string) - name of files to write the pieces
            example: path=somefile results in pieces called somefile1, somefile2 etc.
        RETURNS NOTHING"""
    if len(pieces) > 0:
        for piece in pieces:
            async with aiofiles.open(path+str(pieces.index(piece)+1),'ab') as file:
                await file.write(piece)
    else:
        print("No pieces to write")
#Assuming resource list element local format <Address>:<Filename>:<Piece Number>:<Piece Quantity>
async def trackpieces(filename:str,resourcelist:list[str])->None:
    """Tracks pieces of file being obtained and stores the downloaded file
        INPUT:
        -filename (string) - name of file to obtain
        -resourcelist (list[string]) -list storing resources shared by peers
        RETURNS NOTHING"""
    print("aaaaa")
    filepieces:list[str] = []
    piecenums:list[int] = []
    for res in resourcelist:
        print(res)
        if res.find(filename) != -1:
            filepieces.append(res)
            print(res.split(":")[-2])
            try:
                piecenums.append(int(float(res.split(":")[-2])))
            except ValueError:
                print("Invalid piece number")
            print("bbb")

    print(range(1,int(filepieces[-1].split(":")[-1])+1))
    if sorted(piecenums) != list(range(1,int(filepieces[-1].split(":")[-1])+1)):
        print("Desired file unavailable!")
        return
    content:list[bytes]=[]
    requested:list[int] = []
    print(filepieces)
    for piece in filepieces:
        piecenum:int = int(float(piece.split(":")[-2]))
        if piecenum not in requested:
            requested.append(piecenum)
            tmp = piece.split(":")
            res:str = piece.removeprefix(tmp[0]+":")
            print(res)
            print(tmp[0])
            print(f"requesting piece {piecenum}")
            received=b""
            try:
                received = await obtainFromPeer(res,tmp[0],7050)
            except:
                print("aaa")
            
            print(received)
            if received != b"":
                print(f"received piece {piecenum}")
                content.insert(piecenum-1,received)
            else:
                requested.remove(piecenum)
    await writefile(filename,content)
    
async def writefile(filename:str,pieces:list[bytes])-> None:
    """Writes given pieces to a file
        INPUT:
        -filename (string) - name of file to write
        -pieces (list[bytes]) - list of pieces to write
        RETURNS NOTHING"""
    async with aiofiles.open(filename, "ab") as file:
        content:bytes = b""
        for piece in pieces:
            content += piece
        await file.write(content)

async def updateLocalResources()->None:
    """Updates local resources
        INPUT NOTHING
        RETURNS NOTHING"""
    try:
        while globals.run:
            current = resource_list.copy()
            await shdir(shpath,20,pcpath)
            if resource_list != current:
                resetAnnouncementsPEX.set()
            await asyncio.sleep(600)
    except asyncio.CancelledError:
        return

if __name__ == "__main__":
    file="test.txt"
    pieces = asyncio.run(create_pieces(file,2))
    print(pieces)
    with open("aaa.txt",'ab') as f2:
        content = b""
        for piece in pieces:
            content += piece
        print(content)
        f2.write(content)
