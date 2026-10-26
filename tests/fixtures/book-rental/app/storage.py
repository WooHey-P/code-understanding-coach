"""JSON-file persistence. The whole database is one JSON document."""

import json
import os

from app import config

EMPTY = {"members": {}, "books": {}, "rentals": []}


def load():
    if not os.path.exists(config.DATA_PATH):
        return json.loads(json.dumps(EMPTY))
    with open(config.DATA_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def save(db):
    os.makedirs(os.path.dirname(config.DATA_PATH) or ".", exist_ok=True)
    with open(config.DATA_PATH, "w", encoding="utf-8") as handle:
        json.dump(db, handle, indent=2)
