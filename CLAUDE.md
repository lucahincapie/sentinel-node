# Sentinel Node: agent guide

Sentinel Node is an educational bench-top telemetry prototype in early development. The plan: Arduino UNO R4 Minima firmware will sample inputs and report to a Python ground station over USB serial, with an ESP8266 Wi-Fi link in a later stage. The goal is engineering quality (clear requirements, reliable communication, bounded resource use, tested fault handling, honest documentation), not feature count.

Current stage and hardware status: see the latest entry in `docs/progress-log.md`.

## Mentor mode

Luca is new to embedded C++, wiring, and hardware debugging, and comes from Python automation.

- Work one small milestone at a time. Before any change, state its purpose and the files it touches.
- Keep each implementation small enough for Luca to read in one sitting. Explain the key lines, then ask Luca to predict a behavior or make a small change.
- Build only the current stage. Later stages live in the plan below until their turn.
- Use parts Luca already owns first. Propose any purchase with its reason and cost, and wait for approval.

## Approval gates

Wait for Luca's explicit yes before each of these:

- Committing, pushing, rewriting Git history, or overwriting existing work.
- Installing anything: tools, board cores, Arduino libraries, Python packages, a new venv.
- Changing system configuration, including PowerShell execution policy.
- Uploading firmware.
- Powering a newly assembled circuit (review a wiring photo first), and connecting the ESP8266.

**Hardware checkpoints**: at each upload, first power-on of a new circuit, first sensor reading, and ESP8266 connection, tell Luca exactly what to do and what to look for, then stop until Luca reports what happened.

## Evidence levels

Every claim in the README, docs, commit messages, and chat matches its evidence level:

- **Planned**: described, not built.
- **Implemented**: code exists in the repo.
- **Tested**: a test or hardware run happened. Record the date, conditions, and actual output in `docs/progress-log.md`.

The agent cannot see the board. Hardware results (uploads, readings, LED behavior) count as tested only when Luca reports them or tool output shows them. Report measurements with their test conditions, and state performance numbers only from a measurement.

At the end of each milestone or session, append a dated entry to `docs/progress-log.md`: verified results (with the command or observation that proves each), unresolved problems, next steps.

## Hardware

| Part | Notes |
|---|---|
| Arduino UNO R4 Minima (ABX00080), original | Luca's board. |
| ESP8266 module + adapter (SunFounder 3-in-1 kit) | Module version (ESP-01 / ESP-01S), firmware, baud rate, and adapter circuit unverified. |
| Stage 1 sensor | 10 kΩ kit trimmer pot on A0, fed from 5V through a 1 kΩ current limiter; reads 0-935. As-built layout: `docs/progress-log.md` (2026-09-30). Keep D0-D3 free for the ESP8266 link. |
| Test equipment | No multimeter. Verify circuits with current limiting, predicted readings, and photos. |

### UNO R4 Minima gotchas

The Minima is a Renesas RA4M1 (Arm Cortex-M4, 48 MHz, single-precision FPU). UNO R3 (AVR) and UNO R4 WiFi material may not apply; check the Minima docs.

- **Pins**: 5 V I/O with **8 mA maximum per GPIO pin** (the R3 allowed 20 mA). Size LED resistors and loads for this. `LED_BUILTIN` is D13, which is also SPI SCK.
- **Power header**, in order: BOOT, IOREF, RESET, 3.3V, 5V, GND, GND, VIN, then A0-A5. A misplaced wire lands on a neighbor: 3.3V sits beside 5V, and VIN sits beside A0. **The USB 5V path has no fuse** (verified from the schematic), so a 5V-to-GND short is limited only by the laptop port. New circuits get a current-limiting resistor on first power-on and a wiring-photo review.
- **Memory**: 256 kB flash, of which 245,760 bytes are usable after the 16 kB bootloader. arduino-cli's size report divides by 262,144, so its percentage is optimistic. 32 kB SRAM; an empty sketch already uses 3,940 bytes. The 8 kB data flash emulates EEPROM with about 100k erase cycles, so write it rarely and outside the main loop.
- **USB Serial**: `Serial` is native USB CDC and ignores the baud argument. `Serial1` is the hardware UART on D0 (RX) / D1 (TX). USB `Serial` discards output until the host asserts DTR (pyserial does by default). Opening the port does not reset the board, so messages sent while no host has DTR asserted are lost (observed at boot and after `arduino-cli monitor` closed). On 2026-09-29 the boot line and ticks 0-5 were missing, and reopening the monitor continued at tick 90. **The loop can also stall, probably in `Serial.print` (inferred):** once, after the agent's receiver (pyserial) run closed the port on 2026-09-30, the 200 ms loop stalled (tick advanced by 2 in 78.6 s) until the next session opened it. After `arduino-cli monitor` closed, the loop kept running. The mechanism is unverified; DTR left asserted after pyserial closes is the leading guess. Stage 3 firmware must not let serial writes block sampling (e.g. check `Serial.availableForWrite()` first; verify it on this core). To keep boot messages, wait for the host with a timeout, e.g. `while (!Serial && millis() - start < 2000) {}`, then continue either way.
- **1200 baud**: a host that sets 1200 baud while DTR is low, including opening at 1200 and then closing, sends the board into the bootloader and the COM port disappears. Host code uses 115200.
- **ADC**: `analogRead()` defaults to 10-bit. `analogReadResolution()` accepts 8, 10, 12, or 14 (16 is rescaled from the 14-bit hardware); any other value silently breaks readings. The default reference is the analog supply. Arduino documents about 4.7 V reaching the MCU on USB power, so measure the reference before converting readings to volts. A sensor powered from the board's 5V pin reads *ratiometrically* (the sensor and the reference share the same 5V net), so raw counts do not depend on the laptop's exact voltage. Core 1.6.0 never clears its ADC scan mask: once a second analog pin has been read (or the float `analogReference()` called), every `analogRead()` converts all of those channels. LED_TX (P012) and LED_RX (P013) are ADC-port pins, which Renesas says cannot be general I/O while the ADC is in use, so check this before choosing Stage 3 status LEDs.
- **AVR leftovers**: `serialEvent()` is unsupported, so poll `Serial.available()` in `loop()`. Direct AVR register code (`PORTB`, `TCCR1A`, `avr/io.h`) does not compile.
- **Upload**: dfu-util sends a DFU detach to the running sketch, which resets through the watchdog into the bootloader (USB 2341:0369, no COM port). The 1200-baud touch is not used. Automatic upload fails if the sketch has crashed, disabled USB, or enabled the watchdog (expect this in Stage 3).
- **Recovery**: double-tap reset (two presses within about 0.5 s). The D13 LED fades in and out and the board appears as a DFU device with no COM port; that is expected. Upload a known-good sketch right away, and the COM port returns when it runs.

Sources: [Minima docs](https://docs.arduino.cc/hardware/uno-r4-minima/), [cheat sheet](https://docs.arduino.cc/tutorials/uno-r4-minima/cheat-sheet/), [ArduinoCore-renesas 1.6.0](https://github.com/arduino/ArduinoCore-renesas/tree/1.6.0), [renesas bootloader](https://github.com/arduino/arduino-renesas-bootloader).

### ESP8266: resolve before Stage 4

The kit wiring feeds 5 V to the adapter (AMS1117 regulator down to 3.3 V), uses SoftwareSerial on D2/D3 at 115200, requires the 9 V battery, and connects the adapter's RX pin directly to a 5 V Arduino pin (D3). The kit docs do not say whether the adapter level-shifts RX. Before connecting, read the module and adapter markings and confirm supply capacity and logic levels. Then check the firmware with `AT` / `AT+GMR` through a small USB-to-ESP passthrough sketch, using the "Both NL & CR" line ending and trying 115200 first. The kit's R3 "RESET to GND" bridge method does not work on the R4, because the R4's USB is native to the MCU.

`Serial1` (D0/D1) is free on the R4 and is likely the better link: SoftwareSerial on the R4 has open issues, and no primary source confirms it at 115200. `Serial1` is still 5 V logic, so the level check still applies.

## Toolchain

- **Arduino CLI 1.5.1**, installed 2026-09-29. Stay on 1.5.1. As of 2026-09-29, Arduino's "latest" download links point to the prerelease 1.5.2-rc.1, and the CLI's update notice will likely offer it; mention it to Luca instead of upgrading.
- **Core `arduino:renesas_uno` 1.6.0**; FQBN `arduino:renesas_uno:minima`.
- **Windows upload driver**: the core installs it through a post-install script that runs only from an interactive terminal (or with `--run-post-install`) and shows a Windows prompt Luca must approve. If the install output contains "Skipping platform configuration" or "WARNING: cannot configure platform", the driver did not install, even though the command reports success. `sketch.yaml` profile builds never run this step. At upload time, dfu-util `LIBUSB_ERROR_NOT_FOUND` also means the driver is missing. `core install` skips an already-installed platform and its post-install step (arduino-cli source). To reinstall the driver, Luca runs `arduino-cli core uninstall arduino:renesas_uno` and then `arduino-cli core install arduino:renesas_uno@1.6.0` in a newly opened interactive terminal (not yet verified here).
- **Sketch layout**: a sketch folder's name equals its `.ino` name: `firmware/sentinel_node/sentinel_node.ino`.
- **Python**: run everything through `.venv\Scripts\python.exe` (e.g. `.venv\Scripts\python.exe ground_station\receiver.py`). This skips `Activate.ps1`, which PowerShell's execution policy may block, and avoids the globally installed pytest. Record dependencies with pinned versions in `requirements.txt`. pyserial 3.5 does not officially declare Python 3.14 support, but port listing and the receiver work here (verified 2026-09-30).
- **COM port**: close the ground station before uploading, because the board re-enumerates as a DFU-only device and an open port raises `SerialException`. Windows also opens COM ports exclusively, so the ground station and `arduino-cli monitor` cannot share the port.
- **Agent sandbox**: the agent's shell runs inside the Claude desktop app package, and its reads and writes of `%LOCALAPPDATA%` go to a private copy at `C:\Users\Luca\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Local`. Observed 2026-09-29: the agent saw only its own build cache, not Luca's. To read Luca's real files, use `\\localhost\C$\Users\Luca\AppData\Local\...`. Cores and libraries installed from the agent shell would probably land in the private copy where Luca's builds cannot see them (inferred), so Luca installs them from a regular terminal.
- **Edits before upload**: `notepad` returns to the prompt immediately. Confirm Luca has saved and closed the editor before uploading.

## Verified commands

Add a command here only after it has run successfully on Luca's machine, with the date.

| Command | Verified | Result |
|---|---|---|
| `winget install -e --id ArduinoSA.CLI --version 1.5.1` | 2026-09-29 | Installer hash verified; installed to `C:\Program Files\Arduino CLI` and added to PATH |
| `arduino-cli version` | 2026-09-29 | 1.5.1 |
| `arduino-cli core update-index` then `arduino-cli core install arduino:renesas_uno@1.6.0` (interactive terminal) | 2026-09-29 | Core 1.6.0 installed; Arduino `renesas.inf` driver present in the driver store |
| `arduino-cli compile --fqbn arduino:renesas_uno:minima <sketch-folder>` | 2026-09-29 | Empty sketch compiled: 38,968 B flash, 3,940 B RAM |
| `arduino-cli board list` | 2026-09-29 | `COM3`, Arduino UNO R4 Minima, `arduino:renesas_uno:minima` |
| `arduino-cli compile --upload --port COM3 --fqbn arduino:renesas_uno:minima firmware\sentinel_node` (from repo root, Luca's terminal) | 2026-09-29 | dfu-util "Done!"; LED behavior changed to match edited code |
| `arduino-cli monitor --port COM3 --config baudrate=115200` (Ctrl+C to exit) | 2026-09-29 | Shows the sketch's `tick N` lines; settings show dtr=on |
| `python -m venv .venv`, then `.venv\Scripts\python.exe -m pip install -r requirements.txt` | 2026-09-30 | venv on Python 3.14.7; a fresh venv installed pyserial 3.5 from the file |
| `.venv\Scripts\python.exe -m serial.tools.list_ports -v` | 2026-09-30 | COM3, `VID:PID=2341:0069` (Luca's terminal) |
| `.venv\Scripts\python.exe ground_station\receiver.py` | 2026-09-30 | Records CSV to `ground_station/output/`; messages verified for no board, busy port, and unplug |

## Milestone plan

Move the *(current)* marker when a stage closes.

0. **Setup**: repo, docs, toolchain.
1. **Hardware + USB** (done 2026-09-30): upload and blink `LED_BUILTIN`, serial hello, one kit sensor (wiring photo reviewed before power), Python receiver that adds host timestamps and writes CSV to a gitignored output folder. Text format is temporary. Missing ports and disconnects give understandable errors.
2. **Binary telemetry** *(current)*: write the protocol doc first (framing, version, message type, payload length, sequence number, byte order, units, max message size, exact CRC parameters). Stream parser that handles partial and concatenated packets and resynchronizes with bounded buffering. Shared example packets. pytest cases for valid, corrupted, partial, concatenated, and invalid-length input. Device timestamps stay separate from host timestamps.
3. **Failure handling**: explicit operating modes and status reporting; decide whether link health and sensor health are separate states. Heartbeats and timeouts. Local status and alert LEDs. Detect only the sensor faults the hardware can evidence (an unchanged reading is not a fault by itself). Bounded RAM buffer with defined capacity, overflow, sequence, and replay behavior; RAM contents are lost on power loss. Non-blocking timing.
4. **Wireless**: identify the ESP8266 exactly, verify power and logic levels first, keep the wired path for debugging, test disconnect and reconnect deliberately. Remote actuation waits until command validation and safe behavior are defined.
5. **Demo + docs**: modest plots, a repeatable fault-test procedure, measured results with conditions (software-only and hardware tests separated), and setup, wiring, architecture, protocol, and limitations docs.

When time is short, a working wired demo takes priority over unfinished wireless features.

## Security scope

USB or a trusted local network only, with no internet exposure. CRC detects accidental corruption, not tampering. Credentials and Wi-Fi passwords live only in gitignored files (`arduino_secrets.h`, `.env`); commit templates with placeholder values (`arduino_secrets.h.example`, `.env.example`).
