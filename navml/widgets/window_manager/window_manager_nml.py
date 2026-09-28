# navml: generated
"""Generated from ``window_manager.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.events import Event as _Event
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button    # window_manager.nml:1
from navml.widgets.dialog.dialog import Dialog    # window_manager.nml:2
from navml.widgets.dialog.label import Label    # window_manager.nml:3
from navml.widgets.window_list import WindowList    # window_manager.nml:4

__navml_component__ = "WindowManagerDialog"

__all__ = ["WindowManagerDialog"]


class WindowManagerDialog(Dialog, _Component):
    """Window > List (Alt+0): DOS Navigator's *Windows Manager*.

    Every rectangle is ``dlgWindowManager``'s in ``DN.DNR``, a 70 by 14 dialog,
    and the three ``WindowManager`` inserts beside it in ``COLORS.PAS``: the
    ``~W~indows`` label over the list, the list from column 2 to the scroll bar
    at column 57, and the buttons in a column on the right, ten wide.  The list
    has no frame of its own and its scroll bar is its last column, which is
    where the original's stood.  ``Dialog``'s own row of buttons along the
    bottom is not this dialog's, and the hand-written half hides it.
    """

    #: The document this class was generated from.
    __navml_source__ = "window_manager.nml"

    #: Ids, annotated so the hand-written half completes them.
    caption: Label    # window_manager.nml:21
    windows: WindowList    # window_manager.nml:30
    pick: Button    # window_manager.nml:38
    shut: Button    # window_manager.nml:48
    abandon: Button    # window_manager.nml:56
    helper: Button    # window_manager.nml:65

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_windows_chosen(self, event: _Event) -> bool:    # window_manager.nml:30
        """``windows`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_pick_click(self, event: _Event) -> bool:    # window_manager.nml:38
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_shut_click(self, event: _Event) -> bool:    # window_manager.nml:48
        """``shut`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # window_manager.nml:56
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # window_manager.nml:65
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption = Label(parent=self)    # window_manager.nml:20
        self.windows = WindowList(parent=self)    # window_manager.nml:29
        self.pick = Button(parent=self)    # window_manager.nml:37
        self.shut = Button(parent=self)    # window_manager.nml:47
        self.abandon = Button(parent=self)    # window_manager.nml:55
        self.helper = Button(parent=self)    # window_manager.nml:64

        self.modal_width = 70    # window_manager.nml:16
        self.modal_height = 14    # window_manager.nml:17
        self.title = 'Windows Manager'    # window_manager.nml:18

        self.caption.text = '~W~indows'    # window_manager.nml:22
        self.caption.link = _bind(lambda _o: self.windows)    # window_manager.nml:23
        self.caption.x = 2    # window_manager.nml:24
        self.caption.y = 2    # window_manager.nml:25
        self.caption.width = 43    # window_manager.nml:26
        self.caption.height = 1    # window_manager.nml:27

        self.windows.framed = False    # window_manager.nml:31
        self.windows.x = 2    # window_manager.nml:32
        self.windows.y = 3    # window_manager.nml:33
        self.windows.width = 56    # window_manager.nml:34
        self.windows.height = 9    # window_manager.nml:35
        self.windows.on_chosen = self.on_windows_chosen    # window_manager.nml:30

        self.pick.text = 'O~K~'    # window_manager.nml:39
        self.pick.default = True    # window_manager.nml:40
        self.pick.x = 58    # window_manager.nml:41
        self.pick.y = 3    # window_manager.nml:42
        self.pick.width = 10    # window_manager.nml:43
        self.pick.height = 2    # window_manager.nml:44
        self.pick.on_click = self.on_pick_click    # window_manager.nml:38

        self.shut.text = 'C~l~ose'    # window_manager.nml:49
        self.shut.x = 58    # window_manager.nml:50
        self.shut.y = 5    # window_manager.nml:51
        self.shut.width = 10    # window_manager.nml:52
        self.shut.height = 2    # window_manager.nml:53
        self.shut.on_click = self.on_shut_click    # window_manager.nml:48

        self.abandon.text = 'Cancel'    # window_manager.nml:57
        self.abandon.x = 58    # window_manager.nml:58
        self.abandon.y = 7    # window_manager.nml:59
        self.abandon.width = 10    # window_manager.nml:60
        self.abandon.height = 2    # window_manager.nml:61
        self.abandon.on_click = self.on_abandon_click    # window_manager.nml:56

        self.helper.text = '~H~elp'    # window_manager.nml:66
        self.helper.disabled = True    # window_manager.nml:67
        self.helper.x = 58    # window_manager.nml:68
        self.helper.y = 11    # window_manager.nml:69
        self.helper.width = 10    # window_manager.nml:70
        self.helper.height = 2    # window_manager.nml:71
        self.helper.on_click = self.on_helper_click    # window_manager.nml:65
