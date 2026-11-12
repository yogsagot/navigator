# navml: generated
"""Generated from ``find_bar.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import bind as _bind
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.field import Field    # find_bar.nml:1
from navigator.widgets.editor.commands import CloseFindBar, FindNext, FindPrevious, ReplaceMatch, ReplaceMatches, ShowFindBar, ShowReplaceBar, SwitchMatchCase, SwitchRegex, SwitchWholeWords    # find_bar.nml:2

__navml_component__ = "FindBar"

__all__ = ["FindBar"]


class FindBar(_Component):
    """Ctrl+F (and Ctrl+R with a second line): a small box over the edit area's

    top-right corner, searching as it is typed into -- a departure, asked for,
    after IntelliJ IDEA's: DN had the *Find* and *Replace* dialogs alone, which
    F7 and Ctrl+F7 still open.

    The text to find with its history (shared with the dialogs), then the three
    switches -- *Match case* ``Aa``, *Whole words* ``W``, *Regular expression*
    ``.*`` -- which match and where the cursor is among them (``3/12``), and
    the previous, next and close arrows.  Replacing, a second line for the new
    text with *Replace* and *All* after it.  Everything after the lines is
    painted by the Python half, which also answers a click on it.
    """

    #: The document this class was generated from.
    __navml_source__ = "find_bar.nml"

    #: While the bar holds the keyboard.  Esc puts it away, Enter and F3 go to
    #: the next match (Enter in the new text replaces the one found first).
    keys = {    # find_bar.nml:21
        'escape': CloseFindBar,    # find_bar.nml:22
        'enter': FindNext,    # find_bar.nml:23
        'f3': FindNext,    # find_bar.nml:24
        'shift+enter': FindPrevious,    # find_bar.nml:25
        'shift+f3': FindPrevious,    # find_bar.nml:26
        'alt+c': SwitchMatchCase,    # find_bar.nml:27
        'alt+w': SwitchWholeWords,    # find_bar.nml:28
        'alt+r': SwitchRegex,    # find_bar.nml:29
        'alt+a': ReplaceMatches,    # find_bar.nml:30
        'ctrl+alt+enter': ReplaceMatches,    # find_bar.nml:31
        'ctrl+f': ShowFindBar,    # find_bar.nml:32
        'ctrl+r': ShowReplaceBar,    # find_bar.nml:33
    }

    #: With the line for the new text, *Replace* and *All*: Ctrl+R's.
    replace: bool = _reactive(False)    # find_bar.nml:17

    #: Ids, annotated so the hand-written half completes them.
    query: Field    # find_bar.nml:47
    new: Field    # find_bar.nml:56

    #: The switches flip, and are ticked in the menu while on.
    async def on_find_previous(self, event: _Any) -> bool:    # find_bar.nml:37
        """``FindPrevious``."""
        self.step(backward=True)
        return True

    async def on_switch_match_case(self, event: _Any) -> bool:    # find_bar.nml:38
        """``SwitchMatchCase``."""
        self.case = not self.case
        return True

    async def on_switch_whole_words(self, event: _Any) -> bool:    # find_bar.nml:40
        """``SwitchWholeWords``."""
        self.whole = not self.whole
        return True

    async def on_switch_regex(self, event: _Any) -> bool:    # find_bar.nml:42
        """``SwitchRegex``."""
        self.regex = not self.regex
        return True

    def checks(self, command: _Any) -> bool | None:
        """What the commands block says, then the base's ``checks``."""
        if isinstance(command, SwitchMatchCase):    # find_bar.nml:39
            return bool(self.case)
        if isinstance(command, SwitchWholeWords):    # find_bar.nml:41
            return bool(self.whole)
        if isinstance(command, SwitchRegex):    # find_bar.nml:43
            return bool(self.regex)
        return super().checks(command)

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.query = Field(parent=self)    # find_bar.nml:46
        self.new = Field(parent=self)    # find_bar.nml:55

        self.query.x = 1    # find_bar.nml:48
        self.query.y = 1    # find_bar.nml:49
        self.query.width = _bind(lambda _o: max(4, _o.parent.width - 29))    # find_bar.nml:50
        self.query.label_width = 0    # find_bar.nml:51
        self.query.history_id = 'find_text'    # find_bar.nml:52

        self.new.visible = _bind(lambda _o: self.replace)    # find_bar.nml:57
        self.new.x = 1    # find_bar.nml:58
        self.new.y = 2    # find_bar.nml:59
        self.new.width = _bind(lambda _o: max(4, _o.parent.width - 29))    # find_bar.nml:60
        self.new.label_width = 0    # find_bar.nml:61
        self.new.history_id = 'find_text'    # find_bar.nml:62

        self._navml_built(__class__)
