"""What the terminal's window or tab is called: ``user@host ~/dir — Navigator``.

The pieces a shell's own title is made of (bash's ``\\u@\\h: \\w``), so a tab
running Navigator on another machine over ssh still says which one, followed
by the active panel's directory the way a shell's follows ``cd``.  Built here
because the title the shell had set cannot be read back (see
``navkit.terminal.Terminal.set_title``).  A departure: DOS had no title bar.
"""

from __future__ import annotations

import functools
import getpass
import os
import socket
from pathlib import Path


@functools.cache
def user_host() -> str:
    """``user@host``, the host cut at its first dot as bash's ``\\h`` is."""
    try:
        user = getpass.getuser()
    except (KeyError, OSError):
        user = str(os.getuid())
    host = socket.gethostname().split(".", 1)[0]
    return f"{user}@{host}"


def tilde(where: Path | str) -> str:
    """*where* with the home directory at its start written ``~``, as a shell's prompt does."""
    shown = str(where)
    home = os.path.expanduser("~")
    if home != "/" and (shown == home or shown.startswith(home + os.sep)):
        shown = "~" + shown[len(home):]
    return shown


def window_title(where: Path | None) -> str:
    """The title for a session whose active panel is in *where*, if anywhere."""
    if where is None:
        return f"{user_host()} — Navigator"
    return f"{user_host()} {tilde(where)} — Navigator"
