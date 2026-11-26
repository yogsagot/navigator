"""Where a letter of another script sits on a US keyboard.

A shortcut is named after a Latin key -- Alt+X, Ctrl+O -- and a user typing
Hebrew, Arabic, Persian, Urdu or Georgian presses that same key with the
layout still switched to their own script.  kitty's keyboard protocol reports
the Latin key beside the letter (its *base layout key*); a legacy terminal
sends only the letter, as ``ESC`` + ``ס`` for Alt+X, and these tables are the
one way back to ``x``.  The same tables let a menu whose caption marks a
letter of that script open on a US keyboard: Alt+E for a Hebrew ``~ק~``.

The positions are the standard layouts' -- Israel's SI-1452, the Arabic (101)
layout, and the default variants X11's XKB ships for Iran (``ir``, ISIRI 9147),
Pakistan (``pk``, Urdu phonetic) and Georgia (``ge``) -- for the keys that type
a letter without Shift.  A key that types ASCII (Hebrew's ``q`` is ``/``)
already arrives as itself, and Arabic's lam-alef key types two characters,
which no single key event carries.

Persian and Urdu put letters Arabic also has on other keys (Arabic's ``د`` is
``]``, Persian's ``n``), and share letters with each other on different keys
too (``ی`` is Persian's ``d``, Urdu's ``i``), so no one table can hold them
all: the interface language picks its own, and every other letter is looked
up in the shared one (Hebrew, Arabic and Georgian, whose letters do not meet).
Russian, Armenian and the other scripts have no table: Alt with their own
layout types the marked letter itself, which a menu compares directly.
"""

from __future__ import annotations

from navkit import i18n


def _layout(letters: str, keys: str) -> dict[str, str]:
    return dict(zip(letters, keys, strict=True))


_HEBREW = _layout("קראטוןםפשדגכעיחלךףזסבהנמצתץ", "ertyuiopasdfghjkl;zxcvbnm,.")

_ARABIC = _layout("ضصثقفغعهخحجدذشسيبلاتنمكطئءؤرىةوزظ", "qwertyuiop[]`asdfghjkl;'zxcvnm,./")

_PERSIAN = _layout("ضصثقفغعهخحجچشسیبلاتنمکگظطزرذدپو", "qwertyuiop[]asdfghjkl;'zxcvbnm,")

_URDU = _layout("قوعرتےءیہپاسدفگحجکلزشچطبنم", "qwertyuiopasdfghjklzxcvbnm")

_GEORGIAN = _layout("ქწერტყუიოპასდფგჰჯკლზხცვბნმ", "qwertyuiopasdfghjklzxcvbnm")

#: The shared table: every letter here sits on one key whatever the language.
LATIN: dict[str, str] = _HEBREW | _ARABIC | _GEORGIAN

#: A language's own table, looked in before :data:`LATIN`.
LAYOUTS: dict[str, dict[str, str]] = {"fa": _PERSIAN, "ur": _URDU}


def latin(char: str) -> str | None:
    """The US key typing *char* on the layout of its script, or None: the
    interface language's own layout first (Persian's, Urdu's), then the
    shared one."""
    own = LAYOUTS.get(i18n.LOCALE.current.split("_")[0])
    if own is not None and char in own:
        return own[char]
    return LATIN.get(char)


def same_key(typed: str, mark: str) -> bool:
    """Whether *typed* is the key in the place of *mark*, a marked letter, on
    another layout: ``s`` for a Hebrew menu's ד, ס for a Latin ``x``."""
    return latin(typed) == mark or latin(mark) == typed
