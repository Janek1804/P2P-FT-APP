from aiohttp import web
from asyncio import CancelledError

import globals

from globals import resource_list, resource_list_lock

routes = web.RouteTableDef()


async def get_all(request):
    return web.json_response(resource_list)

async def get_file(request):
    file_list = []
    async with resource_list_lock:
        for res in resource_list:
            if res.find(request.match_info['name']) != -1:
                file_list.append(res)
    return web.json_response(file_list)

async def init():
    app = web.Application()
    runner = web.AppRunner(app)
    app.add_routes([web.get('/', get_all),web.get('/{name}',get_file)])
    await runner.setup()
    try:
        site = web.TCPSite(runner,globals.host,7051)
        await site.start()
    except CancelledError:
        await runner.cleanup()