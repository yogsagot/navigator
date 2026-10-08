"""Translated text: English is the key, one TOML catalogue per language.

DOS Navigator fetched every caption through ``GetString(dlTopName)`` from one
resource set per language (``RESOURCE/ENGLISH``, ``RESOURCE/RUSSIAN``).  This
keeps the one-file-per-language shape and drops the numbered ids: the English
text is the key, so a caption is written once, where it is used, and a
language that lacks it shows the English instead::

    tr("Make directory")
    tr_n("{n} file", "{n} files", count)

A catalogue is ``<code>.toml`` in any directory registered here -- a layer's
``locales`` package, then the user's own -- and later registrations win, entry
by entry::

    [meta]
    name = "Latviešu"

    [strings]
    "Make directory" = "Izveidot direktoriju"
    "~N~ame" = "~V~ārds"
    "{n} file" = ["{n} fails", "{n} faili", "{n} failu"]

**The hotkey belongs to the translator.**  A caption's ``~X~`` is part of the
string, so each language marks its own letter.

**Switching is live.**  :func:`tr` reads :data:`LOCALE`'s reactive ``code``, so
a binding or computed that calls it re-runs when the language changes -- which
is how a markup caption, emitted as ``_bind(lambda _o: _tr('...'))``, follows
Options without reopening anything.  Text formatted once and kept (a message
box, a status line built in a handler) is in the language of the moment it was
built.
"""

from __future__ import annotations

import tomllib
from collections.abc import Callable, Iterable
from importlib.resources import files
from pathlib import Path
from typing import Any

import threading

from navkit.reactive import reactive, untracked

#: The language English text is written in; it needs no catalogue.
SOURCE = "en"


class Locale:
    """The one holder of the current language, so :func:`tr` can be followed."""

    #: A catalogue's file stem: ``"lv"``, ``"ru"``, ``"en"``.
    code: str = reactive(SOURCE)
    #: The same, as a plain attribute: what a worker thread reads, since the
    #: reactive graph's reader stack is the loop's alone.
    current: str = SOURCE

    def _reactive_changed(self, name: str) -> None:
        with untracked():
            self.current = self.code


#: The current language.  Assign ``LOCALE.code`` to switch.
LOCALE = Locale()

#: Where catalogues are looked for, in increasing precedence.
_SOURCES: list[Path | Any] = []
#: Merged ``{text: translation}`` per language, built on first use.
_CACHE: dict[str, dict[str, Any]] = {}
#: The same, keyed and valued without hotkey marks -- see :func:`tr_plain`.
_PLAIN: dict[str, dict[str, str]] = {}


def register_package(package: str) -> None:
    """Look for catalogues in *package* (a ``locales`` package) as well."""
    _register(files(package))


def register_directory(path: Path) -> None:
    """Look for catalogues in *path* as well, ahead of every package."""
    _register(Path(path))


def _register(source: Any) -> None:
    if source not in _SOURCES:
        _SOURCES.append(source)
    _CACHE.clear()
    _PLAIN.clear()


def _files(code: str) -> Iterable[Any]:
    for source in _SOURCES:
        candidate = source.joinpath(f"{code}.toml")
        if candidate.is_file():
            yield candidate


def _read(candidate: Any) -> dict[str, Any]:
    """One catalogue, or nothing when it does not parse: English stands in."""
    try:
        return tomllib.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
        return {}


def catalogue(code: str) -> dict[str, Any]:
    """Every translation for *code*, merged across the registered places."""
    found = _CACHE.get(code)
    if found is None:
        found = {}
        if code != SOURCE:
            for candidate in _files(code):
                strings = _read(candidate).get("strings", {})
                found.update(
                    (key, value) for key, value in strings.items()
                    if value not in ("", [])
                )
        _CACHE[code] = found
    return found


def languages() -> dict[str, str]:
    """``{code: name}`` for every language a catalogue exists for, English first."""
    names = {SOURCE: "English"}
    for source in _SOURCES:
        try:
            entries = list(source.iterdir())
        except OSError:
            continue
        for entry in sorted(entries, key=lambda e: e.name):
            if entry.name.endswith(".toml") and entry.is_file():
                code = entry.name.removesuffix(".toml")
                meta = _read(entry).get("meta", {})
                names[code] = meta.get("name") or names.get(code) or code
    return names


def _code() -> str:
    """The current language, followed on the loop and merely read off it."""
    if threading.current_thread() is threading.main_thread():
        return LOCALE.code
    return LOCALE.current


def tr(text: str) -> str:
    """*text* in the current language, or *text* itself when none is known.

    Safe on a worker thread too, where it is simply not followed.
    """
    found = catalogue(_code()).get(text)
    if isinstance(found, list):
        found = found[0] if found else None
    return found if isinstance(found, str) else text


def tr_n(singular: str, plural: str, n: int, **values: Any) -> str:
    """The form for *n*, formatted with ``n`` and *values*.

    The catalogue's entry is keyed by *singular* and holds the language's
    forms in the order its rule numbers them; a single string serves for all.
    """
    code = _code()
    found = catalogue(code).get(singular)
    if isinstance(found, str):
        text = found
    elif isinstance(found, list) and found:
        text = found[min(plural_form(code, n), len(found) - 1)]
    else:
        text = singular if n == 1 else plural
    return text.format(n=n, **values)


def tr_plain(text: str) -> str:
    """*text*'s translation looked up and returned without hotkey marks.

    What finds a menu entry by its caption: an anchor is written in English
    with no tildes (``"Make directory"``) while the key carries them.
    """
    code = _code()
    plain = _PLAIN.get(code)
    if plain is None:
        plain = {
            key.replace("~", ""): value.replace("~", "")
            for key, value in catalogue(code).items()
            if isinstance(value, str)
        }
        _PLAIN[code] = plain
    bare = text.replace("~", "")
    return plain.get(bare, bare)


def tr_noop(text: str) -> str:
    """*text* unchanged, marked for ``tools/i18n.py`` as a key.

    For a table of captions kept in English and translated where it is shown
    (``tr(entry.title)``): the extractor sees only literal arguments, and this
    is how a table's literals become them.
    """
    return text


# -- plural rules ------------------------------------------------------------


def _english(n: int) -> int:
    return 0 if n == 1 else 1


def _latvian(n: int) -> int:
    # one (..1 but not ..11), other, zero (..0 and ..11-..19): "1 fails",
    # "2 faili", "10 failu".
    if n % 10 == 1 and n % 100 != 11:
        return 0
    if n == 0 or n % 10 == 0 or 11 <= n % 100 <= 19:
        return 2
    return 1


def _slavic(n: int) -> int:
    if n % 10 == 1 and n % 100 != 11:
        return 0
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return 1
    return 2


def _single(n: int) -> int:
    return 0


#: The index into a catalogue's list of forms, per language.  A language not
#: named here counts like English.
PLURAL_RULES: dict[str, Callable[[int], int]] = {
    "en": _english,
    "lv": _latvian,
    "ru": _slavic,
    "uk": _slavic,
    "be": _slavic,
    "ja": _single,
    "zh": _single,
    "ko": _single,
}


def plural_form(code: str, n: int) -> int:
    """Which of *code*'s forms *n* takes."""
    return PLURAL_RULES.get(code.split("_")[0], _english)(abs(n))
