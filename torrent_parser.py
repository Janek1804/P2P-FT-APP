import aiofiles
import asyncio
async def read_torrent(filename:str):
    async with aiofiles.open(file=filename,mode='r') as file :
        try:
            content:str = await file.read()
        except IndexError:
            pass
        await print(content)
if __name__ == "__main__":
    filename = "archlinux-2024.03.01-x86_64.iso.torrent"
    asyncio.run(read_torrent(filename))