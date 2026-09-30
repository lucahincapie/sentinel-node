"""Sentinel Node ground station, Stage 1: USB serial receiver.

Reads lines like "tick 12 a0 517" from the board, adds the laptop's
timestamp, and saves them to a CSV file. The text format is temporary;
Stage 2 replaces it with binary telemetry.

host_time is when this program read the line, not when the board took the
reading. It is later by USB and operating-system delays, and by any time the
line waited. Observed 2026-09-30: after a previous receiver run closed the
port, the sketch stalled (tick advanced by 2 in 78.6 s), so the first row of a new
run can hold a reading taken long before its host_time. Use tick for order;
Stage 2 adds device timestamps.

Run from the repository root:
    .venv\\Scripts\\python.exe ground_station\\receiver.py
    .venv\\Scripts\\python.exe ground_station\\receiver.py --port COM3
"""

import argparse
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

import serial
from serial.tools import list_ports

BOARD_VID = 0x2341  # Arduino
BOARD_PID = 0x0069  # UNO R4 Minima running a sketch (0x0369 is the bootloader)
BAUD = 115200       # the board's native USB ignores this, but never use 1200
LINE_PATTERN = re.compile(r"^tick (\d+) a0 (\d+)$")
OUTPUT_DIR = Path(__file__).parent / "output"


def find_board_port():
    """Return the port name of the first connected UNO R4 Minima, or None."""
    for port in list_ports.comports():
        if port.vid == BOARD_VID and port.pid == BOARD_PID:
            return port.device
    return None


def parse_line(line):
    """Turn "tick 12 a0 517" into (12, 517). Return None for anything else."""
    match = LINE_PATTERN.match(line)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def main():
    parser = argparse.ArgumentParser(description="Record Sentinel Node readings to CSV.")
    parser.add_argument("--port", help="serial port, e.g. COM3 (default: auto-detect)")
    args = parser.parse_args()

    port = args.port or find_board_port()
    if port is None:
        seen = [p.device for p in list_ports.comports()]
        print("No UNO R4 Minima found. Is the USB cable plugged in?")
        print("If it is plugged in but the L LED fades slowly instead of blinking,")
        print("the board is in its bootloader: upload the sketch again.")
        print(f"Serial ports Windows can see: {', '.join(seen) or 'none'}")
        return 1

    try:
        link = serial.Serial(port, BAUD, timeout=1)
    except serial.SerialException as error:
        print(f"Could not open {port}. It may be unplugged, or open in another")
        print("program such as arduino-cli monitor (close it and try again).")
        print(f"Details: {error}")
        return 1

    OUTPUT_DIR.mkdir(exist_ok=True)
    csv_path = OUTPUT_DIR / f"readings_{datetime.now():%Y%m%d_%H%M%S}.csv"
    rows = 0
    skipped = 0
    last_tick = None
    exit_code = 0

    print(f"Recording from {port} to {csv_path}")
    print("Press Ctrl+C to stop.")
    with link, open(csv_path, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["host_time", "tick", "a0"])
        try:
            while True:
                # One line, or whatever arrived before a 1 s gap (may be partial or empty).
                raw = link.readline()
                if not raw:
                    continue  # nothing arrived within the timeout
                host_time = datetime.now().astimezone().isoformat(timespec="milliseconds")
                text = raw.decode("ascii", errors="replace").strip()
                parsed = parse_line(text) if raw.endswith(b"\n") else None
                if parsed is None:
                    skipped += 1  # cut off (no newline) or not in the expected format
                    print(f"Skipped unreadable line: {raw!r}")
                    continue
                tick, a0 = parsed
                if last_tick is not None and tick != last_tick + 1:
                    print(f"Note: tick jumped from {last_tick} to {tick}")
                last_tick = tick
                writer.writerow([host_time, tick, a0])
                csv_file.flush()  # hand each row to the OS so a crash keeps earlier rows
                rows += 1
                print(f"{host_time}  tick {tick}  a0 {a0}")
        except KeyboardInterrupt:
            print("Stopped by user.")
        except serial.SerialException as error:
            print(f"Lost connection to {port}. Was the USB cable unplugged,")
            print("the board reset, or new firmware uploaded?")
            print(f"Details: {error}")
            exit_code = 1

    print(f"Saved {rows} rows to {csv_path} ({skipped} unreadable lines skipped).")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
