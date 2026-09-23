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
from navml.widgets.control import Control    # input_line.nml:1

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
    value: str = _reactive('')    # input_line.nml:15

    #: The longest text this line will accept, or 0 for no limit.
    max_length: int = _reactive(0)    # input_line.nml:18

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
