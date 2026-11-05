"""Utilities > Services' runit backend: service directories, symbolic links
and ``sv`` (Void, Artix, Devuan with runit as its first process).

**runit keeps no database, only directories.**  A service is defined by a
directory of its own (``/etc/sv/<name>``, Artix's ``/etc/runit/sv/<name>``)
holding the ``run`` script it runs and, in ``log/``, its logger's; it is
*enabled* by a symbolic link to that directory in the supervised directory
(``$SVDIR``, else ``/var/service``, ``/run/runit/service``, ``/etc/service`` or
``/service``, the first there), which ``runsvdir`` notices within seconds and
starts.  A ``down`` file in it keeps an enabled service from starting by
itself: *enabled, down*.

**States are root's on Void**: each service's ``supervise/`` is, so ``sv
status`` refuses a user, and enabled services come back :data:`UNKNOWN`
(``states_need_root``) for the window to read through the root helper's
``service_states`` op -- :meth:`Runit.states`, the same fixed ``sv status``.
A disabled service has no supervisor: its state, *down*, needs nothing read.

runit has no descriptions; the column says what the ``run`` script ``exec``\\s.

**Enable** links the definition into the supervised directory, **disable**
removes that link -- only a link, and only one to a definition, never a
directory placed there.  No masking, no user services, no other kinds.

**F3**: a logger that is ``svlogd DIR`` is followed in ``DIR/current``, runit's
own log; any other (Void's ``vlogger`` goes to syslog) in the system log,
filtered to the service's name.  **F4** edits the definition's ``conf``
when its ``run`` script reads one (Void's ``[ -r conf ] && . ./conf``), seeded
with the script commented out; else the ``run`` script itself, after saying a
package update may replace it.  Either counts from the next start, so the
window offers a restart.
"""

from __future__ import annotations

import errno
import os
import re
import shutil
from pathlib import Path

from navigator.lib.system.services import common
from navigator.lib.system.services.common import UNKNOWN, Backend, EditPlan, Journal, LogFile, Unit

#: Where services are defined, the first there.
DEFINITION_DIRS = (Path("/etc/sv"), Path("/etc/runit/sv"))

#: Where enabled services are linked (``runsvdir``'s), the first there, after ``$SVDIR``.
SERVICE_DIRS = (Path("/var/service"), Path("/run/runit/service"), Path("/etc/service"), Path("/service"))

#: What may be done to a service -- here and in the root helper's ``service`` op.
VERBS = ("start", "stop", "restart", "reload", "enable", "disable")

#: How long ``sv`` waits for a start or stop to show, in seconds.
WAIT = 7

#: A service's name: its directory's, never an option, never a path.
SERVICE_NAME = re.compile(r"[A-Za-z0-9_@:+][A-Za-z0-9._@:+-]*")

#: ``sv status``'s line: the state, the service as named, and the rest.
_STATUS_LINE = re.compile(r"^(run|down|finish|fail|warning):\s+([^:]+):\s*(.*)$")

#: How much of a script is read.
_SCRIPT_BYTES = 64 * 1024

#: The line of :func:`conf_text` the cursor starts on: the blank one under the header.
CONF_LINE = 3


def valid_service(name: str) -> bool:
    return len(name) <= 255 and SERVICE_NAME.fullmatch(name) is not None


def definitions() -> Path | None:
    """Where services are defined here, or None."""
    return next((where for where in DEFINITION_DIRS if where.is_dir()), None)


def service_dir() -> Path | None:
    """The supervised directory enabled services are linked into, or None."""
    chosen = os.environ.get("SVDIR", "")
    candidates = ((Path(chosen),) if chosen else ()) + SERVICE_DIRS
    return next((where for where in candidates if where.is_dir()), None)


def refusal() -> str:
    """Why runit is not this system's service manager, or ""."""
    from navkit.i18n import tr

    if shutil.which("sv") is None:
        return tr("There is no sv: install runit")
    if common.pid1() != "runit":
        return tr("runit is not the system's service manager")
    if definitions() is None or service_dir() is None:
        return tr("runit has no service directory here")
    return ""


def _read(path: Path) -> str:
    try:
        with open(path, "rb") as handle:
            return handle.read(_SCRIPT_BYTES).decode("utf-8", "replace")
    except OSError:
        return ""


def runs(script: str) -> str:
    """What a ``run`` script ``exec``\\s, its last ``exec`` line's command, or ""."""
    found = ""
    for line in script.splitlines():
        match = re.match(r"^\s*exec\s+(.*\S)", line)
        if match:
            found = " ".join(match.group(1).split())
    return found[:200]


def _definition(name: str) -> Path | None:
    """*name*'s definition directory: in the definitions, else a directory
    placed in the supervised directory itself."""
    defined = definitions()
    if defined is not None and (defined / name).is_dir():
        return defined / name
    supervised = service_dir()
    if supervised is not None and (supervised / name).is_dir():
        return supervised / name
    return None


# -- states ------------------------------------------------------------------------------------


def parse_status(text: str) -> tuple[dict[str, tuple[str, str]], bool]:
    """``sv status``'s lines: ``{service: (state, sub)}``, and whether any was
    refused (``supervise/`` root's).  The sub is the uptime, or what a down
    service normally is."""
    found: dict[str, tuple[str, str]] = {}
    refused = False
    for line in text.splitlines():
        match = _STATUS_LINE.match(line.strip())
        if not match:
            continue
        state, named, rest = match.groups()
        name = Path(named.strip()).name
        if state == "warning":
            if any(words in rest.lower() for words in common.REFUSALS):
                refused = True
            else:
                # No supervisor answering (``runsv`` not running yet): no state root could read either.
                found[name] = ("fail", "")
            continue
        own = rest.split(";", 1)[0]
        seconds = re.search(r"(\d+)s\b", own)
        sub = "normally up" if "normally up" in own else "normally down" if "normally down" in own else ""
        found[name] = (state, sub or (f"{seconds.group(1)}s" if seconds else ""))
    return found, refused


def enabled_names() -> list[str]:
    supervised = service_dir()
    if supervised is None:
        return []
    try:
        return sorted(entry.name for entry in supervised.iterdir() if valid_service(entry.name) and entry.is_dir())
    except OSError:
        return []


def states() -> dict[str, tuple[str, str]]:
    """Every enabled service's state, by ``sv status``.  Raises ``OSError``
    -- ``EPERM`` when every one was refused."""
    supervised = service_dir()
    names = enabled_names()
    if supervised is None or not names:
        return {}
    result = common.run(["sv", "status", *(str(supervised / name) for name in names)])
    found, refused = parse_status(result.stdout + result.stderr)
    if refused and not found:
        raise OSError(errno.EPERM, "sv: access denied", "sv")
    return found


def gather(user: bool = False, all_types: bool = False) -> list[Unit]:
    """Every service defined or enabled, its state -- :data:`UNKNOWN` for an
    enabled one the user may not read -- and how it starts."""
    defined, supervised = definitions(), service_dir()
    enabled = set(enabled_names())
    names = set(enabled)
    if defined is not None:
        try:
            names |= {entry.name for entry in defined.iterdir() if valid_service(entry.name) and entry.is_dir()}
        except OSError as error:
            raise OSError(error.errno, error.strerror, str(defined)) from error
    try:
        known = states()
    except OSError:
        known = {}
    found = []
    for name in sorted(names):
        where = _definition(name)
        if name in enabled:
            down = (supervised / name / "down").exists() if supervised is not None else False
            startup = "enabled, down" if down else "enabled"
            active, sub = known.get(name, (UNKNOWN, ""))
        else:
            startup, active, sub = "disabled", "down", ""
        description = runs(_read(where / "run")) if where is not None else ""
        found.append(Unit(name, "", active, sub, startup, description, False, "runit"))
    return found


# -- doing something to one --------------------------------------------------------------------


def act(unit: Unit, verb: str) -> None:
    """*verb* done to *unit*: ``sv`` for what it is doing, its link for
    whether it is enabled.  Raises ``OSError`` -- ``EPERM`` when refused."""
    from navkit.i18n import tr

    name = unit.name
    if verb not in VERBS or not valid_service(name):
        raise OSError(errno.EINVAL, "Not something Navigator does to a service", name)
    defined, supervised = definitions(), service_dir()
    if supervised is None:
        raise OSError(errno.ENOENT, tr("runit has no service directory here"), name)
    link = supervised / name
    if verb == "enable":
        target = defined / name if defined is not None else None
        if target is None or not target.is_dir():
            raise OSError(errno.ENOENT, tr("{unit} is not defined in {path}").format(unit=name, path=defined), name)
        if not os.path.lexists(link):
            os.symlink(target, link)
        return
    if verb == "disable":
        if not os.path.lexists(link):
            return
        real = Path(os.path.realpath(link))
        if not link.is_symlink() or defined is None or not real.is_relative_to(Path(os.path.realpath(defined))):
            raise OSError(errno.EINVAL, tr("{path} is not a link Navigator removes").format(path=link), name)
        os.unlink(link)
        return
    if not os.path.lexists(link):
        raise OSError(errno.EINVAL, tr("{unit} is not enabled: enable it first").format(unit=name), name)
    result = common.run(["sv", "-w", str(WAIT), verb, str(link)])
    if result.returncode != 0:
        raise common.failure(result, name)


def details(unit: Unit) -> str:
    from navkit.i18n import tr

    if not valid_service(unit.name):
        raise OSError(errno.EINVAL, "Not a service's name", unit.name)
    supervised = service_dir()
    where = _definition(unit.name)
    lines = [unit.name + (" - " + unit.description if unit.description else "")]
    if unit.startup != "disabled" and supervised is not None:
        result = common.run(["sv", "status", str(supervised / unit.name)])
        lines.append((result.stdout + result.stderr).strip())
    else:
        lines.append(tr("Status: {state}").format(state=unit.active))
    lines.append(tr("Start-up: {state}").format(state=unit.startup))
    if where is not None:
        lines.append(tr("Defined in {path}").format(path=where))
        logger = svlogd_dir(_read(where / "log" / "run"))
        if logger is not None:
            lines.append(tr("Logs to {path}").format(path=logger))
    return "\n".join(lines)


# -- F3: the log ----------------------------------------------------------------------------------


def svlogd_dir(script: str) -> Path | None:
    """The directory a ``log/run`` script's ``svlogd`` writes to, or None for
    another logger.  It is ``svlogd``'s last argument that is a path."""
    for line in script.splitlines():
        words = line.replace('"', " ").replace("'", " ").split()
        if "svlogd" not in (Path(word).name for word in words):
            continue
        after = words[[Path(word).name for word in words].index("svlogd") + 1:]
        paths = [word for word in after if word.startswith("/")]
        if paths:
            return Path(paths[-1])
    return None


def log(unit: Unit) -> LogFile:
    """F3: ``svlogd``'s ``current``, else the system log filtered to its name."""
    where = _definition(unit.name)
    if where is not None:
        logger = svlogd_dir(_read(where / "log" / "run"))
        if logger is not None:
            # Trusted as written: a log directory the user may not read
            # cannot be looked into, and F3 offers it *As root*.
            return LogFile(logger / "current")
    return common.system_log(unit, "runit")


# -- F4 ---------------------------------------------------------------------------------------------


def reads_conf(script: str) -> bool:
    """Whether a ``run`` script reads its directory's ``conf`` (``. ./conf``, ``[ -r conf ]``)."""
    return re.search(r"(?:^|[\s./])conf\b", script, re.MULTILINE) is not None


def conf_text(unit: Unit, run: Path, script: str) -> str:
    """A new ``conf``'s first text: what it is, then *run* commented out."""
    from navkit.i18n import tr

    lines = [
        "# " + tr("Settings for {unit}, read by {path} each time it starts.").format(unit=unit.name, path=run),
        "# " + tr("A setting made here wins over the script's own; restart {unit} for it to count.").format(
            unit=unit.name),
        "",
        "",
        "# " + tr("{path} as it is:").format(path=run),
    ]
    lines += ["#" + (" " + line if line else "") for line in script.splitlines()]
    return "\n".join(lines) + "\n"


def edit_plan(unit: Unit) -> EditPlan:
    from navkit.i18n import tr

    where = _definition(unit.name) if valid_service(unit.name) else None
    if where is None:
        raise OSError(errno.ENOENT, tr("{unit} has no service directory").format(unit=unit.name), unit.name)
    run = where / "run"
    script = _read(run)
    if reads_conf(script):
        conf = where / "conf"
        if conf.exists():
            return EditPlan(conf)
        return EditPlan(conf, conf_text(unit, run, script), CONF_LINE)
    return EditPlan(run, warning=tr("{unit} reads no settings file, so its run script is edited: "
                                    "an update of its package may replace it.").format(unit=unit.name))


class Runit(Backend):
    """runit, through its directories and ``sv``."""

    name = "runit"
    title = "runit"
    verbs = VERBS
    restart_after_edit = True
    states_need_root = True

    def refusal(self) -> str:
        return refusal()

    def valid_name(self, name: str) -> bool:
        return valid_service(name)

    def installed(self, name: str) -> bool:
        """A definition by that name: nothing else is linked or run."""
        return _definition(name) is not None

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

    def states(self) -> dict[str, tuple[str, str]]:
        return states()


BACKEND = Runit()
