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

async def switcher(port: int):
    global _terminate
    signal(SIGINT, signal_handler)
    signal(SIGTERM, signal_handler)
    # rcv_thread = Thread(target=start_receiver, args=(port,)).start()
    _terminate = asyncio.Event()
    _log.info("Starting event receiver")
    await listen_events(port, _terminate)
    await _terminate.wait()
    _log.info("All done, bye bye :)")

def main(port: int=8888, debug: bool=False):
    if debug:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    my_handler = RichHandler(show_path=False, log_time_format="%d %b %H:%m:%S")
    logging.basicConfig(level=log_level, format="%(module)s: %(message)s", handlers=[my_handler])
    asyncio.run(switcher(port))

def cli_entrypoint():
    typer.run(main)
