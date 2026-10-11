# COIN-D6 direct UART connection to Raspberry Pi

The COIN-D6 can connect directly to the Pi's GPIO UART without a USB serial adapter or logic-level converter: its UART uses **3.3 V LVTTL**. The sensor itself needs **5 V power**. Settings are **230400 baud, 8 data bits, no parity, 1 stop bit (8N1)**, without hardware flow control. See the [A1 specification, pages 11 and 13](1%20D6%20LiDAR%20Manual/COIN-D6%20Single-Line%20LiDAR%20Specification%20Sheet%20A1.md).

## Wiring for Pi 4 B

Disconnect power before wiring. Pin numbers below are physical positions on the 40-pin header, not GPIO numbers. Confirm wire colours and connector orientation on the actual sensor against the [instruction manual, page 8](COIN-D6%20Instruction%20Manual.md).

| LiDAR wire / signal | Connection |
| --- | --- |
| Red / TXD | Pi GPIO15 / RXD, physical pin **10** |
| Black / RXD | Pi GPIO14 / TXD, physical pin **8** |
| White / GND | Pi ground, physical pin **6**, and LiDAR supply ground |
| Yellow / 5 V | Regulated **5 V supply** |

TX connects to the other device's RX. Connect grounds together. Never apply 5 V to GPIO14/GPIO15 or power the LiDAR from the Pi's 3.3 V pin.

The A1 sheet specifies 800 mA peak LiDAR current. Budget startup current alongside the Pi, USB webcam, and other devices. A suitably rated regulated 5 V supply is recommended. Using the Pi's 5 V header pins requires enough supply and wiring capacity for the combined load. With a separate LiDAR supply, share ground but do not tie independently regulated 5 V outputs together.

## Enable serial on Raspberry Pi OS

Run on the Pi:

```sh
sudo raspi-config
```

Choose **Interface Options → Serial Port**: disable the serial login shell and enable serial hardware. Reboot. Ubuntu installations need equivalent boot/UART and console configuration; these menu instructions apply to Raspberry Pi OS.

For sustained 230400-baud scanning on Pi 4, prefer PL011. The default mini UART has smaller buffers and clock-related limitations. Verify the active port rather than assuming `/dev/serial0` is PL011. [Raspberry Pi UART documentation](https://www.raspberrypi.com/documentation/computers/configuration.html#configure-uarts)

### Pi 4 option: assign UART0 to GPIO14/15

If onboard Bluetooth is not needed, add these settings under the applicable Pi 4 or `[all]` section in `/boot/firmware/config.txt` (older OS images use `/boot/config.txt`):

```ini
enable_uart=1
dtoverlay=disable-bt
```

This disables onboard Bluetooth and restores UART0/PL011 on GPIO14/15. Disable its Bluetooth UART service if installed:

```sh
sudo systemctl disable --now hciuart
sudo reboot
```

After reboot, verify `/dev/serial0` points to `/dev/ttyAMA0`:

```sh
readlink -f /dev/serial0
ls -l /dev/ttyAMA0
```

Configure the LiDAR driver for that verified port at **230400/8N1**. Only one process may open it. The overlay behavior is documented in the [official firmware overlay reference](https://github.com/raspberrypi/firmware/blob/master/boot/overlays/README).

## Pi 5 differences

The voltage compatibility still applies, but configure its GPIO-header UART separately. `/dev/serial0` can refer to the dedicated debug UART, rather than GPIO14/15. The Pi 4 Bluetooth overlay recipe above does not establish GPIO UART routing on Pi 5; verify the model-specific overlay, pin assignment, and device node before connecting the driver. [Pi UART device names](https://www.raspberrypi.com/documentation/computers/configuration.html#linux-device-names)

## Bring-up and robot integration

1. Keep the robot stationary, with driving and brushes disabled.
2. Confirm stable sensor power, common ground, crossed TX/RX, and serial-console disablement.
3. Open the verified UART and send binary Start bytes: `AA 55 F0 0F`.
4. Allow rotation to stabilize; capture and validate packets, checksums, distances, and scan orientation.
5. Send binary Stop bytes on exit: `AA 55 F5 0A`.

These are byte sequences, not ASCII command strings. See the [protocol specification](1%20D6%20LiDAR%20Manual/COIN-D6%20LiDAR%20Data%20Format%20Standard%20Specification%20V1.0%28EN%29.md) for acknowledgments and packet decoding.

The LiDAR and Roomba need separate serial interfaces. Do not connect both devices to the same TX/RX pair. A practical arrangement is LiDAR on the Pi UART, Roomba on its own compatible USB serial adapter, and webcam on USB. Roomba electrical compatibility must be checked independently.

Continue with [the unified sensor fusion checklist](../../todo.md) after stationary scan validation. UART support is documented here; operation on the project's actual wiring has not yet been tested.
