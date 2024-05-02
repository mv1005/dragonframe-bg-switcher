#!/usr/bin/env python3

import time

from flask import Flask, render_template_string
from turbo_flask import Turbo
from datetime import timedelta

app = Flask(__name__)
turbo = Turbo(app)

LOAD = """
<div id="load">
  load1 = {{ load1 }}<br>
  load5 = {{ load5 }}<br>
  load15 = {{ load15 }}<br>
</div>
"""

INDEX = """
<!doctype html>
<html>
  <head>
    {{ turbo() }}
  </head>
  <body>
""" + LOAD + """
  </body>
</html>
"""

def update_load():
    while not is_terminated:
        print("tick")
        with app.app_context():
            turbo.push(turbo.replace(render_template_string(LOAD), 'load'))
        time.sleep(3)

@app.route("/")
def index():
    return render_template_string(INDEX)

@app.context_processor
def inject_load():
    print("injecting load")
    if sys.platform.startswith('linux'):
        with open('/proc/loadavg', 'rt') as f:
            load = f.read().split()[0:3]
    else:
        load = [int(random.random() * 100) / 100 for _ in range(3)]
    return {'load1': load[0], 'load5': load[1], 'load15': load[2]}

def run_image_server():
    run_in_background(update_load)
    app.run(debug=True, use_reloader=False)
