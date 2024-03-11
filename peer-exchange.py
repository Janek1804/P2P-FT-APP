from asyncio import open_connection

async def advertise(resources:list,bcast:str) -> None: 
    reader, writer = await open_connection(bcast,port=6771)