# Power Outage Alerts and Monitoring

The goal of this project is to monitor the quality and reliability of my electricity,
give devices a chance to shut down cleanly, and notify me when there's an event of
some sort.

## Network UPS Tools

### `nut` Installation

Installing [`nut`](https://networkupstools.org/) is actually pretty easy.  Just do the following as `root`.

```bash
# Install "nut" itself.
apt install nut

# Scan for the UPS and add it to the config file.
nut-scanner | tee -a /etc/nut/ups.conf

# Edit the configuration file.  I renamed the UPS to "apc-1".
vim /etc/nut/ups.conf

# Disable "upsmon" -- we don't need it, as our scripts can do the job.
systemctl disable nut-monitor.service
systemctl stop nut-monitor.service

# But enable the information server and device driver.
systemctl enable nut-server.service nut-driver.service
systemctl start nut-server.service nut-driver.service
```

### Architecture

NUT's architecture is a bit complex.  As the name implies, it's intended to be networked.  It generally has three components.

* A **driver** that interacts directly with the UPS hardware.  In my case, I'm using the [USB HID](https://github.com/networkupstools/nut/blob/master/drivers/usbhid-ups.c) driver, but it might not support everything.
* A **server** that talks to one or more *local* drivers using the [driver/server socket protocol](https://github.com/networkupstools/nut/blob/master/docs/sock-protocol.txt).
* A **client** that talks to one or more *remote* servers using the [network protocol](https://github.com/networkupstools/nut/blob/master/docs/net-protocol.txt).

Sources:
* [Universal Serial Bus Usage Tables for HID Power Devices Release 1.1 (May 29, 2020)](https://www.usb.org/sites/default/files/pdcv11.pdf)
* [HID Usage Tables for Universal Serial Bus (USB) (Version 1.4)](https://usb.org/sites/default/files/hut1_4.pdf)

