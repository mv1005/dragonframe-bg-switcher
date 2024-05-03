#!/usr/bin/env python3

import sys
import atexit
import typer
import asyncio
import logging

from threading import Lock, Thread, Event
from signal import signal, SIGINT, SIGTERM, Signals
from time import sleep
from rich.logging import RichHandler
from pathlib import Path

from dragonframe_bg_switcher.event_receiver import listen_events
from dragonframe_bg_switcher.image_server import run_image_server

_log = logging.getLogger(__name__)
_terminate = None

def set_term_event():
    _log.debug("Termination application")
    if _terminate is not None:
        _terminate.set()
    else:
        _log.warn("Termination requested prior to full startup")

def signal_handler(sig, frame):
    _log.debug(f"Received {Signals(sig).name}")
    asyncio.get_running_loop().call_soon_threadsafe(set_term_event)

async def switcher(port: int, debug: bool, image_dir: Path):
    global _terminate

    _terminate = asyncio.Event()
    _log.info("Starting up")

    name_queue = asyncio.Queue()

    tasks = (
        asyncio.create_task(listen_events(port, _terminate, name_queue)),
        asyncio.create_task(run_image_server(_terminate, name_queue, debug, image_dir)),
        asyncio.create_task(_terminate.wait()),
    )

    _log.info("Application running")

    await asyncio.sleep(0.2)

    signal(SIGINT, signal_handler)
    signal(SIGTERM, signal_handler)

    await asyncio.wait(tasks)

    _log.info("All done, bye bye :)")

def main(image_dir: Path, port: int=8888, debug: bool=False):
    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    my_handler = RichHandler(show_path=False, log_time_format="%d %b %H:%m:%S")
    logging.basicConfig(level=log_level, format="%(module)s: %(message)s", handlers=[my_handler])

    if not image_dir.exists():
        _log.error(f"Image directory does not exist: {image_dir.as_posix()}")
        sys.exit(1)

    if not image_dir.is_dir():
        _log.error(f"Image directory is not a directory: {image_dir.as_posix()}")
        sys.exit(1)

    asyncio.run(switcher(port, debug, image_dir))

def cli_entrypoint():
    typer.run(main)
