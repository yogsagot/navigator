"""Utilities > Services' OpenRC backend: services read and worked through
``rc-status``, ``rc-update`` and ``rc-service`` (Alpine, Gentoo, Artix, Devuan).

**A service is read from two lists merged, with no command per service**:
``rc-status --servicelist`` has every service and its state (``started``,
``stopped``, ``crashed``...), ``rc-update show --verbose`` every service and
the runlevels it starts in -- none is *disabled*.  The description is the
``description=`` line of its script in ``/etc/init.d``, read as a file.

**Enable** adds it to the ``default`` runlevel; **disable** takes it out of
every runlevel it is in, ``boot`` too -- what *disabled* means in the list.
OpenRC has no masking, no user services Navigator can count on, and no kinds
other than services: the window greys what it has not.

**F3**: OpenRC keeps no journal.  A service that names its own log
(``output_log=``/``error_log=``, supervise-daemon's, as a plain path in its
``/etc/conf.d`` file or its script) is followed there; any other is followed
in the system log (``/var/log/messages``, else ``/var/log/syslog``) with only
the lines holding its name shown -- approximate, as a name may appear in
another's lines, and said so in the window's title.

**F4** edits ``/etc/conf.d/<service>``, which the script reads each time it
starts: OpenRC's own way to change a service without touching the
package's script, as a drop-in is systemd's.  A new one is seeded with the
script's settings commented out.  It counts from the next start, so the
window offers a restart instead of systemd's daemon-reload.
"""

from __future__ import annotations

import errno
import re
import shutil
from pathlib import Path

from navigator.lib.system.services import common
from navigator.lib.system.services.common import Backend, EditPlan, Journal, LogFile, Unit

#: Where OpenRC says it is the system's manager (its run state).
RUN_OPENRC = Path("/run/openrc")

#: Its services' scripts, and the settings each reads.
INIT_D = Path("/etc/init.d")
CONF_D = Path("/etc/conf.d")

#: The system logs F3 falls back on, the first one there.
SYSTEM_LOGS = (Path("/var/log/messages"), Path("/var/log/syslog"))

#: What may be done to a service -- here and in the root helper's ``service`` op.
VERBS = ("start", "stop", "restart", "reload", "enable", "disable")

#: The runlevel *enable* adds a service to.
DEFAULT_RUNLEVEL = "default"

#: A service's name: its script's file name, never an option, never a path.
SERVICE_NAME = re.compile(r"[A-Za-z0-9_@:+][A-Za-z0-9._@:+-]*")

#: ``rc-status --servicelist``'s line: the name, then its state in brackets.
_STATUS_LINE = re.compile(r"^\s*(\S+)\s+\[\s*([A-Za-z]+)")

#: A script's ``description="..."`` line.
_DESCRIPTION = re.compile(r"""^\s*description=(["']?)(.*?)\1\s*$""")

#: A plain ``output_log=``/``error_log=`` path: quoted or not, no variable in it.
_LOG_SETTING = re.compile(r"""^\s*(?:output_log|error_log)=(["']?)(/[^"'$`\s]+)\1\s*$""")

#: A setting a script makes, which its ``/etc/conf.d`` file may make instead.
_SETTING = re.compile(r"^\s*[A-Za-z_][A-Za-z0-9_]*=")

#: How much of a script is read for its description and settings.
_SCRIPT_BYTES = 64 * 1024

#: The line of :func:`conf_text` the cursor starts on: the blank one under the header.
CONF_LINE = 3


def valid_service(name: str) -> bool:
    """Whether *name* is a service's that may go on a command line."""
    return len(name) <= 255 and SERVICE_NAME.fullmatch(name) is not None


def refusal() -> str:
    """Why OpenRC is not this system's service manager, or ""."""
    from navkit.i18n import tr

    if shutil.which("rc-service") is None or shutil.which("rc-update") is None:
        return tr("There is no rc-service: install OpenRC")
    if not RUN_OPENRC.is_dir():
        return tr("OpenRC is not the system's service manager")
    return ""


# -- listing ----------------------------------------------------------------------------------


def parse_status(text: str) -> dict[str, str]:
    """``rc-status --servicelist``: ``{service: state}``, the state lower case."""
    found = {}
    for line in text.splitlines():
        match = _STATUS_LINE.match(line)
        if match and valid_service(match.group(1)):
            found[match.group(1)] = match.group(2).lower()
    return found


def parse_runlevels(text: str) -> dict[str, list[str]]:
    """``rc-update show --verbose``: ``{service: [runlevel, ...]}``, empty for one in none."""
    found: dict[str, list[str]] = {}
    for line in text.splitlines():
        name, bar, levels = line.partition("|")
        name = name.strip()
        if bar and valid_service(name):
            found[name] = levels.split()
    return found


def _script(name: str) -> str:
    """The start of *name*'s script, or "" when it cannot be read."""
    try:
        with open(INIT_D / name, "rb") as handle:
            return handle.read(_SCRIPT_BYTES).decode("utf-8", "replace")
    except OSError:
        return ""


def description_of(script: str) -> str:
    """The script's ``description=`` line's text, or ""."""
    for line in script.splitlines():
        match = _DESCRIPTION.match(line)
        if match:
            return match.group(2).strip()
    return ""


def gather(user: bool = False, all_types: bool = False) -> list[Unit]:
    """Every service OpenRC knows, its state and runlevels.  Raises ``OSError``."""
    status = common.run(["rc-status", "--servicelist"])
    if status.returncode != 0:
        raise common.failure(status, "rc-status")
    states = parse_status(status.stdout)
    update = common.run(["rc-update", "show", "--verbose"])
    if update.returncode != 0:
        raise common.failure(update, "rc-update")
    levels = parse_runlevels(update.stdout)
    found = []
    for name in sorted({*states, *levels}):
        startup = ", ".join(levels.get(name, [])) or "disabled"
        found.append(Unit(name, "", states.get(name, "stopped"), "", startup, description_of(_script(name)),
                          False, "openrc"))
    return found


# -- doing something to one ---------------------------------------------------------------


def _checked(unit: Unit, verb: str) -> None:
    if verb not in VERBS or not valid_service(unit.name):
        raise OSError(errno.EINVAL, "Not something Navigator does to a service", unit.name)


def _ran(argv: list[str], name: str) -> None:
    result = common.run(argv)
    if result.returncode != 0:
        raise common.failure(result, name)


def act(unit: Unit, verb: str) -> None:
    """*verb* done to *unit*: ``rc-service`` for what it is doing,
    ``rc-update`` for how it starts.  Raises ``OSError`` -- ``EPERM`` when the
    user was refused."""
    _checked(unit, verb)
    name = unit.name
    if verb == "enable":
        _ran(["rc-update", "add", name, DEFAULT_RUNLEVEL], name)
    elif verb == "disable":
        # Read again rather than taken from the row: the root helper has only the name.
        update = common.run(["rc-update", "show", "--verbose"])
        if update.returncode != 0:
            raise common.failure(update, "rc-update")
        for level in parse_runlevels(update.stdout).get(name, []):
            _ran(["rc-update", "del", name, level], name)
    else:
        _ran(["rc-service", name, verb], name)


def details(unit: Unit) -> str:
    """``rc-service status``, then the script's description, runlevels and path."""
    from navkit.i18n import tr

    if not valid_service(unit.name):
        raise OSError(errno.EINVAL, "Not a service's name", unit.name)
    result = common.run(["rc-service", unit.name, "status"])
    # A stopped service's status exits non-zero, which is no failure.
    said = (result.stdout + result.stderr).strip() or tr("Status: {state}").format(state=unit.active)
    lines = [unit.name + (" - " + unit.description if unit.description else ""), said.strip(" *"),
             tr("Runlevels: {levels}").format(levels=unit.startup), tr("Script: {path}").format(path=INIT_D / unit.name)]
    return "\n".join(lines)


# -- F3: the log --------------------------------------------------------------------------------


def own_log(name: str) -> Path | None:
    """The log *name* declares for itself -- its ``/etc/conf.d`` file's first,
    then its script's -- when it is there."""
    for where in (CONF_D / name, INIT_D / name):
        try:
            text = where.read_text(errors="replace")[:_SCRIPT_BYTES]
        except OSError:
            continue
        for line in text.splitlines():
            match = _LOG_SETTING.match(line)
            if match and Path(match.group(2)).is_file():
                return Path(match.group(2))
    return None


def log(unit: Unit) -> LogFile:
    """F3: the service's own log, else the system log filtered to its name.
    Raises ``OSError`` when there is neither."""
    from navkit.i18n import tr

    path = own_log(unit.name)
    if path is not None:
        return LogFile(path)
    for system in SYSTEM_LOGS:
        if system.is_file():
            return LogFile(system, unit.name)
    raise OSError(errno.ENOENT, tr("OpenRC keeps no log for {unit}, and there is no system log file").format(
        unit=unit.name), unit.name)


# -- F4: its settings ---------------------------------------------------------------------------


def conf_text(unit: Unit, script: Path, text: str) -> str:
    """A new ``/etc/conf.d`` file's first text: what it is, then the settings
    *script* makes, commented out, to uncomment from.  Comments only, so
    saved unchanged it changes nothing."""
    from navkit.i18n import tr

    lines = [
        "# " + tr("Settings for {unit}, read by {path} each time it starts.").format(unit=unit.name, path=script),
        "# " + tr("A setting made here wins over the script's own; restart {unit} for it to count.").format(
            unit=unit.name),
        "",
        "",
        "# " + tr("The settings {path} makes:").format(path=script),
    ]
    lines += ["# " + line.strip() for line in text.splitlines() if _SETTING.match(line)]
    return "\n".join(lines) + "\n"


def edit_plan(unit: Unit) -> EditPlan:
    if not valid_service(unit.name):
        raise OSError(errno.EINVAL, "Not a service's name", unit.name)
    path = CONF_D / unit.name
    if path.exists():
        return EditPlan(path)
    script = INIT_D / unit.name
    return EditPlan(path, conf_text(unit, script, _script(unit.name)), CONF_LINE)


class OpenRC(Backend):
    """OpenRC, through ``rc-status``, ``rc-update`` and ``rc-service``."""

    name = "openrc"
    title = "OpenRC"
    verbs = VERBS
    restart_after_edit = True

    def refusal(self) -> str:
        return refusal()

    def valid_name(self, name: str) -> bool:
        return valid_service(name)

    def installed(self, name: str) -> bool:
        """A script in ``/etc/init.d`` by that name: nothing else is run."""
        return (INIT_D / name).is_file()

    def gather(self, user: bool, all_types: bool) -> list[Unit]:
        return gather(user, all_types)

    def act(self, unit: Unit, verb: str) -> None:
        act(unit, verb)

    def details(self, unit: Unit) -> str:
        return details(unit)

    def log(self, unit: Unit) -> Journal | LogFile:
        return log(unit)

    def edit_plan(self, unit: Unit) -> EditPlan:
        return edit_plan(unit)


BACKEND = OpenRC()
