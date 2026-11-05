"""Desktop notifications: a word to whoever is not looking at the terminal.

Two ways, as :attr:`navkit.capabilities.TerminalInfo.notifications` says.
The terminal's own -- OSC 9 or OSC 777 (:func:`navkit.terminal.notify_osc`)
-- travels with the session, so it reaches the desktop the terminal is on
over ssh and through tmux.  ``notify-send`` reaches this machine's desktop,
whatever the terminal makes of those sequences, and is the fallback where
the terminal is not known to show them.

Neither waits on anything: the sequence is a write to the tty, and
``notify-send`` runs as a child process that is reaped on the loop and never
waited for by the caller.  A failure -- the program missing, the bus down --
is not an error worth a box: the notification was a courtesy.
"""

from __future__ import annotations

import asyncio
import subprocess
from typing import Any

from navkit.capabilities import NOTIFY_NONE, NOTIFY_OSC9, NOTIFY_OSC777, NOTIFY_SEND
from navkit.terminal import _notify_text

#: The ways :func:`send` knows, by name.
METHODS = (NOTIFY_OSC9, NOTIFY_OSC777, NOTIFY_SEND, NOTIFY_NONE)

#: ``notify-send`` runs still being reaped, held so none is collected mid-way.
_RUNNING: set[asyncio.Task[None]] = set()


def send(app: Any, title: str, body: str, method: str, *, app_name: str = "") -> bool:
    """Put up a notification by *method*; whether one was sent on its way.

    *method* is one of :data:`METHODS`.  A terminal way goes through
    ``app.terminal`` (its ``notify``, told which sequence by its own info
    unless *method* names another); ``notify-send`` is started on *app*'s
    loop under *app_name*.
    """
    if method in (NOTIFY_OSC9, NOTIFY_OSC777):
        notify = getattr(app.terminal, "notify", None)
        if notify is None:
            return False
        return bool(notify(title, body, kind=method))
    if method == NOTIFY_SEND:
        loop = getattr(app, "_loop", None)
        if loop is None or loop.is_closed():
            return False
        task = loop.create_task(_notify_send(title, body, app_name))
        _RUNNING.add(task)
        task.add_done_callback(_RUNNING.discard)
        return True
    return False


async def _notify_send(title: str, body: str, app_name: str) -> None:
    argv = ["notify-send"]
    if app_name:
        argv.append(f"--app-name={_notify_text(app_name)}")
    argv += ["--", _notify_text(title) or app_name or "notify-send", _notify_text(body)]
    try:
        process = await asyncio.create_subprocess_exec(
            *argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        await process.wait()
    except (OSError, ValueError):
        pass
