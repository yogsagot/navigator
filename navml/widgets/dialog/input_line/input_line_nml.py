# navml: generated
"""Generated from ``input_line.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.commands import Clear, ClipboardCopy, ClipboardCut, ClipboardPaste, SelectAll    # input_line.nml:1
from navml.widgets.dialog.control import Control    # input_line.nml:2

__navml_component__ = "InputLine"

__all__ = ["InputLine"]


class InputLine(Control, _Component):
    """One line of editable text, with a caret.

    DOS Navigator's ``[50-52] Input normal / selected / arrow``, and Turbo
    Vision's ``TInputLine``.  The widget the terminal's own cursor exists for:
    ``cursor_position()`` reports where the caret belongs and the application
    puts it there at the end of the frame, for whichever widget the keys are
    actually going to.
    """

    #: The document this class was generated from.
    __navml_source__ = "input_line.nml"

    #: The text.  **Seeded, never bound** -- this is a property the widget
    #: *navigates*: every keystroke assigns it, and a markup line would
    #: compile to a binding that makes the first keypress an error.  A
    #: document hands it over with a constructor keyword instead.
    value: str = _reactive('')    # input_line.nml:16

    #: The longest text this line will accept, or 0 for no limit.
    max_length: int = _reactive(0)    # input_line.nml:19

    #: A secret: every character painted as ``*``, and nothing of it copied --
    #: not to the clipboard, not to the primary selection.  For a password.
    password: bool = _reactive(False)    # input_line.nml:23

    #: The clipboard and the selection, by key or from the context menu.
    async def on_clipboard_cut(self, event: _Any) -> bool:    # input_line.nml:27
        """``ClipboardCut``."""
        self.cut()
        return True

    async def on_clipboard_copy(self, event: _Any) -> bool:    # input_line.nml:28
        """``ClipboardCopy``."""
        self.copy(self.selected_text or self.value)
        return True

    async def on_clipboard_paste(self, event: _Any) -> bool:    # input_line.nml:29
        """``ClipboardPaste``."""
        self.request_paste()
        return True

    async def on_clear(self, event: _Any) -> bool:    # input_line.nml:30
        """``Clear``."""
        self._replace_selection('')
        return True

    async def on_select_all(self, event: _Any) -> bool:    # input_line.nml:31
        """``SelectAll``."""
        self.select_all()
        return True

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)

        self._navml_built(__class__)
