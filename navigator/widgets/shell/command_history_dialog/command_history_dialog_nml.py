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
from navml.widgets.dialog.dialog import Dialog    # command_history_dialog.nml:3

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
    commands: HistoryList    # command_history_dialog.nml:15
    run: Button    # command_history_dialog.nml:24
    drop: Button    # command_history_dialog.nml:34
    edit: Button    # command_history_dialog.nml:43
    kill: Button    # command_history_dialog.nml:52
    abandon: Button    # command_history_dialog.nml:60

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_commands_chosen(self, event: _Event) -> bool:    # command_history_dialog.nml:15
        """``commands`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_commands_killed(self, event: _Event) -> bool:    # command_history_dialog.nml:15
        """``commands`` raised an event whose handler is ``on_killed``."""
        return False

    async def on_run_click(self, event: _Event) -> bool:    # command_history_dialog.nml:24
        """``run`` raised an event whose handler is ``on_click``."""
        return False

    async def on_drop_click(self, event: _Event) -> bool:    # command_history_dialog.nml:34
        """``drop`` raised an event whose handler is ``on_click``."""
        return False

    async def on_edit_click(self, event: _Event) -> bool:    # command_history_dialog.nml:43
        """``edit`` raised an event whose handler is ``on_click``."""
        return False

    async def on_kill_click(self, event: _Event) -> bool:    # command_history_dialog.nml:52
        """``kill`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # command_history_dialog.nml:60
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.commands = HistoryList(parent=self)    # command_history_dialog.nml:14
        self.run = Button(parent=self)    # command_history_dialog.nml:23
        self.drop = Button(parent=self)    # command_history_dialog.nml:33
        self.edit = Button(parent=self)    # command_history_dialog.nml:42
        self.kill = Button(parent=self)    # command_history_dialog.nml:51
        self.abandon = Button(parent=self)    # command_history_dialog.nml:59

        self.modal_width = 59    # command_history_dialog.nml:10
        self.modal_height = 17    # command_history_dialog.nml:11
        self.title = _bind(lambda _o: _tr('Commands history'), yielding=True)    # command_history_dialog.nml:12

        self.commands.framed = False    # command_history_dialog.nml:16
        self.commands.x = 2    # command_history_dialog.nml:17
        self.commands.y = 2    # command_history_dialog.nml:18
        self.commands.width = 55    # command_history_dialog.nml:19
        self.commands.height = 11    # command_history_dialog.nml:20
        self.commands.on_chosen = self.on_commands_chosen    # command_history_dialog.nml:15
        self.commands.on_killed = self.on_commands_killed    # command_history_dialog.nml:15

        self.run.text = _bind(lambda _o: _tr('~R~un'), yielding=True)    # command_history_dialog.nml:25
        self.run.default = True    # command_history_dialog.nml:26
        self.run.x = 3    # command_history_dialog.nml:27
        self.run.y = 14    # command_history_dialog.nml:28
        self.run.width = 10    # command_history_dialog.nml:29
        self.run.height = 2    # command_history_dialog.nml:30
        self.run.on_click = self.on_run_click    # command_history_dialog.nml:24

        self.drop.text = _bind(lambda _o: _tr('~D~rop'), yielding=True)    # command_history_dialog.nml:35
        self.drop.x = 14    # command_history_dialog.nml:36
        self.drop.y = 14    # command_history_dialog.nml:37
        self.drop.width = 10    # command_history_dialog.nml:38
        self.drop.height = 2    # command_history_dialog.nml:39
        self.drop.on_click = self.on_drop_click    # command_history_dialog.nml:34

        self.edit.text = _bind(lambda _o: _tr('~E~dit'), yielding=True)    # command_history_dialog.nml:44
        self.edit.x = 25    # command_history_dialog.nml:45
        self.edit.y = 14    # command_history_dialog.nml:46
        self.edit.width = 10    # command_history_dialog.nml:47
        self.edit.height = 2    # command_history_dialog.nml:48
        self.edit.on_click = self.on_edit_click    # command_history_dialog.nml:43

        self.kill.text = _bind(lambda _o: _tr('~K~ill'), yielding=True)    # command_history_dialog.nml:53
        self.kill.x = 36    # command_history_dialog.nml:54
        self.kill.y = 14    # command_history_dialog.nml:55
        self.kill.width = 10    # command_history_dialog.nml:56
        self.kill.height = 2    # command_history_dialog.nml:57
        self.kill.on_click = self.on_kill_click    # command_history_dialog.nml:52

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # command_history_dialog.nml:61
        self.abandon.x = 47    # command_history_dialog.nml:62
        self.abandon.y = 14    # command_history_dialog.nml:63
        self.abandon.width = 10    # command_history_dialog.nml:64
        self.abandon.height = 2    # command_history_dialog.nml:65
        self.abandon.on_click = self.on_abandon_click    # command_history_dialog.nml:60
