from peer_exchange import obtainFromPeer
import aiofiles
import asyncio
from os import scandir

async def shdir(path:str='shared',num_pieces=512,target='pieces') -> None:
    tmp = scandir(path)
    for filename in tmp:
        if filename.is_file():
            pieces:list[bytes]= await create_pieces(f'{path}/{filename}',num_pieces)
            await store_pieces(pieces,f'{target}/{filename}')
        elif filename.is_dir():
            shdir(f'{path}/{filename}',num_pieces,target)

async def create_pieces(filepath:str,num_pieces:int)->list[bytes]:
    async with aiofiles.open(filepath,'rb') as file:
        content:bytes = await file.read()
        filesize:int = len(content)
        print(filesize)
        piecesize:int = filesize//num_pieces
        print(piecesize)
        pieces:list[bytes] = [] 
        for i in range(0,filesize,piecesize):
            pieces.append(content[i:i+piecesize])
        if filesize % num_pieces != 0:
            pieces.append(content[piecesize*(num_pieces-1):-1])
        return pieces
async def store_pieces(pieces:list[bytes],path:str)->None:
    if len(pieces) > 0:
        async with aiofiles.open(path,'ab') as file:
            for piece in pieces:
                await file.write(piece)
    else:
        print("No pieces to write")
#Assuming resource list element local format <Address>:<Port>:<Filename>:<Piece Number>:<Piece Quantity>
async def trackpieces(filename:str,resourcelist:list[str])->None:
    filepieces:list[str] = []
    piecenums:list[int] = []
    for res in resourcelist:
        if res.find(filename) != -1:
            filepieces.append(res)
            piecenums.append(res.split(":")[-2])
    if set(piecenums) != set(range(1,int(filepieces[-1][-1])+1)):
        print("Desired file unavailable!")
        return
    content:list[bytes]=[]
    requested:list[int] = []
    for piece in filepieces:
        piecenum:int = int(piece.split(":")[-2])
        if piecenum not in requested:
            requested.append(piecenum)
            tmp = piece.split(":")
            received = await obtainFromPeer(tmp[2:],tmp[0],tmp[1])
            if received != None:
                content.insert(piecenum-1,received)
            else:
                requested.remove(piecenum)
    writefile(filename,content)
    
async def writefile(filename:str,pieces:list[bytes])-> None:
    with aiofiles.open(filename, "ab") as file:
        content:bytes = b""
        for piece in pieces:
            content += piece
        file.write(content)

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
