"""What each side of the file manager was left showing: Ctrl+H's hidden files
and Alt+I's footer.

**A departure.**  DN's ``ossShowHidden`` was one system option and its panels
had no footer to hide.  Here both are per panel, and a panel turned one way
stays that way: :func:`remember` writes a side each time Ctrl+H or Alt+I
switches it (``Manager.on_toggle_hidden``/``on_toggle_info_lines``), and
:func:`recall` seeds every new file manager's
panels from them, side by side.  A side with nothing kept follows System
Setup's *Show hidden files* and shows its footer.  A saved desktop
(``desktop_state``) is seeded after, so it wins over both.
"""

from __future__ import annotations

from typing import Any

SIDES = ("left", "right")


def kept_values(panel: Any) -> dict[str, Any]:
    """What is kept of *panel*."""
    return {"show_hidden": bool(panel.show_hidden), "show_info": bool(panel.show_info),
            "view_mode": panel.view_mode, "sort_mode": panel.sort_mode,
            "sort_reverse": bool(panel.sort_reverse)}


def remember(manager: Any, side: str) -> None:
    """*manager*'s panel on *side* kept, over what that side had."""
    from navigator.models.panel_state import PanelState

    values = kept_values(getattr(manager, side))
    if PanelState.where(side=side).update(**values) == 0:
        PanelState.create(side=side, **values)


def recall(manager: Any) -> None:
    """*manager*'s panels seeded from what each side was left showing."""
    from navigator.models.panel_state import PanelState
    from navigator.widgets.manager.panel.panel import SORT_MODES

    for side in SIDES:
        row = PanelState.get(side=side)
        if row is None:
            continue
        panel = getattr(manager, side)
        panel.show_hidden = bool(row.show_hidden)
        panel.show_info = bool(row.show_info)
        if row.view_mode in panel.VIEW_MODES:
            panel.view_mode = row.view_mode
        if row.sort_mode in SORT_MODES:
            panel.sort_mode = row.sort_mode
            panel.sort_reverse = bool(row.sort_reverse) and row.sort_mode != "unsorted"
