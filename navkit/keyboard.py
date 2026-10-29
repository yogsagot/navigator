"""Where a Hebrew or Arabic letter sits on a US keyboard.

A shortcut is named after a Latin key -- Alt+X, Ctrl+O -- and a user typing
Hebrew or Arabic presses that same key with the layout still switched to
their own script.  kitty's keyboard protocol reports the Latin key beside the
letter (its *base layout key*); a legacy terminal sends only the letter, as
``ESC`` + ``ס`` for Alt+X, and this table is the one way back to ``x``.

The positions are the standard layouts' -- Israel's SI-1452 and the Arabic
(101) layout every desktop ships -- for the keys that type a letter.  A key
that types ASCII on either (Hebrew's ``q`` is ``/``) already arrives as
itself, and Arabic's lam-alef key types two characters, which no single key
event carries.
"""

from __future__ import annotations

_HEBREW = dict(zip("קראטוןםפשדגכעיחלךףזסבהנמצתץ", "ertyuiopasdfghjkl;zxcvbnm,.", strict=True))

_ARABIC = dict(
    zip("ضصثقفغعهخحجدذشسيبلاتنمكطئءؤرىةوزظ", "qwertyuiop[]`asdfghjkl;'zxcvnm,./", strict=True)
)

LATIN: dict[str, str] = _HEBREW | _ARABIC


def latin(char: str) -> str | None:
    """The US key typing *char* on a Hebrew or Arabic layout, or None."""
    return LATIN.get(char)


def same_key(typed: str, mark: str) -> bool:
    """Whether *typed* is the key in the place of *mark*, a marked letter, on
    another layout: ``s`` for a Hebrew menu's ד, ס for a Latin ``x``."""
    return latin(typed) == mark or latin(mark) == typed
