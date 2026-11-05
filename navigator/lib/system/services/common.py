"""What every service manager's backend shares: the row, running a command,
reading a refusal, and the shapes F3 and F4 are answered in.

A backend's commands all go through :func:`run`, so a test replaces one
function for every backend.
"""

from __future__ import annotations

import errno
import os
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: How long one command may take before it is given up on.
TIMEOUT = 30.0

#: What a manager's tools say, in English (``LANG=C``), when they refuse a
#: user: systemd's polkit, OpenRC's own checks, the kernel's.
REFUSALS = ("access denied", "interactive authentication required", "permission denied",
            "superuser access required", "must be root", "operation not permitted")


@dataclass(frozen=True, slots=True)
class Unit:
    """One service (a systemd unit of any type) as its manager says it."""

    name: str
    load: str = ""
    #: What it is doing: systemd's active state, OpenRC's ``started``/``crashed``...
    active: str = "inactive"
    #: systemd's sub state (``running``, ``dead``); OpenRC has none.
    sub: str = ""
    #: How it starts: systemd's unit file state (enabled, static...), OpenRC's runlevels.
    startup: str = ""
    description: str = ""
    #: The user's own manager's (``systemctl --user``), not the system's.
    user: bool = False
    #: The backend that read it, by :attr:`Backend.name`.
    backend: str = "systemd"

    @property
    def kind(self) -> str:
        """``service``, ``timer``, ``socket``... -- what follows the last dot."""
        return self.name.rpartition(".")[2]

    @property
    def failed(self) -> bool:
        return self.active in ("failed", "crashed")

    @property
    def running(self) -> bool:
        return self.active in ("active", "reloading", "activating", "started", "starting")

    @property
    def masked(self) -> bool:
        return self.startup.startswith("masked") or self.load == "masked"


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """*argv* run with its output gathered, in English so a refusal can be
    read, and given up on after :data:`TIMEOUT`.  Raises ``OSError``."""
    environment = {**os.environ, "LANG": "C", "LC_ALL": "C", "SYSTEMD_PAGER": "", "SYSTEMD_COLORS": "0",
                   "EINFO_COLOR": "NO"}
    try:
        return subprocess.run(argv, capture_output=True, text=True, errors="replace", timeout=TIMEOUT,
                              stdin=subprocess.DEVNULL, env=environment, check=False)
    except subprocess.TimeoutExpired as error:
        raise OSError(errno.ETIMEDOUT, f"{argv[0]} did not answer in time", argv[0]) from error


def failure(result: subprocess.CompletedProcess[str], name: str) -> OSError:
    """The ``OSError`` a failed command is: ``EPERM`` when the user was
    refused, so it is offered *As root*; ``EIO`` with what it said otherwise."""
    said = (result.stderr or result.stdout or "").strip() or f"exit status {result.returncode}"
    code = errno.EPERM if any(words in said.lower() for words in REFUSALS) else errno.EIO
    return OSError(code, said.splitlines()[-1].strip(" *") if code == errno.EPERM else said, name)


# -- what F3 and F4 are answered in ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Journal:
    """F3 follows *argv* (``journalctl --follow``) into a file; *readable*
    says whether the user sees all of it without root."""

    argv: list[str]
    readable: bool = True


@dataclass(frozen=True, slots=True)
class LogFile:
    """F3 follows *path* in the viewer -- its lines holding *pattern* only,
    when given (a system log shared by every service)."""

    path: Path
    pattern: str | None = None


@dataclass(frozen=True, slots=True)
class EditPlan:
    """What F4 opens: *path*, and *seed* -- its first text -- when it does
    not exist yet, the cursor put on *line* (counted from 1)."""

    path: Path
    seed: str | None = None
    line: int = 1


class Backend:
    """A service manager.  Every method that runs a command or reads a file
    is meant for a thread, and raises ``OSError``."""

    #: How the root helper and :attr:`Unit.backend` name it.
    name = ""
    #: How the window names it.
    title = ""
    #: What may be done to a service, a closed list the root helper checks again.
    verbs: tuple[str, ...] = ()
    #: Whether it has the user's own services (*User units*).
    user_scope = False
    #: Whether it has kinds other than services (*All types*).
    all_types = False
    #: Whether its unit files must be read again once one was edited (systemd's daemon-reload).
    reload_after_edit = False
    #: Whether an edit counts only from the service's next start (OpenRC's conf.d).
    restart_after_edit = False

    def refusal(self) -> str:
        """Why it is not this system's service manager, or ""."""
        raise NotImplementedError

    def valid_name(self, name: str) -> bool:
        """Whether *name* may go on its command line as a service's."""
        raise NotImplementedError

    def installed(self, name: str) -> bool:
        """Whether *name* is a service here -- what the root helper asks
        before acting, beyond :meth:`valid_name`."""
        return True

    def gather(self, user: bool, all_types: bool) -> list[Unit]:
        raise NotImplementedError

    def act(self, unit: Unit, verb: str) -> None:
        raise NotImplementedError

    def details(self, unit: Unit) -> str:
        raise NotImplementedError

    def log(self, unit: Unit) -> Journal | LogFile:
        raise NotImplementedError

    def edit_plan(self, unit: Unit) -> EditPlan:
        raise NotImplementedError

    def after_edit(self, user: bool) -> None:
        """What makes an edit count, when :attr:`reload_after_edit` says there is something."""


# -- following -----------------------------------------------------------------------------


class Follower:
    """A command (``journalctl --follow``) writing into a file, as the user."""

    def __init__(self, argv: list[str], path: Path) -> None:
        with open(path, "ab") as out:
            self.process = subprocess.Popen(argv, stdout=out, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                            env={**os.environ, "SYSTEMD_PAGER": "", "SYSTEMD_COLORS": "0"},
                                            start_new_session=True)

    @property
    def pid(self) -> int:
        return self.process.pid

    def stop(self) -> None:
        """Ended, and waited for -- on a thread."""
        stop_process(self.process)


def stop_process(process: subprocess.Popen[Any]) -> None:
    """*process* asked to end, killed if it will not, and waited for."""
    if process.poll() is None:
        try:
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        except ProcessLookupError:
            pass
