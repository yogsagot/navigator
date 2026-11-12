# navml: generated
"""Generated from ``usage_window.nml``.

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
from navigator.widgets.manager.commands import Delete, Rescan    # usage_window.nml:1
from navigator.widgets.shell.commands import GoToUsage, ToggleApparentSize, UsageSortItems, UsageSortName, UsageSortSize    # usage_window.nml:2
from navigator.widgets.shell.usage_list import UsageList    # usage_window.nml:3
from navml.commands import CloseWindow    # usage_window.nml:4
from navml.widgets.dialog.button import Button    # usage_window.nml:5
from navml.widgets.dialog.check_boxes import CheckBoxes    # usage_window.nml:6
from navml.widgets.dialog.commands import SelectNext, SelectPrevious    # usage_window.nml:7
from navml.widgets.dialog.static_text import StaticText    # usage_window.nml:8
from navml.widgets.menu.menu_item import MenuItem    # usage_window.nml:9
from navml.widgets.menu.menu_line import MenuLine    # usage_window.nml:10
from navml.widgets.menu.sub_menu import SubMenu    # usage_window.nml:11
from navml.widgets.dialog.scroll_bar import ScrollBar    # usage_window.nml:12
from navml.widgets.window import Window    # usage_window.nml:13

__navml_component__ = "UsageWindow"

__all__ = ["UsageWindow"]


class UsageWindow(Window, _Component):
    """Disk > Directory sizes: what takes the room under a directory, biggest

    first, a row each with its size, its share, a bar and how many entries are
    under it -- ``ncdu``'s view.  **Not DOS Navigator's**: a departure, asked
    for; ``navigator/lib/file_ops/dirusage.py`` says what of DN's it borders.

    Laid out as Disk > Volumes is: the list without a frame of its own, one
    column into the window's; under it the status line -- where the listed
    directory is and what it adds up to, or what the scan has met so far --
    *Apparent size* on the left, *Go* and *Close* on the right.

    The whole tree is read once, on a thread, when the window opens -- on the
    active panel's directory, any drive's -- and again only on Ctrl+R; going
    down (Enter, Right) and up (Backspace, Left, Enter on ``..``) is then free.
    Another file system is not entered, as ``ncdu -x``.  F8 or Del erases the
    entry under the cursor as F8 in a panel does -- its dialog, its Trash, its
    questions -- and takes it off the totals with no second read.  *Go* sends
    the active panel there and closes the window; Enter on a file does that
    and leaves it open.  Ctrl+N, Ctrl+S and Ctrl+E sort by name, size and
    entries -- not the F-keys DN sorted a panel by, which the desktop and the
    global table already hold here (Ctrl+F3 *New manager*, Ctrl+F4 closing,
    Ctrl+F5 sizing); the same key again turns the order round.  Ctrl+A, or the box, shows the bytes
    files say they hold instead of the room they take on the disk.
    """

    #: The document this class was generated from.
    __navml_source__ = "usage_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # usage_window.nml:40
        'escape': CloseWindow,    # usage_window.nml:41
        'ctrl+r': Rescan,    # usage_window.nml:42
        'alt+r': Rescan,    # usage_window.nml:43
        'f8': Delete,    # usage_window.nml:44
        'delete': Delete,    # usage_window.nml:45
        'ctrl+a': ToggleApparentSize,    # usage_window.nml:46
        'ctrl+n': UsageSortName,    # usage_window.nml:47
        'ctrl+s': UsageSortSize,    # usage_window.nml:48
        'ctrl+e': UsageSortItems,    # usage_window.nml:49
        'tab': SelectNext,    # usage_window.nml:50
        'shift+tab': SelectPrevious,    # usage_window.nml:51
    }

    #: Ids, annotated so the hand-written half completes them.
    entries: UsageList    # usage_window.nml:54
    hbar: ScrollBar    # usage_window.nml:66
    status: StaticText    # usage_window.nml:79
    apparent_box: CheckBoxes    # usage_window.nml:86
    go_button: Button    # usage_window.nml:96
    close_button: Button    # usage_window.nml:106
    usage_menu: SubMenu    # usage_window.nml:118

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_entries_chosen(self, event: _Event) -> bool:    # usage_window.nml:54
        """``entries`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_hbar_scroll(self, event: _Event) -> bool:    # usage_window.nml:66
        """``hbar`` raised an event whose handler is ``on_scroll``."""
        return False

    async def on_go_button_click(self, event: _Event) -> bool:    # usage_window.nml:96
        """``go_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_close_button_click(self, event: _Event) -> bool:    # usage_window.nml:106
        """``close_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.entries = UsageList(parent=self)    # usage_window.nml:53
        self.hbar = ScrollBar(parent=self)    # usage_window.nml:65
        self.status = StaticText(parent=self)    # usage_window.nml:78
        self.apparent_box = CheckBoxes(parent=self)    # usage_window.nml:85
        self.go_button = Button(parent=self)    # usage_window.nml:95
        self.close_button = Button(parent=self)    # usage_window.nml:105
        self.usage_menu = SubMenu(parent=self)    # usage_window.nml:117
        _w1 = MenuItem(parent=self.usage_menu)    # usage_window.nml:120
        _w2 = MenuLine(parent=self.usage_menu)    # usage_window.nml:121
        _w3 = MenuItem(parent=self.usage_menu)    # usage_window.nml:122
        _w4 = MenuItem(parent=self.usage_menu)    # usage_window.nml:123
        _w5 = MenuItem(parent=self.usage_menu)    # usage_window.nml:124
        _w6 = MenuItem(parent=self.usage_menu)    # usage_window.nml:125
        _w7 = MenuLine(parent=self.usage_menu)    # usage_window.nml:127
        _w8 = MenuItem(parent=self.usage_menu)    # usage_window.nml:128
        _w9 = MenuItem(parent=self.usage_menu)    # usage_window.nml:129
        _w10 = MenuLine(parent=self.usage_menu)    # usage_window.nml:130
        _w11 = MenuItem(parent=self.usage_menu)    # usage_window.nml:131

        self.title = _bind(lambda _o: _tr('Directory sizes'), yielding=True)    # usage_window.nml:38

        self.entries.framed = False    # usage_window.nml:55
        self.entries.x = 1    # usage_window.nml:57
        self.entries.width = _bind(lambda _o: max(0, _o.parent.width - 1))    # usage_window.nml:58
        self.entries.y = 1    # usage_window.nml:59
        self.entries.height = _bind(lambda _o: max(0, _o.parent.height - 4))    # usage_window.nml:60
        self.entries.on_chosen = self.on_entries_chosen    # usage_window.nml:54

        self.hbar.orientation = 'horizontal'    # usage_window.nml:67
        self.hbar.visible = _bind(    # usage_window.nml:68
            lambda _o: self.entries.overflows_across and _o.width >= 4
        )
        self.hbar.x = _bind(lambda _o: self.entries.x + self.entries.name_x)    # usage_window.nml:69
        self.hbar.width = _bind(lambda _o: max(0, _o.parent.width - 2 - _o.x))    # usage_window.nml:70
        self.hbar.height = 1    # usage_window.nml:71
        self.hbar.value = _bind(lambda _o: self.entries.x_delta)    # usage_window.nml:74
        self.hbar.maximum = _bind(    # usage_window.nml:75
            lambda _o: max(0, self.entries.name_span - self.entries.name_room, self.entries.x_delta)
        )
        self.hbar.page = _bind(lambda _o: self.entries.name_room)    # usage_window.nml:76
        self.hbar.y = _bind(lambda _o: max(0, _o.parent.height - _o.height))    # usage_window.nml:73
        self.hbar.on_scroll = self.on_hbar_scroll    # usage_window.nml:66

        self.status.x = 2    # usage_window.nml:81
        self.status.width = _bind(lambda _o: max(0, _o.parent.width - 28))    # usage_window.nml:82
        self.status.y = _bind(    # usage_window.nml:83
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )

        self.apparent_box.x = 2    # usage_window.nml:87
        self.apparent_box.width = 22    # usage_window.nml:88
        self.apparent_box.height = 1    # usage_window.nml:89
        self.apparent_box.items = _bind(    # usage_window.nml:92
            lambda _o: [_tr('~A~pparent size')],
            yielding=True,
        )
        self.apparent_box.tooltips = _bind(    # usage_window.nml:93
            lambda _o: [_tr('The bytes files hold rather than the room they take on the disk')],
            yielding=True,
        )
        self.apparent_box.y = _bind(    # usage_window.nml:91
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )

        self.go_button.text = _bind(lambda _o: _tr('~G~o'), yielding=True)    # usage_window.nml:97
        self.go_button.default = True    # usage_window.nml:98
        self.go_button.width = 10    # usage_window.nml:99
        self.go_button.height = 2    # usage_window.nml:100
        self.go_button.x = _bind(    # usage_window.nml:102
            lambda _o: max(0, _o.parent.width - 13 - _o.width)
        )
        self.go_button.y = _bind(    # usage_window.nml:103
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )
        self.go_button.on_click = self.on_go_button_click    # usage_window.nml:96

        self.close_button.text = _bind(lambda _o: _tr('Close'), yielding=True)    # usage_window.nml:107
        self.close_button.width = 10    # usage_window.nml:108
        self.close_button.height = 2    # usage_window.nml:109
        self.close_button.x = _bind(    # usage_window.nml:111
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )
        self.close_button.y = _bind(    # usage_window.nml:112
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )
        self.close_button.on_click = self.on_close_button_click    # usage_window.nml:106

        self.usage_menu.text = _bind(lambda _o: _tr('~S~izes'), yielding=True)    # usage_window.nml:117
        self.usage_menu.after = 'File'    # usage_window.nml:117
        self.usage_menu.tooltip = _bind(    # usage_window.nml:119
            lambda _o: _tr('Sort, re-read and erase what the directory sizes list'),
            yielding=True,
        )

        _w1.text = _bind(lambda _o: _tr('~R~e-read'), yielding=True)    # usage_window.nml:120
        _w1.command = Rescan    # usage_window.nml:120
        _w1.key = 'Ctrl-R'    # usage_window.nml:120

        _w3.text = _bind(lambda _o: _tr('Sort by ~n~ame'), yielding=True)    # usage_window.nml:122
        _w3.command = UsageSortName    # usage_window.nml:122
        _w3.key = 'Ctrl-N'    # usage_window.nml:122

        _w4.text = _bind(lambda _o: _tr('Sort by ~s~ize'), yielding=True)    # usage_window.nml:123
        _w4.command = UsageSortSize    # usage_window.nml:123
        _w4.key = 'Ctrl-S'    # usage_window.nml:123

        _w5.text = _bind(lambda _o: _tr('Sort by ~e~ntries'), yielding=True)    # usage_window.nml:124
        _w5.command = UsageSortItems    # usage_window.nml:124
        _w5.key = 'Ctrl-E'    # usage_window.nml:124

        _w6.text = _bind(lambda _o: _tr('~A~pparent size'), yielding=True)    # usage_window.nml:125
        _w6.command = ToggleApparentSize    # usage_window.nml:125
        _w6.key = 'Ctrl-A'    # usage_window.nml:125
        _w6.tooltip = _bind(    # usage_window.nml:126
            lambda _o: _tr('The bytes files hold rather than the room they take on the disk'),
            yielding=True,
        )

        _w8.text = _bind(lambda _o: _tr('~G~o to directory'), yielding=True)    # usage_window.nml:128
        _w8.command = GoToUsage    # usage_window.nml:128

        _w9.text = _bind(lambda _o: _tr('~D~elete...'), yielding=True)    # usage_window.nml:129
        _w9.command = Delete    # usage_window.nml:129
        _w9.key = 'F8'    # usage_window.nml:129

        _w11.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # usage_window.nml:131
        _w11.command = CloseWindow    # usage_window.nml:131
