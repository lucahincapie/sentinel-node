# Progress Log

Dated entries, newest last. **Verified** items were observed on this machine or hardware; the command or observation behind each is named.

## 2026-09-29: Stage 0, inspection and setup

### Verified
- OS: Windows 11 Home, build 10.0.26200 (reported by the environment; confirmed by Luca).
- Repo cloned from GitHub to `Desktop\sentinel-node` at commit `bda682d` (README + MIT LICENSE) (`git log --oneline`).
- Present at start: Git 2.55.0, Python 3.14.7, pip 26.2.1, pytest 9.1.1 (global install) (`git --version`, `python --version`, `pip --version`, `pip list`).
- Absent at start: Arduino IDE, arduino-cli, board cores, PlatformIO, pyserial (`Get-Command`, standard install folders, the Windows installed-programs list, `pip list`).
- No serial ports detected during inspection; the board was not connected (`Get-CimInstance Win32_SerialPort` and `Get-PnpDevice -Class Ports -PresentOnly` returned nothing).
- Git identity set globally: `lucahincapie` with the GitHub no-reply email (`git config --global user.name` / `user.email`).
- Arduino CLI installed with `winget install -e --id ArduinoSA.CLI --version 1.5.1`. winget reported "Successfully verified installer hash". `arduino-cli version` prints `1.5.1 Commit: 01f3d4f2b`.
- Board core installed by Luca from an interactive terminal (`core update-index`, then `core install arduino:renesas_uno@1.6.0`). `arduino-cli core list` shows `arduino:renesas_uno 1.6.0`. Bundled tools present: arm-none-eabi-gcc 7-2017q4, dfu-util 0.11.0-arduino5, bossac 1.9.1-arduino5, openocd 0.11.0-arduino2.
- Upload driver installed: `pnputil /enum-drivers` lists `renesas.inf`, provider Arduino, signed by Arduino SA. A successful upload in Stage 1 is the final proof that it works.
- Compile check (no hardware): an empty sketch builds for `arduino:renesas_uno:minima` (`arduino-cli compile`). It uses 38,968 bytes of flash and 3,940 bytes of global RAM, leaving 28,828 of 32,768 bytes of RAM. The tool reports a 262,144-byte flash maximum, but about 240 KB is usable after the bootloader. This baseline is the core's USB stack and support code before any project code.

### Decisions
- **Toolchain: Arduino CLI 1.5.1 + `arduino:renesas_uno` 1.6.0.** It is Arduino's official tool, each step can be written down as a command, and Arduino IDE 2 runs on the same CLI and shares the same installed cores. PlatformIO supports the Minima too; it was left out to avoid an extra toolchain layer.
- Folders are created when they get real content: `firmware/` and `ground_station/` in Stage 1, `tests/` with the first automated test.

### Unresolved
- No upload to real hardware yet. The board has not been connected.
- A data-capable USB-C cable has not been confirmed.
- ESP8266 module version, firmware, and adapter logic levels unknown (needed before Stage 4).
- pyserial on Python 3.14 not smoke-tested yet.

### Next steps
1. Review the Stage 0 files, then commit on approval.
2. Stage 1: connect the board, confirm it appears in `arduino-cli board list`, upload Blink, then a serial "hello".

## 2026-09-29: Stage 1, board bring-up and first upload

### Verified
- Board detected over USB. `arduino-cli board list` shows `COM3 ... Arduino UNO R4 Minima arduino:renesas_uno:minima`. `Get-PnpDevice` shows USB ID `2341:0069` with three entries: USB Serial Device (COM3), DFU-RT Port (status OK), and USB Composite Device.
- Green power LED ("ON") lit on USB power (observed by Luca).
- The USB-C cable carries data: detection and uploads work over it.
- First upload succeeded: `arduino-cli compile --upload --port COM3 --fqbn arduino:renesas_uno:minima firmware\sentinel_node`. dfu-util sent a DFU detach request, the board re-attached in DFU mode, 39,016 bytes were downloaded, and dfu-util ended with "Done!" and no errors. The bundled dfu-util prints its version as `0.11-arduino4`, although its package is labelled `0.11.0-arduino5`.
- Blink sketch size: 39,008 bytes flash (40 bytes more than the empty sketch) and 3,940 bytes RAM.
- **The uploaded code controls the L LED (cause-and-effect test).** With `delay(100)` / `delay(900)`, Luca saw the yellow L LED flash about once per second. Luca then changed both delays to 1000 ms, predicted 5 flashes in 10 s, re-uploaded, and counted 5. The compiled source in Luca's build cache (compiled 23:35:32, read through `\\localhost\C$\Users\Luca\AppData\Local\arduino\sketches\...`) contains `delay(1000)` twice.

- **USB serial output works, and output sent while no host is listening is lost.** The sketch prints "Sentinel Node booted" in `setup()`, then "tick N" once per second. It compiled to 39,180 B flash and 3,944 B RAM; the extra 4 bytes are the `unsigned long` counter. Luca uploaded it, waited about 5 s, and opened `arduino-cli monitor --port COM3 --config baudrate=115200` (dtr=on). The first line shown was `tick 6`: the boot line and ticks 0-5 never appeared. After closing the monitor at about tick 22 and reopening it later, the first line was `tick 90`.
- **Opening the port does not restart the sketch** (observed): neither session showed the boot line or restarted the count.

### Problems found and resolved
- **Editor/upload race:** `notepad` launched from PowerShell returns immediately, so an upload can compile the file before the edit is saved. Fix: save and close the editor before uploading.
- **Agent sandbox redirection:** the AI assistant's shell runs inside the Claude desktop app package, so its reads and writes of `%LOCALAPPDATA%` go to a private copy (`...\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Local`). Its build-cache checks therefore showed its own earlier compile, and it wrongly concluded the new code had not been uploaded. Reading the real folder through the `\\localhost\C$\...` path showed Luca's compile. Recorded in `CLAUDE.md`.

### Unresolved
- pyserial on Python 3.14 not smoke-tested yet.
- ESP8266 module version, firmware, and adapter logic levels unknown (needed before Stage 4).

### Next steps
1. Commit on approval.
2. Choose the Stage 1 sensor (analog, on A0); review a wiring photo before powering it.

## 2026-09-30: Stage 1, first sensor (potentiometer on A0)

### Circuit as built
Wired with USB unplugged, on the left half of the full-size breadboard (each numbered line's holes a-e are connected):

| Part | Position | Role |
|---|---|---|
| 10 kΩ kit trimmer potentiometer (3 legs in a triangle) | b22, c23, b24 | b22 and b24 are the track ends; c23 is the wiper |
| 1 kΩ resistor (checked by Luca) | e18 to e22 | Current limiter between 5V and the top of the pot |
| Red wire | board 5V to a18 | Supply |
| Signal wire | board A0 to e23 | Wiper voltage |
| Black wire | board GND to e24 | Return |

Why the 1 kΩ resistor: the USB 5V path on the Minima has no fuse (schematic), no multimeter was available, and the wiper leg could not be confirmed from documentation. If a leg were misidentified, the resistor caps a 5V-to-GND fault at about 5 mA. The expected cost is a lower top reading: about 1023 × 10/11 ≈ 930.

The first placement put two legs on the same breadboard line (a23 and c23), which would have joined them. The pot was rotated 90° before any wires were added. The wiring-photo review was skipped at Luca's choice; the circuit was verified by its readings instead (below).

### Verified
- After power-on the board enumerated normally on COM3 (`arduino-cli board list`; `Get-PnpDevice` status OK). Luca reported the power LED on, the L LED blinking, and no warm parts.
- Sketch: `analogRead(A0)` every 200 ms, printed as `tick <n> a0 <value>` (temporary text format). 39,220 B flash, 3,948 B RAM.
- Readings with `arduino-cli monitor` on laptop USB power:
  - At rest the value varies by 1-3 counts (e.g. 448-451, 932-935).
  - Physical end stops read **0** and **934-935** (predicted about 930, range 900-945).
  - The knob at roughly mid-travel read about 430-450 (a linear divider predicts about 465).
- Derived from the top reading (a calculation, not a measurement): 934/1024 = R/(R + 1 kΩ) gives R ≈ 10.4 kΩ, within a few percent of the 10 kΩ rating.
- The single leg (c23) is the wiper. If a paired leg were the wiper, mid-travel would read about 850 instead of about 450. Mid-travel was judged by eye, so this is strong but not exact evidence.
- An earlier sweep (188-835) did not reach the end stops; the full sweep did.

### Unresolved
- pyserial on Python 3.14 not smoke-tested yet.
- ESP8266 module version, firmware, and adapter logic levels unknown (needed before Stage 4).

### Next steps
1. Commit on approval.
2. Python ground station: create `.venv`, install pyserial (approval needed), smoke-test port listing, then write a receiver that adds host timestamps and saves CSV.

## 2026-09-30: Stage 1, Python receiver

### Verified
- `.venv` created with Python 3.14.7 (`python -m venv .venv`). `pyserial==3.5` installed from PyPI and pinned in `requirements.txt`. `.venv/` is gitignored (`git check-ignore`).
- pyserial works on Python 3.14 here: in Luca's terminal, `.venv\Scripts\python.exe -m serial.tools.list_ports -v` lists `COM3`, `USB VID:PID=2341:0069`.
- `ground_station/receiver.py`: auto-detects the board by USB ID, reads lines, adds host timestamps, and writes `ground_station/output/readings_<date>_<time>.csv` (gitignored). An ad-hoc offline check of `parse_line` (not saved in the repo), run before the review fixes, passed 7 cases: two valid lines, a missing value, a wrong prefix, a non-digit value, an empty line, and the boot message. The trailing-newline rejection added in review is in `main()` and is not unit-tested.
- Agent run on hardware (5 s, simulated Ctrl+C, receiver before the review fixes): 24 rows at 200 ms spacing, clean stop, summary printed, exit code 0. The CSV reads back with `Import-Csv` (columns host_time, tick, a0).
- Luca's run (12.6 s, knob turned, receiver before the review fixes): 64 rows, ticks 814-877 with no gaps, 5.0 rows/s, a0 from 3 to 604. The Ctrl+C output as pasted ends at "Stopped by user."; the summary line was not in the paste. It did print in the agent's Ctrl+C run and in failure test C (below).

### Observed problem: the sketch can stall when a host stops reading
The agent's 5 s run ended at tick 812 (00:58:02.221). Luca's run started 78.6 s later at tick **814**; a free-running 200 ms loop would have advanced about 393. The loop stopped advancing while no program was reading, most likely blocked in `Serial.print` (inferred from the code; the L LED was not checked during the stall). This was observed once, after the agent's receiver run. After `arduino-cli monitor` sessions closed on 2026-09-29, the loop kept running (tick 22, then 90 on reopen). The difference probably lies in how each host program leaves the port on close; the mechanism is not verified. Consequences:
- The project requirement that local monitoring continues during communication loss is **not** met by the current firmware. This belongs to Stage 3: serial writes must not block sampling.
- The first CSV row of a run can hold a reading taken long before its host_time. The receiver docstring now says so. Stage 2 is planned to add device timestamps, which would show when each reading was actually taken.

### Review fixes applied to the receiver
An agent review (two reviewers) led to these changes: reject lines without a trailing newline (a partial line whose digits were cut off could otherwise be saved as a wrong value); print each skipped line; accurate `readline()` and `host_time` comments; a broader disconnection hint (unplug, reset, or upload); a bootloader hint when no board is found. Not changed: `host_time` stays ISO 8601 with a UTC offset. Python parses it, but Excel treats it as text.

### Failure tests (Luca's terminal, updated receiver)
- **A, no board** (USB unplugged): printed "No UNO R4 Minima found. Is the USB cable plugged in?", the bootloader hint, and "Serial ports Windows can see: none". No traceback.
- **B, port busy** (`arduino-cli monitor` holding COM3, receiver started in a second window): printed "Could not open COM3. ... open in another program such as arduino-cli monitor ...", with "Details: could not open port 'COM3': PermissionError(13, 'Access is denied.', None, 5)".
- **C, USB unplugged mid-recording**: after 24 rows it printed "Lost connection to COM3. Was the USB cable unplugged, the board reset, or new firmware uploaded?", with "Details: ClearCommError failed (PermissionError(13, 'The device does not recognize the command.', None, 22))", then "Saved 24 rows ... (0 unreadable lines skipped)". The summary line prints on this path.
- Side observations: after test A's replug, the monitor's first line was tick 47 (the board restarted on power-up). Between the monitor session (ended at tick 280) and the next receiver run (started at tick 340), the counter advanced 60 ticks. The gap's duration was not recorded, so this only shows the loop did not stall the way it did after the pyserial session.
- `.venv\Scripts\python.exe -m pip install -r requirements.txt` runs cleanly ("Requirement already satisfied: pyserial==3.5"). A fresh venv created from Python 3.14.7 in a scratch folder installed `pyserial 3.5` from the file with no errors.

### Stage 1 acceptance status
- Reproducible upload and run process: documented in the README; each command there has run on this machine.
- Python receives changing readings from real hardware: yes (one knob-turn run recorded, a0 3-604).
- CSV output usable: yes (reads back with `Import-Csv`). Excel is expected to show host_time as text (not checked).
- Missing port and disconnection give understandable errors: yes (tests A-C).
- Luca can explain the data flow and code: yes, after one round of correction. On the first try, the data-flow answer had the right outline but skipped the ADC and parsing steps, and the USB-ID check was explained correctly. The ~935 ceiling and the stale first reading were first attributed to "knob direction" and "code errors". Luca then explained both correctly: the 1 kΩ limiter leaves 10/11 of the supply at the top of the pot, and the board froze in `Serial.print` while no program was reading.

### Unresolved
- The loop stall after a pyserial session closes the port: observed once, mechanism unverified. It blocks the requirement that local monitoring continues during communication loss (Stage 3).
- The receiver's `--port` option and a Ctrl+C stop of the final receiver version have not been run on hardware.
- ESP8266 module version, firmware, and adapter logic levels unknown (needed before Stage 4).
- Resolved: pyserial 3.5 on Python 3.14 (see Verified).

### Next steps
1. Commit Stage 1 (after the doc review).
2. Stage 2: write the binary telemetry protocol document before any code.
