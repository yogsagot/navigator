"""Every caption in every dialog and window, in a language: what does not fit.

A translation longer than its English is cut off silently -- the last letters
of a check box, a label, a drop-down choice or a button go past the edge of its
control.  This opens each dialog and window and measures every caption against
the room it is given:

* **the screenshot scenes** (``tools/screenshot.py``'s ``SCENES``): each stage
  opens its box as the picture does, with real contents, and what it opened is
  measured -- the box in front and every window on the desktop;
* **the rest**: every ``Dialog`` and ``Window`` subclass in navml and Navigator
  that no scene opened, made with no arguments (``FACTORIES`` for one that needs
  some) and opened over the desktop.

Run::

    ./venv/bin/python tools/fitcheck.py [--language CODE]... [--check]

with no ``--language`` every catalogue shipped and English.  It prints one line a
caption that does not fit, ``CODE Where: kind 'caption' needs N, has M``;
``--check`` exits 1 when there is any.  ``tests/test_dialog_fit.py`` runs the
second half (no scenes) in every language; ``tests/test_settings_fit.py`` the
Settings box.  A finding is fixed by giving the control the room where the box
has it, else by a shorter translation (the ``i18n`` skill, *A translation must fit*).
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import inspect
import pkgutil
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from navkit.bidi import display_width  # noqa: E402

#: The languages checked with no ``--language``: English and every catalogue.
LANGUAGES = ("en", "he", "ar", "ja", "lv", "ru", "zh", "de", "es", "fr", "pt", "uk", "pl", "it", "ko",
             "cs", "tr", "zh_TW", "nl", "sv", "da", "nb", "sk", "hr", "sr", "sl", "bg", "ro")

#: Scenes whose picture is no box with captions of its own (a panel, the
#: console, a menu): nothing for this check to measure.
NOT_BOXES = frozenset({
    "desktop", "file-menu", "panel", "panel-detailed", "completion", "console", "miller", "info-panel",
    "tree-panel", "quick-view", "open-archive", "trash", "user-menu", "bookmarks",
})

#: Classes left out of the bare pass: bases, the file manager, a window made
#: only on a running service's journal (a viewer, no captions of its own), and
#: the windows that read the machine as they open -- *Directory sizes* would
#: walk the directory it is started in, the user's home under a test -- which
#: the screenshot scenes open on made-up rows.
NOT_BARE = frozenset({
    "Dialog", "Window", "Manager", "JournalWindow",
    "UsageWindow", "ProcessWindow", "ServiceWindow", "MonitorWindow", "VolumesWindow",
})


def _plain(text: str | None) -> str:
    from navml.widgets.dialog.control.control import parse_shortcut

    return parse_shortcut(text or "")[0]


def _name_of(widget: Any) -> str:
    """*widget*'s id in its document: the attribute of the component above it
    that holds it (the generated half makes each child one), or ""."""
    node = widget.parent
    while node is not None:
        for name, value in vars(node).items():
            if value is widget and not name.startswith("_"):
                return name
        node = node.parent
    return ""


def clipped(widget: Any, where: str) -> list[str]:
    """What under *widget* is wider than the room it has.

    * a check box's or radio button's caption: its column's start, ``[x]`` and a
      blank, then the caption, against the cluster's width;
    * a drop-down choice against its line, a blank either side;
    * a button's caption against its face -- a caption too wide for the markers
      takes the whole face (``Button.crowded``), so only past that is it cut;
    * a one-row label or static text against its width.
    """
    from navml.widgets.dialog.button.button import Button
    from navml.widgets.dialog.choice_line.choice_line import ChoiceLine
    from navml.widgets.dialog.cluster.cluster import Cluster
    from navml.widgets.dialog.label import Label
    from navml.widgets.dialog.static_text import StaticText

    found: list[str] = []
    if not widget.visible or widget.width <= 0:
        return found
    named = _name_of(widget)
    if named:
        where = f"{where.split('#')[0]}#{named}"
    if isinstance(widget, Cluster):
        rows = max(1, widget.height)
        for index, item in enumerate(widget.items):
            need = widget.column_x(index // rows) + 4 + display_width(_plain(item))
            if need > widget.width:
                found.append(f"{where}: {type(widget).__name__} {_plain(item)!r} needs {need}, has {widget.width}")
    elif isinstance(widget, ChoiceLine):
        button = next((child for child in widget.parent.children if hasattr(child, "choices")), None)
        for choice in getattr(button, "choices", None) or []:
            if display_width(choice) > widget.width - 2:
                found.append(f"{where}: choice {choice!r} needs {display_width(choice)}, has {widget.width - 2}")
    elif isinstance(widget, Button):
        text = _plain(getattr(widget, "text", ""))
        face = widget.face[0]
        if text and display_width(text) > face:
            found.append(f"{where}: Button {text!r} needs {display_width(text)}, has {face}")
        return found  # its caption is drawn by the button, not by a child
    elif isinstance(widget, (Label, StaticText)) and widget.height <= 1:
        text = _plain(getattr(widget, "text", ""))
        if "\n" not in text and display_width(text) > widget.width:
            found.append(f"{where}: {type(widget).__name__} {text!r} needs {display_width(text)}, has {widget.width}")
    for child in widget.children:
        found.extend(clipped(child, where))
    return found


def boxes(app: Any) -> list[Any]:
    """What is open over the file manager: the box in front, overlays, windows."""
    found = []
    if app.modal is not None:
        found.append(app.modal)
    found.extend(child for child in app.root.children[1:]
                 if child is not app.modal and type(child).__name__ != "Desktop")
    found.extend(window for window in app.shell.desktop.windows() if type(window).__name__ != "Manager")
    return found


def classes() -> dict[str, type]:
    """Every ``Dialog`` and ``Window`` subclass navml and Navigator define, by name."""
    from navml.widgets.dialog.dialog import Dialog
    from navml.widgets.window import Window

    found: dict[str, type] = {}
    for package in ("navml.widgets", "navigator.widgets"):
        root = importlib.import_module(package)
        for info in pkgutil.walk_packages(root.__path__, package + "."):
            if info.name.endswith(("_nml", "__main__")):
                continue
            try:
                module = importlib.import_module(info.name)
            except Exception:  # noqa: BLE001 - a module that will not import has no box to check
                continue
            for name, value in vars(module).items():
                if (inspect.isclass(value) and issubclass(value, (Dialog, Window))
                        and value.__module__ == module.__name__):
                    found[name] = value
    return found


def _table_format() -> Any:
    from navigator.lib.viewer.table import Dialect
    from navigator.widgets.viewer.table_format_dialog import TableFormatDialog

    return TableFormatDialog(Dialect())


#: How a class that needs arguments is made for the bare pass.
FACTORIES: dict[str, Callable[[], Any]] = {"TableFormatDialog": _table_format}


async def open_and_measure(app: Any, names: list[str], where: str = "") -> tuple[list[str], dict[str, str]]:
    """Each class of *names* made and opened over *app*'s desktop, measured, and
    closed: the findings, and why any could not be opened."""
    from navml.widgets.window import Window

    every = classes()
    found: list[str] = []
    failed: dict[str, str] = {}
    for name in names:
        try:
            widget = FACTORIES[name]() if name in FACTORIES else every[name]()
        except Exception as error:  # noqa: BLE001 - reported, not fatal
            failed[name] = f"{type(error).__name__}: {error}"
            continue
        try:
            if isinstance(widget, Window):
                app.shell.desktop.open(widget)
            else:
                asyncio.create_task(widget.execute(app))
            await asyncio.sleep(0.08)
            found.extend(clipped(widget, f"{where}{name}"))
            widget.close()
            await asyncio.sleep(0.03)
        except Exception as error:  # noqa: BLE001 - reported, not fatal
            failed[name] = f"open: {type(error).__name__}: {error}"
    return found, failed


# -- what is not a box: the menu bar, menus, the key bar, column headings ---------


def _submenus(menu: Any) -> list[Any]:
    """*menu*'s submenus, every level down."""
    from navml.widgets.menu.sub_menu import SubMenu

    found = []
    for entry in menu.entries():
        if isinstance(entry, SubMenu):
            found.append(entry)
            found.extend(_submenus(entry))
    return found


def chrome(app: Any, where: str) -> list[str]:
    """What the screen's own lines cut, with the window in front as it is:
    an entry of the menu bar run under the clock or off the edge, a menu box
    wider than the screen, an F-key the key bar leaves out for want of room."""
    from navml.widgets.menu.menu_box.menu_box import MenuBox
    from navigator.widgets.shell.keybar.keybar import FKEY, _label

    found: list[str] = []
    bar = app.shell.menu
    entries = bar.entries()
    if entries:
        start, width = bar.item_span(len(entries) - 1)
        if start + width > bar.width - bar.reserve:
            found.append(f"{where}: menu bar ends at {start + width}, has {bar.width - bar.reserve}")
    behind = app.focused
    for menu in [entry for entry in entries if hasattr(entry, "entries")]:
        for each in [menu, *_submenus(menu)]:
            width, _height = MenuBox.measure(each, app, behind)
            if width > app.shell.width:
                found.append(f"{where}: menu {_plain(each.text)!r} needs {width}, has {app.shell.width}")
    keybar = app.shell.keybar
    shown = {key for key, *_ in keybar.items()}
    for key, command in keybar._row():
        if FKEY.fullmatch(_label(key, command)) and key not in shown:
            found.append(f"{where}: key bar leaves out {_label(key, command)}")
    return found


def headings() -> list[str]:
    """Each detailed-mode column heading against its fixed width."""
    from navigator.widgets.manager.panel import Panel

    found = []
    for key, (_english, width, _attribute) in Panel.DETAIL_COLUMNS.items():
        text = Panel.heading(key)
        if width is not None and key != "links" and display_width(text) > width:
            found.append(f"panel heading {key}: {text!r} needs {display_width(text)}, has {width}")
    return found


async def chrome_everywhere(app: Any, scratch: Path = Path(".")) -> list[str]:
    """:func:`chrome` on the file manager, then with a viewer and an editor in
    front, on a file of text written in *scratch*."""
    from navigator.lib.config.file_history import open_editor, open_viewer

    # The real key bar: the screenshots pin the file panel's line on the
    # instance, which would measure that line in a viewer and an editor too.
    app.__dict__.pop("bindings", None)
    found = chrome(app, "panels") + headings()
    text = scratch / "chrome-check.txt"
    text.write_text("A line of text.\n")
    for name, opening in (("viewer", open_viewer), ("editor", open_editor)):
        window = await opening(app.shell.desktop, text)
        await asyncio.sleep(0.1)
        found.extend(chrome(app, name))
        window.close()
        await asyncio.sleep(0.05)
    return found


def check_language(code: str) -> list[str]:
    """Every finding in *code*: the scenes', then the bare pass's."""
    from tools import screenshot

    found: list[str] = []
    seen: set[str] = set()
    for scene in screenshot.SCENES:
        if scene.name in NOT_BOXES:
            continue

        async def measured(app: Any, stage: Any = scene.stage, name: str = scene.name) -> Any:
            keep = await stage(app)
            await asyncio.sleep(0.1)
            for box in boxes(app):
                seen.add(type(box).__name__)
                found.extend(clipped(box, f"{name}/{type(box).__name__}"))
            return keep

        try:
            screenshot.paint(screenshot.Scene(scene.name, measured, scene.size), "default", None, code)
        except Exception as error:  # noqa: BLE001 - one scene's failure is reported, the rest go on
            found.append(f"{scene.name}: the scene failed, {type(error).__name__}: {error}")

    bare = sorted(set(classes()) - seen - NOT_BARE)
    failures: dict[str, str] = {}

    async def stage(app: Any) -> None:
        more, why = await open_and_measure(app, bare)
        found.extend(more)
        failures.update(why)
        return None

    screenshot.paint(screenshot.Scene("bare", stage, screenshot.WIDE), "default", None, code)

    async def lines(app: Any) -> None:
        found.extend(await chrome_everywhere(app))
        return None

    # The screen's own lines at 80 columns, the narrowest Navigator is used in.
    screenshot.paint(screenshot.Scene("chrome", lines, (80, 24)), "default", None, code)
    found.extend(f"{name}: could not be opened, {why}" for name, why in sorted(failures.items()))
    # One finding once: a box several scenes open is measured each time.
    return list(dict.fromkeys(found))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--language", action="append", metavar="CODE",
                        help="check this language (repeatable); default: English and every catalogue")
    parser.add_argument("--check", action="store_true", help="exit 1 if any caption does not fit")
    args = parser.parse_args(argv)
    total = 0
    for code in args.language or LANGUAGES:
        for line in check_language(code):
            print(f"{code} {line}")
            total += 1
    return 1 if args.check and total else 0


if __name__ == "__main__":
    sys.exit(main())
