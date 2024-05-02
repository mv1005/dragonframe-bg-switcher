#!/usr/bin/env python3

import typer
import asyncio

from asyncio.streams import StreamReader, StreamWriter


def handle_event(message: str):
    print(f"Received: {message}")
    fields = message.split(" ")
    if fields[0] == "PF":
        if len(fields) < 4:
            print("Incomplete event data!")
        else:
            print("Detected valid PF event")
            print(f"Switching to image: {fields[3]}")


async def handle_connection(reader: StreamReader, writer: StreamWriter):

    addr = writer.get_extra_info("peername")
    print(f"New connection: {addr}")

    while not reader.at_eof():
        data = await reader.readline()
        if not reader.at_eof():
            message = data.decode().strip()
            handle_event(message)

    writer.close()
    await writer.wait_closed()
    print(f"Connection closed: {addr}")


async def listen_events(port: int):
    server = await asyncio.start_server(
        handle_connection, "0.0.0.0", port)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving: {addrs}')

    async with server:
        await server.serve_forever()


def run_server(port: int=8888):
    asyncio.run(listen_events(port))


def main():
    typer.run(run_server)
