import aiofiles
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
        content:bytes = file.read()
        filesize:int = len(content)
        piecesize:int = filesize//num_pieces
        pieces:list[bytes] = [content[i:i+piecesize] for i in range(0,num_pieces,piecesize)]
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