#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import logging
from asyncio.streams import StreamReader, StreamWriter
from pathlib import Path

_log = logging.getLogger(__name__)
_name_queue: asyncio.Queue[str] | None = None
_image_dir = Path()


def find_image(name: str) -> str | None:
    image_glob = Path(_image_dir).glob(f"{name}.*")
    image_path = next(image_glob, None)
    if image_path is not None:
        _log.info(f"Found image: {image_path.name}")
        return image_path.name
    else:
        _log.warn(f"No image found matching name: {name}.*")
        return None


async def handle_event(message: str) -> None:
    _log.info(f"Received: {message}")
    fields = message.split(" ")
    if fields[0] == "PF":
        if len(fields) < 4:
            _log.warn("Incomplete event data")
        else:
            _log.info(f"Valid PF event detected with frame name '{fields[3]}'")
            if _name_queue:
                image_name = find_image(fields[3])
                if image_name:
                    await _name_queue.put(image_name)
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
    port: int, terminate: asyncio.Event, name_queue: asyncio.Queue[str], image_dir: Path
) -> None:
    global _name_queue
    global _image_dir

    _name_queue = name_queue
    _image_dir = image_dir

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
