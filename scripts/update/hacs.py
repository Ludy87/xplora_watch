"""Update the hacs file."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HACS_FILE = Path(f"{os.getcwd()}/hacs.json")


def update_hacs():
    """Update the hacs file."""
    hacs = "0.0.0"
    hassversion = "0.0.0"
    for index, value in enumerate(sys.argv):
        if value in ["--version", "-V"]:
            hacs = sys.argv[index + 1]
        if value in ["--hversion", "-hV"]:
            hassversion = sys.argv[index + 1]

    with open(HACS_FILE, encoding="utf-8") as hacsfile:
        base: dict = json.load(hacsfile)
        base["homeassistant"] = hassversion
        base["hacs"] = hacs

    with open(HACS_FILE, "w", encoding="utf-8") as hacsfile:
        hacsfile.write(json.dumps({**base}, indent=4))


update_hacs()
