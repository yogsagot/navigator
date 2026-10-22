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


def remember(manager: Any, side: str) -> None:
    """*manager*'s panel on *side* kept, over what that side had."""
    from navigator.models.panel_state import PanelState

    panel = getattr(manager, side)
    values = {"show_hidden": bool(panel.show_hidden), "show_info": bool(panel.show_info)}
    if PanelState.where(side=side).update(**values) == 0:
        PanelState.create(side=side, **values)


def recall(manager: Any) -> None:
    """*manager*'s panels seeded from what each side was left showing."""
    from navigator.models.panel_state import PanelState

    for side in SIDES:
        row = PanelState.get(side=side)
        if row is not None:
            panel = getattr(manager, side)
            panel.show_hidden = bool(row.show_hidden)
            panel.show_info = bool(row.show_info)
