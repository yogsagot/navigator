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
from navigator.widgets.manager.commands import DiffFiles, Rescan, SetAllSyncActions, SetSyncAction, Synchronize, SyncSetup, ToggleHidden, ToggleSyncShow, ToggleTree    # sync_window.nml:2
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
    dialog's rows under it.  The *Show* boxes say which rows are listed --
    on the left alone, on the right alone, different, identical (Ctrl+H, as
    it shows a panel's dot-files) -- and only what is listed is synchronized,
    as in Total Commander.  *Options* (``SyncOptionsDialog``) has the file
    mask, how near two times are the same, and *Asymmetric*; Ctrl+R and Alt+R
    compare again.
    """

    #: The document this class was generated from.
    __navml_source__ = "sync_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # sync_window.nml:44
        'escape': CloseWindow,    # sync_window.nml:45
        'enter': DiffFiles,    # sync_window.nml:46
        'f3': DiffFiles,    # sync_window.nml:47
        'f5': Synchronize,    # sync_window.nml:48
        'ctrl+r': Rescan,    # sync_window.nml:49
        'alt+r': Rescan,    # sync_window.nml:50
        'ctrl+h': ToggleHidden,    # sync_window.nml:51
        'ctrl+t': ToggleTree,    # sync_window.nml:52
        'tab': SelectNext,    # sync_window.nml:53
        'shift+tab': SelectPrevious,    # sync_window.nml:54
    }

    #: Ids, annotated so the hand-written half completes them.
    rows: SyncList    # sync_window.nml:57
    info: StaticText    # sync_window.nml:68
    show: CheckBoxes    # sync_window.nml:78
    tree_box: CheckBoxes    # sync_window.nml:89
    summary: StaticText    # sync_window.nml:99
    options_button: Button    # sync_window.nml:107
    sync_button: Button    # sync_window.nml:117
    close_button: Button    # sync_window.nml:126
    sync_menu: SubMenu    # sync_window.nml:137
    sync_menu_show: SubMenu    # sync_window.nml:182

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_options_button_click(self, event: _Event) -> bool:    # sync_window.nml:107
        """``options_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_sync_button_click(self, event: _Event) -> bool:    # sync_window.nml:117
        """``sync_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_close_button_click(self, event: _Event) -> bool:    # sync_window.nml:126
        """``close_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.rows = SyncList(parent=self)    # sync_window.nml:56
        self.info = StaticText(parent=self)    # sync_window.nml:67
        self.show = CheckBoxes(parent=self)    # sync_window.nml:77
        self.tree_box = CheckBoxes(parent=self)    # sync_window.nml:88
        self.summary = StaticText(parent=self)    # sync_window.nml:98
        self.options_button = Button(parent=self)    # sync_window.nml:106
        self.sync_button = Button(parent=self)    # sync_window.nml:116
        self.close_button = Button(parent=self)    # sync_window.nml:125
        self.sync_menu = SubMenu(parent=self)    # sync_window.nml:136
        _w1 = MenuItem(parent=self.sync_menu)    # sync_window.nml:141
        _w2 = MenuItem(parent=self.sync_menu)    # sync_window.nml:144
        _w3 = MenuLine(parent=self.sync_menu)    # sync_window.nml:147
        _w4 = MenuItem(parent=self.sync_menu)    # sync_window.nml:148
        _w5 = MenuItem(parent=self.sync_menu)    # sync_window.nml:151
        _w6 = MenuItem(parent=self.sync_menu)    # sync_window.nml:154
        _w7 = MenuItem(parent=self.sync_menu)    # sync_window.nml:157
        _w8 = MenuItem(parent=self.sync_menu)    # sync_window.nml:160
        _w9 = MenuLine(parent=self.sync_menu)    # sync_window.nml:164
        _w10 = MenuItem(parent=self.sync_menu)    # sync_window.nml:165
        _w11 = MenuItem(parent=self.sync_menu)    # sync_window.nml:168
        _w12 = MenuItem(parent=self.sync_menu)    # sync_window.nml:171
        _w13 = MenuLine(parent=self.sync_menu)    # sync_window.nml:175
        _w14 = MenuItem(parent=self.sync_menu)    # sync_window.nml:176
        self.sync_menu_show = SubMenu(parent=self.sync_menu)    # sync_window.nml:181
        _w15 = MenuItem(parent=self.sync_menu_show)    # sync_window.nml:185
        _w16 = MenuItem(parent=self.sync_menu_show)    # sync_window.nml:189
        _w17 = MenuItem(parent=self.sync_menu_show)    # sync_window.nml:193
        _w18 = MenuItem(parent=self.sync_menu_show)    # sync_window.nml:197
        _w19 = MenuItem(parent=self.sync_menu)    # sync_window.nml:201
        _w20 = MenuItem(parent=self.sync_menu)    # sync_window.nml:205
        _w21 = MenuLine(parent=self.sync_menu)    # sync_window.nml:209
        _w22 = MenuItem(parent=self.sync_menu)    # sync_window.nml:210

        self.title = _bind(lambda _o: _tr('Synchronize'), yielding=True)    # sync_window.nml:40
        self.zoomed = True    # sync_window.nml:42

        self.rows.framed = False    # sync_window.nml:58
        self.rows.x = 1    # sync_window.nml:60
        self.rows.width = _bind(lambda _o: max(0, _o.parent.width - 1))    # sync_window.nml:61
        self.rows.y = 1    # sync_window.nml:62
        self.rows.height = _bind(lambda _o: max(0, _o.parent.height - 6))    # sync_window.nml:63

        self.info.name = 'info'    # sync_window.nml:69
        self.info.x = 1    # sync_window.nml:70
        self.info.width = _bind(    # sync_window.nml:71
            lambda _o: min(display_width(_o.text), max(0, _o.parent.width - 3))
        )
        self.info.height = 1    # sync_window.nml:72
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - _o.height))    # sync_window.nml:74

        self.show.height = 1    # sync_window.nml:79
        self.show.items = _bind(    # sync_window.nml:84
            lambda _o: [_tr('Le~f~t only'), _tr('Ri~g~ht only'), _tr('~D~ifferent'), _tr('~I~dentical')],
            yielding=True,
        )
        self.show.tooltips = _bind(    # sync_window.nml:85
            lambda _o: [_tr('List what only the left side has'), _tr('List what only the right side has'), _tr('List the files that differ, and the conflicts'), _tr('List the files that are the same on both sides too')],
            yielding=True,
        )
        self.show.x = 2    # sync_window.nml:81
        self.show.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # sync_window.nml:82
        self.show.y = _bind(    # sync_window.nml:83
            lambda _o: max(0, _o.parent.height - 4 - _o.height)
        )

        self.tree_box.x = 2    # sync_window.nml:90
        self.tree_box.width = 18    # sync_window.nml:91
        self.tree_box.height = 1    # sync_window.nml:92
        self.tree_box.items = _bind(    # sync_window.nml:95
            lambda _o: [_tr('~T~ree view')],
            yielding=True,
        )
        self.tree_box.tooltips = _bind(    # sync_window.nml:96
            lambda _o: [_tr('Show the rows under their directories, as a tree')],
            yielding=True,
        )
        self.tree_box.y = _bind(    # sync_window.nml:94
            lambda _o: max(0, _o.parent.height - 3 - _o.height)
        )

        self.summary.height = 1    # sync_window.nml:100
        self.summary.x = 2    # sync_window.nml:102
        self.summary.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # sync_window.nml:103
        self.summary.y = _bind(    # sync_window.nml:104
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )

        self.options_button.text = _bind(    # sync_window.nml:108
            lambda _o: _tr('O~p~tions'),
            yielding=True,
        )
        self.options_button.tooltip = _bind(    # sync_window.nml:109
            lambda _o: _tr('The file mask, how near two times are the same, and Asymmetric'),
            yielding=True,
        )
        self.options_button.width = 12    # sync_window.nml:110
        self.options_button.height = 2    # sync_window.nml:111
        self.options_button.x = _bind(    # sync_window.nml:113
            lambda _o: max(0, _o.parent.width - 33 - _o.width)
        )
        self.options_button.y = _bind(    # sync_window.nml:114
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.options_button.on_click = self.on_options_button_click    # sync_window.nml:107

        self.sync_button.text = _bind(    # sync_window.nml:118
            lambda _o: _tr('~S~ynchronize'),
            yielding=True,
        )
        self.sync_button.width = 16    # sync_window.nml:119
        self.sync_button.height = 2    # sync_window.nml:120
        self.sync_button.x = _bind(    # sync_window.nml:122
            lambda _o: max(0, _o.parent.width - 15 - _o.width)
        )
        self.sync_button.y = _bind(    # sync_window.nml:123
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.sync_button.on_click = self.on_sync_button_click    # sync_window.nml:117

        self.close_button.text = _bind(lambda _o: _tr('Close'), yielding=True)    # sync_window.nml:127
        self.close_button.width = 10    # sync_window.nml:128
        self.close_button.height = 2    # sync_window.nml:129
        self.close_button.x = _bind(    # sync_window.nml:131
            lambda _o: max(0, _o.parent.width - 3 - _o.width)
        )
        self.close_button.y = _bind(    # sync_window.nml:132
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )
        self.close_button.on_click = self.on_close_button_click    # sync_window.nml:126

        self.sync_menu.text = _bind(    # sync_window.nml:138
            lambda _o: _tr('~S~ynchronize'),
            yielding=True,
        )
        self.sync_menu.tooltip = _bind(    # sync_window.nml:139
            lambda _o: _tr('Choose what happens to each file, then synchronize'),
            yielding=True,
        )
        self.sync_menu.after = 'File'    # sync_window.nml:140

        _w1.text = _bind(lambda _o: _tr('~S~ynchronize'), yielding=True)    # sync_window.nml:142
        _w1.command = Synchronize    # sync_window.nml:143

        _w2.text = _bind(lambda _o: _tr('~C~ompare files'), yielding=True)    # sync_window.nml:145
        _w2.command = DiffFiles    # sync_window.nml:146

        _w4.text = _bind(lambda _o: _tr('Copy ~r~ight'), yielding=True)    # sync_window.nml:149
        _w4.command = SetSyncAction('right')    # sync_window.nml:150

        _w5.text = _bind(lambda _o: _tr('Copy ~l~eft'), yielding=True)    # sync_window.nml:152
        _w5.command = SetSyncAction('left')    # sync_window.nml:153

        _w6.text = _bind(lambda _o: _tr('~D~elete'), yielding=True)    # sync_window.nml:155
        _w6.command = SetSyncAction('delete')    # sync_window.nml:156

        _w7.text = _bind(lambda _o: _tr('S~k~ip'), yielding=True)    # sync_window.nml:158
        _w7.command = SetSyncAction('skip')    # sync_window.nml:159

        _w8.text = _bind(lambda _o: _tr('D~e~fault action'), yielding=True)    # sync_window.nml:161
        _w8.tooltip = _bind(    # sync_window.nml:162
            lambda _o: _tr('Give the row back the action the comparison chose'),
            yielding=True,
        )
        _w8.command = SetSyncAction('default')    # sync_window.nml:163

        _w10.text = _bind(lambda _o: _tr('~A~ll right'), yielding=True)    # sync_window.nml:166
        _w10.command = SetAllSyncActions('right')    # sync_window.nml:167

        _w11.text = _bind(lambda _o: _tr('All le~f~t'), yielding=True)    # sync_window.nml:169
        _w11.command = SetAllSyncActions('left')    # sync_window.nml:170

        _w12.text = _bind(lambda _o: _tr('All defa~u~lt'), yielding=True)    # sync_window.nml:172
        _w12.tooltip = _bind(    # sync_window.nml:173
            lambda _o: _tr('Give every row back the action the comparison chose'),
            yielding=True,
        )
        _w12.command = SetAllSyncActions('default')    # sync_window.nml:174

        _w14.text = _bind(lambda _o: _tr('Compare a~g~ain'), yielding=True)    # sync_window.nml:177
        _w14.command = Rescan    # sync_window.nml:178

        self.sync_menu_show.text = _bind(    # sync_window.nml:183
            lambda _o: _tr('Sho~w~'),
            yielding=True,
        )
        self.sync_menu_show.tooltip = _bind(    # sync_window.nml:184
            lambda _o: _tr('Which rows the list shows'),
            yielding=True,
        )

        _w15.text = _bind(lambda _o: _tr('Show left o~n~ly'), yielding=True)    # sync_window.nml:186
        _w15.tooltip = _bind(    # sync_window.nml:187
            lambda _o: _tr('List what only the left side has'),
            yielding=True,
        )
        _w15.command = ToggleSyncShow(0)    # sync_window.nml:188

        _w16.text = _bind(lambda _o: _tr('Show right onl~y~'), yielding=True)    # sync_window.nml:190
        _w16.tooltip = _bind(    # sync_window.nml:191
            lambda _o: _tr('List what only the right side has'),
            yielding=True,
        )
        _w16.command = ToggleSyncShow(1)    # sync_window.nml:192

        _w17.text = _bind(lambda _o: _tr('Sho~w~ different'), yielding=True)    # sync_window.nml:194
        _w17.tooltip = _bind(    # sync_window.nml:195
            lambda _o: _tr('List the files that differ, and the conflicts'),
            yielding=True,
        )
        _w17.command = ToggleSyncShow(2)    # sync_window.nml:196

        _w18.text = _bind(lambda _o: _tr('Show ~i~dentical'), yielding=True)    # sync_window.nml:198
        _w18.tooltip = _bind(    # sync_window.nml:199
            lambda _o: _tr('List the files that are the same on both sides too'),
            yielding=True,
        )
        _w18.command = ToggleHidden    # sync_window.nml:200

        _w19.text = _bind(lambda _o: _tr('~T~ree view'), yielding=True)    # sync_window.nml:202
        _w19.tooltip = _bind(    # sync_window.nml:203
            lambda _o: _tr('Show the rows under their directories, as a tree'),
            yielding=True,
        )
        _w19.command = ToggleTree    # sync_window.nml:204

        _w20.text = _bind(lambda _o: _tr('O~p~tions...'), yielding=True)    # sync_window.nml:206
        _w20.tooltip = _bind(    # sync_window.nml:207
            lambda _o: _tr('The file mask, how near two times are the same, and Asymmetric'),
            yielding=True,
        )
        _w20.command = SyncSetup    # sync_window.nml:208

        _w22.text = _bind(lambda _o: _tr('Cl~o~se'), yielding=True)    # sync_window.nml:211
        _w22.command = CloseWindow    # sync_window.nml:212
