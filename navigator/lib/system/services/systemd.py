"""Utilities > Services' systemd backend: units read and worked through ``systemctl``.

Everything here runs ``systemctl`` or ``journalctl`` and is meant for a
thread (``navml.background.Background``, ``asyncio.to_thread``).  Every
command goes through :func:`navigator.lib.system.services.common.run`, so a
test replaces one function.

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
helper's ``service`` op checks both again, as its ``kill`` checks a pid.
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
from pathlib import Path
from typing import Any

from navigator.lib.system.services import common
from navigator.lib.system.services.common import Backend, EditPlan, Journal, LogFile, Unit
from navigator.lib.system.which import which as _which

#: Where systemd says it is the system's manager (``sd_booted()``).
RUN_SYSTEMD = Path("/run/systemd/system")

#: What may be done to a unit -- here and in the root helper's ``service`` op.
VERBS = ("start", "stop", "restart", "reload", "enable", "disable", "mask", "unmask")

#: A unit's name as systemd allows it (``unit_name_is_valid``): letters,
#: digits and ``:-_.\@``, never starting with ``-`` so it is never an option.
UNIT_NAME = re.compile(r"[A-Za-z0-9:_.\\@][A-Za-z0-9:_.\\@-]*")

#: The groups whose members read the whole system journal.
JOURNAL_GROUPS = ("systemd-journal", "adm", "wheel")


def valid_unit(name: str) -> bool:
    """Whether *name* is a unit's name that may go on a command line."""
    return len(name) <= 256 and UNIT_NAME.fullmatch(name) is not None and "." in name


def refusal() -> str:
    """Why systemd is not this system's service manager, or ""."""
    from navkit.i18n import tr

    if _which("systemctl") is None:
        return tr("There is no systemctl: install systemd")
    if not RUN_SYSTEMD.is_dir():
        return tr("systemd is not the system's service manager")
    return ""


# -- running systemctl ---------------------------------------------------------------


def _systemctl(user: bool) -> list[str]:
    return ["systemctl", "--user"] if user else ["systemctl"]


def _listing(argv: list[str]) -> tuple[list[dict[str, Any]] | None, str]:
    """``argv --output=json``'s rows, or None and the plain columns when
    this systemd has no JSON output."""
    result = common.run([*argv, "--output=json", "--no-pager"])
    if result.returncode == 0:
        try:
            rows = json.loads(result.stdout or "[]")
        except ValueError:
            rows = None
        if isinstance(rows, list):
            return rows, ""
    plain = common.run([*argv, "--plain", "--no-legend", "--no-pager"])
    if plain.returncode != 0:
        raise common.failure(plain, argv[0])
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
                            row["description"], user, "systemd")
    for name, state in files.items():
        if name in merged or not valid_unit(name) or "@." in name:
            continue
        merged[name] = Unit(name, "", "inactive", "dead", state, "", user, "systemd")
    return list(merged.values())


def gather(user: bool = False, all_types: bool = False) -> list[Unit]:
    """Every unit of the system's manager (the user's, with *user*): services
    only, or every type with *all_types*.  Raises ``OSError``."""
    kinds = [] if all_types else ["--type=service"]
    base = _systemctl(user)
    units = parse_units(*_listing([*base, "list-units", "--all", *kinds]))
    files = parse_unit_files(*_listing([*base, "list-unit-files", *kinds]))
    return merge(units, files, user)


# -- doing something to one ------------------------------------------------------------


def act(unit: Unit, verb: str) -> None:
    """``systemctl VERB UNIT`` as the user, asking no password.  Raises
    ``OSError`` -- ``EPERM`` when polkit refused it."""
    if verb not in VERBS or not valid_unit(unit.name):
        raise OSError(errno.EINVAL, "Not something Navigator does to a unit", unit.name)
    result = common.run([*_systemctl(unit.user), "--no-ask-password", verb, "--", unit.name])
    if result.returncode != 0:
        raise common.failure(result, unit.name)


def details(unit: Unit) -> str:
    """What ``systemctl status`` says of *unit*, its log lines left to F3."""
    if not valid_unit(unit.name):
        raise OSError(errno.EINVAL, "Not a unit's name", unit.name)
    result = common.run([*_systemctl(unit.user), "status", "--no-pager", "--lines=0", "--full", "--", unit.name])
    # ``status`` exits 3 for a unit that is not running, which is no failure.
    text = (result.stdout or "").rstrip()
    if not text:
        raise common.failure(result, unit.name)
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
    result = common.run([*_systemctl(unit.user), "show", "--property=FragmentPath", "--value", "--", unit.name])
    if result.returncode != 0:
        raise common.failure(result, unit.name)
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
    result = common.run([*_systemctl(user), "--no-ask-password", "daemon-reload"])
    if result.returncode != 0:
        raise common.failure(result, "daemon-reload")


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


class Systemd(Backend):
    """systemd, through ``systemctl`` and ``journalctl``."""

    name = "systemd"
    title = "systemd"
    verbs = VERBS
    user_scope = True
    all_types = True
    reload_after_edit = True

    def refusal(self) -> str:
        return refusal()

    def valid_name(self, name: str) -> bool:
        return valid_unit(name)

    def gather(self, user: bool, all_types: bool) -> list[Unit]:
        return gather(user, all_types)

    def act(self, unit: Unit, verb: str) -> None:
        act(unit, verb)

    def details(self, unit: Unit) -> str:
        return details(unit)

    def log(self, unit: Unit) -> Journal | LogFile:
        from navigator.lib.system.services import journal_lines

        return Journal(journal_argv(unit.name, unit.user, journal_lines()), can_read_journal(unit))

    def edit_plan(self, unit: Unit) -> EditPlan:
        """The unit's file, or a drop-in override of a package's, seeded with
        the package's file commented out (:func:`edit_target`)."""
        fragment = unit_file(unit)
        path, vendor = edit_target(unit, fragment)
        if vendor is None or path.exists():
            return EditPlan(path)
        return EditPlan(path, override_text(unit, vendor, vendor.read_text(errors="replace")), OVERRIDE_LINE)

    def after_edit(self, user: bool) -> None:
        daemon_reload(user)


BACKEND = Systemd()
