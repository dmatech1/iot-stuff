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
            "content": os.getenv("DISCORD_RECIPIENT", "") + "**" + obj["event"] + "** - " + device,
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

# Construct a Discord-style message for status messages.
def get_status_message(lines):
    # TODO: Make sure this isn't longer than 4096 characters.
    # https://discord.com/developers/docs/resources/channel#embed-object-embed-limits
    msg = {
        "content": os.getenv("DISCORD_RECIPIENT", "") + "Starting up!",
        "embeds": [
            {
                "title": "Starting Up...",
                "description": "```\n" + "\n".join(lines) + "\n```",
                "color": 0x0000FF,
                "thumbnail": {
                    "url": "https://m.media-amazon.com/images/I/71Hrs7B6+BL._AC_SX679_.jpg"
                }
            }
        ]
    }
    return msg

# Allow for the user to specify the webhook URL in a script or interactively.
TOKEN = os.getenv('DISCORD_WEBHOOK')

# Buffered-up list of status lines.
status_lines = []

# Iterate through the JSON-formatted events until the program exits.
with subprocess.Popen(["rtl_433", "-F", "json"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8") as proc:
    while line := proc.stdout.readline():
        # Get rid of those annoying newlines.
        line = line.rstrip()

        # Print it.
        print(line, flush=True)
        
        # At the start of the run, rtl_433 outputs some diagnostic stuff to STDERR (which we've
        # redirected to STDOUT for convenience).  Ideally, I'd use some sort of timeout, but I
        # have devices that should send a message every couple minutes, so it shouldn't be necessary.
        if not line.startswith("{"):
            status_lines.append(line)
        else:
            # Send any status lines to Discord.
            try:
                if len(status_lines) > 0:
                    msg = get_status_message(status_lines)

                    if msg is not None:
                        req = requests.post(TOKEN, json=msg)

                    # If this ever happens again, start with an empty list.
                    status_lines = []
            except:
                logging.exception("Failed to send status lines.")

            # Send the event to Discord.
            try:
                # Get an event.
                obj = json.loads(line)

                # Create a Discord message for it (if possible).
                msg = get_message(obj)

                if msg is not None:
                    req = requests.post(TOKEN, json=msg)
            except:
                logging.exception("Failed to process message.")

# I should probably include some notification that the program exited.
