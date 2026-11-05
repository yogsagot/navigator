"""Which way a desktop notification goes, as ``[system] notifications`` says.

Not DN's, which had no desktop to tell.  navkit knows the ways
(:mod:`navkit.notify`) and guesses which this terminal shows
(``TerminalInfo.notifications``); the setting may take that guess, insist on
the terminal's sequence or on ``notify-send``, or turn it all off.  Whether
to notify at all -- only while the terminal has said it is in the background
-- is ``Shell.notify_away``'s.
"""

from __future__ import annotations

from navkit.capabilities import NOTIFY_NONE, NOTIFY_OSC9, NOTIFY_OSC777, NOTIFY_SEND


def method(setting: str, detected: str) -> str:
    """The navkit way for *setting* (one of ``settings.NOTIFICATIONS``), the
    terminal having been guessed to show *detected*.

    *Terminal* keeps the guess where it names a sequence, else sends OSC 9,
    the one most terminals that show any show.
    """
    if setting == "off":
        return NOTIFY_NONE
    if setting == "notify-send":
        return NOTIFY_SEND
    if setting == "terminal":
        return detected if detected in (NOTIFY_OSC9, NOTIFY_OSC777) else NOTIFY_OSC9
    return detected or NOTIFY_NONE
