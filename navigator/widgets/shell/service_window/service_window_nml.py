# navml: generated
"""Generated from ``service_window.nml``.

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
from navigator.widgets.manager.commands import Rescan    # service_window.nml:1
from navigator.widgets.shell.commands import DisableService, EditUnitFile, EnableService, FilterServices, MaskService, ReloadService, RestartService, ServiceAllTypes, ServiceDetails, ServiceJournal, ServiceSortActive, ServiceSortDescription, ServiceSortFileState, ServiceSortName, ServiceUserUnits, StartService, StopService, UnmaskService    # service_window.nml:2
from navigator.widgets.shell.process_list import ProcessFilter    # service_window.nml:3
from navigator.widgets.shell.service_list import ServiceList    # service_window.nml:4
from navml.commands import CloseWindow    # service_window.nml:5
from navml.widgets.dialog.button import Button    # service_window.nml:6
from navml.widgets.dialog.check_boxes import CheckBoxes    # service_window.nml:7
from navml.widgets.dialog.commands import SelectNext, SelectPrevious    # service_window.nml:8
from navml.widgets.dialog.label import Label    # service_window.nml:9
from navml.widgets.dialog.static_text import StaticText    # service_window.nml:10
from navml.widgets.menu.menu_item import MenuItem    # service_window.nml:11
from navml.widgets.menu.menu_line import MenuLine    # service_window.nml:12
from navml.widgets.menu.sub_menu import SubMenu    # service_window.nml:13
from navml.widgets.window import Window    # service_window.nml:14

__navml_component__ = "ServiceWindow"

__all__ = ["ServiceWindow"]


class ServiceWindow(Window, _Component):
    """Utilities > Services: systemd's units -- name, whether it runs, how it

    starts, what it is -- a row each, read again every ``[services] refresh``
    seconds.  **Not DOS Navigator's**: a departure, asked for -- DOS had no
    service manager.  Process list's sibling, laid out as it is;
    ``navigator/lib/system/services.py`` says how ``systemctl`` is asked.

    *Filter* and its X across the top; the list under them; the status line,
    then *User units* and *All types* on the left, *Start*, *Stop*, *Journal*,
    *Edit* and *Close* on the right, the window never narrower than all of them.

    F4 opens the unit's file in the editor, and saving it runs ``systemctl
    daemon-reload`` (as root when the user may not).  Not Filter, as F4 is in
    Process list: F4 is Edit everywhere else in Navigator.

    F5 starts the unit under the cursor, F6 restarts it, F7 reloads it, F8 or
    Del stops it after asking; Ctrl+E enables it and Ctrl+D disables it, and
    the menu masks and unmasks.  What the user may not do alone is offered *As
    root*, through the root helper's ``systemctl``.  F3 opens the unit's
    journal in the viewer, following its end; Enter says what ``systemctl
    status`` does.  Ctrl+U lists the user's own manager's units, Ctrl+A every
    type rather than services; Ctrl+N and Ctrl+L sort by name and state, as a
    click on a column's title does.  Typing, Ctrl+S or Alt+F goes to the
    filter; Esc empties it, then closes the window; Ctrl+R reads again.
    """

    #: The document this class was generated from.
    __navml_source__ = "service_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # service_window.nml:43
        'escape': CloseWindow,    # service_window.nml:44
        'ctrl+r': Rescan,    # service_window.nml:45
        'alt+r': Rescan,    # service_window.nml:46
        'f3': ServiceJournal,    # service_window.nml:47
        'f5': StartService,    # service_window.nml:48
        'f6': RestartService,    # service_window.nml:49
        'f7': ReloadService,    # service_window.nml:50
        'f8': StopService,    # service_window.nml:51
        'delete': StopService,    # service_window.nml:52
        'ctrl+e': EnableService,    # service_window.nml:53
        'ctrl+d': DisableService,    # service_window.nml:54
        'ctrl+u': ServiceUserUnits,    # service_window.nml:55
        'ctrl+a': ServiceAllTypes,    # service_window.nml:56
        'ctrl+n': ServiceSortName,    # service_window.nml:57
        'ctrl+l': ServiceSortActive,    # service_window.nml:58
        'f4': EditUnitFile,    # service_window.nml:59
        'ctrl+s': FilterServices,    # service_window.nml:60
        'tab': SelectNext,    # service_window.nml:61
        'shift+tab': SelectPrevious,    # service_window.nml:62
    }

    #: Ids, annotated so the hand-written half completes them.
    filter_caption: Label    # service_window.nml:66
    filter: ProcessFilter    # service_window.nml:77
    clear_filter: Button    # service_window.nml:86
    units: ServiceList    # service_window.nml:95
    status: StaticText    # service_window.nml:103
    user_box: CheckBoxes    # service_window.nml:111
    types_box: CheckBoxes    # service_window.nml:120
    start_button: Button    # service_window.nml:129
    stop_button: Button    # service_window.nml:138
    journal_button: Button    # service_window.nml:147
    edit_button: Button    # service_window.nml:157
    close_button: Button    # service_window.nml:166
    service_menu: SubMenu    # service_window.nml:177

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_clear_filter_click(self, event: _Event) -> bool:    # service_window.nml:86
        """``clear_filter`` raised an event whose handler is ``on_click``."""
        return False

    async def on_units_chosen(self, event: _Event) -> bool:    # service_window.nml:95
        """``units`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_units_sort_chosen(self, event: _Event) -> bool:    # service_window.nml:95
        """``units`` raised an event whose handler is ``on_sort_chosen``."""
        return False

    async def on_start_button_click(self, event: _Event) -> bool:    # service_window.nml:129
        """``start_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_stop_button_click(self, event: _Event) -> bool:    # service_window.nml:138
        """``stop_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_journal_button_click(self, event: _Event) -> bool:    # service_window.nml:147
        """``journal_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_edit_button_click(self, event: _Event) -> bool:    # service_window.nml:157
        """``edit_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_close_button_click(self, event: _Event) -> bool:    # service_window.nml:166
        """``close_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.filter_caption = Label(parent=self)    # service_window.nml:65
        self.filter = ProcessFilter(parent=self)    # service_window.nml:76
        self.clear_filter = Button(parent=self)    # service_window.nml:85
        self.units = ServiceList(parent=self)    # service_window.nml:94
        self.status = StaticText(parent=self)    # service_window.nml:102
        self.user_box = CheckBoxes(parent=self)    # service_window.nml:110
        self.types_box = CheckBoxes(parent=self)    # service_window.nml:119
        self.start_button = Button(parent=self)    # service_window.nml:128
        self.stop_button = Button(parent=self)    # service_window.nml:137
        self.journal_button = Button(parent=self)    # service_window.nml:146
        self.edit_button = Button(parent=self)    # service_window.nml:156
        self.close_button = Button(parent=self)    # service_window.nml:165
        self.service_menu = SubMenu(parent=self)    # service_window.nml:176
        _w1 = MenuItem(parent=self.service_menu)    # service_window.nml:181
        _w2 = MenuLine(parent=self.service_menu)    # service_window.nml:185
        _w3 = MenuItem(parent=self.service_menu)    # service_window.nml:186
        _w4 = MenuItem(parent=self.service_menu)    # service_window.nml:190
        _w5 = MenuItem(parent=self.service_menu)    # service_window.nml:194
        _w6 = MenuItem(parent=self.service_menu)    # service_window.nml:197
        _w7 = MenuLine(parent=self.service_menu)    # service_window.nml:200
        _w8 = MenuItem(parent=self.service_menu)    # service_window.nml:201
        _w9 = MenuItem(parent=self.service_menu)    # service_window.nml:206
        _w10 = MenuItem(parent=self.service_menu)    # service_window.nml:211
        _w11 = MenuLine(parent=self.service_menu)    # service_window.nml:216
        _w12 = MenuItem(parent=self.service_menu)    # service_window.nml:217
        _w13 = MenuItem(parent=self.service_menu)    # service_window.nml:222
        _w14 = MenuItem(parent=self.service_menu)    # service_window.nml:227
        _w15 = MenuLine(parent=self.service_menu)    # service_window.nml:231
        _w16 = MenuItem(parent=self.service_menu)    # service_window.nml:232
        _w17 = MenuItem(parent=self.service_menu)    # service_window.nml:236
        _w18 = MenuItem(parent=self.service_menu)    # service_window.nml:240
        _w19 = MenuItem(parent=self.service_menu)    # service_window.nml:244
        _w20 = MenuLine(parent=self.service_menu)    # service_window.nml:248
        _w21 = MenuItem(parent=self.service_menu)    # service_window.nml:249
        _w22 = MenuItem(parent=self.service_menu)    # service_window.nml:254
        _w23 = MenuItem(parent=self.service_menu)    # service_window.nml:259
        _w24 = MenuItem(parent=self.service_menu)    # service_window.nml:263
        _w25 = MenuLine(parent=self.service_menu)    # service_window.nml:266
        _w26 = MenuItem(parent=self.service_menu)    # service_window.nml:267

        self.title = _bind(lambda _o: _tr('Services'), yielding=True)    # service_window.nml:40
        self.min_width = _bind(    # service_window.nml:41
            lambda _o: max(self.user_box.width, self.types_box.width) + self.start_button.width + self.stop_button.width + self.journal_button.width + self.edit_button.width + self.close_button.width + 9
        )

        self.filter_caption.x = 2    # service_window.nml:67
        self.filter_caption.y = 1    # service_window.nml:68
        self.filter_caption.width = _bind(    # service_window.nml:69
            lambda _o: self.caption_width(_o.text) + 1
        )
        self.filter_caption.height = 1    # service_window.nml:70
        self.filter_caption.text = _bind(    # service_window.nml:71
            lambda _o: _tr('~F~ilter'),
            yielding=True,
        )
        self.filter_caption.link = _bind(lambda _o: self.filter)    # service_window.nml:72

        self.filter.x = _bind(    # service_window.nml:78
            lambda _o: self.filter_caption.x + self.filter_caption.width
        )
        self.filter.y = 1    # service_window.nml:79
        self.filter.width = _bind(    # service_window.nml:80
            lambda _o: max(1, _o.parent.width - 6 - _o.x)
        )
        self.filter.height = 1    # service_window.nml:81
        self.filter.tooltip = _bind(    # service_window.nml:82
            lambda _o: _tr('Show only the units whose name or description holds this'),
            yielding=True,
        )

        self.clear_filter.flat = True    # service_window.nml:87
        self.clear_filter.x = _bind(lambda _o: max(0, _o.parent.width - 5))    # service_window.nml:88
        self.clear_filter.y = 1    # service_window.nml:89
        self.clear_filter.width = 3    # service_window.nml:90
        self.clear_filter.height = 1    # service_window.nml:91
        self.clear_filter.tooltip = _bind(    # service_window.nml:92
            lambda _o: _tr('Clear the filter'),
            yielding=True,
        )
        self.clear_filter.on_click = self.on_clear_filter_click    # service_window.nml:86

        self.units.framed = False    # service_window.nml:96
        self.units.x = 1    # service_window.nml:97
        self.units.y = 2    # service_window.nml:98
        self.units.width = _bind(lambda _o: max(0, _o.parent.width - 1))    # service_window.nml:99
        self.units.height = _bind(lambda _o: max(0, _o.parent.height - 6))    # service_window.nml:100
        self.units.on_chosen = self.on_units_chosen    # service_window.nml:95
        self.units.on_sort_chosen = self.on_units_sort_chosen    # service_window.nml:95

        self.status.x = 2    # service_window.nml:104
        self.status.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # service_window.nml:105
        self.status.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # service_window.nml:106
        self.status.height = 1    # service_window.nml:107

        self.user_box.x = 2    # service_window.nml:112
        self.user_box.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # service_window.nml:113
        self.user_box.width = _bind(lambda _o: _o.column_x(1))    # service_window.nml:114
        self.user_box.height = 1    # service_window.nml:115
        self.user_box.items = _bind(    # service_window.nml:116
            lambda _o: [_tr('~U~ser units')],
            yielding=True,
        )
        self.user_box.tooltips = _bind(    # service_window.nml:117
            lambda _o: [_tr("Your own service manager's units (systemctl --user), not the system's")],
            yielding=True,
        )

        self.types_box.x = 2    # service_window.nml:121
        self.types_box.y = _bind(lambda _o: max(0, _o.parent.height - 2))    # service_window.nml:122
        self.types_box.width = _bind(lambda _o: _o.column_x(1))    # service_window.nml:123
        self.types_box.height = 1    # service_window.nml:124
        self.types_box.items = _bind(    # service_window.nml:125
            lambda _o: [_tr('~A~ll types')],
            yielding=True,
        )
        self.types_box.tooltips = _bind(    # service_window.nml:126
            lambda _o: [_tr('Timers, sockets, mounts and the rest too, not only services')],
            yielding=True,
        )

        self.start_button.text = _bind(    # service_window.nml:130
            lambda _o: _tr('S~t~art'),
            yielding=True,
        )
        self.start_button.x = _bind(    # service_window.nml:131
            lambda _o: max(0, self.stop_button.x - 1 - _o.width)
        )
        self.start_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # service_window.nml:132
        self.start_button.width = _bind(    # service_window.nml:133
            lambda _o: self.caption_width(_o.text) + 5
        )
        self.start_button.height = 2    # service_window.nml:134
        self.start_button.disabled = _bind(lambda _o: not self.allows())    # service_window.nml:135
        self.start_button.on_click = self.on_start_button_click    # service_window.nml:129

        self.stop_button.text = _bind(lambda _o: _tr('St~o~p'), yielding=True)    # service_window.nml:139
        self.stop_button.x = _bind(    # service_window.nml:140
            lambda _o: max(0, self.journal_button.x - 1 - _o.width)
        )
        self.stop_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # service_window.nml:141
        self.stop_button.width = _bind(    # service_window.nml:142
            lambda _o: self.caption_width(_o.text) + 5
        )
        self.stop_button.height = 2    # service_window.nml:143
        self.stop_button.disabled = _bind(lambda _o: not self.allows())    # service_window.nml:144
        self.stop_button.on_click = self.on_stop_button_click    # service_window.nml:138

        self.journal_button.text = _bind(    # service_window.nml:148
            lambda _o: _tr('~J~ournal'),
            yielding=True,
        )
        self.journal_button.default = True    # service_window.nml:149
        self.journal_button.x = _bind(    # service_window.nml:150
            lambda _o: max(0, self.edit_button.x - 1 - _o.width)
        )
        self.journal_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # service_window.nml:151
        self.journal_button.width = _bind(    # service_window.nml:152
            lambda _o: self.caption_width(_o.text) + 5
        )
        self.journal_button.height = 2    # service_window.nml:153
        self.journal_button.disabled = _bind(lambda _o: not self.allows())    # service_window.nml:154
        self.journal_button.on_click = self.on_journal_button_click    # service_window.nml:147

        self.edit_button.text = _bind(lambda _o: _tr('~E~dit'), yielding=True)    # service_window.nml:158
        self.edit_button.x = _bind(    # service_window.nml:159
            lambda _o: max(0, self.close_button.x - 1 - _o.width)
        )
        self.edit_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # service_window.nml:160
        self.edit_button.width = _bind(    # service_window.nml:161
            lambda _o: self.caption_width(_o.text) + 5
        )
        self.edit_button.height = 2    # service_window.nml:162
        self.edit_button.disabled = _bind(lambda _o: not self.allows())    # service_window.nml:163
        self.edit_button.on_click = self.on_edit_button_click    # service_window.nml:157

        self.close_button.text = _bind(lambda _o: _tr('Close'), yielding=True)    # service_window.nml:167
        self.close_button.x = _bind(    # service_window.nml:168
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )
        self.close_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # service_window.nml:169
        self.close_button.width = _bind(    # service_window.nml:170
            lambda _o: self.caption_width(_o.text) + 5
        )
        self.close_button.height = 2    # service_window.nml:171
        self.close_button.on_click = self.on_close_button_click    # service_window.nml:166

        self.service_menu.text = _bind(    # service_window.nml:178
            lambda _o: _tr('~S~ervices'),
            yielding=True,
        )
        self.service_menu.tooltip = _bind(    # service_window.nml:179
            lambda _o: _tr("Start, stop, enable and follow systemd's units"),
            yielding=True,
        )
        self.service_menu.after = 'File'    # service_window.nml:180

        _w1.text = _bind(lambda _o: _tr('~R~e-read'), yielding=True)    # service_window.nml:182
        _w1.command = Rescan    # service_window.nml:183
        _w1.key = 'Ctrl-R'    # service_window.nml:184

        _w3.text = _bind(lambda _o: _tr('Sort by ~n~ame'), yielding=True)    # service_window.nml:187
        _w3.command = ServiceSortName    # service_window.nml:188
        _w3.key = 'Ctrl-N'    # service_window.nml:189

        _w4.text = _bind(lambda _o: _tr('Sort by ~s~tate'), yielding=True)    # service_window.nml:191
        _w4.command = ServiceSortActive    # service_window.nml:192
        _w4.key = 'Ctrl-L'    # service_window.nml:193

        _w5.text = _bind(lambda _o: _tr('Sort by start-~u~p'), yielding=True)    # service_window.nml:195
        _w5.command = ServiceSortFileState    # service_window.nml:196

        _w6.text = _bind(    # service_window.nml:198
            lambda _o: _tr('Sort by ~d~escription'),
            yielding=True,
        )
        _w6.command = ServiceSortDescription    # service_window.nml:199

        _w8.text = _bind(lambda _o: _tr('Us~e~r units'), yielding=True)    # service_window.nml:202
        _w8.tooltip = _bind(    # service_window.nml:203
            lambda _o: _tr("Your own service manager's units (systemctl --user), not the system's"),
            yielding=True,
        )
        _w8.command = ServiceUserUnits    # service_window.nml:204
        _w8.key = 'Ctrl-U'    # service_window.nml:205

        _w9.text = _bind(lambda _o: _tr('~A~ll types'), yielding=True)    # service_window.nml:207
        _w9.tooltip = _bind(    # service_window.nml:208
            lambda _o: _tr('Timers, sockets, mounts and the rest too, not only services'),
            yielding=True,
        )
        _w9.command = ServiceAllTypes    # service_window.nml:209
        _w9.key = 'Ctrl-A'    # service_window.nml:210

        _w10.text = _bind(lambda _o: _tr('~F~ilter'), yielding=True)    # service_window.nml:212
        _w10.tooltip = _bind(    # service_window.nml:213
            lambda _o: _tr('Show only the units whose name or description holds what is typed'),
            yielding=True,
        )
        _w10.command = FilterServices    # service_window.nml:214
        _w10.key = 'Ctrl-S'    # service_window.nml:215

        _w12.text = _bind(lambda _o: _tr('~J~ournal'), yielding=True)    # service_window.nml:218
        _w12.tooltip = _bind(    # service_window.nml:219
            lambda _o: _tr("The unit's journal in the viewer, following its end"),
            yielding=True,
        )
        _w12.command = ServiceJournal    # service_window.nml:220
        _w12.key = 'F3'    # service_window.nml:221

        _w13.text = _bind(lambda _o: _tr('Edit unit file'), yielding=True)    # service_window.nml:223
        _w13.tooltip = _bind(    # service_window.nml:224
            lambda _o: _tr("The unit's file in the editor, a package's through a drop-in override; saved, systemd reads its unit files again"),
            yielding=True,
        )
        _w13.command = EditUnitFile    # service_window.nml:225
        _w13.key = 'F4'    # service_window.nml:226

        _w14.text = _bind(lambda _o: _tr('Detai~l~s...'), yielding=True)    # service_window.nml:228
        _w14.command = ServiceDetails    # service_window.nml:229
        _w14.key = 'Enter'    # service_window.nml:230

        _w16.text = _bind(lambda _o: _tr('S~t~art'), yielding=True)    # service_window.nml:233
        _w16.command = StartService    # service_window.nml:234
        _w16.key = 'F5'    # service_window.nml:235

        _w17.text = _bind(lambda _o: _tr('Restart'), yielding=True)    # service_window.nml:237
        _w17.command = RestartService    # service_window.nml:238
        _w17.key = 'F6'    # service_window.nml:239

        _w18.text = _bind(lambda _o: _tr('Rel~o~ad'), yielding=True)    # service_window.nml:241
        _w18.command = ReloadService    # service_window.nml:242
        _w18.key = 'F7'    # service_window.nml:243

        _w19.text = _bind(lambda _o: _tr('Sto~p~...'), yielding=True)    # service_window.nml:245
        _w19.command = StopService    # service_window.nml:246
        _w19.key = 'F8'    # service_window.nml:247

        _w21.text = _bind(lambda _o: _tr('Ena~b~le'), yielding=True)    # service_window.nml:250
        _w21.tooltip = _bind(    # service_window.nml:251
            lambda _o: _tr('Started at boot, or at log-in for a user unit'),
            yielding=True,
        )
        _w21.command = EnableService    # service_window.nml:252
        _w21.key = 'Ctrl-E'    # service_window.nml:253

        _w22.text = _bind(lambda _o: _tr('D~i~sable'), yielding=True)    # service_window.nml:255
        _w22.tooltip = _bind(    # service_window.nml:256
            lambda _o: _tr('Not started at boot any more'),
            yielding=True,
        )
        _w22.command = DisableService    # service_window.nml:257
        _w22.key = 'Ctrl-D'    # service_window.nml:258

        _w23.text = _bind(lambda _o: _tr('~M~ask...'), yielding=True)    # service_window.nml:260
        _w23.tooltip = _bind(    # service_window.nml:261
            lambda _o: _tr('Never started, not even by another unit'),
            yielding=True,
        )
        _w23.command = MaskService    # service_window.nml:262

        _w24.text = _bind(lambda _o: _tr('Unmas~k~'), yielding=True)    # service_window.nml:264
        _w24.command = UnmaskService    # service_window.nml:265

        _w26.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # service_window.nml:268
        _w26.command = CloseWindow    # service_window.nml:269
