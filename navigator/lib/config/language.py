"""Which language Navigator speaks, and where its catalogues are.

:mod:`navkit.i18n` does the translating; this decides what it translates
into.  Precedence runs as everywhere else -- ``--language``, then
``navigator.ini``'s ``[interface] language``, then the environment
(``$LC_ALL``, ``$LC_MESSAGES``, ``$LANG``), then English -- and a language
with no catalogue is English.  Changing it in Options > Interface sets the
setting, which wins over the flag from then on.
"""

from __future__ import annotations

import os
from pathlib import Path

from navkit.i18n import LOCALE, SOURCE, languages, register_directory, register_package

#: What the setting holds for "follow the environment".
AUTOMATIC = ""

#: Beside ``navigator.ini``: the user's own catalogues, ahead of the shipped
#: ones -- a translation finished or corrected without reinstalling.
DIRECTORY = "locales"


def install(config: Path) -> None:
    """Register the shipped catalogues, then the user's beside *config*."""
    register_package("navml.locales")
    register_package("navigator.locales")
    register_directory(config / DIRECTORY)


def from_environment() -> str:
    """The language the environment asks for, as POSIX spells it: ``lv_LV``."""
    for name in ("LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(name, "")
        if value:
            return value.split(".")[0].split("@")[0]
    return SOURCE


def resolve(code: str) -> str:
    """*code* as a language a catalogue exists for: itself, its bare language
    (``lv_LV`` to ``lv``), or English.  Automatic asks the environment."""
    wanted = code or from_environment()
    known = languages()
    for candidate in (wanted, wanted.split("_")[0]):
        if candidate in known:
            return candidate
    return SOURCE


def apply(code: str) -> None:
    """Speak *code* (or what automatic resolves to) from now on."""
    LOCALE.code = resolve(code)
