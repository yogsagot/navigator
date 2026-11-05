"""Utilities > Services' model: the system's services, through its service manager.

**Not DOS Navigator's**: a departure, asked for.  DOS had no service manager
and DN nothing to list; this is the Process list's sibling, a window of the
system's services that starts, stops, restarts, reloads, enables and disables
them -- through the root helper when the user may not -- follows a service's
log in the F3 viewer and edits how it is set up with F4.

**One interface, a backend per manager** (:class:`common.Backend`): systemd
(:mod:`.systemd`), OpenRC (:mod:`.openrc`), runit (:mod:`.runit`) and SysVinit
(:mod:`.sysvinit`).  :func:`current` picks the one running this system --
systemd when ``/run/systemd/system`` is there, else OpenRC when ``/run/openrc``
is, else runit when it is the first process, else SysVinit when ``init`` is
and ``/etc/inittab`` is there (Gentoo and Devuan run OpenRC under a sysvinit
``init``, which is why it is asked last) -- unless ``[services] manager``
names one.
The window calls only the functions here, which hand each service to the
backend that read it; what a backend has not (masking, user
services) is greyed by the window from the backend's attributes.

**What may be done is a closed list per backend** (``verbs``), and a name is
checked (``valid_name``) before it reaches an argument list: the root
helper's ``service`` op checks both again, as its ``kill`` checks a pid.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from navigator.lib.system.services import common, openrc, runit, systemd, sysvinit
from navigator.lib.system.services.common import (
    UNKNOWN, Backend, EditPlan, Follower, Journal, LogFile, Unit, stop_process, with_states,
)

#: Every backend, by its name -- the root helper's closed list too.
BACKENDS: dict[str, Backend] = {backend.name: backend
                                for backend in (systemd.BACKEND, openrc.BACKEND, runit.BACKEND, sysvinit.BACKEND)}

#: ``[services] manager``'s choices.
MANAGERS = ("auto", *BACKENDS)

#: The columns the list sorts by.
SORTS = ("name", "active", "startup", "description")


def _chosen() -> str:
    from navigator.settings import SETTINGS

    try:
        chosen = str(SETTINGS.services.manager)
    except AttributeError:
        return "auto"
    return chosen if chosen in MANAGERS else "auto"


def current() -> Backend | None:
    """The backend running this system's services: the one ``[services]
    manager`` names, else the first that says it is the manager here."""
    chosen = _chosen()
    if chosen != "auto":
        return BACKENDS[chosen]
    for backend in BACKENDS.values():
        if not backend.refusal():
            return backend
    return None


def refusal_reason() -> str:
    """Why there are no services to list, or "" -- the menu entry's grey."""
    from navkit.i18n import tr

    chosen = _chosen()
    if chosen != "auto":
        return BACKENDS[chosen].refusal()
    if current() is None:
        return tr("No service manager Navigator knows runs here: systemd, OpenRC, runit or SysVinit")
    return ""


def available() -> bool:
    return not refusal_reason()


def backend_of(unit: Unit) -> Backend:
    """The backend that read *unit*."""
    return BACKENDS.get(unit.backend) or systemd.BACKEND


def journal_lines() -> int:
    """``[services] journal_lines``: how much of a log F3 shows before following it."""
    from navigator.settings import SETTINGS

    try:
        return max(0, int(SETTINGS.services.journal_lines))
    except (AttributeError, TypeError, ValueError):
        return 200


# -- what the window calls ----------------------------------------------------------------------


def gather(user: bool = False, all_types: bool = False) -> list[Unit]:
    """Every service the current manager has.  Raises ``OSError``."""
    import errno

    backend = current()
    if backend is None:
        raise OSError(errno.ENOENT, refusal_reason())
    return backend.gather(user and backend.user_scope, all_types and backend.all_types)


def act(unit: Unit, verb: str) -> None:
    """*verb* done to *unit* as the user.  Raises ``OSError`` -- ``EPERM`` when refused."""
    backend_of(unit).act(unit, verb)


def details(unit: Unit) -> str:
    return backend_of(unit).details(unit)


def log(unit: Unit) -> Journal | LogFile:
    """What F3 follows for *unit*.  Raises ``OSError`` when there is nothing."""
    return backend_of(unit).log(unit)


def edit_plan(unit: Unit) -> EditPlan:
    """What F4 opens for *unit*.  Raises ``OSError`` when there is nothing to edit."""
    return backend_of(unit).edit_plan(unit)


def after_edit(unit: Unit) -> None:
    """What makes an edit of *unit*'s count, as the user (systemd's daemon-reload)."""
    backend_of(unit).after_edit(unit.user)


# -- sorting and the filter -------------------------------------------------------------------


def sort_key(by: str) -> Any:
    if by == "active":
        return lambda unit: (unit.active, unit.sub)
    if by == "startup":
        return lambda unit: unit.startup
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


__all__ = [
    "BACKENDS", "MANAGERS", "SORTS", "UNKNOWN", "Backend", "EditPlan", "Follower", "Journal", "LogFile", "Unit",
    "act", "after_edit", "available", "backend_of", "common", "current", "details", "edit_plan", "gather",
    "journal_lines", "log", "matches", "openrc", "ordered", "refusal_reason", "runit", "stop_process", "sysvinit",
    "systemd", "with_states",
]
