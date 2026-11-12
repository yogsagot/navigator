# navml: generated
"""Generated from ``command_palette.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog    # command_palette.nml:1
from navml.widgets.dialog.input_line import InputLine    # command_palette.nml:2
from navml.widgets.dialog.static_text import StaticText    # command_palette.nml:3
from navigator.widgets.shell.command_palette.command_list import CommandList    # command_palette.nml:4
from navml.widgets.dialog.commands import Default    # command_palette.nml:5

__navml_component__ = "CommandPalette"

__all__ = ["CommandPalette"]


class CommandPalette(Dialog, _Component):
    """≡ > *Command palette* (Alt+Shift+P): every command that applies where the

    keyboard was -- the menus' items, the active window's own menus among
    them, and the commands keys are bound to there that no menu holds -- each
    with its key, greyed when it cannot run.  The line across the top narrows
    them by a few of their letters, in order (``navml.fuzzy``); Enter runs the
    one under the cursor.  Not DOS Navigator's (a departure, asked for).

    ``Dialog``'s own row of buttons and its message are not this layout, and
    the hand-written half hides them.
    """

    #: The document this class was generated from.
    __navml_source__ = "command_palette.nml"

    #: Ids, annotated so the hand-written half completes them.
    filter: InputLine    # command_palette.nml:30
    results: CommandList    # command_palette.nml:36
    hint: StaticText    # command_palette.nml:45

    #: The commands this component handles itself.
    async def on_default(self, event: _Any) -> bool:    # command_palette.nml:26
        """``Default``."""
        self.take()
        return True

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.filter = InputLine(parent=self)    # command_palette.nml:29
        self.results = CommandList(parent=self)    # command_palette.nml:35
        self.hint = StaticText(parent=self)    # command_palette.nml:44

        self.modal_width = _bind(    # command_palette.nml:17
            lambda _o: max(40, min(_o.parent.width - 4, 72)) if _o.parent is not None else 72
        )
        self.modal_height = _bind(    # command_palette.nml:18
            lambda _o: max(10, min(_o.parent.height - 2, 22)) if _o.parent is not None else 22
        )
        self.title = _bind(lambda _o: _tr('Commands'), yielding=True)    # command_palette.nml:19
        self.close_on_outside_click = True    # command_palette.nml:20
        self.buttons = 'none'    # command_palette.nml:21
        self.first_focus = _bind(lambda _o: self.filter)    # command_palette.nml:23

        self.filter.x = 2    # command_palette.nml:31
        self.filter.y = 2    # command_palette.nml:32
        self.filter.width = _bind(lambda _o: max(1, _o.parent.width - 4))    # command_palette.nml:33

        self.results.x = 2    # command_palette.nml:37
        self.results.y = 3    # command_palette.nml:38
        self.results.width = _bind(lambda _o: max(1, _o.parent.width - 4))    # command_palette.nml:39
        self.results.height = _bind(lambda _o: max(3, _o.parent.height - 6))    # command_palette.nml:40

        self.hint.x = 2    # command_palette.nml:47
        self.hint.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # command_palette.nml:48
        self.hint.y = _bind(    # command_palette.nml:49
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
