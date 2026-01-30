#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import logging
from asyncio.streams import StreamReader, StreamWriter

_log = logging.getLogger(__name__)
_name_queue: asyncio.Queue[str] | None = None


async def handle_event(message: str) -> None:
    _log.info(f"Received: {message}")
    fields = message.split(" ")
    if fields[0] == "PF":
        if len(fields) < 4:
            _log.warn("Incomplete event data")
        else:
            _log.info(f"Valid PF event detected with frame name '{fields[3]}'")
            if _name_queue:
                await _name_queue.put(fields[3])
            else:
                _log.warn("Event queue not intialized yet.")


async def handle_connection(reader: StreamReader, writer: StreamWriter) -> None:
    addr = ":".join([str(x) for x in writer.get_extra_info("peername")])
    _log.info(f"New connection from {addr}")

    while not reader.at_eof():
        data = await reader.readline()
        if not reader.at_eof():
            message = data.decode().strip()
            await handle_event(message)

    writer.close()
    await writer.wait_closed()

    _log.info(f"Connection closed by peer {addr}")


async def listen_events(
    port: int, terminate: asyncio.Event, name_queue: asyncio.Queue[str]
) -> None:
    global _name_queue

    _name_queue = name_queue

    server = await asyncio.start_server(handle_connection, "0.0.0.0", port)

    addr = ":".join([str(x) for x in server.sockets[0].getsockname()])
    _log.info(f"Listening on {addr}")

    tasks = (
        asyncio.create_task(server.serve_forever()),
        asyncio.create_task(terminate.wait()),
    )

    async with server:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)

    _log.info("Terminating")
