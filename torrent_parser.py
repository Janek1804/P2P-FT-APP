import aiofiles
from bcoding import bdecode
import asyncio
class torrent:
    def __init__(self,torrent_dict) -> None:
        try:
            self.length:int = int(torrent_dict['info']['length'])
        except ValueError:
            print("Invalid length value!")
            return
        self.name:str = torrent_dict['info']['name']
        try:
            self.piece_length:int = int(torrent_dict['info']['piece length'])
        except ValueError:
            print("Invalid piece length!")
            return
        self.url_list:list[str] =  torrent_dict['info']['url-list']
async def read_torrent(filename:str)->list[dict,bytes]:
    async with aiofiles.open(file=filename,mode='br') as file :
        content:str = await file.read()
        decoded = bdecode(content)
        pieces:bytes = decoded['info']['pieces']
        print(type(pieces))
        del decoded['info']['pieces']
        data = [decoded,pieces]
        print(decoded)
        return data
if __name__ == "__main__":
    filename = "archlinux-2024.03.01-x86_64.iso.torrent"
    asyncio.run(read_torrent(filename))
