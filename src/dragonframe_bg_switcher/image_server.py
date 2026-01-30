#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import base64
import logging
import sys
import time
from datetime import timedelta
from multiprocessing import Process
from pathlib import Path
from random import randint
from threading import Thread

from flask import Flask, Response, render_template_string
from turbo_flask import Turbo  # type: ignore

app = Flask(__name__)
turbo = Turbo(app)

_log = logging.getLogger(__name__)
_image_dir = Path()

IMAGE = """
{% if image_name %}
<div style="width:100%" id="image_container">
    <img src="/image/{{ image_name }}" style="width:100%">
<div>
{% else %}
<div style="width:100%;margin:10%;font-size=300%" id="image_container">
    <p>No event received yet.</p>
<div>
{% endif %}
"""

INDEX = (
    """
<!doctype html>
<html>
  <head>
    {{ turbo() }}
  </head>
  <body style="margin:0px">
"""
    + IMAGE
    + """
  </body>
</html>
"""
)


async def update_image_name(
    terminate: asyncio.Event,
    name_queue: asyncio.Queue[str],
) -> None:
    while not terminate.is_set():
        _log.debug("waiting for name update")
        name_task = asyncio.create_task(name_queue.get())
        terminate_task = asyncio.create_task(terminate.wait())
        await asyncio.wait(
            (name_task, terminate_task), return_when=asyncio.FIRST_COMPLETED
        )
        if name_task.done():
            image_name = name_task.result()
            _log.debug(f"Received image name: {image_name}")
            with app.app_context():
                turbo.push(
                    turbo.replace(
                        render_template_string(IMAGE, image_name=image_name),
                        "image_container",
                    )
                )


@app.route("/")
def index() -> str:
    return render_template_string(INDEX)


@app.route("/image/<filename>")
def image(filename: str) -> Response:
    with Path(_image_dir, filename).open("rb") as f:
        image_data = f.read()
    return Response(image_data)


async def run_image_server(
    terminate: asyncio.Event,
    name_queue: asyncio.Queue[str],
    debug: bool,
    image_dir: Path,
) -> None:
    t = Thread(
        target=lambda: app.run(debug=debug, use_reloader=False, host="0.0.0.0"),
        daemon=True,
    )
    tasks = (asyncio.create_task(update_image_name(terminate, name_queue)),)

    global _image_dir
    _image_dir = image_dir

    t.start()

    _log.info("Running")

    await asyncio.wait(tasks)

    _log.info("Terminating")
