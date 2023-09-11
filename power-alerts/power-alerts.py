#!/usr/bin/env python3

import socket
import re
import typing
import time
import requests
import os

_re_var_value = re.compile(R'VAR ([^ ]+) ([^ ]+) "(.*)"')

class NutNetClient:
    """
    Extremely primitive "upsd" client.  Note that "upsd" has a very low idle timeout,
    so requests will need to be fairly frequent.

    See: https://github.com/networkupstools/nut/blob/master/docs/net-protocol.txt
    """

    def _getline(self) -> str:
        return self.file.readline().rstrip()

    def __init__(self, address):
        self.sock = socket.create_connection(address)
        self.file = self.sock.makefile("rw", encoding="utf-8")

    def list_vars(self, upsname: str) -> typing.Dict[str, str]:
        print("LIST VAR " + upsname, file=self.file, flush=True)

        ret = {}

        # Skip the 'BEGIN LIST VAR apc-1' line.
        line = self._getline()

        while True:
            line = self._getline()
            if m := _re_var_value.match(line):
                # Parse a line like 'VAR apc-1 battery.charge.warning "50"'.
                ret[m.group(2)] = m.group(3)
            else:
                # This should be a 'END LIST VAR apc-1' line.
                break
        
        return ret


# Allow for the user to specify the webhook URL in a script or interactively.
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')
DISCORD_RECIPIENT = os.getenv('DISCORD_RECIPIENT')
assert(isinstance(DISCORD_WEBHOOK, str))
assert(isinstance(DISCORD_RECIPIENT, str))

interesting_fields = [
    "ups.status",
    "ups.load",
    "input.voltage",
    "input.transfer.reason",
    "battery.runtime",
    "battery.voltage"
]

nnc = NutNetClient(("127.0.0.1", 3493))

ups_status : typing.Optional[str] = "Unknown"

while True:
    ups_vars = nnc.list_vars("apc-1")
    new_ups_status = ups_vars.get("ups.status", "")

    if new_ups_status == "OL":
        color = 0x00FF00
    elif new_ups_status == "OB DISCHRG":
        color = 0xFF0000
    else:
        color = 0x0000FF
    
    if ups_status != new_ups_status:
        msg = {
            "content": DISCORD_RECIPIENT + "UPS Status: `" + ups_status + "` :arrow_right: `" + new_ups_status + "`",
            "embeds": [
                {
                    "title": "Status Change: apc-1",
                    "color": color,
                    "fields": [{"name": k, "inline": True, "value": ups_vars.get(k, "")} for k in interesting_fields]
                }
            ]
        }

        r = req = requests.post(DISCORD_WEBHOOK, json=msg)
        
        # Notify.
        pass

    ups_status = new_ups_status
    time.sleep(10)

