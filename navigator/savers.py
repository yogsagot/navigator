"""Screen savers: DOS Navigator's ``Idlers`` unit (IDLERS.PAS) and its
Options > Configuration > Screen savers (``TSaversDialog``, SETUPS.PAS).

DN's four savers are built in -- *Star flight*, *Flash-light*, *Clock* and
*Blackness* (:class:`navigator.widgets.shell.screen_saver.ScreenSaver`) --
and beside them it offered the programs in its ``SSAVERS`` directory.  Here
that directory is ``savers/`` beside ``navigator.ini``: every executable file
in it is offered by its name, and run on the console as a command is, until
it exits (``CallExternalSaver``) -- ``cmatrix`` or ``asciiquarium`` will do.

One of the selected savers, at random, comes after *Time* minutes without a
key or a click (``InsertIdler``), or at once from ≡ > Screen rest; with *Use
mouse*, the pointer parked in the screen's top right corner calls one and in
its bottom right corner keeps one away.
"""

from __future__ import annotations

import os
from pathlib import Path

from navkit.i18n import tr

from navigator.settings import config_dir

#: The built-in savers by name.
BUILT_IN: tuple[str, ...] = ("star_flight", "flash_light", "clock", "blackness")


def built_in_captions() -> dict[str, str]:
    """The built-in savers' captions in DN's dialog, the bullet marking them
    as DN's own (``#249``)."""
    return {
        "star_flight": tr("∙ Star flight"),
        "flash_light": tr("∙ Flash-light"),
        "clock": tr("∙ Clock"),
        "blackness": tr("∙ Blackness"),
    }

#: *Time*'s choices in seconds; ``never`` is none.
DELAYS = {"never": None, "1": 60.0, "2": 120.0, "5": 300.0, "10": 600.0}


def savers_dir() -> Path:
    """Where external savers are looked for: ``savers/`` beside ``navigator.ini``."""
    return config_dir() / "savers"


def external() -> list[str]:
    """The executable files in :func:`savers_dir`, by name.  Touches the disk."""
    try:
        entries = sorted(os.scandir(savers_dir()), key=lambda e: e.name)
    except OSError:
        return []
    return [e.name for e in entries if e.is_file() and os.access(e.path, os.X_OK)]


def caption(name: str) -> str:
    """What the dialog lists *name* as."""
    return built_in_captions().get(name, name)


def name_of(caption_text: str) -> str:
    """The name a dialog caption stands for."""
    for name, text in built_in_captions().items():
        if text == caption_text:
            return name
    return caption_text
