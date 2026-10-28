# navml: generated
"""Generated from ``terminal_window.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.widgets.shell.terminal_view import TerminalView    # terminal_window.nml:1
from navml.widgets.window import Window    # terminal_window.nml:2

__navml_component__ = "TerminalWindow"

__all__ = ["TerminalWindow"]


class TerminalWindow(Window, _Component):
    """A command run in a window of its own: ``&command`` on the command line,

    Shift+Enter, File > Execute OS command's *In a window*, or a user menu item
    with a ``<&`` line.

    **A departure**: DOS Navigator ran one program at a time and was not
    running itself while it did, which the console still is.  Here the command
    has a pty and a screen of its own (``TerminalView``, ``sh -c``) inside the
    frame, so it runs beside the panels and the other windows.  It gets every
    key but the ones that bring another window forward; closing the window
    hangs it up.  Once it has ended the window keeps its output, the title says
    how it ended, and Esc or Enter closes it.
    """

    #: The document this class was generated from.
    __navml_source__ = "terminal_window.nml"

    #: Ids, annotated so the hand-written half completes them.
    view: TerminalView    # terminal_window.nml:20

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.view = TerminalView(parent=self)    # terminal_window.nml:19

        self.min_width = 20    # terminal_window.nml:16
        self.min_height = 5    # terminal_window.nml:17

        self.view.x = 1    # terminal_window.nml:21
        self.view.y = 1    # terminal_window.nml:22
        self.view.width = _bind(lambda _o: max(1, _o.parent.width - 2))    # terminal_window.nml:23
        self.view.height = _bind(lambda _o: max(1, _o.parent.height - 2))    # terminal_window.nml:24
