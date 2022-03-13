#!/usr/bin/env python3

import os
import sys
import json
import subprocess
import requests
import logging

# These are various sensors I have around the house.  I numbered them for my own convenience.
# Please don't drive by my house and send out spoofed messages to make me think my house is
# flooding.  That would annoy me quite a bit.
DEVICES = {
    16402: "#1: Under the downstairs bathroom toilet",
    29517: "#2: Under the kitchen sink",
    17163: "#3: Next to the kitchen refrigerator",
    30073: "#4: Next to the dishwasher",
    17292: "#5: Under the master bathroom sink",
    16534: "#6: Under the master bathroom toilet",
    16984: "#7: Next to water heater",
    29875: "#8: Under the office bathroom sink",
    29994: "#9: Under the office bathroom toilet",
    30021: "#10: Next to the washing machine"
}

# Construct a Discord-style message given an RTL-433 data packet.
def get_message(obj):
    # Is it a Govee water sensor, and is it one of mine?
    if ("id" in obj and "model" in obj and obj["model"] == "Govee-Water" and obj["id"] in DEVICES):
        device = DEVICES[obj["id"]]
        msg = {
            "content": "<@448074627420258306>: Please read this!",
            "embeds": [
                {
                    "title": obj["event"],
                    "description": device,
                    "color": 0xFFFF00,
                    "fields": [
                        {"name": k, "value": str(v), "inline": True} for k, v in obj.items()
                    ],
                    "thumbnail": {
                        "url": "https://m.media-amazon.com/images/I/514QYrvIu+L._AC_SS450_.jpg"
                    }
                }
            ]
        }
        return msg

    # I don't know what this is.
    return None

# Allow for the user to specify the webhook URL in a script or interactively.
TOKEN = os.getenv('DISCORD_WEBHOOK')

# Iterate through the JSON-formatted events until the program exits.
with subprocess.Popen(["rtl_433", "-F", "json"], stdout=subprocess.PIPE) as proc:
    while line := proc.stdout.readline():
        # Print it.
        sys.stdout.buffer.write(line)
        sys.stdout.flush()

        try:
            # Get an event.
            obj = json.loads(line)

            # Create a Discord message for it (if possible).
            msg = get_message(obj)

            if msg is not None:
                req = requests.post(TOKEN, json=msg)
        except:
            logging.exception("Failed to process message.")
