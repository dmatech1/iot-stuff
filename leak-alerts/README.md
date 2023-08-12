# leak-alerts

After I had an issue with a water heater leaking, I bought a bunch of
[Govee H5054 water leak sensors](https://us.govee.com/products/wireless-water-leak-detector) that
transmit on 433MHz and make a loud noise when they get wet.  Rather than get the manufacturer's receiver,
I decided to make my own and use Discord as the notification medium.  For the moment, I'm using the 
[RTL-SDR](https://www.rtl-sdr.com/) hardware, but I might switch over to something that doesn't require
an SDR.

This is a simple script designed to listen to messages with [`rtl_433`](https://github.com/merbanan/rtl_433)
and send ones of interest to a [Discord Webhook](https://discord.com/developers/docs/resources/webhook).
I could have sent an email, but I didn't want to deal with spam filtering, authentication, or remembering
to look at the messages.

# Installation

Installing this script requires a working Python, the `rtl_433` program, and a unit file.

## Installing `rtl_433`

Installing `rtl_433` [isn't too difficult](https://github.com/merbanan/rtl_433/blob/master/docs/BUILDING.md)
on a fresh Raspberry Pi.

### Required Packages
```bash
sudo apt install libssl-dev libtool libusb-1.0-0-dev librtlsdr-dev rtl-sdr build-essential cmake pkg-config
```

### Building From Source

```bash
git clone https://github.com/merbanan/rtl_433
cd rtl_433
mkdir build
cd build
cmake -DCMAKE_INSTALL_PREFIX=$HOME/.local/ ..
make
make install
```

## Adding `systemd` Unit

```bash
mkdir -pv $HOME/.config/systemd/user/
cp sensor-alerts.service $HOME/.config/systemd/user/
systemctl --user enable sensor-alerts
```
