# navml: generated
"""Generated from ``volumes_window.nml``.

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
from navigator.widgets.manager.commands import Rescan, ToggleHidden    # volumes_window.nml:1
from navigator.widgets.shell.commands import EjectVolume, MountVolume, UnmountVolume    # volumes_window.nml:2
from navigator.widgets.shell.volume_list import VolumeList    # volumes_window.nml:3
from navml.commands import CloseWindow    # volumes_window.nml:4
from navml.widgets.dialog.button import Button    # volumes_window.nml:5
from navml.widgets.dialog.check_boxes import CheckBoxes    # volumes_window.nml:6
from navml.widgets.dialog.commands import SelectNext, SelectPrevious    # volumes_window.nml:7
from navml.widgets.menu.menu_item import MenuItem    # volumes_window.nml:8
from navml.widgets.menu.menu_line import MenuLine    # volumes_window.nml:9
from navml.widgets.menu.sub_menu import SubMenu    # volumes_window.nml:10
from navml.widgets.window import Window    # volumes_window.nml:11

__navml_component__ = "VolumesWindow"

__all__ = ["VolumesWindow"]


class VolumesWindow(Window, _Component):
    """Disk > Volumes: every mounted volume -- its name, type, mount point, free

    space and size -- a row each.  **Not DOS Navigator's**: a departure, asked
    for.  DN 1.51's drive chooser (``SelectDrive``, FILESCOL.PAS) listed bare
    drive letters, and only ``TDiskInfo`` (Ctrl+L) told a drive's size, free
    space and label -- of the current drive alone.  This is the two together:
    what ``TDiskInfo`` said, for every drive ``SelectDrive`` would offer, in
    the place and under the letter of DN's *Volume label*, which has no POSIX
    meaning.

    Laid out as the Directory Tree window is: the list without a frame of its
    own, one column into the window's, its scroll bar on the right edge; under
    it, a dialog's row: *Show all mounts* on the left, *Go* and *Close* on the
    right.  Enter in the list sends the file manager's active panel to the
    volume's mount point, as Enter in the tree window sends it to a directory,
    and the window stays; *Go* does the same and closes it.  Esc closes it;
    Ctrl+R and Alt+R read the mounts again, as they re-read a panel; *Show all
    mounts* -- or Ctrl+H, as it shows a panel's dot-files -- lists the kernel's
    own file systems as well; *Show free %* turns the *Use %* column, ``df``'s,
    into *Free %*.  Tab walks the controls, Alt and a marked letter
    takes one, as in a dialog.

    Where the desktop's ``gio`` or KDE's Solid is -- else udisks2's own
    ``udisksctl`` -- the volumes udisks knows but has not
    mounted are listed too, *not mounted*, and *Mount* (F5, Ctrl+N), *Unmount*
    (F6, Ctrl+U) and *Eject* (F7, Ctrl+E) act on the one under the cursor, as
    the desktop's file manager does -- a further departure.  Each is a button
    too, greyed where the volume cannot: on *Go* and *Close*'s row where the
    window is wide enough beside the boxes, in a row over them where it is
    not; the F-keys are what puts them on the key bar.  Enter or *Go* on one not
    mounted mounts it first.
    """

    #: The document this class was generated from.
    __navml_source__ = "volumes_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # volumes_window.nml:46
        'escape': CloseWindow,    # volumes_window.nml:47
        'ctrl+r': Rescan,    # volumes_window.nml:48
        'alt+r': Rescan,    # volumes_window.nml:49
        'ctrl+h': ToggleHidden,    # volumes_window.nml:50
        'f5': MountVolume,    # volumes_window.nml:51
        'ctrl+n': MountVolume,    # volumes_window.nml:52
        'f6': UnmountVolume,    # volumes_window.nml:53
        'ctrl+u': UnmountVolume,    # volumes_window.nml:54
        'f7': EjectVolume,    # volumes_window.nml:55
        'ctrl+e': EjectVolume,    # volumes_window.nml:56
        'tab': SelectNext,    # volumes_window.nml:57
        'shift+tab': SelectPrevious,    # volumes_window.nml:58
    }

    #: Ids, annotated so the hand-written half completes them.
    volumes: VolumeList    # volumes_window.nml:61
    everything: CheckBoxes    # volumes_window.nml:69
    free_box: CheckBoxes    # volumes_window.nml:77
    mount_button: Button    # volumes_window.nml:88
    unmount_button: Button    # volumes_window.nml:97
    eject_button: Button    # volumes_window.nml:106
    go_button: Button    # volumes_window.nml:115
    close_button: Button    # volumes_window.nml:124
    volumes_menu: SubMenu    # volumes_window.nml:136

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_volumes_chosen(self, event: _Event) -> bool:    # volumes_window.nml:61
        """``volumes`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_mount_button_click(self, event: _Event) -> bool:    # volumes_window.nml:88
        """``mount_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_unmount_button_click(self, event: _Event) -> bool:    # volumes_window.nml:97
        """``unmount_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_eject_button_click(self, event: _Event) -> bool:    # volumes_window.nml:106
        """``eject_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_go_button_click(self, event: _Event) -> bool:    # volumes_window.nml:115
        """``go_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_close_button_click(self, event: _Event) -> bool:    # volumes_window.nml:124
        """``close_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.volumes = VolumeList(parent=self)    # volumes_window.nml:60
        self.everything = CheckBoxes(parent=self)    # volumes_window.nml:68
        self.free_box = CheckBoxes(parent=self)    # volumes_window.nml:76
        self.mount_button = Button(parent=self)    # volumes_window.nml:87
        self.unmount_button = Button(parent=self)    # volumes_window.nml:96
        self.eject_button = Button(parent=self)    # volumes_window.nml:105
        self.go_button = Button(parent=self)    # volumes_window.nml:114
        self.close_button = Button(parent=self)    # volumes_window.nml:123
        self.volumes_menu = SubMenu(parent=self)    # volumes_window.nml:135
        _w1 = MenuItem(parent=self.volumes_menu)    # volumes_window.nml:139
        _w2 = MenuItem(parent=self.volumes_menu)    # volumes_window.nml:142
        _w3 = MenuLine(parent=self.volumes_menu)    # volumes_window.nml:145
        _w4 = MenuItem(parent=self.volumes_menu)    # volumes_window.nml:146
        _w5 = MenuItem(parent=self.volumes_menu)    # volumes_window.nml:150
        _w6 = MenuItem(parent=self.volumes_menu)    # volumes_window.nml:154
        _w7 = MenuLine(parent=self.volumes_menu)    # volumes_window.nml:158
        _w8 = MenuItem(parent=self.volumes_menu)    # volumes_window.nml:159

        self.title = _bind(lambda _o: _tr('Volumes'), yielding=True)    # volumes_window.nml:44

        self.volumes.framed = False    # volumes_window.nml:62
        self.volumes.x = 1    # volumes_window.nml:63
        self.volumes.y = 1    # volumes_window.nml:64
        self.volumes.width = _bind(lambda _o: max(0, _o.parent.width - 1))    # volumes_window.nml:65
        self.volumes.height = _bind(    # volumes_window.nml:66
            lambda _o: max(0, _o.parent.height - (5 if _o.parent.width >= 82 else 7))
        )
        self.volumes.on_chosen = self.on_volumes_chosen    # volumes_window.nml:61

        self.everything.x = 2    # volumes_window.nml:70
        self.everything.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # volumes_window.nml:71
        self.everything.width = 22    # volumes_window.nml:72
        self.everything.height = 1    # volumes_window.nml:73
        self.everything.items = _bind(    # volumes_window.nml:74
            lambda _o: [_tr('~S~how all mounts')],
            yielding=True,
        )

        self.free_box.x = 2    # volumes_window.nml:78
        self.free_box.y = _bind(lambda _o: max(0, _o.parent.height - 2))    # volumes_window.nml:79
        self.free_box.width = 22    # volumes_window.nml:80
        self.free_box.height = 1    # volumes_window.nml:81
        self.free_box.items = _bind(    # volumes_window.nml:82
            lambda _o: [_tr('Show ~f~ree %')],
            yielding=True,
        )

        self.mount_button.text = _bind(    # volumes_window.nml:89
            lambda _o: _tr('~M~ount'),
            yielding=True,
        )
        self.mount_button.x = _bind(    # volumes_window.nml:90
            lambda _o: max(0, _o.parent.width - (57 if _o.parent.width >= 82 else 35))
        )
        self.mount_button.y = _bind(    # volumes_window.nml:91
            lambda _o: max(0, _o.parent.height - (3 if _o.parent.width >= 82 else 5))
        )
        self.mount_button.width = 10    # volumes_window.nml:92
        self.mount_button.height = 2    # volumes_window.nml:93
        self.mount_button.disabled = _bind(lambda _o: not self.allows('mount'))    # volumes_window.nml:94
        self.mount_button.on_click = self.on_mount_button_click    # volumes_window.nml:88

        self.unmount_button.text = _bind(    # volumes_window.nml:98
            lambda _o: _tr('~U~nmount'),
            yielding=True,
        )
        self.unmount_button.x = _bind(    # volumes_window.nml:99
            lambda _o: max(0, _o.parent.width - (46 if _o.parent.width >= 82 else 24))
        )
        self.unmount_button.y = _bind(    # volumes_window.nml:100
            lambda _o: max(0, _o.parent.height - (3 if _o.parent.width >= 82 else 5))
        )
        self.unmount_button.width = 11    # volumes_window.nml:101
        self.unmount_button.height = 2    # volumes_window.nml:102
        self.unmount_button.disabled = _bind(    # volumes_window.nml:103
            lambda _o: not self.allows('unmount')
        )
        self.unmount_button.on_click = self.on_unmount_button_click    # volumes_window.nml:97

        self.eject_button.text = _bind(    # volumes_window.nml:107
            lambda _o: _tr('~E~ject'),
            yielding=True,
        )
        self.eject_button.x = _bind(    # volumes_window.nml:108
            lambda _o: max(0, _o.parent.width - (34 if _o.parent.width >= 82 else 12))
        )
        self.eject_button.y = _bind(    # volumes_window.nml:109
            lambda _o: max(0, _o.parent.height - (3 if _o.parent.width >= 82 else 5))
        )
        self.eject_button.width = 10    # volumes_window.nml:110
        self.eject_button.height = 2    # volumes_window.nml:111
        self.eject_button.disabled = _bind(lambda _o: not self.allows('eject'))    # volumes_window.nml:112
        self.eject_button.on_click = self.on_eject_button_click    # volumes_window.nml:106

        self.go_button.text = _bind(lambda _o: _tr('~G~o'), yielding=True)    # volumes_window.nml:116
        self.go_button.default = True    # volumes_window.nml:117
        self.go_button.x = _bind(lambda _o: max(0, _o.parent.width - 23))    # volumes_window.nml:118
        self.go_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # volumes_window.nml:119
        self.go_button.width = 10    # volumes_window.nml:120
        self.go_button.height = 2    # volumes_window.nml:121
        self.go_button.on_click = self.on_go_button_click    # volumes_window.nml:115

        self.close_button.text = _bind(lambda _o: _tr('Close'), yielding=True)    # volumes_window.nml:125
        self.close_button.x = _bind(lambda _o: max(0, _o.parent.width - 12))    # volumes_window.nml:126
        self.close_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # volumes_window.nml:127
        self.close_button.width = 10    # volumes_window.nml:128
        self.close_button.height = 2    # volumes_window.nml:129
        self.close_button.on_click = self.on_close_button_click    # volumes_window.nml:124

        self.volumes_menu.text = _bind(    # volumes_window.nml:137
            lambda _o: _tr('~V~olumes'),
            yielding=True,
        )
        self.volumes_menu.after = 'File'    # volumes_window.nml:138

        _w1.text = _bind(lambda _o: _tr('~R~e-read'), yielding=True)    # volumes_window.nml:140
        _w1.command = Rescan    # volumes_window.nml:141

        _w2.text = _bind(lambda _o: _tr('~S~how all mounts'), yielding=True)    # volumes_window.nml:143
        _w2.command = ToggleHidden    # volumes_window.nml:144

        _w4.text = _bind(lambda _o: _tr('~M~ount'), yielding=True)    # volumes_window.nml:147
        _w4.command = MountVolume    # volumes_window.nml:148
        _w4.key = 'F5'    # volumes_window.nml:149

        _w5.text = _bind(lambda _o: _tr('~U~nmount'), yielding=True)    # volumes_window.nml:151
        _w5.command = UnmountVolume    # volumes_window.nml:152
        _w5.key = 'F6'    # volumes_window.nml:153

        _w6.text = _bind(lambda _o: _tr('~E~ject'), yielding=True)    # volumes_window.nml:155
        _w6.command = EjectVolume    # volumes_window.nml:156
        _w6.key = 'F7'    # volumes_window.nml:157

        _w8.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # volumes_window.nml:160
        _w8.command = CloseWindow    # volumes_window.nml:161
