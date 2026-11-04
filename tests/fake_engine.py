#!/usr/bin/env python3
"""A stand-in ``docker``, ``podman`` and ``adb`` for the container and device
drives' tests (``tests/test_container_drives.py``): which one by the name it
is run as.

The "container" and the "device" are this machine: a command run in one runs
here, so a test's paths are its ``tmp_path``'s.  What exists, and whether it
is running or attached, is read from ``$FAKE_ENGINE_STATE``:
``containers.json`` (``[{"name", "image", "running", "workdir"}]``) and
``devices.json`` (``[{"serial", "state", "model"}]``).  Each call is appended
to ``calls.log`` there, one JSON list a line.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

STATE = Path(os.environ.get("FAKE_ENGINE_STATE", "."))


def _load(name: str) -> list[dict]:
    try:
        return json.loads((STATE / name).read_text())
    except (OSError, ValueError):
        return []


def _fail(text: str, status: int = 1) -> None:
    sys.stderr.write(text + "\n")
    sys.exit(status)


def _log(argv: list[str]) -> None:
    try:
        with open(STATE / "calls.log", "a") as log:
            log.write(json.dumps(argv) + "\n")
    except OSError:
        pass


def engine(name: str, args: list[str]) -> None:
    containers = {each["name"]: each for each in _load("containers.json")}
    if not args:
        _fail("usage")
    command, rest = args[0], args[1:]
    if command == "version":
        print("27.1.1")
        return
    if command == "ps":
        for each in containers.values():
            if not each.get("running", True):
                continue
            if name == "podman":
                record = {"Names": [each["name"]], "Image": each.get("image", ""), "State": "running",
                          "Id": "f" * 64}
            else:
                record = {"Names": each["name"], "Image": each.get("image", ""), "Status": "Up 2 hours",
                          "ID": "abc123def456"}
            print(json.dumps(record))
        return
    if command == "inspect":
        target = rest[-1]
        each = containers.get(target)
        if each is None:
            _fail(f"Error: No such container: {target}")
        print(json.dumps([{"State": {"Running": each.get("running", True)},
                           "Config": {"Image": each.get("image", ""), "WorkingDir": each.get("workdir", "")}}]))
        return
    if command == "exec":
        while rest and rest[0].startswith("-"):
            flag = rest.pop(0)
            if flag in ("-u", "-w", "-e"):
                rest.pop(0)
        target, words = rest[0], rest[1:]
        each = containers.get(target)
        if each is None:
            _fail(f"Error response from daemon: No such container: {target}", 125)
        if not each.get("running", True):
            _fail(f"Error response from daemon: container {target} is not running", 125)
        os.execvp(words[0], words)
    _fail(f"unknown command {command}")


def adb(args: list[str]) -> None:
    devices = {each["serial"]: each for each in _load("devices.json")}
    serial = ""
    if args[:1] == ["-s"]:
        serial, args = args[1], args[2:]
    command, rest = args[0], args[1:]
    if command == "devices":
        print("List of devices attached")
        for each in devices.values():
            model = each.get("model", "")
            print(f"{each['serial']}\t{each.get('state', 'device')} usb:1-1 product:x model:{model} transport_id:1")
        return
    if not serial:
        if len(devices) != 1:
            _fail("adb: more than one device/emulator" if devices else "adb: no devices/emulators found")
        serial = next(iter(devices))
    each = devices.get(serial)
    if each is None:
        _fail(f"adb: device '{serial}' not found")
    state = each.get("state", "device")
    if command == "get-state":
        if state != "device":
            _fail(f"error: device {state}")
        print("device")
        return
    if command == "shell":
        if state != "device":
            _fail(f"error: device {state}")
        if rest and rest[0] in ("-T", "-t"):
            rest = rest[1:]
        line = " ".join(rest)
        line = line.replace("getprop ro.product.model", f"echo {each.get('model', 'Phone')}")
        line = line.replace("getprop ro.build.version.release", "echo 14")
        os.execvp("sh", ["sh", "-c", line])
    _fail(f"unknown command {command}")


def main() -> None:
    name = os.environ.pop("FAKE_ENGINE_NAME", "") or Path(sys.argv[0]).name
    _log([name, *sys.argv[1:]])
    if name == "adb":
        adb(sys.argv[1:])
    else:
        engine(name, sys.argv[1:])


if __name__ == "__main__":
    main()
