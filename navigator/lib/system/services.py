"""Utilities > Services' model: systemd's units, read and worked through ``systemctl``.

**Not DOS Navigator's**: a departure, asked for.  DOS had no service manager
and DN nothing to list; this is the Process list's sibling, a window of
systemd's units that starts, stops, restarts, reloads, enables and disables
them -- through the root helper when the user may not -- and follows a unit's
journal in the F3 viewer.

Everything here runs ``systemctl`` or ``journalctl`` and is meant for a
thread (``navml.background.Background``, ``asyncio.to_thread``).  Every
command goes through :func:`_run`, so a test replaces one function.

**A unit is read from two lists merged**: ``list-units --all`` has what is
loaded (its active and sub state and description), ``list-unit-files`` what
is installed (enabled, disabled, static, masked).  A unit installed but never
loaded is only in the second, and is shown inactive.  A template
(``getty@.service``) is left out: it cannot be started or followed until it
has an instance, and its instances are listed by their own names.  JSON is
asked for (systemd 246 and later) and the plain columns read when it is
refused.

**What may be done is a closed list** (:data:`VERBS`), and a unit's name is
checked (:func:`valid_unit`) before it reaches an argument list: the root
helper's ``systemctl`` op checks both again, as its ``kill`` checks a pid.
``--no-ask-password`` keeps polkit from asking on the terminal Navigator is
drawing on; its refusal comes back as ``EPERM``, which
:func:`navigator.lib.system.elevate.refused` takes for a step to offer *As root*.
"""

from __future__ import annotations

import errno
import grp
import json
import os
import re
import shutil
import signal
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: Where systemd says it is the system's manager (``sd_booted()``).
RUN_SYSTEMD = Path("/run/systemd/system")

#: The columns the list sorts by.
SORTS = ("name", "active", "file_state", "description")

#: What may be done to a unit -- here and in the root helper's ``systemctl`` op.
VERBS = ("start", "stop", "restart", "reload", "enable", "disable", "mask", "unmask")

#: A unit's name as systemd allows it (``unit_name_is_valid``): letters,
#: digits and ``:-_.\@``, never starting with ``-`` so it is never an option.
UNIT_NAME = re.compile(r"[A-Za-z0-9:_.\\@][A-Za-z0-9:_.\\@-]*")

#: The groups whose members read the whole system journal.
JOURNAL_GROUPS = ("systemd-journal", "adm", "wheel")

#: How long one ``systemctl`` may take before it is given up on.
TIMEOUT = 30.0

#: What ``systemctl`` says, in English (``LANG=C``), when polkit refuses.
_REFUSALS = ("access denied", "interactive authentication required", "permission denied")


def valid_unit(name: str) -> bool:
    """Whether *name* is a unit's name that may go on a command line."""
    return len(name) <= 256 and UNIT_NAME.fullmatch(name) is not None and "." in name


def refusal_reason() -> str:
    """Why there are no services to list, or "" -- the menu entry's grey."""
    from navkit.i18n import tr

    if shutil.which("systemctl") is None:
        return tr("There is no systemctl: install systemd")
    if not RUN_SYSTEMD.is_dir():
        return tr("systemd is not the system's service manager")
    return ""


def available() -> bool:
    return not refusal_reason()


@dataclass(frozen=True, slots=True)
class Unit:
    """One unit as the two lists say it."""

    name: str
    load: str = ""
    active: str = "inactive"
    sub: str = "dead"
    file_state: str = ""
    description: str = ""
    #: The user's own manager's (``systemctl --user``), not the system's.
    user: bool = False

    @property
    def kind(self) -> str:
        """``service``, ``timer``, ``socket``... -- what follows the last dot."""
        return self.name.rpartition(".")[2]

    @property
    def failed(self) -> bool:
        return self.active == "failed"

    @property
    def running(self) -> bool:
        return self.active in ("active", "reloading", "activating")

    @property
    def masked(self) -> bool:
        return self.file_state.startswith("masked") or self.load == "masked"


# -- running systemctl ---------------------------------------------------------------


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    """*argv* run with its output gathered, in English so a refusal can be
    read, and given up on after :data:`TIMEOUT`.  Raises ``OSError``."""
    environment = {**os.environ, "LANG": "C", "LC_ALL": "C", "SYSTEMD_PAGER": "", "SYSTEMD_COLORS": "0"}
    try:
        return subprocess.run(argv, capture_output=True, text=True, errors="replace", timeout=TIMEOUT,
                              stdin=subprocess.DEVNULL, env=environment, check=False)
    except subprocess.TimeoutExpired as error:
        raise OSError(errno.ETIMEDOUT, "systemctl did not answer in time", argv[0]) from error


def _systemctl(user: bool) -> list[str]:
    return ["systemctl", "--user"] if user else ["systemctl"]


def failure(result: subprocess.CompletedProcess[str], name: str) -> OSError:
    """The ``OSError`` a failed ``systemctl`` is: ``EPERM`` when polkit said
    no, so it is offered *As root*; ``EIO`` with what it said otherwise."""
    said = (result.stderr or result.stdout or "").strip() or f"exit status {result.returncode}"
    code = errno.EPERM if any(words in said.lower() for words in _REFUSALS) else errno.EIO
    return OSError(code, said.splitlines()[-1] if code == errno.EPERM else said, name)


def _listing(argv: list[str]) -> tuple[list[dict[str, Any]] | None, str]:
    """``argv --output=json``'s rows, or None and the plain columns when
    this systemd has no JSON output."""
    result = _run([*argv, "--output=json", "--no-pager"])
    if result.returncode == 0:
        try:
            rows = json.loads(result.stdout or "[]")
        except ValueError:
            rows = None
        if isinstance(rows, list):
            return rows, ""
    plain = _run([*argv, "--plain", "--no-legend", "--no-pager"])
    if plain.returncode != 0:
        raise failure(plain, argv[0])
    return None, plain.stdout


def parse_units(rows: list[dict[str, Any]] | None, plain: str = "") -> list[dict[str, str]]:
    """``list-units``' rows, from JSON or the plain columns: unit, load,
    active, sub and the description, which is the rest of a plain line."""
    if rows is not None:
        return [{key: str(row.get(key) or "") for key in ("unit", "load", "active", "sub", "description")}
                for row in rows if isinstance(row, dict) and row.get("unit")]
    found = []
    for line in plain.splitlines():
        words = line.lstrip("●* ").split(None, 4)
        if len(words) >= 4:
            found.append({"unit": words[0], "load": words[1], "active": words[2], "sub": words[3],
                          "description": words[4] if len(words) > 4 else ""})
    return found


def parse_unit_files(rows: list[dict[str, Any]] | None, plain: str = "") -> dict[str, str]:
    """``list-unit-files``' rows, from JSON or the plain columns: ``{name: state}``."""
    if rows is not None:
        return {str(row["unit_file"]): str(row.get("state") or "") for row in rows
                if isinstance(row, dict) and row.get("unit_file")}
    found = {}
    for line in plain.splitlines():
        words = line.split()
        if len(words) >= 2:
            found[words[0]] = words[1]
    return found


def merge(units: list[dict[str, str]], files: dict[str, str], user: bool) -> list[Unit]:
    """The two lists as one: every loaded unit with its file's state, then
    every installed one not loaded, inactive.  Templates are left out."""
    merged: dict[str, Unit] = {}
    for row in units:
        name = row["unit"]
        if not valid_unit(name):
            continue
        template = name.split("@", 1)[0] + "@." + name.rpartition(".")[2] if "@" in name else ""
        state = files.get(name) or (files.get(template, "") if template else "")
        merged[name] = Unit(name, row["load"], row["active"] or "inactive", row["sub"] or "dead", state,
                            row["description"], user)
    for name, state in files.items():
        if name in merged or not valid_unit(name) or "@." in name:
            continue
        merged[name] = Unit(name, "", "inactive", "dead", state, "", user)
    return list(merged.values())


def gather(user: bool = False, all_types: bool = False) -> list[Unit]:
    """Every unit of the system's manager (the user's, with *user*): services
    only, or every type with *all_types*.  Raises ``OSError``."""
    kinds = [] if all_types else ["--type=service"]
    base = _systemctl(user)
    units = parse_units(*_listing([*base, "list-units", "--all", *kinds]))
    files = parse_unit_files(*_listing([*base, "list-unit-files", *kinds]))
    return merge(units, files, user)


# -- sorting and the filter -----------------------------------------------------------


def sort_key(by: str) -> Any:
    if by == "active":
        return lambda unit: (unit.active, unit.sub)
    if by == "file_state":
        return lambda unit: unit.file_state
    if by == "description":
        return lambda unit: unit.description.casefold()
    return lambda unit: unit.name.casefold()


def ordered(found: Iterable[Unit], by: str, descending: bool) -> list[Unit]:
    """*found* sorted *by* one of :data:`SORTS`, the name breaking ties."""
    by_name = sorted(found, key=lambda unit: unit.name.casefold())
    return sorted(by_name, key=sort_key(by), reverse=descending)


def matches(unit: Unit, text: str) -> bool:
    """Whether the filter's *text* is in *unit*'s name or description, in any case."""
    text = text.strip().casefold()
    return not text or text in unit.name.casefold() or text in unit.description.casefold()


# -- doing something to one ------------------------------------------------------------


def act(unit: Unit, verb: str) -> None:
    """``systemctl VERB UNIT`` as the user, asking no password.  Raises
    ``OSError`` -- ``EPERM`` when polkit refused it."""
    if verb not in VERBS or not valid_unit(unit.name):
        raise OSError(errno.EINVAL, "Not something Navigator does to a unit", unit.name)
    result = _run([*_systemctl(unit.user), "--no-ask-password", verb, "--", unit.name])
    if result.returncode != 0:
        raise failure(result, unit.name)


def details(unit: Unit) -> str:
    """What ``systemctl status`` says of *unit*, its log lines left to F3."""
    if not valid_unit(unit.name):
        raise OSError(errno.EINVAL, "Not a unit's name", unit.name)
    result = _run([*_systemctl(unit.user), "status", "--no-pager", "--lines=0", "--full", "--", unit.name])
    # ``status`` exits 3 for a unit that is not running, which is no failure.
    text = (result.stdout or "").rstrip()
    if not text:
        raise failure(result, unit.name)
    return text.lstrip("●○×↻* ")


# -- its unit file ----------------------------------------------------------------------


#: Where the system's administrator keeps unit files of their own; a unit
#: file anywhere else (``/usr/lib/systemd/system``: the package's) is not
#: edited but overridden by a drop-in here, as ``systemctl edit`` does.
ADMIN_SYSTEM = Path("/etc/systemd/system")

#: The drop-in an override is written to, in ``<unit>.d/`` -- ``systemctl edit``'s name.
OVERRIDE = "override.conf"


def admin_dir(user: bool) -> Path:
    """Where unit files of the user's own go: ``/etc/systemd/system``, or for
    a user unit ``$XDG_CONFIG_HOME/systemd/user``."""
    if not user:
        return ADMIN_SYSTEM
    config = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return Path(config) / "systemd" / "user"


def unit_file(unit: Unit) -> Path:
    """The file *unit* was loaded from (``FragmentPath``), for F4 to edit.
    Raises ``OSError`` for a masked unit -- unmasked first, or the edit would
    never count -- and for one with none: generated in memory, or not found."""
    from navkit.i18n import tr

    if not valid_unit(unit.name):
        raise OSError(errno.EINVAL, "Not a unit's name", unit.name)
    if unit.masked:
        raise OSError(errno.EINVAL, tr("{unit} is masked: unmask it first").format(unit=unit.name), unit.name)
    result = _run([*_systemctl(unit.user), "show", "--property=FragmentPath", "--value", "--", unit.name])
    if result.returncode != 0:
        raise failure(result, unit.name)
    found = (result.stdout or "").strip()
    if not found or found == os.devnull:
        raise OSError(errno.ENOENT, tr("{unit} has no unit file to edit").format(unit=unit.name), unit.name)
    return Path(found)


def edit_target(unit: Unit, fragment: Path) -> tuple[Path, Path | None]:
    """What F4 opens for *unit* loaded from *fragment*: the fragment itself
    when it is the administrator's own (under :func:`admin_dir`, links
    resolved), else the drop-in ``<unit>.d/override.conf`` there -- with the
    vendor's file it overrides, None for the first case.  A file a package
    put in place is overwritten by the next upgrade; a drop-in is not."""
    own = admin_dir(unit.user)
    real = Path(os.path.realpath(fragment))
    if real.is_relative_to(Path(os.path.realpath(own))):
        return fragment, None
    return own / f"{unit.name}.d" / OVERRIDE, fragment


def override_text(unit: Unit, vendor: Path, original: str) -> str:
    """A new drop-in's first text: what it is, then *original* -- the vendor's
    file -- commented out, to uncomment from.  Comments only, so saved
    unchanged it changes nothing."""
    from navkit.i18n import tr

    lines = [
        "# " + tr("Override for {unit}: what is set here wins over {path}.").format(unit=unit.name, path=vendor),
        "# " + tr("A list setting such as ExecStart= is emptied first by a line of its own, ExecStart= alone."),
        "",
        "",
        "# " + tr("{path} as it is:").format(path=vendor),
    ]
    lines += ["#" + (" " + line if line else "") for line in original.splitlines()]
    return "\n".join(lines) + "\n"


#: The line of :func:`override_text` the cursor starts on: the blank one under the header.
OVERRIDE_LINE = 3


def daemon_reload(user: bool) -> None:
    """``systemctl daemon-reload``: the unit files read again after one was
    edited.  Raises ``OSError`` -- ``EPERM`` when polkit refused it."""
    result = _run([*_systemctl(user), "--no-ask-password", "daemon-reload"])
    if result.returncode != 0:
        raise failure(result, "daemon-reload")


# -- the journal -------------------------------------------------------------------------


def journal_argv(name: str, user: bool, lines: int) -> list[str]:
    """``journalctl`` following *name*'s journal, its last *lines* first."""
    return ["journalctl", "--no-pager", "--follow", "--lines", str(max(0, int(lines))), "--output", "short-iso",
            "--user-unit" if user else "--unit", name]


def can_read_journal(unit: Unit) -> bool:
    """Whether the user reads *unit*'s whole journal as they are: their own
    unit's, or root's, or a member of a group journald lets read it all."""
    if unit.user or os.geteuid() == 0:
        return True
    names = set()
    for gid in {*os.getgroups(), os.getegid()}:
        try:
            names.add(grp.getgrgid(gid).gr_name)
        except KeyError:
            continue
    return any(group in names for group in JOURNAL_GROUPS)


class Follower:
    """``journalctl --follow`` writing into a file, as the user."""

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
