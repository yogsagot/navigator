"""Options > Save desktop / Load desktop: DOS Navigator's ``SaveDesktop`` and
``RetrieveDesktop`` (DNUTIL.PAS).

DN streamed every window object to ``DN.DSK`` and read them back.  Here a
desktop is a dict -- each window's kind, rectangle and the state worth
coming back to, bottom to top, and which was in front -- kept as JSON in the
database (:class:`~navigator.models.saved_desktop.SavedDesktop`).

What a window keeps:

- a **file manager** each panel's directory, view mode, order, hidden files,
  file mask, columns, *Display* boxes and the entry at its cursor; which
  panel was active, a side hidden, and a tree, quick view or information
  panel standing in for one.  A *Find:* listing is not kept: the panel comes
  back on the directory it was found from.
- an **editor** or a **viewer** its file (and the viewer its mode); the rest
  -- cursor, scroll -- is the file's own history's, which opening restores.
  SmartPad comes back as SmartPad.
- a **tree window** the directory it was on.
- the **calculator** its expression, and the **calendar** that it was open (on today again).

And whether the trash can shows, and where (``TTrashCan``).

A window that cannot be made again -- a file gone, a directory gone -- is
left out, and the rest come back.  Startup's *Autosave desktop* saves one on
the way out and restores it at the next start (``Navigator``).
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

#: What a desktop is saved under, as DN's was ``DN.DSK``.
DEFAULT = "default"

#: The version of the dict's shape; a desktop of another is not read.
VERSION = 1


# -- what is kept --------------------------------------------------------------------------


def _panel(panel: Any) -> dict[str, Any]:
    entry = panel.selected
    found = panel.found
    return {
        "path": str(found.origin if found is not None else panel.path),
        "view_mode": panel.view_mode,
        "sort_mode": panel.sort_mode,
        "show_hidden": bool(panel.show_hidden),
        "file_mask": panel.file_mask,
        "columns": sorted(panel.columns),
        "display": sorted(panel.display) if panel.display is not None else None,
        "cursor": entry.name if entry is not None and found is None else None,
    }


def _window(window: Any) -> dict[str, Any] | None:
    """*window*'s entry, or None for one that is not kept."""
    from navigator.file_history import window_values
    from navigator.widgets.editor.edit_window import EditWindow
    from navigator.widgets.manager.manager import Manager
    from navigator.widgets.shell.calculator_window import CalculatorWindow
    from navigator.widgets.shell.calendar_window import CalendarWindow
    from navigator.widgets.tree.tree_window import TreeWindow
    from navigator.widgets.viewer.file_window import FileWindow

    kept: dict[str, Any] = {"rect": window_values(window)}
    if isinstance(window, Manager):
        replacement = window.replacement
        kept.update(
            kind="manager",
            left=_panel(window.left),
            right=_panel(window.right),
            active="right" if window.active_panel is window.right else "left",
            hidden=window.hidden_side,
            view={window.tree: "tree", window.quick: "quick", window.info: "info"}.get(replacement)
            if replacement is not None else None,
        )
    elif isinstance(window, EditWindow):
        if window.editor.path is None:
            return None
        kept.update(kind="editor", path=str(window.editor.path), smartpad=bool(window.smartpad))
    elif isinstance(window, FileWindow):
        if window.viewer.path is None:
            return None
        kept.update(kind="viewer", path=str(window.viewer.path), mode=window.viewer.mode)
    elif isinstance(window, TreeWindow):
        where = window.tree.selected_path
        kept.update(kind="tree", path=str(where) if where is not None else None,
                    hidden=bool(window.tree.show_hidden))
    elif isinstance(window, CalculatorWindow):
        kept.update(kind="calculator", expression=window.line.value)
    elif isinstance(window, CalendarWindow):
        kept.update(kind="calendar")
    else:
        return None
    return kept


def snapshot(desktop: Any) -> dict[str, Any]:
    """*desktop*'s windows, bottom to top, and the one in front."""
    windows, front = [], None
    for window in desktop.windows():
        kept = _window(window)
        if kept is None:
            continue
        if window is desktop.active_window:
            front = len(windows)
        windows.append(kept)
    data: dict[str, Any] = {"version": VERSION, "windows": windows, "front": front}
    trash = getattr(desktop.parent, "trash", None)
    if trash is not None:
        # ``SaveDesktop`` wrote whether the trash can showed, and where.
        data["trash"] = {"shown": bool(trash.shown), "gap_x": trash.gap_x, "gap_y": trash.gap_y}
    return data


# -- the database ----------------------------------------------------------------------------


def save(desktop: Any, name: str = DEFAULT) -> None:
    """``SaveDesktop``: *desktop* kept under *name*, over what was there."""
    from navigator.models.saved_desktop import SavedDesktop

    data = json.dumps(snapshot(desktop))
    if SavedDesktop.where(name=name).update(data=data) == 0:
        SavedDesktop.create(name=name, data=data)


def load(name: str = DEFAULT) -> dict[str, Any] | None:
    """The desktop kept under *name*, or None for none, or one not read."""
    from navigator.models.saved_desktop import SavedDesktop

    row = SavedDesktop.get(name=name)
    if row is None:
        return None
    try:
        data = json.loads(row.data)
    except ValueError:
        return None
    return data if isinstance(data, dict) and data.get("version") == VERSION else None


# -- making it again ---------------------------------------------------------------------------


def _directory(text: Any) -> Path | None:
    path = Path(text) if text else None
    return path if path is not None and path.is_dir() else None


def _seed_panel(panel: Any, kept: dict[str, Any]) -> None:
    from navigator.widgets.manager.panel.panel import SORT_MODES

    if kept.get("view_mode") in ("simple", "detailed", "list"):
        panel.view_mode = kept["view_mode"]
    if kept.get("sort_mode") in SORT_MODES:
        panel.sort_mode = kept["sort_mode"]
    panel.show_hidden = bool(kept.get("show_hidden", panel.show_hidden))
    panel.file_mask = kept.get("file_mask") or panel.file_mask
    if isinstance(kept.get("columns"), list):
        panel.columns = frozenset(kept["columns"])
    if isinstance(kept.get("display"), list):
        panel.display = frozenset(kept["display"])
    if kept.get("cursor"):
        panel._return_to = kept["cursor"]


def _manager(desktop: Any, kept: dict[str, Any], dirs: tuple[Path, Path] | None) -> Any:
    from navigator.widgets.manager.manager import Manager

    left = dirs[0] if dirs else _directory(kept.get("left", {}).get("path")) or Path.cwd()
    right = dirs[1] if dirs else _directory(kept.get("right", {}).get("path")) or left
    manager = Manager(left, right)
    for side in ("left", "right"):
        panel_kept = dict(kept.get(side) or {})
        if dirs:
            panel_kept.pop("cursor", None)
        _seed_panel(getattr(manager, side), panel_kept)
    desktop.open(manager)
    active = manager.right if kept.get("active") == "right" else manager.left
    active.focus()
    view = {"tree": manager.tree, "quick": manager.quick, "info": manager.info}.get(kept.get("view"))
    if view is not None:
        manager.switch_view(view)
    if kept.get("hidden") in ("left", "right"):
        manager.hide_side(kept["hidden"])
    return manager


async def _make(desktop: Any, kept: dict[str, Any], dirs: tuple[Path, Path] | None) -> Any:
    """One window from *kept*, opened on *desktop*; None if it cannot be."""
    kind = kept.get("kind")
    if kind == "manager":
        return _manager(desktop, kept, dirs)
    if kind == "editor":
        if kept.get("smartpad"):
            from navigator.smartpad import open_smartpad

            return await open_smartpad(desktop)
        from navigator.file_history import open_editor

        return await open_editor(desktop, kept["path"])
    if kind == "viewer":
        from navigator.file_history import open_viewer

        return await open_viewer(desktop, kept["path"], kept.get("mode"))
    if kind == "tree":
        from navigator.widgets.tree.tree_window import TreeWindow

        return desktop.open(TreeWindow(start=_directory(kept.get("path")), hidden=kept.get("hidden", True)))
    if kind == "calculator":
        from navigator.widgets.shell.calculator_window import CalculatorWindow

        window = desktop.open(CalculatorWindow())
        window.line.value = kept.get("expression") or ""
        return window
    if kind == "calendar":
        from navigator.widgets.shell.calendar_window import CalendarWindow

        return desktop.open(CalendarWindow())
    return None


async def restore(desktop: Any, data: dict[str, Any], *,
                  dirs: tuple[Path, Path] | None = None, here: Path | None = None) -> list[Any]:
    """``RetrieveDesktop``: *data*'s windows opened on *desktop*, where they
    were, bottom to top, the one in front brought forward.  *dirs* are the
    command line's directories, given: the first file manager's panels go
    there.  The windows made, those that could be.

    *here* is the current directory, DN's DOS one: the active panel of the
    topmost file manager opens there unless Startup's *Preserve directory*
    is ticked -- ``TFilePanelRoot.Store`` wrote that panel's drive as nil
    otherwise, which read back as wherever DOS was.  Decided here rather than
    when saving, so the box can be changed either way after.
    """
    from navigator.file_history import place_window
    from navigator.settings import SETTINGS

    made: list[Any] = []
    front = data.get("front")
    in_front = None
    windows = list(data.get("windows") or [])
    managers = [index for index, kept in enumerate(windows)
                if isinstance(kept, dict) and kept.get("kind") == "manager"]
    if here is not None and managers and not SETTINGS.startup.preserve_directory \
            and not (dirs and managers[-1] == managers[0]):
        top = dict(windows[managers[-1]])
        side = "right" if top.get("active") == "right" else "left"
        top[side] = {**(top.get(side) or {}), "path": str(here), "cursor": None}
        windows[managers[-1]] = top
    for index, kept in enumerate(windows):
        try:
            window = await _make(desktop, kept, dirs)
        except (OSError, KeyError, TypeError, ValueError):
            window = None
        if window is None:
            continue
        if kept.get("kind") == "manager":
            dirs = None  # the command line's directories are the first manager's alone
        rect = kept.get("rect")
        if isinstance(rect, dict):
            place_window(window, SimpleNamespace(**rect))
        made.append(window)
        if index == front:
            in_front = window
    if in_front is not None:
        desktop.activate(in_front)
    trash, kept = getattr(desktop.parent, "trash", None), data.get("trash")
    if trash is not None and isinstance(kept, dict):
        trash.shown = bool(kept.get("shown"))
        trash.gap_x = max(0, int(kept.get("gap_x", 1)))
        trash.gap_y = max(0, int(kept.get("gap_y", 1)))
    return made
