#!/usr/bin/env python3

import socket
import re
import typing
import time
import requests
import os
import netutils

_re_var_value = re.compile(R'VAR ([^ ]+) ([^ ]+) "(.*)"')

# See: https://github.com/networkupstools/nut/blob/master/docs/new-drivers.txt#L223-L238
_status_desc = {
    "OL":       "Online",
    "OB":       "On Battery",
    "LB":       "Low Battery",
    "HB":       "High Battery",
    "RB":       "Replace Battery",
    "CHRG":     "Charging",
    "DISCHRG":  "Discharging",
    "BYPASS":   "Bypassed",
    "CAL":      "Calibrating",
    "OFF":      "Offline",
    "OVER":     "Overloaded",
    "TRIM":     "Trimming",
    "BOOST":    "Boosting",
    "FSD":      "Forced Shutdown"
}

def describe_ups_status(ups_status: typing.Optional[str]) -> str:
    if isinstance(ups_status, str):
        return ", ".join(_status_desc.get(x, x) for x in ups_status.split())
    else:
        return "Unknown"

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
ups_name = "apc-1"
ups_status : typing.Optional[str] = "Unknown"

rs = requests.Session()
rs.mount("https://", netutils.AlternateInterfaceAdapter("usb0"))

while True:
    ups_vars = nnc.list_vars(ups_name)
    new_ups_status = ups_vars.get("ups.status", "")

    # Set the embed color based on the status.
    if new_ups_status == "OL":
        color = 0x00FF00
    elif new_ups_status == "OB DISCHRG":
        color = 0xFF0000
    else:
        color = 0x0000FF
    
    if ups_status != new_ups_status:
        msg = {
            "content": ups_name + ": " + describe_ups_status(new_ups_status) + " \u2B05\uFE0F " + describe_ups_status(ups_status) + " - " + DISCORD_RECIPIENT,
            "embeds": [
                {
                    "title": "Status Change: " + ups_name,
                    "color": color,
                    "fields": [{"name": k, "inline": True, "value": ups_vars.get(k, "")} for k in interesting_fields],
                    "thumbnail": {
                        # Taken from https://download.schneider-electric.com/files?p_Doc_Ref=SPD_MMAE-7UCQFM_FL_V&p_File_Type=rendition_369_jpg&default_image=DefaultProductImage.png
                        "url": "https://cdn.discordapp.com/attachments/768106411765923878/1155262743931265084/SPD_MMAE-7UCQFM_FL_V_web.JPG"
                    }
                }
            ]
        }

        r = req = rs.post(DISCORD_WEBHOOK, json=msg)
        
        # Notify.
        pass

    ups_status = new_ups_status
    time.sleep(10)

