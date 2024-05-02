#!/usr/bin/env python3

import typer

from dragonframe_bg_switcher.server import run as run_server


def main(port: int=8888):
    run_server(port)

def entrypoint():
    typer.run(main)
