import aiofiles
from os import listdir

async def create_pieces(filepath:str,num_pieces:int)->list[bytes]:
    async with aiofiles.open(filepath,'rb') as file:
        content:bytes = file.read()
        size = len(content)
        pieces:list[bytes] = [content[i:i+(size/num_pieces)] for i in range(0,num_pieces,size/num_pieces)]
        return pieces
async def store_pieces(pieces:list[bytes],path:str)->None:
    if len(pieces) > 0:
        async with aiofiles.open(path,'ab') as file:
            for piece in pieces:
                await file.write(piece)