#!/usr/bin/env python3

import time
import sys
import asyncio
import logging
import base64

from flask import Flask, render_template_string, Response
from turbo_flask import Turbo
from datetime import timedelta
from multiprocessing import Process
from threading import Thread
from random import randint
from pathlib import Path

app = Flask(__name__)
turbo = Turbo(app)

_log = logging.getLogger(__name__)
_frame_name = None
_image_dir = None

IMAGE = """
{% if frame_name %}
<div style="width:100%" id="image_container">
    <img src="/image/{{ frame_name }}" style="width:100%">
<div>
{% else %}
<div style="width:100%;margin:10%;font-size=300%" id="image_container">
    <p>No event received yet.</p>
<div>
{% endif %}
"""

INDEX = """
<!doctype html>
<html>
  <head>
    {{ turbo() }}
  </head>
  <body style="margin:0px">
""" + IMAGE + """
  </body>
</html>
"""

async def update_frame_name(terminate: asyncio.Event, name_queue: asyncio.Queue):
    while not terminate.is_set():
        _log.debug(f"waiting for name update")
        name_task = asyncio.create_task(name_queue.get())
        await asyncio.wait((name_task, terminate.wait()), return_when=asyncio.FIRST_COMPLETED)
        if name_task.done():
            global _frame_name
            _frame_name = name_task.result()
            _log.debug(f"Received frame name: {_frame_name}")
            with app.app_context():
                turbo.push(turbo.replace(render_template_string(IMAGE), "image_container"))


@app.route("/")
def index():
    return render_template_string(INDEX)

@app.route("/image/<filename>")
def image(filename: str):
    image_path = Path(_image_dir, filename)
    try:
        with image_path.open("rb") as f:
            image_data = f.read()
        _log.info(f"Loaded image: {image_path.as_posix()}")
        return Response(image_data)
    except FileNotFoundError:
        _log.error(f"File not found: {image_path.as_posix()}")
        return Response(status=404)

@app.context_processor
def inject_frame_name():
    _log.debug(f"Current frame name: {_frame_name}")
    return {"frame_name": _frame_name}

async def run_image_server(terminate: asyncio.Event, name_queue: asyncio.Queue, debug: bool, image_dir: Path):
    t = Thread(target=lambda: app.run(debug=debug, use_reloader=False, host="0.0.0.0"), daemon=True)
    tasks = (
        asyncio.create_task(update_frame_name(terminate, name_queue)),
    )

    global _image_dir
    _image_dir = image_dir

    t.start()

    _log.info(f"Running")

    await asyncio.wait(tasks)

    _log.info(f"Terminating")
