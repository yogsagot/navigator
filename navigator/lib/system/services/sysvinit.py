"""Utilities > Services' SysVinit backend: the scripts in ``/etc/init.d``,
their ``rc?.d`` links, and ``update-rc.d`` or ``chkconfig`` (Devuan, Debian
or old Red Hat with sysvinit as the first process).

**SysVinit has no list and no states**: a service is an executable script
in ``/etc/init.d`` (``/etc/rc.d/init.d`` on old Red Hat), described by its LSB
header (``### BEGIN INIT INFO``) or Red Hat's ``# description:``; it starts in
the runlevels whose ``rc<N>.d`` holds an ``S<NN><name>`` link to it.  Its state
is only its own ``status`` action's exit code (LSB: 0 running, 1 and 2 dead
with a pid or lock file left, 3 stopped, 4 unknown) -- a process per script,
run :data:`PARALLEL` at once, each given up on after :data:`STATUS_TIMEOUT`
seconds, which is why the window reads it at most every :attr:`refresh_floor`.

**Safety, which matters more here than with any other manager**:

- The scripts that halt, reboot or take the system down are never listed
  (:data:`HIDDEN`, and any whose LSB header starts it only in runlevels 0 or 6):
  F5 on ``halt`` must not be possible.
- ``status`` is run only on a script with a ``status`` case
  (:func:`has_status`): an old script that ignores its argument would start
  on any.  One without shows *unknown*, run never.
- The root helper runs only a script root owns and nobody else may write
  (:meth:`SysVinit.installed`): a script the user could change would be their
  code run as root.

Status code 4 (or a refusal said) is a state the user may not read
(``UNKNOWN``): the window reads those as root, as runit's.  The actions run
the script itself, never ``service``, which on some systems hands over to
systemd; their LSB code 4, *insufficient privilege*, is a refusal.  Enable and
disable are ``update-rc.d`` (Debian, Devuan) or ``chkconfig`` (Red Hat), and are
not offered with neither.

**F3**: ``/var/log/<name>.log`` when there is one -- found by the name alone,
and said so -- else the system log filtered to the name.  **F4**: the
``/etc/default/<name>`` (``/etc/sysconfig/<name>``) the script reads, seeded
with the script's settings when new; else the script itself, after saying an
update of its package may replace it.
"""

from __future__ import annotations

import errno
import os
import re
import shutil
import stat
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from navigator.lib.system.services import common
from navigator.lib.system.services.common import UNKNOWN, Backend, EditPlan, Journal, LogFile, Unit
from navigator.lib.system.which import which as _which

#: Where the scripts are, the first there.
INIT_DIRS = (Path("/etc/init.d"), Path("/etc/rc.d/init.d"))

#: Where ``rc<N>.d`` are: Debian's ``/etc/rc2.d``, Red Hat's ``/etc/rc.d/rc2.d``.
RC_BASES = (Path("/etc"), Path("/etc/rc.d"))

#: The runlevels a service's start-up is told by: multi-user ones, and ``S``, boot.
RUNLEVELS = ("S", "1", "2", "3", "4", "5")

#: What sysvinit's own file says.
INITTAB = Path("/etc/inittab")

#: Settings a script may read, Debian's then Red Hat's.
DEFAULTS = (Path("/etc/default"), Path("/etc/sysconfig"))

#: Where a log by the service's name is looked for.
LOG_DIR = Path("/var/log")

#: Never listed: not services, or what takes the system down.
HIDDEN = frozenset({
    "rc", "rcS", "rc.local", "README", "skeleton", "functions", "halt", "reboot", "single", "sendsigs",
    "killprocs", "umountfs", "umountnfs.sh", "umountroot", "killall", "netfs-shutdown",
})

#: The actions every script has.
SCRIPT_VERBS = ("start", "stop", "restart", "reload")

#: How long one script's ``status`` may take, and how many run at once.
STATUS_TIMEOUT = 3.0
PARALLEL = 8

#: Who must own a script the root helper runs.
OWNER = 0

#: A script's name: never an option, never a path.
SERVICE_NAME = re.compile(r"[A-Za-z0-9_@:+][A-Za-z0-9._@:+-]*")

#: A ``case`` that handles ``status``: ``status)``, ``status|``, ``"status")``...
_STATUS_CASE = re.compile(r"""(?m)(?:^|[\s|(])["']?status["']?\s*[|)]""")

#: How much of a script is read.
_SCRIPT_BYTES = 64 * 1024

#: The line of the seed the cursor starts on.
CONF_LINE = 3


def valid_service(name: str) -> bool:
    return len(name) <= 255 and SERVICE_NAME.fullmatch(name) is not None


def init_dir() -> Path | None:
    return next((where for where in INIT_DIRS if where.is_dir()), None)


def refusal() -> str:
    from navkit.i18n import tr

    if init_dir() is None:
        return tr("There is no /etc/init.d")
    if common.pid1() != "init" or not INITTAB.is_file():
        return tr("SysVinit is not the system's service manager")
    return ""


def _read(path: Path) -> str:
    try:
        with open(path, "rb") as handle:
            return handle.read(_SCRIPT_BYTES).decode("utf-8", "replace")
    except OSError:
        return ""


# -- the scripts --------------------------------------------------------------------------------


def header(script: str) -> dict[str, str]:
    """The LSB header's fields (``Short-Description``, ``Default-Start``...),
    with Red Hat's ``description`` and ``chkconfig`` where there is no LSB one."""
    fields: dict[str, str] = {}
    inside = False
    last = ""
    for line in script.splitlines():
        if line.startswith("### BEGIN INIT INFO"):
            inside = True
            continue
        if line.startswith("### END INIT INFO"):
            break
        if inside:
            match = re.match(r"^#\s*([A-Za-z-]+):\s*(.*)$", line)
            if match:
                last = match.group(1)
                fields[last] = match.group(2).strip()
            elif last and re.match(r"^#(\s{2,}|\t)", line):
                fields[last] = (fields[last] + " " + line[1:].strip()).strip()
    if not fields:
        for line in script.splitlines()[:40]:
            match = re.match(r"^#\s*(description|chkconfig):\s*(.*?)\s*\\?$", line)
            if match:
                fields.setdefault(match.group(1), match.group(2))
    return fields


def shutdown_only(fields: dict[str, str]) -> bool:
    """Whether a script's header starts it only to take the system down
    (halt, reboot): runlevels 0 and 6, or none, and stopped in 0 or 6."""
    if "Default-Start" not in fields and "Default-Stop" not in fields:
        return False
    starts = set(fields.get("Default-Start", "").split())
    stops = set(fields.get("Default-Stop", "").split())
    return starts <= {"0", "6"} and bool(stops & {"0", "6"})


def describe(fields: dict[str, str]) -> str:
    return fields.get("Short-Description") or fields.get("description") or fields.get("Description", "")


def has_status(script: str) -> bool:
    """Whether the script handles a ``status`` action -- the only ones asked."""
    return _STATUS_CASE.search(script) is not None


def scripts() -> dict[str, Path]:
    """Every service's script, by name: executable files, :data:`HIDDEN` and
    the shutdown-only left out."""
    where = init_dir()
    if where is None:
        return {}
    found = {}
    try:
        entries = sorted(where.iterdir())
    except OSError as error:
        raise OSError(error.errno, error.strerror, str(where)) from error
    for path in entries:
        name = path.name
        if (name in HIDDEN or not valid_service(name) or ".dpkg-" in name or name.endswith((".rpmnew", ".rpmsave"))
                or not path.is_file() or not os.access(path, os.X_OK)):
            continue
        if shutdown_only(header(_read(path))):
            continue
        found[name] = path
    return found


def _rc_dir(level: str) -> Path | None:
    return next((base / f"rc{level}.d" for base in RC_BASES if (base / f"rc{level}.d").is_dir()), None)


def startup_of(name: str) -> str:
    """The runlevels *name* starts in (``2, 3, 4, 5``, ``boot`` for ``S``), or ``disabled``."""
    levels = []
    for level in RUNLEVELS:
        where = _rc_dir(level)
        if where is None:
            continue
        try:
            linked = any(re.fullmatch(rf"S\d\d{re.escape(name)}", entry) for entry in os.listdir(where))
        except OSError:
            continue
        if linked:
            levels.append("boot" if level == "S" else level)
    return ", ".join(levels) or "disabled"


def _linked_at_all(name: str) -> bool:
    for level in ("0", *RUNLEVELS, "6"):
        where = _rc_dir(level)
        if where is None:
            continue
        try:
            if any(re.fullmatch(rf"[SK]\d\d{re.escape(name)}", entry) for entry in os.listdir(where)):
                return True
        except OSError:
            continue
    return False


# -- states -------------------------------------------------------------------------------------


def state_of(path: Path) -> tuple[str, str]:
    """*path*'s ``status``: ``running``, ``fail`` (dead, a pid or lock file
    left), ``stopped``, :data:`UNKNOWN` (code 4 or refused: root may know) or
    ``unknown`` (no status action, no answer, or one LSB does not have)."""
    if not has_status(_read(path)):
        return "unknown", "no status action"
    try:
        result = common.run([str(path), "status"], timeout=STATUS_TIMEOUT)
    except OSError:
        return "unknown", "no answer"
    said = (result.stdout + result.stderr).lower()
    if result.returncode == 0:
        return "running", ""
    if result.returncode in (1, 2):
        return "fail", "pid file left" if result.returncode == 1 else "lock file left"
    if result.returncode == 3:
        return "stopped", ""
    if result.returncode == 4 or any(words in said for words in common.REFUSALS):
        return UNKNOWN, ""
    return "unknown", f"status {result.returncode}"


def states() -> dict[str, tuple[str, str]]:
    """Every listed script's state, :data:`PARALLEL` at a time -- also the root
    helper's ``service_states``, which runs these fixed ``status`` actions."""
    found = scripts()
    if not found:
        return {}
    with ThreadPoolExecutor(max_workers=PARALLEL, thread_name_prefix="nav-sysv-status") as pool:
        return dict(zip(found, pool.map(state_of, found.values())))


def gather(user: bool = False, all_types: bool = False) -> list[Unit]:
    known = states()
    found = []
    for name, path in scripts().items():
        active, sub = known.get(name, ("unknown", ""))
        found.append(Unit(name, "", active, sub, startup_of(name), describe(header(_read(path))), False,
                          "sysvinit"))
    return found


# -- doing something to one -------------------------------------------------------------------


def enabler() -> str | None:
    """What enables a service here: ``update-rc.d``, ``chkconfig``, or None."""
    return next((tool for tool in ("update-rc.d", "chkconfig") if _which(tool)), None)


def verbs() -> tuple[str, ...]:
    return SCRIPT_VERBS + (("enable", "disable") if enabler() else ())


def _ran(argv: list[str], name: str) -> None:
    result = common.run(argv)
    if result.returncode == 0:
        return
    if result.returncode == 4:
        # LSB's "user had insufficient privilege".
        said = (result.stderr or result.stdout or "").strip().splitlines()
        raise OSError(errno.EPERM, said[-1] if said else os.strerror(errno.EPERM), name)
    raise common.failure(result, name)


def act(unit: Unit, verb: str) -> None:
    """*verb* done to *unit*: its script for what it is doing, ``update-rc.d``
    or ``chkconfig`` for whether it starts.  Raises ``OSError`` -- ``EPERM``
    when refused."""
    name = unit.name
    script = scripts().get(name) if valid_service(name) else None
    if verb not in verbs() or script is None:
        raise OSError(errno.EINVAL, "Not something Navigator does to a service", name)
    if verb in SCRIPT_VERBS:
        _ran([str(script), verb], name)
        return
    tool = enabler()
    if tool == "update-rc.d":
        if verb == "enable" and not _linked_at_all(name):
            _ran(["update-rc.d", name, "defaults"], name)
        _ran(["update-rc.d", name, verb], name)
    else:
        if verb == "enable":
            _ran(["chkconfig", "--add", name], name)
        _ran(["chkconfig", name, "on" if verb == "enable" else "off"], name)


def details(unit: Unit) -> str:
    from navkit.i18n import tr

    script = scripts().get(unit.name) if valid_service(unit.name) else None
    if script is None:
        raise OSError(errno.ENOENT, "Not a service's script", unit.name)
    text = _read(script)
    fields = header(text)
    lines = [unit.name + (" - " + describe(fields) if describe(fields) else "")]
    if has_status(text):
        try:
            result = common.run([str(script), "status"], timeout=STATUS_TIMEOUT)
            lines.append((result.stdout + result.stderr).strip() or tr("Status: {state}").format(state=unit.active))
        except OSError:
            lines.append(tr("Status: {state}").format(state=unit.active))
    else:
        lines.append(tr("{path} has no status action").format(path=script))
    lines.append(tr("Start-up: {state}").format(state=unit.startup))
    for key in ("Provides", "Required-Start", "Default-Start", "Default-Stop", "chkconfig"):
        if fields.get(key):
            lines.append(f"{key}: {fields[key]}")
    lines.append(tr("Script: {path}").format(path=script))
    return "\n".join(lines)


# -- F3 and F4 --------------------------------------------------------------------------------


def log(unit: Unit) -> LogFile:
    own = LOG_DIR / f"{unit.name}.log"
    if valid_service(unit.name) and own.is_file():
        return LogFile(own, guessed=True)
    return common.system_log(unit, "SysVinit")


def settings_file(name: str, script: str) -> Path | None:
    """The ``/etc/default/<name>`` or ``/etc/sysconfig/<name>`` the script
    reads -- it names that directory -- or None."""
    for where in DEFAULTS:
        if f"{where}/" in script:
            return where / name
    return None


def edit_plan(unit: Unit) -> EditPlan:
    from navkit.i18n import tr

    from navigator.lib.system.services.openrc import conf_text

    script = scripts().get(unit.name) if valid_service(unit.name) else None
    if script is None:
        raise OSError(errno.ENOENT, "Not a service's script", unit.name)
    text = _read(script)
    settings = settings_file(unit.name, text)
    if settings is not None:
        if settings.exists():
            return EditPlan(settings)
        return EditPlan(settings, conf_text(unit, script, text), CONF_LINE)
    return EditPlan(script, warning=tr("{unit} reads no settings file, so its script is edited: "
                                       "an update of its package may replace it or ask about it.").format(
        unit=unit.name))


class SysVinit(Backend):
    """SysVinit, through its scripts, their links and ``update-rc.d``/``chkconfig``."""

    name = "sysvinit"
    title = "SysVinit"
    restart_after_edit = True
    states_need_root = True
    refresh_floor = 15

    @property
    def verbs(self) -> tuple[str, ...]:  # type: ignore[override]
        """The script's actions, and enable/disable only with a tool for them."""
        return verbs()

    def refusal(self) -> str:
        return refusal()

    def valid_name(self, name: str) -> bool:
        return valid_service(name)

    def installed(self, name: str) -> bool:
        """A listed script root owns and nobody else may write: the only
        kind the root helper runs."""
        script = scripts().get(name)
        if script is None:
            return False
        try:
            info = os.stat(script)
        except OSError:
            return False
        return info.st_uid == OWNER and not info.st_mode & (stat.S_IWGRP | stat.S_IWOTH)

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


BACKEND = SysVinit()
