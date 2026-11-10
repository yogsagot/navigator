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
- an **editor** its file, and -- whatever *Track editing* says, as
  ``TFileEditor.Store`` wrote it -- its cursor, scroll, markers, margins and
  modes (``EditWindow.desktop_state``), put back over the file's own record.
  SmartPad comes back as SmartPad, without a new stamp (``Awaken`` only
  loaded the file).  A **viewer** its file and mode; the rest is the file's own
  history's, which opening restores.
- a **tree window** the directory it was on.
- a **database window** (dBase, SQLite, CSV) its file, the table or query,
  the cell, the scroll, the column widths, the F7 search and the code page
  or *Format* it is read with -- not an F8 sort, so it comes back in the
  file's order on the same record.  One on a copy fetched from another
  drive or as root is left out, as DN dropped a ``KillAfterUse`` file.
- the **calculator** its expression and its face, and the **calendar** that it was open (on today again), the calendar
  system and the view its menu chose.

And whether the trash can shows, and where (``TTrashCan``).

A window that cannot be made again -- a file gone, a directory gone -- is
left out, and the rest come back.  A departure for an editor's file: DN
reopened it empty under its name, which F2 would then save over a deleted
file's name.  Startup's *Autosave desktop* saves one on
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


def _panel_values(panel: Any) -> dict[str, Any]:
    """A panel's own settings, wherever it is: not those of a remembered
    directory it shows, which come back with the directory
    (``directory_settings``)."""
    own = panel.own_settings()
    return {
        "view_mode": own["view_mode"],
        "sort_mode": own["sort_mode"],
        "sort_reverse": bool(own["sort_reverse"]),
        "show_hidden": bool(own["show_hidden"]),
        "show_info": bool(panel.show_info),
        "file_mask": own["file_mask"],
        "columns": sorted(own["columns"]),
        "display": sorted(own["display"]) if own["display"] is not None else None,
    }


def _panel(panel: Any) -> dict[str, Any]:
    entry = panel.selected
    found = panel.found
    outer = panel.location.outer
    if outer is not None:
        # In an archive: kept as the directory it is in, the cursor on it --
        # where ``..`` at its root would have gone.
        return {**_panel_values(panel), "path": str(outer.parent), "cursor": outer.name,
                "local": str(panel.local_anchor.local)}
    return {
        "path": str(found.origin if found is not None else panel.location),
        # Where it falls back to, for a panel on another drive that is not
        # there to go back to.
        "local": str(panel.local_anchor.local) if not panel.location.is_local else None,
        **_panel_values(panel),
        "cursor": entry.name if entry is not None and found is None else None,
    }


def _miller(window: Any) -> dict[str, Any] | None:
    """Where Miller columns (Alt+F12) browse, or None while the panels show:
    the directory and its cursor, and the side the panels give it back to."""
    current = window.miller.current
    if current is None:
        return None
    entry = current.selected
    return {"path": str(current.location), "cursor": entry.name if entry is not None else None,
            "side": window._miller_side}


def _window(window: Any) -> dict[str, Any] | None:
    """*window*'s entry, or None for one that is not kept."""
    from navigator.lib.config.file_history import window_values
    from navigator.widgets.editor.edit_window import EditWindow
    from navigator.widgets.manager.manager import Manager
    from navigator.widgets.shell.calculator_window import CalculatorWindow
    from navigator.widgets.shell.calendar_window import CalendarWindow
    from navigator.widgets.shell.volumes_window import VolumesWindow
    from navigator.widgets.tree.tree_window import TreeWindow
    from navigator.widgets.viewer.db_window import DBWindow
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
            split=window.split,
            view={window.tree: "tree", window.quick: "quick", window.info: "info"}.get(replacement)
            if replacement is not None else None,
            miller=_miller(window),
        )
    elif isinstance(window, EditWindow):
        if window.editor.path is None:
            return None
        kept.update(kind="editor", path=str(window.editor.path), smartpad=bool(window.smartpad),
                    state=window.desktop_state())
    elif isinstance(window, FileWindow):
        if window.viewer.path is None:
            return None
        kept.update(kind="viewer", path=str(window.viewer.path), mode=window.viewer.mode)
    elif isinstance(window, TreeWindow):
        where = window.tree.selected_path
        kept.update(kind="tree", path=str(where) if where is not None else None,
                    hidden=bool(window.tree.show_hidden))
    elif isinstance(window, CalculatorWindow):
        kept.update(kind="calculator", expression=window.line.value, mode=window.mode)
    elif isinstance(window, CalendarWindow):
        kept.update(kind="calendar", calendar=window.chosen, view=window.display)
    elif isinstance(window, VolumesWindow):
        kept.update(kind="volumes", all=bool(window.show_all), free=bool(window.show_free))
    elif isinstance(window, DBWindow):
        state = window.kept_state()
        if state is None:
            return None
        kept.update(state, kind="database")
    else:
        return None
    return kept


def snapshot(desktop: Any) -> dict[str, Any]:
    """*desktop*'s windows, bottom to top, and the one in front."""
    windows, front = [], None
    #: Each text's first kept window, by its buffer: a later window on the
    #: same text (Window > *New view*) is kept as a view of it.
    first_of: dict[int, int] = {}
    for window in desktop.windows():
        kept = _window(window)
        if kept is None:
            continue
        buffer = getattr(getattr(window, "editor", None), "buffer", None)
        if kept.get("kind") == "editor" and buffer is not None:
            if id(buffer) in first_of:
                kept["view_of"] = first_of[id(buffer)]
            else:
                first_of[id(buffer)] = len(windows)
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
    if isinstance(text, str) and "://" in text:
        return None  # another drive's: see _remote
    path = Path(text) if text else None
    return path if path is not None and path.is_dir() else None


def _remote(kept: dict[str, Any]) -> Any:
    """The place on another drive a kept panel was on, or None."""
    from navigator.lib.drives import Location

    text = kept.get("path")
    if not isinstance(text, str) or "://" not in text:
        return None
    location = Location.parse(text)
    return None if location.is_local else location


def _seed_panel(panel: Any, kept: dict[str, Any]) -> None:
    from navigator.widgets.manager.panel.panel import SORT_MODES

    # Onto the panel's own settings, and the directory's record over them again.
    panel.drop_directory_settings()
    if kept.get("view_mode") in ("simple", "detailed", "list"):
        panel.view_mode = kept["view_mode"]
    if kept.get("sort_mode") in SORT_MODES:
        panel.sort_mode = kept["sort_mode"]
    panel.sort_reverse = bool(kept.get("sort_reverse", panel.sort_reverse)) and panel.sort_mode != "unsorted"
    panel.show_hidden = bool(kept.get("show_hidden", panel.show_hidden))
    panel.show_info = bool(kept.get("show_info", panel.show_info))
    panel.file_mask = kept.get("file_mask") or panel.file_mask
    if isinstance(kept.get("columns"), list):
        panel.columns = frozenset(kept["columns"])
    if isinstance(kept.get("display"), list):
        panel.display = frozenset(kept["display"])
    panel.settle_directory()
    if kept.get("cursor"):
        panel._return_to = kept["cursor"]


def _manager(desktop: Any, kept: dict[str, Any], dirs: tuple[Path, Path] | None) -> Any:
    from navigator.widgets.manager.manager import Manager

    sides = {side: kept.get(side) or {} for side in ("left", "right")}
    left = dirs[0] if dirs else (_directory(sides["left"].get("path"))
                                 or _directory(sides["left"].get("local")) or Path.cwd())
    right = dirs[1] if dirs else (_directory(sides["right"].get("path"))
                                  or _directory(sides["right"].get("local")) or left)
    manager = Manager(left, right)
    if not dirs:
        # A panel kept on another drive opens on the disk, and goes back
        # there once the shell has connected -- asking whatever it must.
        shell = getattr(getattr(desktop, "application", None), "shell", None)
        for side in ("left", "right"):
            remote = _remote(sides[side])
            if remote is not None and shell is not None and hasattr(shell, "go_remote"):
                shell.spawn(shell.go_remote(getattr(manager, side), remote))
    for side in ("left", "right"):
        panel_kept = dict(kept.get(side) or {})
        if dirs:
            panel_kept.pop("cursor", None)
        _seed_panel(getattr(manager, side), panel_kept)
    split = kept.get("split")
    if isinstance(split, (int, float)) and not isinstance(split, bool) and 0 < split < 1:
        manager.split = float(split)
    desktop.open(manager)
    active = manager.right if kept.get("active") == "right" else manager.left
    active.focus()
    view = {"tree": manager.tree, "quick": manager.quick, "info": manager.info}.get(kept.get("view"))
    if view is not None:
        manager.switch_view(view)
    if kept.get("hidden") in ("left", "right"):
        manager.hide_side(kept["hidden"])
    miller = kept.get("miller")
    if isinstance(miller, dict) and isinstance(miller.get("path"), str) and not dirs:
        from navigator.lib.drives import Location

        # On the disk only: another drive is not connected yet, and a
        # panel kept there opens on the disk too (``_remote``).
        location = Location.parse(miller["path"])
        if location.is_local and Path(location.local).is_dir():
            if miller.get("side") == "right":
                manager.right.focus()
            manager.toggle_miller(location, miller.get("cursor") or None)
    return manager


async def _make(desktop: Any, kept: dict[str, Any], dirs: tuple[Path, Path] | None) -> Any:
    """One window from *kept*, opened on *desktop*; None if it cannot be."""
    kind = kept.get("kind")
    if kind == "manager":
        return _manager(desktop, kept, dirs)
    if kind == "editor":
        if kept.get("smartpad"):
            from navigator.lib.utilities.smartpad import open_smartpad

            window = await open_smartpad(desktop, stamp=False)
        else:
            from navigator.lib.config.file_history import open_editor

            window = await open_editor(desktop, kept["path"])
        # ``Awaken``: the editor as it was kept, over the file's own record.
        if window is not None and isinstance(kept.get("state"), dict):
            window.restore_desktop_state(kept["state"])
        return window
    if kind == "viewer":
        from navigator.lib.config.file_history import open_viewer

        return await open_viewer(desktop, kept["path"], kept.get("mode"))
    if kind == "tree":
        from navigator.widgets.tree.tree_window import TreeWindow

        return desktop.open(TreeWindow(start=_directory(kept.get("path")), hidden=kept.get("hidden", True)))
    if kind == "calculator":
        from navigator.settings import CalculatorData
        from navigator.widgets.shell.calculator_window import CalculatorWindow

        window = desktop.open(CalculatorWindow())
        mode = kept.get("mode")
        # An older desktop kept no face: DN's, the only one there was.
        window.set_mode(mode if mode in CalculatorData.MODES else "classic", focus=False, save=False)
        window.line.value = kept.get("expression") or ""
        return window
    if kind == "calendar":
        from navigator.widgets.shell.calendar_window import CalendarWindow

        window = desktop.open(CalendarWindow())
        chosen = kept.get("calendar")
        window.chosen = chosen if isinstance(chosen, str) else ""
        view = kept.get("view")
        window.display = view if isinstance(view, str) else ""
        return window
    if kind == "database":
        return await _database(desktop, kept)
    if kind == "volumes":
        from navigator.widgets.shell.volumes_window import VolumesWindow

        return desktop.open(VolumesWindow(show_all=bool(kept.get("all")), show_free=bool(kept.get("free"))))
    return None


async def _database(desktop: Any, kept: dict[str, Any]) -> Any:
    """A database window from *kept*: the file opened as it was read; its
    cell and the rest are put back once it is placed (``restore_state``)."""
    from navigator.lib.viewer.table import Dialect
    from navigator.widgets.viewer.db_window.db_window import open_csv, open_database, open_sqlite

    path = Path(kept["path"])
    source = kept.get("source")
    if source == "sqlite":
        query, table = kept.get("query"), kept.get("table")
        if isinstance(query, str):
            return await open_sqlite(desktop, path, query=query)
        return await open_sqlite(desktop, path, table=table) if isinstance(table, str) else None
    if source == "csv":
        dialect = kept.get("dialect")
        chosen = Dialect(**{key: dialect[key] for key in ("delimiter", "quotechar", "header", "encoding")
                            if key in dialect}) if isinstance(dialect, dict) else None
        record = kept.get("record")
        return await open_csv(desktop, path, dialect=chosen,
                              row=record if isinstance(record, int) and record >= 0 else 0)
    window = await open_database(desktop, path)
    codec = kept.get("codec")
    if window is not None and isinstance(codec, str):
        import codecs

        codecs.lookup(codec)  # a name Python does not know: LookupError, left out
        window.db.set_codec(codec)
    return window


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
    from navigator.lib.config.file_history import place_window
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
    #: What each kept entry became, by its index: a view comes back on its text's.
    made_at: dict[int, Any] = {}
    for index, kept in enumerate(windows):
        source = made_at.get(kept.get("view_of")) if isinstance(kept, dict) else None
        try:
            if source is not None and hasattr(source, "open_view"):
                window = source.open_view()
                # A view keeps a place and modes of its own, as each was stored.
                if window is not None and isinstance(kept.get("state"), dict):
                    window.restore_desktop_state(kept["state"])
            else:
                window = await _make(desktop, kept, dirs)
        except (OSError, KeyError, TypeError, ValueError, LookupError):
            # ``dbf.DBFError`` is a ``ValueError``: a table that is no more.
            window = None
        if window is None:
            continue
        made_at[index] = window
        if kept.get("kind") == "manager":
            dirs = None  # the command line's directories are the first manager's alone
        rect = kept.get("rect")
        if isinstance(rect, dict):
            place_window(window, SimpleNamespace(**rect))
            if kept.get("kind") == "calendar":
                # It cannot be resized: its own size, whatever an older
                # Navigator saved, so a row added since is not cut off.
                width, height = window.size()
                window.locate(window.x, window.y, min(width, desktop.width), min(height, desktop.height))
        if kept.get("kind") == "database":
            # Once it has its rectangle, so the scroll is the screen's.
            if window.parent is not None:
                window.layout(window.parent.width, window.parent.height)
            window.restore_state(kept)
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
