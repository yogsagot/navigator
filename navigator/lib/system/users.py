"""A user's and a group's name by number, as a listing shows an owner.

Kept apart from :mod:`navigator.lib.file_ops.fileattr`, which re-exports
both: every panel's listing names owners, and importing Alt+E's whole model
(its ACLs, flags and the copier under it) for two lookups was a few
milliseconds of every start.
"""

from __future__ import annotations

import grp
import pwd


def user_name(uid: int) -> str:
    """*uid*'s name, or the number when it has none."""
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)


def group_name(gid: int) -> str:
    """*gid*'s name, or the number when it has none."""
    try:
        return grp.getgrgid(gid).gr_name
    except KeyError:
        return str(gid)
