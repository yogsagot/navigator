"""The base every focusable widget shares."""

from navml.widgets.dialog.control.control import (
    Control, caption_runs, escape_caption, parse_shortcut, shortcut_runs,
)

__all__ = ["Control", "caption_runs", "escape_caption", "parse_shortcut", "shortcut_runs"]
