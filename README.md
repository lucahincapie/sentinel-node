# Sentinel Node

A bench-top telemetry and monitoring prototype in early development. The plan: an Arduino UNO R4 Minima will sample sensor data and report to a Python ground station, first over USB serial and later over an ESP8266 Wi-Fi link. The engineering goal is to detect, handle, and test communication and sensor faults, and to document the results honestly.

Educational prototype: not safety-critical, not certified, and not hardened for production security.

## Roadmap and status

Status levels: **Planned** (described, not built), **Implemented** (code in this repo), **Tested** (test or hardware run recorded with its conditions in [`docs/progress-log.md`](docs/progress-log.md)).

| Stage | Scope | Status |
|---|---|---|
| 0. Setup | Repository, docs, toolchain | Done |
| 1. Hardware + USB | Upload and blink, serial output, one kit sensor, Python receiver writing timestamped CSV | Done: end stops read 0 and 934-935 in the serial monitor; knob readings (a0 3-604) recorded to CSV with laptop timestamps; error messages tested for no board, busy port, and unplugged cable |
| 2. Binary telemetry | Documented, versioned packet format with sequence numbers and CRC corruption detection; stream parser with automated tests | Planned |
| 3. Failure handling | Operating modes and status reporting, heartbeats and link timeouts, supported sensor-fault detection, status and alert LEDs, bounded buffer for short disconnections | Planned |
| 4. Wireless | ESP8266 link, added only after the wired system works | Planned |
| 5. Demo + docs | Ground-station plots, repeatable fault-injection tests, measured results, wiring and architecture docs | Planned |

Firmware so far reads a potentiometer on A0 every 200 ms and prints the value with a line counter over USB serial (temporary text format). A Python receiver records those lines to CSV.

## Hardware

| Part | Notes |
|---|---|
| Arduino UNO R4 Minima | Renesas RA4M1, 5 V logic. From a SunFounder 3-in-1 Super Starter Kit. Connected over USB-C; uploads verified. |
| ESP8266 Wi-Fi module + adapter | From the same kit. Exact module and firmware not yet verified. |
| 10 kΩ potentiometer + 1 kΩ resistor | First sensor input on A0. The resistor limits current if the circuit is miswired. |
| Windows 11 laptop | Runs the build tools and the ground station. |

**Wiring** (make changes with USB unplugged): board 5V → 1 kΩ resistor → one end of the pot's track; pot wiper → A0; other end of the track → GND. Breadboard positions are in [`docs/progress-log.md`](docs/progress-log.md) (2026-09-30, "Circuit as built"). On the power header, 3.3V sits beside 5V and VIN sits beside A0, and the board's USB 5V path has no fuse, so check each wire before plugging in USB.

## Toolchain

| Tool | Version | Purpose |
|---|---|---|
| [Arduino CLI](https://arduino.github.io/arduino-cli/) | 1.5.1 | Compile and upload firmware |
| Arduino UNO R4 Boards core (`arduino:renesas_uno`) | 1.6.0 | Board support (FQBN `arduino:renesas_uno:minima`) |
| Python | 3.14 | Ground station |

## Build and upload (Windows)

Verified 2026-09-29.

One-time setup. Install Arduino CLI 1.5.1 by version: Arduino's "latest" links pointed to a prerelease when this was written.

```
winget install -e --id ArduinoSA.CLI --version 1.5.1
```

Open a **new** terminal so `arduino-cli` is on PATH, and check that `arduino-cli version` prints 1.5.1. Then, in that regular (non-admin) terminal, run these two commands and approve the Windows driver prompt:

```
arduino-cli core update-index
arduino-cli core install arduino:renesas_uno@1.6.0
```

If no driver prompt appears, or the output contains "Skipping platform configuration" or "WARNING: cannot configure platform", the upload driver did not install.

With the board on USB, from the repository root:

```
arduino-cli board list
arduino-cli compile --upload --port COM3 --fqbn arduino:renesas_uno:minima firmware\sentinel_node
```

Use the port that `board list` reports; `COM3` is what it showed on the development laptop. Save and close your editor before uploading.

## Record readings (ground station)

Verified 2026-09-30. Requires Python 3.14 on PATH as `python` (tested with 3.14.7; check with `python --version`). One-time setup, from the repository root:

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Record, with the board on USB and no other program using its port:

```
.venv\Scripts\python.exe ground_station\receiver.py
```

Press Ctrl+C to stop. Each run writes `ground_station\output\readings_<date>_<time>.csv` with these columns:
- `host_time`: laptop time when the line was read (ISO 8601 with UTC offset)
- `tick`: the board's line counter
- `a0`: the raw 10-bit reading, 0-1023

Known limitations at this stage:
- The text format is temporary.
- `host_time` is when the laptop read the line, not when the board measured it.
- After the receiver closed the port, the current firmware stalled until a program opened the port again (observed once on 2026-09-30; cause unverified), so a run's first row can hold an old reading. Removing the stall is planned for Stage 3, and Stage 2 device timestamps are planned to make old readings visible.

## Repository layout

```
firmware/         Arduino sketch (reads A0, prints over USB serial)
ground_station/   Python receiver that records readings to CSV
tests/            Automated tests           (planned)
docs/             Progress log; later protocol, wiring, and test procedures
CLAUDE.md         Working rules for the AI assistant used on this project
```

Folders are added when they have real content.

## Scope and security

- Communication is planned for USB or a trusted local network only. The device is not meant to be reachable from the internet.
- The planned CRC will detect accidental corruption. It will not authenticate or encrypt data.

## How this project is built

Development is incremental, one verified stage at a time. I use an AI assistant (Claude Code) as a mentor and pair programmer; its working rules are in [`CLAUDE.md`](CLAUDE.md).

## License

MIT. See [LICENSE](LICENSE).
