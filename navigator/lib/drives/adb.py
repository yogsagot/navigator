"""An Android device as a drive, over the Android Debug Bridge: ``adb://serial/path``.

Every step is ``adb shell -T`` (:class:`~navigator.lib.drives.execdrive.ExecDrive`):
shell protocol v2 without a terminal, which keeps standard output and error
apart, passes bytes untouched, carries the exit status back and reads
standard input -- one mechanism for a listing, a ``cat`` that reads and a
``cat >`` that writes.  Android's toybox has the ``stat -c`` and ``df -P``
the listing uses.  A device before Android 7 has no shell protocol v2: its
writes would never end, and it is not supported.

**adb joins its arguments into one command line for the device's shell**,
so the words are quoted here (``shlex.join``), unlike ``docker exec``'s.

The site's host is the serial, kept as written (``R58M123ABC``); a device
reached over the network (``adb connect``) has ``host:port`` for a serial,
which a URL writes as host and port and :attr:`AdbDrive.serial` puts back
together.  No host means the one device attached (no ``-s``).  The
device's user is the shell's; ``/sdcard`` is home.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from navigator.lib.drives.base import CHMOD, FREE_SPACE, RENAME, WRITE, DriveGone
from navigator.lib.drives.execdrive import ExecDrive
from navigator.lib.drives.location import Site
from navigator.lib.drives.sessions import Answers
from navigator.lib.system.which import which as _which

#: Where a device's files are, for the user.
HOME = PurePosixPath("/sdcard")

#: Words in adb's own failure that say the device cannot be reached.
LOST_WORDS = ("no devices/emulators found", "device offline", "device unauthorized",
              "more than one device/emulator", "device still authorizing", "cannot connect to daemon")


def sdk_dirs() -> list[Path]:
    """The ``platform-tools`` directories an Android SDK keeps ``adb`` in, when
    it is not on ``PATH``: ``$ANDROID_HOME``'s, ``$ANDROID_SDK_ROOT``'s, then
    where Android Studio installs the SDK (``~/Android/Sdk`` on Linux,
    ``~/Library/Android/sdk`` on macOS) -- Studio does not add it to ``PATH``."""
    roots = [os.environ.get(name, "") for name in ("ANDROID_HOME", "ANDROID_SDK_ROOT")]
    home = Path.home()
    places = [Path(root) for root in roots if root] + [home / "Android" / "Sdk", home / "Library" / "Android" / "sdk"]
    return [place / "platform-tools" for place in places]


#: :func:`sdk_dirs` itself, which the tests stand in for.
SDK_DIRS = sdk_dirs


def program() -> str | None:
    """Where ``adb`` is -- on ``PATH``, else in an Android SDK -- or None."""
    found = _which("adb")
    if found:
        return found
    for place in sdk_dirs():
        found = _which("adb", path=str(place))
        if found:
            return found
    return None


def command() -> str:
    """The word that runs ``adb``: plain ``adb`` when ``PATH`` has it, the
    SDK's full path when only an SDK does."""
    return "adb" if _which("adb") else (program() or "adb")


def available() -> str | None:
    if program() is None:
        return "Android devices need the adb command (Android platform tools)"
    return None


def serial_of(site: Site) -> str:
    """The serial ``-s`` names: the host, with the port of a networked device."""
    if not site.host:
        return ""
    host = f"[{site.host}]" if ":" in site.host else site.host
    return f"{host}:{site.port}" if site.port else site.host


def lost(text: str) -> str | None:
    """Why the device cannot be reached, from adb's own *text*; None for a
    command that failed on the device."""
    lower = text.lower()
    if any(words in lower for words in LOST_WORDS) or ("device '" in lower and "not found" in lower):
        if "unauthorized" in lower:
            return "Allow USB debugging on the device, then try again"
        return " ".join(text.split())
    return None


def _argv(serial: str, *words: str) -> list[str]:
    return [command(), *(["-s", serial] if serial else []), *words]


class AdbDrive(ExecDrive):
    """A device's files, through ``adb shell -T``."""

    capabilities = frozenset((WRITE, RENAME, CHMOD, FREE_SPACE))

    def __init__(self, site: Site, *, model: str = "", release: str = "") -> None:
        super().__init__(site)
        self.serial = serial_of(site)
        self.model = model
        self.release = release
        self.home = HOME

    @property
    def name(self) -> str:
        return self.serial or self.model or "adb"

    def argv(self, words: list[str], *, stdin: bool = False) -> list[str]:
        return _argv(self.serial, "shell", "-T", shlex.join(words))

    def lost(self, text: str, status: int) -> str | None:
        return lost(text)

    def describe(self) -> list[tuple[str, str]]:
        facts = []
        if self.model:
            facts.append(("Device", f"{self.model} ({self.serial})" if self.serial else self.model))
        elif self.serial:
            facts.append(("Device", self.serial))
        if self.release:
            facts.append(("Android", self.release))
        return facts


def connect(site: Site, answers: Answers) -> AdbDrive:
    """*site*'s device, attached and allowing debugging: blocks."""
    serial = serial_of(site)
    name = serial or "adb"
    try:
        done = subprocess.run(_argv(serial, "get-state"), capture_output=True, stdin=subprocess.DEVNULL,
                              timeout=30)
    except FileNotFoundError as error:
        raise DriveGone(name, "adb: command not found") from error
    except subprocess.TimeoutExpired as error:
        raise DriveGone(name, "adb did not answer") from error
    text = done.stderr.decode("utf-8", "replace") + done.stdout.decode("utf-8", "replace")
    if done.returncode != 0 or done.stdout.decode("utf-8", "replace").strip() != "device":
        raise DriveGone(name, lost(text) or " ".join(text.split()) or f"Device {name} is not attached")
    drive = AdbDrive(site)
    try:
        out = drive._run(["sh", "-c", "getprop ro.product.model; getprop ro.build.version.release"], timeout=30)
        lines = out.decode("utf-8", "replace").splitlines()
        drive.model = lines[0].strip() if lines else ""
        drive.release = lines[1].strip() if len(lines) > 1 else ""
    except DriveGone:
        raise
    except OSError:
        pass
    return drive


@dataclass(frozen=True)
class Device:
    """One device ``adb devices -l`` lists: its serial, its state
    (``device``, ``unauthorized``, ``offline``) and its model."""

    serial: str
    state: str = "device"
    model: str = ""

    def site(self) -> Site:
        """The site a URL names it by: a networked ``host:port`` split."""
        host, colon, port = self.serial.rpartition(":")
        if colon and port.isdigit() and host:
            return Site("adb", "", host.strip("[]"), int(port))
        return Site("adb", "", self.serial)


def parse_devices(text: str) -> list[Device]:
    """``adb devices -l``'s lines, less its heading and the daemon's notes."""
    found = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("*", "List of devices")):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        facts = dict(part.split(":", 1) for part in parts[2:] if ":" in part)
        found.append(Device(parts[0], parts[1], facts.get("model", "").replace("_", " ")))
    return found


def list_devices() -> list[Device]:
    """The devices attached now (on a thread).  Raises ``OSError`` with adb's
    words when it cannot say."""
    try:
        done = subprocess.run([command(), "devices", "-l"], capture_output=True, stdin=subprocess.DEVNULL, timeout=30)
    except FileNotFoundError as error:
        raise OSError("adb: command not found") from error
    except subprocess.TimeoutExpired as error:
        raise OSError("adb did not answer") from error
    if done.returncode != 0:
        raise OSError(" ".join(done.stderr.decode("utf-8", "replace").split()) or "adb devices failed")
    return parse_devices(done.stdout.decode("utf-8", "replace"))


__all__ = ["AdbDrive", "Device", "HOME", "available", "command", "connect", "list_devices", "lost",
           "parse_devices", "program", "sdk_dirs", "serial_of"]
