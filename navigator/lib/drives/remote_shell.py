"""Utilities > *Remote shell*: what DOS Navigator's ``cmTerminal`` became.

DN's *Terminal* talked to a modem.  Here it is a login shell on the server a
panel is browsing over SFTP: ``ssh -t`` run in a command window
(``TerminalWindow``), starting in the panel's directory there.

Nothing but the site's own host, user and port is passed: ``ssh`` reads
``~/.ssh/config`` -- HostName, Port, User, IdentityFile, ProxyJump -- just as
:func:`navigator.lib.drives.credentials.host_config` does for the SFTP drive,
so both reach the same machine as the same user.  A password or passphrase is
asked by ``ssh`` itself, in the window, which is a real terminal.
"""

from __future__ import annotations

import os
import shlex
import shutil
from pathlib import PurePosixPath

from navigator.lib.drives.location import Location, Site

#: The schemes whose servers take an SSH login.
SCHEMES = frozenset({"sftp"})


#: The status ``ssh`` exits with when it fails itself -- refused, unreachable,
#: authentication failed -- rather than passing on the remote shell's.
SSH_FAILED = 255


def ended_well(status: int) -> bool:
    """Whether a Remote shell that ended with wait *status* closes its window:
    ``ssh`` exited -- Ctrl+D or ``exit`` there, with whatever status the
    remote shell's last command left -- and not with its own failure, nor by
    a signal, either of which the window stays to show."""
    return os.WIFEXITED(status) and os.WEXITSTATUS(status) != SSH_FAILED


def program() -> str | None:
    """Where the ``ssh`` command is, or None when OpenSSH's client is not installed."""
    return shutil.which("ssh")


def target(location: Location | None) -> Location | None:
    """The directory on an SSH server *location* stands for, or None.

    Inside an archive opened on the server (``arc``, stacked on the file it
    was opened from), that archive's directory: the shell cannot enter it.
    """
    inside = False
    while location is not None and location.site.scheme == "arc":
        location, inside = location.outer, True
    if location is None or location.site.scheme not in SCHEMES:
        return None
    if inside:
        return Location(location.site, PurePosixPath(location.path).parent)
    return location


def login(site: Site) -> str:
    """*site* as ``ssh`` would be told it, for a title: ``user@host:port``."""
    user = f"{site.user}@" if site.user else ""
    host = f"[{site.host}]" if ":" in site.host and site.port else site.host
    port = f":{site.port}" if site.port else ""
    return f"{user}{host}{port}"


def command(location: Location) -> str:
    """The command line that logs in to *location*'s server and starts a
    login shell in its directory -- or the home directory, if that one has
    gone -- quoted for the local ``sh -c`` and the remote shell both.  With
    no directory (``profiles.HOME``, ``.``) the shell starts where ``ssh``
    puts it, the home directory."""
    site = location.site
    remote = 'exec "${SHELL:-/bin/sh}" -l'
    if str(location.path) not in ("", "."):
        remote = f"cd {shlex.quote(str(location.path))} 2>/dev/null; {remote}"
    words = ["ssh", "-t"]
    if site.port:
        words += ["-p", str(site.port)]
    if site.user:
        words += ["-l", site.user]
    words += ["--", site.host, remote]
    return shlex.join(words)
