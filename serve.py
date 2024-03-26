from aiohttp import web
from globals import resource_list

routes = web.RouteTableDef()

@routes.get('/')
async def get_all(request):
    return resource_list

async def init():
    app = web.Application()
    runner = web.AppRunner(app)
    app.router.add_get('/', get_all)
    await runner.setup()
    try:
        site = web.TCPSite(runner,'localhost',8080)
        await site.start()
    except CancelledError:
        await runner.cleanup()