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
from navkit.i18n import verbatim    # service_window.nml:15

__navml_component__ = "ServiceWindow"

__all__ = ["ServiceWindow"]


class ServiceWindow(Window, _Component):
    """Utilities > Services: the system's services -- systemd's units, OpenRC's,

    runit's or SysVinit's services: name, whether it runs, how it starts, what it is -- a row each,
    read again every ``[services] refresh`` seconds.  **Not DOS Navigator's**:
    a departure, asked for -- DOS had no service manager.  Process list's
    sibling, laid out as it is; ``navigator/lib/system/services/`` says how
    each manager is asked, and what one has not is greyed with the reason.

    *Filter* and its X across the top; the list under them; the status line,
    then *User units* and *All types* on the left, *Start*, *Stop*, *Journal*,
    *Edit* and *Close* on the right, the window never narrower than all of them.

    F4 opens the unit's file in the editor -- a package's through a drop-in, an
    OpenRC service's ``/etc/conf.d`` file -- and saving it runs ``systemctl
    daemon-reload`` (as root when the user may not), or OpenRC offers a restart.  Not Filter, as F4 is in
    Process list: F4 is Edit everywhere else in Navigator.

    F5 starts the unit under the cursor, F6 restarts it, F7 reloads it, F8 or
    Del stops it after asking; Ctrl+E enables it and Ctrl+D disables it, and
    the menu masks and unmasks.  What the user may not do alone is offered *As
    root*, through the root helper's ``service``.  F3 opens the unit's
    journal (OpenRC: its log, or the system log's lines naming it) in the
    viewer, following its end; Enter says what its status is.  Ctrl+U lists the user's own manager's units, Ctrl+A every
    type rather than services; Ctrl+N and Ctrl+L sort by name and state, as a
    click on a column's title does.  Typing, Ctrl+S or Alt+F goes to the
    filter; Esc empties it, then closes the window; Ctrl+R reads again.
    """

    #: The document this class was generated from.
    __navml_source__ = "service_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # service_window.nml:46
        'escape': CloseWindow,    # service_window.nml:47
        'ctrl+r': Rescan,    # service_window.nml:48
        'alt+r': Rescan,    # service_window.nml:49
        'f3': ServiceJournal,    # service_window.nml:50
        'f5': StartService,    # service_window.nml:51
        'f6': RestartService,    # service_window.nml:52
        'f7': ReloadService,    # service_window.nml:53
        'f8': StopService,    # service_window.nml:54
        'delete': StopService,    # service_window.nml:55
        'ctrl+e': EnableService,    # service_window.nml:56
        'ctrl+d': DisableService,    # service_window.nml:57
        'ctrl+u': ServiceUserUnits,    # service_window.nml:58
        'ctrl+a': ServiceAllTypes,    # service_window.nml:59
        'ctrl+n': ServiceSortName,    # service_window.nml:60
        'ctrl+l': ServiceSortActive,    # service_window.nml:61
        'f4': EditUnitFile,    # service_window.nml:62
        'ctrl+s': FilterServices,    # service_window.nml:63
        'tab': SelectNext,    # service_window.nml:64
        'shift+tab': SelectPrevious,    # service_window.nml:65
    }

    #: Ids, annotated so the hand-written half completes them.
    filter_caption: Label    # service_window.nml:81
    filter: ProcessFilter    # service_window.nml:91
    clear_filter: Button    # service_window.nml:100
    units: ServiceList    # service_window.nml:112
    status: StaticText    # service_window.nml:121
    user_box: CheckBoxes    # service_window.nml:129
    types_box: CheckBoxes    # service_window.nml:139
    start_button: Button    # service_window.nml:149
    stop_button: Button    # service_window.nml:160
    journal_button: Button    # service_window.nml:171
    edit_button: Button    # service_window.nml:183
    close_button: Button    # service_window.nml:194
    service_menu: SubMenu    # service_window.nml:207

    #: The commands this component handles itself.
    async def on_service_sort_name(self, event: _Any) -> bool:    # service_window.nml:69
        """``ServiceSortName``."""
        self._sort_by('name')
        return True

    async def on_service_sort_active(self, event: _Any) -> bool:    # service_window.nml:70
        """``ServiceSortActive``."""
        self._sort_by('active')
        return True

    async def on_service_sort_file_state(self, event: _Any) -> bool:    # service_window.nml:71
        """``ServiceSortFileState``."""
        self._sort_by('startup')
        return True

    async def on_service_sort_description(self, event: _Any) -> bool:    # service_window.nml:72
        """``ServiceSortDescription``."""
        self._sort_by('description')
        return True

    async def on_rescan(self, event: _Any) -> bool:    # service_window.nml:73
        """``Rescan``."""
        self.spawn(self._rescan())
        return True

    async def on_select_next(self, event: _Any) -> bool:    # service_window.nml:74
        """``SelectNext``."""
        self._step(1)
        return True

    async def on_select_previous(self, event: _Any) -> bool:    # service_window.nml:75
        """``SelectPrevious``."""
        self._step(-1)
        return True

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_clear_filter_click(self, event: _Event) -> bool:    # service_window.nml:100
        """``clear_filter`` raised an event whose handler is ``on_click``."""
        return False

    async def on_units_chosen(self, event: _Event) -> bool:    # service_window.nml:112
        """``units`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_units_sort_chosen(self, event: _Event) -> bool:    # service_window.nml:112
        """``units`` raised an event whose handler is ``on_sort_chosen``."""
        return False

    async def on_start_button_click(self, event: _Event) -> bool:    # service_window.nml:149
        """``start_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_stop_button_click(self, event: _Event) -> bool:    # service_window.nml:160
        """``stop_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_journal_button_click(self, event: _Event) -> bool:    # service_window.nml:171
        """``journal_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_edit_button_click(self, event: _Event) -> bool:    # service_window.nml:183
        """``edit_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.filter_caption = Label(parent=self)    # service_window.nml:80
        self.filter = ProcessFilter(parent=self)    # service_window.nml:90
        self.clear_filter = Button(parent=self)    # service_window.nml:99
        self.units = ServiceList(parent=self)    # service_window.nml:111
        self.status = StaticText(parent=self)    # service_window.nml:120
        self.user_box = CheckBoxes(parent=self)    # service_window.nml:128
        self.types_box = CheckBoxes(parent=self)    # service_window.nml:138
        self.start_button = Button(parent=self)    # service_window.nml:148
        self.stop_button = Button(parent=self)    # service_window.nml:159
        self.journal_button = Button(parent=self)    # service_window.nml:170
        self.edit_button = Button(parent=self)    # service_window.nml:182
        self.close_button = Button(parent=self)    # service_window.nml:193
        self.service_menu = SubMenu(parent=self)    # service_window.nml:206
        _w1 = MenuItem(parent=self.service_menu)    # service_window.nml:209
        _w2 = MenuLine(parent=self.service_menu)    # service_window.nml:210
        _w3 = MenuItem(parent=self.service_menu)    # service_window.nml:211
        _w4 = MenuItem(parent=self.service_menu)    # service_window.nml:212
        _w5 = MenuItem(parent=self.service_menu)    # service_window.nml:213
        _w6 = MenuItem(parent=self.service_menu)    # service_window.nml:214
        _w7 = MenuLine(parent=self.service_menu)    # service_window.nml:215
        _w8 = MenuItem(parent=self.service_menu)    # service_window.nml:216
        _w9 = MenuItem(parent=self.service_menu)    # service_window.nml:218
        _w10 = MenuItem(parent=self.service_menu)    # service_window.nml:220
        _w11 = MenuLine(parent=self.service_menu)    # service_window.nml:222
        _w12 = MenuItem(parent=self.service_menu)    # service_window.nml:223
        _w13 = MenuItem(parent=self.service_menu)    # service_window.nml:225
        _w14 = MenuItem(parent=self.service_menu)    # service_window.nml:227
        _w15 = MenuLine(parent=self.service_menu)    # service_window.nml:228
        _w16 = MenuItem(parent=self.service_menu)    # service_window.nml:229
        _w17 = MenuItem(parent=self.service_menu)    # service_window.nml:230
        _w18 = MenuItem(parent=self.service_menu)    # service_window.nml:231
        _w19 = MenuItem(parent=self.service_menu)    # service_window.nml:232
        _w20 = MenuLine(parent=self.service_menu)    # service_window.nml:233
        _w21 = MenuItem(parent=self.service_menu)    # service_window.nml:234
        _w22 = MenuItem(parent=self.service_menu)    # service_window.nml:236
        _w23 = MenuItem(parent=self.service_menu)    # service_window.nml:238
        _w24 = MenuItem(parent=self.service_menu)    # service_window.nml:240
        _w25 = MenuLine(parent=self.service_menu)    # service_window.nml:241
        _w26 = MenuItem(parent=self.service_menu)    # service_window.nml:242

        self.title = _bind(lambda _o: _tr('Services'), yielding=True)    # service_window.nml:43
        self.min_width = _bind(    # service_window.nml:44
            lambda _o: max(self.user_box.width, self.types_box.width) + self.start_button.width + self.stop_button.width + self.journal_button.width + self.edit_button.width + self.close_button.width + 9
        )
        self.first_focus = _bind(lambda _o: self.units)    # service_window.nml:77

        self.filter_caption.x = 2    # service_window.nml:82
        self.filter_caption.y = 1    # service_window.nml:83
        self.filter_caption.width = _bind(    # service_window.nml:84
            lambda _o: self.caption_width(_o.text) + 1
        )
        self.filter_caption.text = _bind(    # service_window.nml:85
            lambda _o: _tr('~F~ilter'),
            yielding=True,
        )
        self.filter_caption.link = _bind(lambda _o: self.filter)    # service_window.nml:86

        self.filter.y = 1    # service_window.nml:92
        self.filter.width = _bind(    # service_window.nml:93
            lambda _o: max(1, _o.parent.width - 6 - _o.x)
        )
        self.filter.tooltip = _bind(    # service_window.nml:96
            lambda _o: _tr('Show only the units whose name or description holds this'),
            yielding=True,
        )
        self.filter.x = _bind(    # service_window.nml:95
            lambda _o: self.filter_caption.x + self.filter_caption.width
        )

        self.clear_filter.text = verbatim('X')    # service_window.nml:102
        self.clear_filter.flat = True    # service_window.nml:103
        self.clear_filter.y = 1    # service_window.nml:104
        self.clear_filter.width = 3    # service_window.nml:105
        self.clear_filter.height = 1    # service_window.nml:106
        self.clear_filter.tooltip = _bind(    # service_window.nml:109
            lambda _o: _tr('Clear the filter'),
            yielding=True,
        )
        self.clear_filter.x = _bind(    # service_window.nml:108
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )
        self.clear_filter.on_click = self.on_clear_filter_click    # service_window.nml:100

        self.units.framed = False    # service_window.nml:113
        self.units.x = 1    # service_window.nml:115
        self.units.width = _bind(lambda _o: max(0, _o.parent.width - 1))    # service_window.nml:116
        self.units.y = 2    # service_window.nml:117
        self.units.height = _bind(lambda _o: max(0, _o.parent.height - 6))    # service_window.nml:118
        self.units.on_chosen = self.on_units_chosen    # service_window.nml:112
        self.units.on_sort_chosen = self.on_units_sort_chosen    # service_window.nml:112

        self.status.x = 2    # service_window.nml:123
        self.status.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # service_window.nml:124
        self.status.y = _bind(    # service_window.nml:125
            lambda _o: max(0, _o.parent.height - 3 - _o.height)
        )

        self.user_box.x = 2    # service_window.nml:130
        self.user_box.width = _bind(lambda _o: _o.column_x(1))    # service_window.nml:131
        self.user_box.height = 1    # service_window.nml:132
        self.user_box.items = _bind(    # service_window.nml:135
            lambda _o: [_tr('~U~ser units')],
            yielding=True,
        )
        self.user_box.tooltips = _bind(    # service_window.nml:136
            lambda _o: [_tr("Your own service manager's units (systemctl --user), not the system's")],
            yielding=True,
        )
        self.user_box.y = _bind(    # service_window.nml:134
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )

        self.types_box.x = 2    # service_window.nml:140
        self.types_box.width = _bind(lambda _o: _o.column_x(1))    # service_window.nml:141
        self.types_box.height = 1    # service_window.nml:142
        self.types_box.items = _bind(    # service_window.nml:145
            lambda _o: [_tr('~A~ll types')],
            yielding=True,
        )
        self.types_box.tooltips = _bind(    # service_window.nml:146
            lambda _o: [_tr('Timers, sockets, mounts and the rest too, not only services')],
            yielding=True,
        )
        self.types_box.y = _bind(    # service_window.nml:144
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )

        self.start_button.text = _bind(    # service_window.nml:150
            lambda _o: _tr('S~t~art'),
            yielding=True,
        )
        self.start_button.width = _bind(    # service_window.nml:151
            lambda _o: self.caption_width(_o.text) + 5
        )
        self.start_button.height = 2    # service_window.nml:152
        self.start_button.disabled = _bind(lambda _o: not self.allows())    # service_window.nml:156
        self.start_button.command = StartService    # service_window.nml:157
        self.start_button.x = _bind(    # service_window.nml:154
            lambda _o: max(0, self.stop_button.x - 1 - _o.width)
        )
        self.start_button.y = _bind(    # service_window.nml:155
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )
        self.start_button.on_click = self.on_start_button_click    # service_window.nml:149

        self.stop_button.text = _bind(lambda _o: _tr('St~o~p'), yielding=True)    # service_window.nml:161
        self.stop_button.width = _bind(    # service_window.nml:162
            lambda _o: self.caption_width(_o.text) + 5
        )
        self.stop_button.height = 2    # service_window.nml:163
        self.stop_button.disabled = _bind(lambda _o: not self.allows())    # service_window.nml:167
        self.stop_button.command = StopService    # service_window.nml:168
        self.stop_button.x = _bind(    # service_window.nml:165
            lambda _o: max(0, self.journal_button.x - 1 - _o.width)
        )
        self.stop_button.y = _bind(    # service_window.nml:166
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )
        self.stop_button.on_click = self.on_stop_button_click    # service_window.nml:160

        self.journal_button.text = _bind(    # service_window.nml:172
            lambda _o: _tr('~J~ournal'),
            yielding=True,
        )
        self.journal_button.default = True    # service_window.nml:173
        self.journal_button.width = _bind(    # service_window.nml:174
            lambda _o: self.caption_width(_o.text) + 5
        )
        self.journal_button.height = 2    # service_window.nml:175
        self.journal_button.disabled = _bind(lambda _o: not self.allows())    # service_window.nml:179
        self.journal_button.command = ServiceJournal    # service_window.nml:180
        self.journal_button.x = _bind(    # service_window.nml:177
            lambda _o: max(0, self.edit_button.x - 1 - _o.width)
        )
        self.journal_button.y = _bind(    # service_window.nml:178
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )
        self.journal_button.on_click = self.on_journal_button_click    # service_window.nml:171

        self.edit_button.text = _bind(lambda _o: _tr('~E~dit'), yielding=True)    # service_window.nml:184
        self.edit_button.width = _bind(    # service_window.nml:185
            lambda _o: self.caption_width(_o.text) + 5
        )
        self.edit_button.height = 2    # service_window.nml:186
        self.edit_button.disabled = _bind(lambda _o: not self.allows())    # service_window.nml:190
        self.edit_button.command = EditUnitFile    # service_window.nml:191
        self.edit_button.x = _bind(    # service_window.nml:188
            lambda _o: max(0, self.close_button.x - 1 - _o.width)
        )
        self.edit_button.y = _bind(    # service_window.nml:189
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )
        self.edit_button.on_click = self.on_edit_button_click    # service_window.nml:183

        self.close_button.text = _bind(lambda _o: _tr('Close'), yielding=True)    # service_window.nml:195
        self.close_button.width = _bind(    # service_window.nml:196
            lambda _o: self.caption_width(_o.text) + 5
        )
        self.close_button.height = 2    # service_window.nml:197
        self.close_button.x = _bind(    # service_window.nml:199
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )
        self.close_button.y = _bind(    # service_window.nml:200
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )

        async def _on_click(event):    # service_window.nml:201
            self.request_close()
            return True
        self.close_button.on_click = _on_click

        self.service_menu.text = _bind(    # service_window.nml:206
            lambda _o: _tr('~S~ervices'),
            yielding=True,
        )
        self.service_menu.after = 'File'    # service_window.nml:206
        self.service_menu.tooltip = _bind(    # service_window.nml:208
            lambda _o: _tr("Start, stop, enable and follow the system's services"),
            yielding=True,
        )

        _w1.text = _bind(lambda _o: _tr('~R~e-read'), yielding=True)    # service_window.nml:209
        _w1.command = Rescan    # service_window.nml:209
        _w1.key = 'Ctrl-R'    # service_window.nml:209

        _w3.text = _bind(lambda _o: _tr('Sort by ~n~ame'), yielding=True)    # service_window.nml:211
        _w3.command = ServiceSortName    # service_window.nml:211
        _w3.key = 'Ctrl-N'    # service_window.nml:211

        _w4.text = _bind(lambda _o: _tr('Sort by ~s~tate'), yielding=True)    # service_window.nml:212
        _w4.command = ServiceSortActive    # service_window.nml:212
        _w4.key = 'Ctrl-L'    # service_window.nml:212

        _w5.text = _bind(lambda _o: _tr('Sort by start-~u~p'), yielding=True)    # service_window.nml:213
        _w5.command = ServiceSortFileState    # service_window.nml:213

        _w6.text = _bind(    # service_window.nml:214
            lambda _o: _tr('Sort by ~d~escription'),
            yielding=True,
        )
        _w6.command = ServiceSortDescription    # service_window.nml:214

        _w8.text = _bind(lambda _o: _tr('Us~e~r units'), yielding=True)    # service_window.nml:216
        _w8.command = ServiceUserUnits    # service_window.nml:216
        _w8.key = 'Ctrl-U'    # service_window.nml:216
        _w8.tooltip = _bind(    # service_window.nml:217
            lambda _o: _tr("Your own service manager's units (systemctl --user), not the system's"),
            yielding=True,
        )

        _w9.text = _bind(lambda _o: _tr('~A~ll types'), yielding=True)    # service_window.nml:218
        _w9.command = ServiceAllTypes    # service_window.nml:218
        _w9.key = 'Ctrl-A'    # service_window.nml:218
        _w9.tooltip = _bind(    # service_window.nml:219
            lambda _o: _tr('Timers, sockets, mounts and the rest too, not only services'),
            yielding=True,
        )

        _w10.text = _bind(lambda _o: _tr('~F~ilter'), yielding=True)    # service_window.nml:220
        _w10.command = FilterServices    # service_window.nml:220
        _w10.key = 'Ctrl-S'    # service_window.nml:220
        _w10.tooltip = _bind(    # service_window.nml:221
            lambda _o: _tr('Show only the units whose name or description holds what is typed'),
            yielding=True,
        )

        _w12.text = _bind(lambda _o: _tr('~J~ournal'), yielding=True)    # service_window.nml:223
        _w12.command = ServiceJournal    # service_window.nml:223
        _w12.key = 'F3'    # service_window.nml:223
        _w12.tooltip = _bind(    # service_window.nml:224
            lambda _o: _tr("The unit's journal in the viewer, following its end"),
            yielding=True,
        )

        _w13.text = _bind(lambda _o: _tr('Edit unit file'), yielding=True)    # service_window.nml:225
        _w13.command = EditUnitFile    # service_window.nml:225
        _w13.key = 'F4'    # service_window.nml:225
        _w13.tooltip = _bind(    # service_window.nml:226
            lambda _o: _tr("The unit's file in the editor, a package's through a drop-in override; saved, systemd reads its unit files again"),
            yielding=True,
        )

        _w14.text = _bind(lambda _o: _tr('Detai~l~s...'), yielding=True)    # service_window.nml:227
        _w14.command = ServiceDetails    # service_window.nml:227
        _w14.key = 'Enter'    # service_window.nml:227

        _w16.text = _bind(lambda _o: _tr('S~t~art'), yielding=True)    # service_window.nml:229
        _w16.command = StartService    # service_window.nml:229
        _w16.key = 'F5'    # service_window.nml:229

        _w17.text = _bind(lambda _o: _tr('Restart'), yielding=True)    # service_window.nml:230
        _w17.command = RestartService    # service_window.nml:230
        _w17.key = 'F6'    # service_window.nml:230

        _w18.text = _bind(lambda _o: _tr('Rel~o~ad'), yielding=True)    # service_window.nml:231
        _w18.command = ReloadService    # service_window.nml:231
        _w18.key = 'F7'    # service_window.nml:231

        _w19.text = _bind(lambda _o: _tr('Sto~p~...'), yielding=True)    # service_window.nml:232
        _w19.command = StopService    # service_window.nml:232
        _w19.key = 'F8'    # service_window.nml:232

        _w21.text = _bind(lambda _o: _tr('Ena~b~le'), yielding=True)    # service_window.nml:234
        _w21.command = EnableService    # service_window.nml:234
        _w21.key = 'Ctrl-E'    # service_window.nml:234
        _w21.tooltip = _bind(    # service_window.nml:235
            lambda _o: _tr('Started at boot, or at log-in for a user unit'),
            yielding=True,
        )

        _w22.text = _bind(lambda _o: _tr('D~i~sable'), yielding=True)    # service_window.nml:236
        _w22.command = DisableService    # service_window.nml:236
        _w22.key = 'Ctrl-D'    # service_window.nml:236
        _w22.tooltip = _bind(    # service_window.nml:237
            lambda _o: _tr('Not started at boot any more'),
            yielding=True,
        )

        _w23.text = _bind(lambda _o: _tr('~M~ask...'), yielding=True)    # service_window.nml:238
        _w23.command = MaskService    # service_window.nml:238
        _w23.tooltip = _bind(    # service_window.nml:239
            lambda _o: _tr('Never started, not even by another unit'),
            yielding=True,
        )

        _w24.text = _bind(lambda _o: _tr('Unmas~k~'), yielding=True)    # service_window.nml:240
        _w24.command = UnmaskService    # service_window.nml:240

        _w26.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # service_window.nml:242
        _w26.command = CloseWindow    # service_window.nml:242

        self._navml_built(__class__)
