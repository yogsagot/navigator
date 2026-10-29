# navml: generated
"""Generated from ``sync_window.nml``.

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
from navkit.bidi import display_width    # sync_window.nml:1
from navigator.widgets.manager.commands import DiffFiles, Rescan, SetAllSyncActions, SetSyncAction, Synchronize, ToggleHidden, ToggleTree    # sync_window.nml:2
from navigator.widgets.manager.sync_list import SyncList    # sync_window.nml:3
from navml.commands import CloseWindow    # sync_window.nml:4
from navml.widgets.dialog.button import Button    # sync_window.nml:5
from navml.widgets.dialog.check_boxes import CheckBoxes    # sync_window.nml:6
from navml.widgets.dialog.commands import SelectNext, SelectPrevious    # sync_window.nml:7
from navml.widgets.dialog.static_text import StaticText    # sync_window.nml:8
from navml.widgets.menu.menu_item import MenuItem    # sync_window.nml:9
from navml.widgets.menu.menu_line import MenuLine    # sync_window.nml:10
from navml.widgets.menu.sub_menu import SubMenu    # sync_window.nml:11
from navml.widgets.window import Window    # sync_window.nml:12

__navml_component__ = "SyncWindow"

__all__ = ["SyncWindow"]


class SyncWindow(Window, _Component):
    """*Compare directories*' *Window, recursive*: every path below the two

    panels' directories that is on one side alone, or differs from its
    namesake, a row each with what is to be done with it.

    **Not DOS Navigator's**: a departure, asked for.  DN compared one level and
    tagged (``CM_CompareDirs``); this is Total Commander's *Synchronize
    directories*, whose keys it takes -- Right and Left copy a row that way,
    Space leaves it, Del deletes it from the one side it is on, Backspace gives
    it back what its status suggests; Ctrl+Right and Ctrl+Left set every row.
    Enter or F3 on a pair that differs compares the two files side by side
    (``DiffWindow``).  F5, or *Synchronize*, does it all: the copies as one
    F5 copy, files kept with their times so the next compare finds them the
    same, then the deletes as one F8.

    *Tree view* -- or Ctrl+T -- shows the rows under their directories, a tree (``SyncList.tree``):
    an action on a directory acts on every row beneath it that allows it;
    Gray + and - and Enter open and close one, * opens them all.

    Laid out as Disk > Volumes is: the list without a frame of its own, a
    dialog's row under it.  *Show identical* -- or Ctrl+H, as it shows a
    panel's dot-files -- lists the paths that are the same too; Ctrl+R and
    Alt+R compare again.
    """

    #: The document this class was generated from.
    __navml_source__ = "sync_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # sync_window.nml:41
        'escape': CloseWindow,    # sync_window.nml:42
        'enter': DiffFiles,    # sync_window.nml:43
        'f3': DiffFiles,    # sync_window.nml:44
        'f5': Synchronize,    # sync_window.nml:45
        'ctrl+r': Rescan,    # sync_window.nml:46
        'alt+r': Rescan,    # sync_window.nml:47
        'ctrl+h': ToggleHidden,    # sync_window.nml:48
        'ctrl+t': ToggleTree,    # sync_window.nml:49
        'tab': SelectNext,    # sync_window.nml:50
        'shift+tab': SelectPrevious,    # sync_window.nml:51
    }

    #: Ids, annotated so the hand-written half completes them.
    rows: SyncList    # sync_window.nml:54
    info: StaticText    # sync_window.nml:64
    identical: CheckBoxes    # sync_window.nml:72
    tree_box: CheckBoxes    # sync_window.nml:82
    summary: StaticText    # sync_window.nml:91
    sync_button: Button    # sync_window.nml:98
    close_button: Button    # sync_window.nml:106
    sync_menu: SubMenu    # sync_window.nml:116

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_sync_button_click(self, event: _Event) -> bool:    # sync_window.nml:98
        """``sync_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_close_button_click(self, event: _Event) -> bool:    # sync_window.nml:106
        """``close_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.rows = SyncList(parent=self)    # sync_window.nml:53
        self.info = StaticText(parent=self)    # sync_window.nml:63
        self.identical = CheckBoxes(parent=self)    # sync_window.nml:71
        self.tree_box = CheckBoxes(parent=self)    # sync_window.nml:81
        self.summary = StaticText(parent=self)    # sync_window.nml:90
        self.sync_button = Button(parent=self)    # sync_window.nml:97
        self.close_button = Button(parent=self)    # sync_window.nml:105
        self.sync_menu = SubMenu(parent=self)    # sync_window.nml:115
        _w1 = MenuItem(parent=self.sync_menu)    # sync_window.nml:120
        _w2 = MenuItem(parent=self.sync_menu)    # sync_window.nml:123
        _w3 = MenuLine(parent=self.sync_menu)    # sync_window.nml:126
        _w4 = MenuItem(parent=self.sync_menu)    # sync_window.nml:127
        _w5 = MenuItem(parent=self.sync_menu)    # sync_window.nml:130
        _w6 = MenuItem(parent=self.sync_menu)    # sync_window.nml:133
        _w7 = MenuItem(parent=self.sync_menu)    # sync_window.nml:136
        _w8 = MenuItem(parent=self.sync_menu)    # sync_window.nml:139
        _w9 = MenuLine(parent=self.sync_menu)    # sync_window.nml:143
        _w10 = MenuItem(parent=self.sync_menu)    # sync_window.nml:144
        _w11 = MenuItem(parent=self.sync_menu)    # sync_window.nml:147
        _w12 = MenuItem(parent=self.sync_menu)    # sync_window.nml:150
        _w13 = MenuLine(parent=self.sync_menu)    # sync_window.nml:154
        _w14 = MenuItem(parent=self.sync_menu)    # sync_window.nml:155
        _w15 = MenuItem(parent=self.sync_menu)    # sync_window.nml:158
        _w16 = MenuItem(parent=self.sync_menu)    # sync_window.nml:162
        _w17 = MenuLine(parent=self.sync_menu)    # sync_window.nml:166
        _w18 = MenuItem(parent=self.sync_menu)    # sync_window.nml:167

        self.title = _bind(lambda _o: _tr('Synchronize'), yielding=True)    # sync_window.nml:37
        self.zoomed = True    # sync_window.nml:39

        self.rows.framed = False    # sync_window.nml:55
        self.rows.x = 1    # sync_window.nml:56
        self.rows.y = 1    # sync_window.nml:57
        self.rows.width = _bind(lambda _o: max(0, _o.parent.width - 1))    # sync_window.nml:58
        self.rows.height = _bind(lambda _o: max(0, _o.parent.height - 4))    # sync_window.nml:59

        self.info.name = 'info'    # sync_window.nml:65
        self.info.x = 1    # sync_window.nml:66
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # sync_window.nml:67
        self.info.width = _bind(    # sync_window.nml:68
            lambda _o: min(display_width(_o.text), max(0, _o.parent.width - 3))
        )
        self.info.height = 1    # sync_window.nml:69

        self.identical.x = 2    # sync_window.nml:73
        self.identical.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # sync_window.nml:74
        self.identical.width = 22    # sync_window.nml:75
        self.identical.height = 1    # sync_window.nml:76
        self.identical.items = _bind(    # sync_window.nml:77
            lambda _o: [_tr('Show ~i~dentical')],
            yielding=True,
        )
        self.identical.tooltips = _bind(    # sync_window.nml:78
            lambda _o: [_tr('List the files that are the same on both sides too')],
            yielding=True,
        )

        self.tree_box.x = 26    # sync_window.nml:83
        self.tree_box.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # sync_window.nml:84
        self.tree_box.width = 18    # sync_window.nml:85
        self.tree_box.height = 1    # sync_window.nml:86
        self.tree_box.items = _bind(    # sync_window.nml:87
            lambda _o: [_tr('~T~ree view')],
            yielding=True,
        )
        self.tree_box.tooltips = _bind(    # sync_window.nml:88
            lambda _o: [_tr('Show the rows under their directories, as a tree')],
            yielding=True,
        )

        self.summary.x = 2    # sync_window.nml:92
        self.summary.y = _bind(lambda _o: max(0, _o.parent.height - 2))    # sync_window.nml:93
        self.summary.width = _bind(lambda _o: max(0, _o.parent.width - 30))    # sync_window.nml:94
        self.summary.height = 1    # sync_window.nml:95

        self.sync_button.text = _bind(    # sync_window.nml:99
            lambda _o: _tr('~S~ynchronize'),
            yielding=True,
        )
        self.sync_button.x = _bind(lambda _o: max(0, _o.parent.width - 31))    # sync_window.nml:100
        self.sync_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # sync_window.nml:101
        self.sync_button.width = 16    # sync_window.nml:102
        self.sync_button.height = 2    # sync_window.nml:103
        self.sync_button.on_click = self.on_sync_button_click    # sync_window.nml:98

        self.close_button.text = _bind(lambda _o: _tr('Close'), yielding=True)    # sync_window.nml:107
        self.close_button.x = _bind(lambda _o: max(0, _o.parent.width - 13))    # sync_window.nml:108
        self.close_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # sync_window.nml:109
        self.close_button.width = 10    # sync_window.nml:110
        self.close_button.height = 2    # sync_window.nml:111
        self.close_button.on_click = self.on_close_button_click    # sync_window.nml:106

        self.sync_menu.text = _bind(    # sync_window.nml:117
            lambda _o: _tr('~S~ynchronize'),
            yielding=True,
        )
        self.sync_menu.tooltip = _bind(    # sync_window.nml:118
            lambda _o: _tr('Choose what happens to each file, then synchronize'),
            yielding=True,
        )
        self.sync_menu.after = 'File'    # sync_window.nml:119

        _w1.text = _bind(lambda _o: _tr('~S~ynchronize'), yielding=True)    # sync_window.nml:121
        _w1.command = Synchronize    # sync_window.nml:122

        _w2.text = _bind(lambda _o: _tr('~C~ompare files'), yielding=True)    # sync_window.nml:124
        _w2.command = DiffFiles    # sync_window.nml:125

        _w4.text = _bind(lambda _o: _tr('Copy ~r~ight'), yielding=True)    # sync_window.nml:128
        _w4.command = SetSyncAction('right')    # sync_window.nml:129

        _w5.text = _bind(lambda _o: _tr('Copy ~l~eft'), yielding=True)    # sync_window.nml:131
        _w5.command = SetSyncAction('left')    # sync_window.nml:132

        _w6.text = _bind(lambda _o: _tr('~D~elete'), yielding=True)    # sync_window.nml:134
        _w6.command = SetSyncAction('delete')    # sync_window.nml:135

        _w7.text = _bind(lambda _o: _tr('S~k~ip'), yielding=True)    # sync_window.nml:137
        _w7.command = SetSyncAction('skip')    # sync_window.nml:138

        _w8.text = _bind(lambda _o: _tr('D~e~fault action'), yielding=True)    # sync_window.nml:140
        _w8.tooltip = _bind(    # sync_window.nml:141
            lambda _o: _tr('Give the row back the action the comparison chose'),
            yielding=True,
        )
        _w8.command = SetSyncAction('default')    # sync_window.nml:142

        _w10.text = _bind(lambda _o: _tr('~A~ll right'), yielding=True)    # sync_window.nml:145
        _w10.command = SetAllSyncActions('right')    # sync_window.nml:146

        _w11.text = _bind(lambda _o: _tr('All le~f~t'), yielding=True)    # sync_window.nml:148
        _w11.command = SetAllSyncActions('left')    # sync_window.nml:149

        _w12.text = _bind(lambda _o: _tr('All defa~u~lt'), yielding=True)    # sync_window.nml:151
        _w12.tooltip = _bind(    # sync_window.nml:152
            lambda _o: _tr('Give every row back the action the comparison chose'),
            yielding=True,
        )
        _w12.command = SetAllSyncActions('default')    # sync_window.nml:153

        _w14.text = _bind(lambda _o: _tr('Compare a~g~ain'), yielding=True)    # sync_window.nml:156
        _w14.command = Rescan    # sync_window.nml:157

        _w15.text = _bind(lambda _o: _tr('Show ~i~dentical'), yielding=True)    # sync_window.nml:159
        _w15.tooltip = _bind(    # sync_window.nml:160
            lambda _o: _tr('List the files that are the same on both sides too'),
            yielding=True,
        )
        _w15.command = ToggleHidden    # sync_window.nml:161

        _w16.text = _bind(lambda _o: _tr('~T~ree view'), yielding=True)    # sync_window.nml:163
        _w16.tooltip = _bind(    # sync_window.nml:164
            lambda _o: _tr('Show the rows under their directories, as a tree'),
            yielding=True,
        )
        _w16.command = ToggleTree    # sync_window.nml:165

        _w18.text = _bind(lambda _o: _tr('Cl~o~se'), yielding=True)    # sync_window.nml:168
        _w18.command = CloseWindow    # sync_window.nml:169
