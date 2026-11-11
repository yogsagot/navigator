# navml: generated
"""Generated from ``command_history_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.events import Event as _Event
from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.widgets.shell.command_history_dialog.history_list import HistoryList    # command_history_dialog.nml:1
from navml.widgets.dialog.button import Button    # command_history_dialog.nml:2
from navml.widgets.dialog.button_row import ButtonRow    # command_history_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # command_history_dialog.nml:4

__navml_component__ = "CommandHistoryDialog"

__all__ = ["CommandHistoryDialog"]


class CommandHistoryDialog(Dialog, _Component):
    """Alt+F8, Utilities > Commands History: DOS Navigator's ``dlgCommandsHistory``.

    The commands typed, the newest at the foot and the cursor on it, over
    *Run*, *Drop*, *Edit*, *Kill* and *Cancel* where ``DN.DNR`` put them.
    """

    #: The document this class was generated from.
    __navml_source__ = "command_history_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    commands: HistoryList    # command_history_dialog.nml:17
    run: Button    # command_history_dialog.nml:35
    drop: Button    # command_history_dialog.nml:41
    edit: Button    # command_history_dialog.nml:46
    kill: Button    # command_history_dialog.nml:51
    abandon: Button    # command_history_dialog.nml:55

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_commands_chosen(self, event: _Event) -> bool:    # command_history_dialog.nml:17
        """``commands`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_commands_killed(self, event: _Event) -> bool:    # command_history_dialog.nml:17
        """``commands`` raised an event whose handler is ``on_killed``."""
        return False

    async def on_run_click(self, event: _Event) -> bool:    # command_history_dialog.nml:35
        """``run`` raised an event whose handler is ``on_click``."""
        return False

    async def on_drop_click(self, event: _Event) -> bool:    # command_history_dialog.nml:41
        """``drop`` raised an event whose handler is ``on_click``."""
        return False

    async def on_edit_click(self, event: _Event) -> bool:    # command_history_dialog.nml:46
        """``edit`` raised an event whose handler is ``on_click``."""
        return False

    async def on_kill_click(self, event: _Event) -> bool:    # command_history_dialog.nml:51
        """``kill`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # command_history_dialog.nml:55
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.commands = HistoryList(parent=self)    # command_history_dialog.nml:16
        _w1 = ButtonRow(parent=self)    # command_history_dialog.nml:25
        self.run = Button(parent=_w1)    # command_history_dialog.nml:34
        self.drop = Button(parent=_w1)    # command_history_dialog.nml:40
        self.edit = Button(parent=_w1)    # command_history_dialog.nml:45
        self.kill = Button(parent=_w1)    # command_history_dialog.nml:50
        self.abandon = Button(parent=_w1)    # command_history_dialog.nml:54

        self.modal_width = 59    # command_history_dialog.nml:11
        self.modal_height = 17    # command_history_dialog.nml:12
        self.title = _bind(lambda _o: _tr('Commands history'), yielding=True)    # command_history_dialog.nml:13
        self.buttons = 'none'    # command_history_dialog.nml:14

        self.commands.framed = False    # command_history_dialog.nml:18
        self.commands.x = 2    # command_history_dialog.nml:19
        self.commands.y = 2    # command_history_dialog.nml:20
        self.commands.width = 55    # command_history_dialog.nml:21
        self.commands.height = 11    # command_history_dialog.nml:22
        self.commands.on_chosen = self.on_commands_chosen    # command_history_dialog.nml:17
        self.commands.on_killed = self.on_commands_killed    # command_history_dialog.nml:17

        _w1.justify = 'start'    # command_history_dialog.nml:26
        _w1.button_width = 10    # command_history_dialog.nml:27
        _w1.spacing = 1    # command_history_dialog.nml:28
        _w1.y = 14# command_history_dialog.nml:29
        _w1.x = 3# command_history_dialog.nml:31
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 3))    # command_history_dialog.nml:32

        self.run.text = _bind(lambda _o: _tr('~R~un'), yielding=True)    # command_history_dialog.nml:36
        self.run.default = True    # command_history_dialog.nml:37
        self.run.on_click = self.on_run_click    # command_history_dialog.nml:35

        self.drop.text = _bind(lambda _o: _tr('~D~rop'), yielding=True)    # command_history_dialog.nml:42
        self.drop.on_click = self.on_drop_click    # command_history_dialog.nml:41

        self.edit.text = _bind(lambda _o: _tr('~E~dit'), yielding=True)    # command_history_dialog.nml:47
        self.edit.on_click = self.on_edit_click    # command_history_dialog.nml:46

        self.kill.text = _bind(lambda _o: _tr('~K~ill'), yielding=True)    # command_history_dialog.nml:52
        self.kill.on_click = self.on_kill_click    # command_history_dialog.nml:51

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # command_history_dialog.nml:56
        self.abandon.on_click = self.on_abandon_click    # command_history_dialog.nml:55
