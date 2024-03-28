import asyncio

async def handle_client(reader, writer):
    # Read data from the client
    data = await reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    print(f"Received {message} from {addr}")

    # Send response to the client
    response = f"Echo: {message}"
    writer.write(response.encode())
    await writer.drain()

    # Close the connection
    print("Closing the connection")
    writer.close()

async def main():
    server = await asyncio.start_server(handle_client, '', 8888)
    addr = server.sockets[0].getsockname()
    print(f"Serving on {addr}")

    async with server:
        await server.serve_forever()

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Server stopped manually.")

