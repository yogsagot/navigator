"""The desktop's clipboard, through the tools that own it.

A terminal application has two ways to reach a clipboard, and neither is
enough alone.  **OSC 52** asks the terminal to do it
(:func:`navkit.terminal.clipboard_osc`), which works over ssh and inside tmux
and needs nothing installed -- but VTE (GNOME Terminal, Tilix) and JetBrains'
JediTerm ignore it, and most terminals that honour a *write* refuse a *read*
or ask the user first.  **The desktop's own tools** -- ``wl-copy``/``wl-paste``
on Wayland, ``xclip`` or ``xsel`` on X -- work whatever the terminal, but only
on the machine whose display it is, and only if one is installed.

So a copy goes both ways (:meth:`Application.copy_to_clipboard`), and a paste
tries the tool first and asks the terminal only if there is none
(:meth:`Application.request_clipboard`).  Everything here blocks, briefly, and
is run in an executor; nothing here knows an application exists.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Callable, Mapping

#: How long a tool may take before it is given up on.  ``xclip`` serving a
#: selection forks and its parent returns at once; a tool that does not is
#: talking to a display that is not answering.
TIMEOUT = 2.0


def _tools(
    *, paste: bool, primary: bool, env: Mapping[str, str], which: Callable[[str], str | None]
) -> list[list[str]]:
    candidates: list[list[str]] = []
    if env.get("WAYLAND_DISPLAY"):
        if paste:
            candidates.append(["wl-paste", "--no-newline"] + (["--primary"] if primary else []))
        else:
            candidates.append(["wl-copy"] + (["--primary"] if primary else []))
    if env.get("DISPLAY"):
        selection = "primary" if primary else "clipboard"
        if paste:
            candidates.append(["xclip", "-selection", selection, "-o"])
            candidates.append(["xsel", "--primary" if primary else "--clipboard", "--output"])
        else:
            candidates.append(["xclip", "-selection", selection])
            candidates.append(["xsel", "--primary" if primary else "--clipboard", "--input"])
    return [argv for argv in candidates if which(argv[0])]


def copy_command(
    *,
    primary: bool = False,
    env: Mapping[str, str] | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> list[str] | None:
    """The command that puts its standard input on the clipboard, if there is one."""
    tools = _tools(paste=False, primary=primary, env=os.environ if env is None else env, which=which)
    return tools[0] if tools else None


def paste_command(
    *,
    primary: bool = False,
    env: Mapping[str, str] | None = None,
    which: Callable[[str], str | None] = shutil.which,
) -> list[str] | None:
    """The command that prints the clipboard, if there is one."""
    tools = _tools(paste=True, primary=primary, env=os.environ if env is None else env, which=which)
    return tools[0] if tools else None


def copy(text: str, *, primary: bool = False) -> bool:
    """Hand *text* to the desktop's clipboard tool; whether one took it."""
    argv = copy_command(primary=primary)
    if argv is None:
        return False
    try:
        result = subprocess.run(
            argv,
            input=text.encode("utf-8"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def paste(*, primary: bool = False) -> str | None:
    """What the desktop's clipboard holds, or None if no tool could say."""
    argv = paste_command(primary=primary)
    if argv is None:
        return None
    try:
        result = subprocess.run(
            argv,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", "replace")
