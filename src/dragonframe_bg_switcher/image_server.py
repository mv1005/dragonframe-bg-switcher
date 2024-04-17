#!/usr/bin/env python3

import time
import sys
import asyncio
import logging

from flask import Flask, render_template_string
from turbo_flask import Turbo
from datetime import timedelta
from multiprocessing import Process
from threading import Thread
from random import randint

app = Flask(__name__)
turbo = Turbo(app)

_log = logging.getLogger(__name__)

FRAME = """
<div id="frame_name">
    {% if frame_name %}
        Frame name: {{ frame_name }}
    {% else %}
        No event received yet.
    {% endif %}
</div>
"""

INDEX = """
<!doctype html>
<html>
  <head>
    {{ turbo() }}
  </head>
  <body>
""" + FRAME + """
  </body>
</html>
"""

async def update_frame_name(terminate: asyncio.Event, name_queue: asyncio.Queue):
    while not terminate.is_set():
        _log.debug(f"waiting for name update")
        name_task = asyncio.create_task(name_queue.get())
        await asyncio.wait((name_task, terminate.wait()), return_when=asyncio.FIRST_COMPLETED)
        if name_task.done():
            name = name_task.result()
            _log.debug(f"updating name: {name}")
            with app.app_context():
                turbo.push(turbo.replace(render_template_string(FRAME, frame_name=name), 'frame_name'))


@app.route("/")
def index():
    return render_template_string(INDEX)

# @app.context_processor
# def inject_load():
#     if sys.platform.startswith('linux'):
#         with open('/proc/loadavg', 'rt') as f:
#             load = f.read().split()[0:3]
#     else:
#         load = [int(random.random() * 100) / 100 for _ in range(3)]
#     return {'load1': load[0], 'load5': load[1], 'load15': load[2]}

async def run_image_server(terminate: asyncio.Event, name_queue: asyncio.Queue):
    t = Thread(target=lambda: app.run(debug=False, use_reloader=False), daemon=True)
    tasks = (
        asyncio.create_task(update_frame_name(terminate, name_queue)),
    )

    t.start()

    _log.info(f"Running")

    await asyncio.wait(tasks)

    _log.info(f"Terminating")
