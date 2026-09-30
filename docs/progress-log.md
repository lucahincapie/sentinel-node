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
