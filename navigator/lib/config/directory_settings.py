"""Settings remembered per directory, and where the cursor was left in one.

**A departure.**  DN's sort order, file mask and display flags belonged to
the panel (``TFilePanelRoot.SortMode``/``FileMask``/``PanelFlags``) and went
wherever it went; nothing was kept by path.  Here File Manager Setup's
*Remember directory settings* says which directories keep their own:

- ``off``: none -- every directory is shown with the panel's own settings,
  as in DN;
- ``marked`` (the default): those Panel > *Remember for this directory* marks,
  each alone or with the directories below it, the nearest marked one winning;
- ``all``: those too, and any directory a setting is changed in.

A remembered directory is shown with its record (:data:`KEPT`) while the
panel is in it.  The panel holds its own settings aside meanwhile
(``Panel._base``) and takes them back on leaving for a directory with no
record, so nothing leaks out of one.  A change made inside one is the
record's, not the panel's.

Apart from that, *Return to last cursor position* (``[file_manager]
restore_cursor``) puts the cursor back on the entry it was left on, in any
directory -- and always in a remembered one.  The newest :data:`CURSORS` are
kept.
"""

from __future__ import annotations

import time
from typing import Any

#: What a record holds: what Alt+S, Alt+B, Ctrl+Y, Alt+K, Ctrl+H and Alt+Del
#: change.  Not Alt+I's footer, which is the panel's and not the directory's.
KEPT = ("view_mode", "sort_mode", "sort_reverse", "file_mask", "show_hidden", "columns", "display")

#: How many directories' cursors are kept.
CURSORS = 2000


def mode() -> str:
    from navigator.settings import SETTINGS

    return SETTINGS.file_manager.remember_directories


def rememberable(location: Any) -> bool:
    """Whether *location* is a place a record could be kept for: not inside
    an archive, whose columns are its own and which is no place to come
    back to."""
    return location.outer is None


def key_of(location: Any) -> str:
    """The name *location* is remembered under: a bookmark's, and a ``root:``
    place's own on the disk -- reading it as root is the same directory."""
    from navigator.lib.config.bookmarks import key_of as bookmark_key
    from navigator.lib.drives import root

    return bookmark_key(root.on_disk(location))


def values(panel: Any) -> dict[str, Any]:
    """What *panel* shows of :data:`KEPT`."""
    display = panel.display
    return {
        "view_mode": panel.view_mode,
        "sort_mode": panel.sort_mode,
        "sort_reverse": bool(panel.sort_reverse),
        "file_mask": panel.file_mask,
        "show_hidden": bool(panel.show_hidden),
        "columns": frozenset(panel.columns),
        "display": frozenset(display) if display is not None else None,
    }


def assign(panel: Any, kept: dict[str, Any]) -> None:
    """*kept* (:func:`values`' shape) onto *panel*, what it is not refused."""
    from navigator.widgets.manager.panel.panel import SORT_MODES

    if kept.get("view_mode") in panel.VIEW_MODES:
        panel.view_mode = kept["view_mode"]
    if kept.get("sort_mode") in SORT_MODES:
        panel.sort_mode = kept["sort_mode"]
    panel.sort_reverse = bool(kept.get("sort_reverse")) and panel.sort_mode != "unsorted"
    panel.file_mask = kept.get("file_mask") or panel.file_mask
    panel.show_hidden = bool(kept.get("show_hidden", panel.show_hidden))
    if kept.get("columns"):
        panel.columns = frozenset(kept["columns"])
    panel.display = kept.get("display")


def _row_values(row: Any) -> dict[str, Any]:
    return {
        "view_mode": row.view_mode,
        "sort_mode": row.sort_mode,
        "sort_reverse": bool(row.sort_reverse),
        "file_mask": row.file_mask,
        "show_hidden": bool(row.show_hidden),
        "columns": frozenset(name for name in row.columns.split(",") if name),
        "display": None if row.display == "*" else frozenset(name for name in row.display.split(",") if name),
    }


def _fields(kept: dict[str, Any]) -> dict[str, Any]:
    display = kept["display"]
    return {
        "view_mode": kept["view_mode"],
        "sort_mode": kept["sort_mode"],
        "sort_reverse": bool(kept["sort_reverse"]),
        "file_mask": kept["file_mask"],
        "show_hidden": bool(kept["show_hidden"]),
        "columns": ",".join(sorted(kept["columns"])),
        "display": "*" if display is None else ",".join(sorted(display)),
    }


def find(location: Any) -> tuple[str, dict[str, Any]] | None:
    """The record *location* is shown with -- its own, else the nearest
    directory above marked for the directories below -- as its key and
    :func:`values`' shape; None for none, or with the setting ``off``."""
    if mode() == "off" or not rememberable(location):
        return None
    from navigator.models.directory_settings import DirectorySettings

    keys = [key_of(location)]
    place = location
    while not place.is_root:
        place = place.parent
        keys.append(key_of(place))
    rows = {row.path: row for row in DirectorySettings.where(path__in=keys).all()}
    for index, key in enumerate(keys):
        row = rows.get(key)
        if row is not None and (index == 0 or row.subdirs):
            return key, _row_values(row)
    return None


def record(key: str) -> Any:
    """The row kept under *key*, or None."""
    from navigator.models.directory_settings import DirectorySettings

    return DirectorySettings.get(path=key)


def remember(key: str, kept: dict[str, Any], subdirs: bool | None = None) -> None:
    """*kept* written as the record under *key*; *subdirs* None keeps what
    an existing one says."""
    from navigator.models.directory_settings import DirectorySettings

    fields = _fields(kept)
    if subdirs is not None:
        fields["subdirs"] = subdirs
    if DirectorySettings.where(path=key).update(**fields) == 0:
        DirectorySettings.create(path=key, **fields)


def forget(key: str) -> None:
    from navigator.models.directory_settings import DirectorySettings

    DirectorySettings.delete_where(path=key)


def records() -> list[Any]:
    """Every record, by path."""
    from navigator.models.directory_settings import DirectorySettings

    return DirectorySettings.where().order("path").all()


# -- the cursor ----------------------------------------------------------------------------


def cursor_of(location: Any) -> str | None:
    """The entry the cursor was left on in *location*, or None."""
    if not rememberable(location):
        return None
    from navigator.models.directory_cursor import DirectoryCursor

    row = DirectoryCursor.get(path=key_of(location))
    return row.name if row is not None else None


def keep_cursor(location: Any, name: str) -> None:
    """*name* kept as where the cursor was left in *location*; the oldest
    beyond :data:`CURSORS` go."""
    if not rememberable(location):
        return
    from navigator.models.directory_cursor import DirectoryCursor

    key = key_of(location)
    now = time.time()
    if DirectoryCursor.where(path=key).update(name=name, used=now) == 0:
        DirectoryCursor.create(path=key, name=name, used=now)
        extra = DirectoryCursor.count() - CURSORS
        if extra > 0:
            DirectoryCursor.where().order("used").limit(extra).delete()
