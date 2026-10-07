"""Utilities > Edit environment: DOS Navigator's ``EditDOSEvironment`` (MACRO.PAS).

DN edited DOS's master environment, which every program it started after
inherited.  Here there are two: Navigator's own (``os.environ``), which the
programs it starts take -- the external viewer and editor, the user menu's
script, a shell started anew -- and the console's shell, already running
with a copy of its own, which is told the changes in a line it runs unseen
(:meth:`navigator.subshell.Subshell.set_environment`).

A departure: names keep their case.  DN upper-cased them, as DOS's were.
"""

from __future__ import annotations

import os
from typing import Mapping


def valid_name(name: str) -> bool:
    """Whether *name* can be a variable's: something, without ``=`` or a NUL."""
    return bool(name) and "=" not in name and "\0" not in name


def changes(before: Mapping[str, str], after: Mapping[str, str]) -> dict[str, str | None]:
    """What turns *before* into *after*: each name set to its new value, or
    to None where it went."""
    found: dict[str, str | None] = {name: None for name in before if name not in after}
    found.update({name: value for name, value in after.items() if before.get(name) != value})
    return found


def apply(found: Mapping[str, str | None], environ: os._Environ[str] | dict[str, str] = os.environ) -> None:
    """*found* made so in *environ*, Navigator's own unless said."""
    for name, value in found.items():
        if value is None:
            environ.pop(name, None)
        else:
            environ[name] = value
