"""Doing a refused step again as root: ``sudo``, else ``pkexec``.

A departure -- DOS had no permissions to be refused, so DN never asked.  When
a step on the disk fails with ``EACCES``/``EPERM`` the file manager and the
editor offer *As root*; :data:`ELEVATION` then starts
:mod:`navigator.lib.system.roothelper` under ``sudo -S`` (the password asked in
Navigator's own box and written to sudo's stdin, never kept) or ``pkexec``
(polkit's agent asks), and :class:`~navigator.lib.drives.root.RootDrive` sends
it the steps.  It is Navigator's own code that runs as root, so a copy, an
erase or a save does as root exactly what it does without.

**Everything here blocks**: :meth:`Elevation.begin`, :meth:`~Elevation.answer`
and :meth:`~Elevation.call` run on a thread, never the loop.  The helper is
kept for ``[system] root_timeout`` minutes after its last step -- sudo's own
timestamp -- or closed at the end of each operation when that is 0, and
always at exit.  The ``navigator-elevation`` skill has the rules.
"""

from __future__ import annotations

import errno
import os
import selectors
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from navigator.lib.system.roothelper import READY, receive, send
from navigator.settings import ELEVATE

#: The tools, in the order ``auto`` tries them.
TOOLS = ("sudo", "pkexec")
#: ``[system] elevate``'s choices, which System Setup's *Root access* buttons are in order.
CHOICES = ELEVATE

#: What sudo is told to prompt with, so its asking can be told from its talk.
MARKER = "\x01navigator-password\x01"
#: How long starting the helper may take once nothing more is asked.
START_TIMEOUT = 120.0

#: The errors a step is offered *As root* for.
REFUSED = frozenset({errno.EACCES, errno.EPERM})

#: The helper's program: ``-I`` so nothing of the user's environment or
#: current directory is imported as root, the package found where this one is.
_ROOT = str(Path(__file__).resolve().parents[3])
_BOOT = (f"import sys; sys.path.insert(0, {_ROOT!r}); "
         "from navigator.lib.system.roothelper import main; main()")


@dataclass
class Asked:
    """Starting the helper wants a password; *wrong* when one was refused."""

    prompt: str
    wrong: bool = False


@dataclass
class Refused:
    """Starting the helper failed, for *reason*."""

    reason: str


#: Starting the helper worked.
READY_STATE = "ready"


def refused(error: BaseException) -> bool:
    """Whether *error* is a refusal *As root* could get past."""
    return isinstance(error, OSError) and error.errno in REFUSED


class Elevation:
    """The one root helper, started on demand and shared by every step."""

    def __init__(self) -> None:
        self._process: subprocess.Popen[bytes] | None = None
        self._lock = threading.Lock()
        self._stderr = b""
        self._last = 0.0
        #: Files a window keeps open through the helper (F3's): while any
        #: is, neither the idle timeout nor :meth:`release` closes it.
        self._held = 0
        self._reaper: threading.Thread | None = None
        #: The command to start instead of a tool's: the tests run the helper
        #: unprivileged with it.
        self.command: list[str] | None = None

    # -- what there is ---------------------------------------------------------

    def tool(self) -> str | None:
        """The tool ``[system] elevate`` names and is installed, or None."""
        from navigator.settings import SETTINGS

        chosen = SETTINGS.system.elevate
        if chosen == "off":
            return None
        for name in TOOLS if chosen == "auto" else (chosen,):
            if shutil.which(name):
                return name
        return None

    def available(self) -> bool:
        """Whether *As root* may be offered: not root already, and a tool to ask."""
        if self.command is not None:
            return True
        return hasattr(os, "geteuid") and os.geteuid() != 0 and self.tool() is not None

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None and self._ready

    _ready = False

    def argv(self, tool: str) -> list[str]:
        # ``-B``: nothing imported as root writes a ``.pyc`` -- it would be
        # root's, in the user's tree (or site-packages), and outlive this.
        helper = [sys.executable, "-I", "-B", "-c", _BOOT]
        if self.command is not None:
            return list(self.command)
        if tool == "sudo":
            return ["sudo", "-S", "-p", MARKER, "--", *helper]
        return [tool, *helper]

    # -- starting ----------------------------------------------------------------

    def begin(self) -> Asked | Refused | str:
        """Start the helper: :data:`READY_STATE`, a password :class:`Asked`
        for, or why not.  Already running answers ready."""
        with self._lock:
            if self.running:
                return READY_STATE
            self._shut()
            tool = self.tool() if self.command is None else "test"
            if tool is None:
                return Refused("sudo or pkexec is needed to work as root")
            try:
                # sudo gets no terminal of ours: its asking comes through the
                # pipe, and nothing it says can reach the screen.
                self._process = subprocess.Popen(
                    self.argv(tool), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, start_new_session=tool == "sudo", bufsize=0,
                )
            except OSError as error:
                self._process = None
                return Refused(error.strerror or str(error))
            self._stderr = b""
            return self._wait()

    def answer(self, password: str | None) -> Asked | Refused | str:
        """Give sudo *password* (None gives up): what :meth:`begin` answers."""
        with self._lock:
            process = self._process
            if process is None:
                return Refused("not started")
            if password is None:
                self._shut()
                return Refused("")
            try:
                assert process.stdin is not None
                process.stdin.write(password.encode() + b"\n")
                process.stdin.flush()
            except OSError as error:
                self._shut()
                return Refused(error.strerror or str(error))
            return self._wait()

    def _wait(self) -> Asked | Refused | str:
        """Read sudo's talk and the helper's first line until one says what next."""
        process = self._process
        assert process is not None and process.stdout is not None and process.stderr is not None
        out, err = process.stdout.fileno(), process.stderr.fileno()
        seen_out = b""
        talk_from = len(self._stderr)
        deadline = time.monotonic() + START_TIMEOUT
        with selectors.DefaultSelector() as selector:
            selector.register(out, selectors.EVENT_READ)
            selector.register(err, selectors.EVENT_READ)
            open_fds = {out, err}
            while open_fds:
                left = deadline - time.monotonic()
                if left <= 0:
                    self._shut()
                    return Refused("no answer from the authentication agent")
                for key, _ in selector.select(min(left, 1.0)):
                    # One byte of the helper's at a time, so nothing of what
                    # comes after READY is read past.
                    data = os.read(key.fd, 1 if key.fd == out else 4096)
                    if not data:
                        selector.unregister(key.fd)
                        open_fds.discard(key.fd)
                        continue
                    if key.fd == out:
                        seen_out += data
                        if seen_out == READY:
                            self._started()
                            return READY_STATE
                        if not READY.startswith(seen_out):
                            self._shut()
                            return Refused(seen_out.decode(errors="replace").strip())
                        continue
                    self._stderr += data
                    marker = MARKER.encode()
                    if marker in self._stderr[talk_from:]:
                        before = self._stderr[talk_from:].split(marker)[0].decode(errors="replace")
                        self._stderr = self._stderr.replace(marker, b"\n")
                        user = os.environ.get("USER") or ""
                        return Asked(f"[sudo] password for {user}:" if user else "[sudo] password:",
                                     wrong="sorry" in before.lower())
        process.wait()
        reason = self._stderr.decode(errors="replace").strip().splitlines()
        self._shut()
        return Refused(reason[-1] if reason else f"exit status {process.returncode}")

    def _started(self) -> None:
        self._ready = True
        self._last = time.monotonic()
        process = self._process
        assert process is not None and process.stderr is not None
        threading.Thread(target=_drain, args=(process.stderr,), daemon=True, name="root-stderr").start()
        if self._reaper is None or not self._reaper.is_alive():
            self._reaper = threading.Thread(target=self._reap, daemon=True, name="root-reaper")
            self._reaper.start()

    # -- steps -------------------------------------------------------------------

    def call(self, op: str, payload: bytes = b"", **args: Any) -> Any:
        """One step as root: its answer, or the ``OSError`` it raised there."""
        value, _ = self.call_data(op, payload, **args)
        return value

    def call_data(self, op: str, payload: bytes = b"", **args: Any) -> tuple[Any, bytes]:
        with self._lock:
            process = self._process
            if not self.running or process is None:
                raise OSError(errno.EACCES, "Root access is not open", args.get("path"))
            assert process.stdin is not None and process.stdout is not None
            try:
                send(process.stdin, {"op": op, "args": args}, payload)
                message, data = receive(process.stdout)
            except (OSError, EOFError, ValueError) as error:
                self._shut()
                raise OSError(errno.EIO, f"The root helper ended: {error}", args.get("path")) from None
            self._last = time.monotonic()
        if "ok" not in message:
            raise OSError(message.get("errno") or errno.EIO, message.get("strerror"), message.get("filename"))
        return message["ok"], data

    # -- ending ------------------------------------------------------------------

    def hold(self) -> None:
        """A file stays open through the helper until :meth:`unhold`."""
        with self._lock:
            self._held += 1

    def unhold(self) -> None:
        with self._lock:
            self._held = max(0, self._held - 1)

    def release(self) -> None:
        """An operation is over: with ``root_timeout`` 0, close the helper
        now -- unless a window still holds a file open through it."""
        from navigator.settings import SETTINGS

        with self._lock:
            if SETTINGS.system.root_timeout <= 0 and not self._held:
                self._shut()

    def close(self) -> None:
        with self._lock:
            self._shut()

    def _shut(self) -> None:
        self._held = 0
        process, self._process = self._process, None
        self._ready = False
        if process is None:
            return
        # The helper ends at the end of its input; root's process cannot be
        # killed by us, and need not be.
        for stream in (process.stdin, process.stdout):
            try:
                if stream is not None:
                    stream.close()
            except OSError:
                pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except OSError:
                pass

    def _reap(self) -> None:
        from navigator.settings import SETTINGS

        while True:
            time.sleep(10)
            minutes = SETTINGS.system.root_timeout
            with self._lock:
                if self._process is None:
                    return
                if minutes > 0 and not self._held and time.monotonic() - self._last > minutes * 60:
                    self._shut()
                    return


def _drain(stream: Any) -> None:
    try:
        while stream.read(4096):
            pass
    except (OSError, ValueError):
        pass


#: The one helper.
ELEVATION = Elevation()


__all__ = ["CHOICES", "ELEVATION", "Asked", "Elevation", "READY_STATE", "REFUSED", "Refused", "refused"]
