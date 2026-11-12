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
from navigator.widgets.manager.commands import MountImage, Rescan, ToggleHidden, UnmountImage    # volumes_window.nml:1
from navigator.widgets.shell.commands import EjectVolume, MountVolume, UnmountVolume    # volumes_window.nml:2
from navigator.widgets.shell.volume_list import VolumeList    # volumes_window.nml:3
from navml.commands import CloseWindow    # volumes_window.nml:4
from navml.widgets.dialog.button import Button    # volumes_window.nml:5
from navml.widgets.dialog.check_boxes import CheckBoxes    # volumes_window.nml:6
from navml.widgets.dialog.commands import SelectNext, SelectPrevious    # volumes_window.nml:7
from navml.widgets.menu.menu_item import MenuItem    # volumes_window.nml:8
from navml.widgets.menu.menu_line import MenuLine    # volumes_window.nml:9
from navml.widgets.menu.sub_menu import SubMenu    # volumes_window.nml:10
from navml.widgets.dialog.scroll_bar import ScrollBar    # volumes_window.nml:11
from navml.widgets.window import Window    # volumes_window.nml:12

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
    mounted mounts it first.  *Mount image...* asks for a disk image file and
    mounts it (``udisksctl loop-setup``); *Unmount image*, on a row of one,
    unmounts every file system of that image and detaches it -- the Disk
    menu's two, which this window answers while it is active.
    """

    #: The document this class was generated from.
    __navml_source__ = "volumes_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # volumes_window.nml:50
        'escape': CloseWindow,    # volumes_window.nml:51
        'ctrl+r': Rescan,    # volumes_window.nml:52
        'alt+r': Rescan,    # volumes_window.nml:53
        'ctrl+h': ToggleHidden,    # volumes_window.nml:54
        'f5': MountVolume,    # volumes_window.nml:55
        'ctrl+n': MountVolume,    # volumes_window.nml:56
        'f6': UnmountVolume,    # volumes_window.nml:57
        'ctrl+u': UnmountVolume,    # volumes_window.nml:58
        'f7': EjectVolume,    # volumes_window.nml:59
        'ctrl+e': EjectVolume,    # volumes_window.nml:60
        'tab': SelectNext,    # volumes_window.nml:61
        'shift+tab': SelectPrevious,    # volumes_window.nml:62
    }

    #: Ids, annotated so the hand-written half completes them.
    volumes: VolumeList    # volumes_window.nml:77
    hbar: ScrollBar    # volumes_window.nml:94
    everything: CheckBoxes    # volumes_window.nml:107
    free_box: CheckBoxes    # volumes_window.nml:117
    mount_button: Button    # volumes_window.nml:130
    unmount_button: Button    # volumes_window.nml:145
    eject_button: Button    # volumes_window.nml:160
    go_button: Button    # volumes_window.nml:175
    close_button: Button    # volumes_window.nml:186
    volumes_menu: SubMenu    # volumes_window.nml:200

    #: The commands this component handles itself.
    async def on_mount_image(self, event: _Any) -> bool:    # volumes_window.nml:66
        """``MountImage``."""
        self.spawn(self._mount_image())
        return True

    async def on_rescan(self, event: _Any) -> bool:    # volumes_window.nml:67
        """``Rescan``."""
        self.reload()
        return True

    async def on_toggle_hidden(self, event: _Any) -> bool:    # volumes_window.nml:68
        """``ToggleHidden``."""
        self.show_all = not self.show_all
        return True

    async def on_select_next(self, event: _Any) -> bool:    # volumes_window.nml:69
        """``SelectNext``."""
        self._step(1)
        return True

    async def on_select_previous(self, event: _Any) -> bool:    # volumes_window.nml:70
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

    async def on_volumes_chosen(self, event: _Event) -> bool:    # volumes_window.nml:77
        """``volumes`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_hbar_scroll(self, event: _Event) -> bool:    # volumes_window.nml:94
        """``hbar`` raised an event whose handler is ``on_scroll``."""
        return False

    async def on_mount_button_click(self, event: _Event) -> bool:    # volumes_window.nml:130
        """``mount_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_unmount_button_click(self, event: _Event) -> bool:    # volumes_window.nml:145
        """``unmount_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_eject_button_click(self, event: _Event) -> bool:    # volumes_window.nml:160
        """``eject_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.volumes = VolumeList(parent=self)    # volumes_window.nml:76
        self.hbar = ScrollBar(parent=self)    # volumes_window.nml:93
        self.everything = CheckBoxes(parent=self)    # volumes_window.nml:106
        self.free_box = CheckBoxes(parent=self)    # volumes_window.nml:116
        self.mount_button = Button(parent=self)    # volumes_window.nml:129
        self.unmount_button = Button(parent=self)    # volumes_window.nml:144
        self.eject_button = Button(parent=self)    # volumes_window.nml:159
        self.go_button = Button(parent=self)    # volumes_window.nml:174
        self.close_button = Button(parent=self)    # volumes_window.nml:185
        self.volumes_menu = SubMenu(parent=self)    # volumes_window.nml:199
        _w1 = MenuItem(parent=self.volumes_menu)    # volumes_window.nml:202
        _w2 = MenuItem(parent=self.volumes_menu)    # volumes_window.nml:203
        _w3 = MenuLine(parent=self.volumes_menu)    # volumes_window.nml:205
        _w4 = MenuItem(parent=self.volumes_menu)    # volumes_window.nml:206
        _w5 = MenuItem(parent=self.volumes_menu)    # volumes_window.nml:207
        _w6 = MenuItem(parent=self.volumes_menu)    # volumes_window.nml:208
        _w7 = MenuLine(parent=self.volumes_menu)    # volumes_window.nml:209
        _w8 = MenuItem(parent=self.volumes_menu)    # volumes_window.nml:210
        _w9 = MenuItem(parent=self.volumes_menu)    # volumes_window.nml:212
        _w10 = MenuLine(parent=self.volumes_menu)    # volumes_window.nml:214
        _w11 = MenuItem(parent=self.volumes_menu)    # volumes_window.nml:215

        self.title = _bind(lambda _o: _tr('Volumes'), yielding=True)    # volumes_window.nml:48
        self.first_focus = _bind(lambda _o: self.volumes)    # volumes_window.nml:72
        self.local_menu = _bind(lambda _o: self.volumes_menu)    # volumes_window.nml:74

        self.volumes.framed = False    # volumes_window.nml:78
        self.volumes.x = 1    # volumes_window.nml:80
        self.volumes.width = _bind(lambda _o: max(0, _o.parent.width - 1))    # volumes_window.nml:81
        self.volumes.y = 1    # volumes_window.nml:82
        self.volumes.height = _bind(    # volumes_window.nml:83
            lambda _o: max(0, _o.parent.height - 7) if _o.parent.width < 82 else max(0, _o.parent.height - 5)
        )
        self.volumes.on_chosen = self.on_volumes_chosen    # volumes_window.nml:77

        self.hbar.orientation = 'horizontal'    # volumes_window.nml:95
        self.hbar.visible = _bind(    # volumes_window.nml:96
            lambda _o: self.volumes.overflows_across and _o.width >= 4
        )
        self.hbar.x = _bind(lambda _o: self.volumes.x + self.volumes.mount_x)    # volumes_window.nml:97
        self.hbar.width = _bind(lambda _o: self.volumes.mount_width)    # volumes_window.nml:98
        self.hbar.height = 1    # volumes_window.nml:99
        self.hbar.value = _bind(    # volumes_window.nml:102
            lambda _o: max(0, self.volumes.mount_reach - self.volumes.back)
        )
        self.hbar.maximum = _bind(    # volumes_window.nml:103
            lambda _o: max(self.volumes.mount_reach, self.volumes.back)
        )
        self.hbar.page = _bind(lambda _o: self.volumes.mount_room)    # volumes_window.nml:104
        self.hbar.y = _bind(lambda _o: max(0, _o.parent.height - _o.height))    # volumes_window.nml:101
        self.hbar.on_scroll = self.on_hbar_scroll    # volumes_window.nml:94

        self.everything.x = 2    # volumes_window.nml:108
        self.everything.width = 22    # volumes_window.nml:109
        self.everything.height = 1    # volumes_window.nml:110
        self.everything.items = _bind(    # volumes_window.nml:113
            lambda _o: [_tr('~S~how all mounts')],
            yielding=True,
        )
        self.everything.tooltips = _bind(    # volumes_window.nml:114
            lambda _o: [_tr("Show the kernel's own file systems too")],
            yielding=True,
        )
        self.everything.y = _bind(    # volumes_window.nml:112
            lambda _o: max(0, _o.parent.height - 2 - _o.height)
        )

        self.free_box.x = 2    # volumes_window.nml:118
        self.free_box.width = 22    # volumes_window.nml:119
        self.free_box.height = 1    # volumes_window.nml:120
        self.free_box.items = _bind(    # volumes_window.nml:123
            lambda _o: [_tr('Show ~f~ree %')],
            yielding=True,
        )
        self.free_box.tooltips = _bind(    # volumes_window.nml:124
            lambda _o: [_tr('Show the share that is free rather than the share used')],
            yielding=True,
        )
        self.free_box.y = _bind(    # volumes_window.nml:122
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )

        self.mount_button.text = _bind(    # volumes_window.nml:131
            lambda _o: _tr('~M~ount'),
            yielding=True,
        )
        self.mount_button.width = 10    # volumes_window.nml:132
        self.mount_button.height = 2    # volumes_window.nml:133
        self.mount_button.disabled = _bind(lambda _o: not self.allows('mount'))    # volumes_window.nml:141
        self.mount_button.command = MountVolume    # volumes_window.nml:142
        self.mount_button.x = _bind(    # volumes_window.nml:135
            lambda _o: max(0, _o.parent.width - 25 - _o.width) if _o.parent.width < 82 else max(0, _o.parent.width - 47 - _o.width)
        )
        self.mount_button.y = _bind(    # volumes_window.nml:136
            lambda _o: max(0, _o.parent.height - 3 - _o.height) if _o.parent.width < 82 else max(0, _o.parent.height - 1 - _o.height)
        )
        self.mount_button.on_click = self.on_mount_button_click    # volumes_window.nml:130

        self.unmount_button.text = _bind(    # volumes_window.nml:146
            lambda _o: _tr('~U~nmount'),
            yielding=True,
        )
        self.unmount_button.width = 11    # volumes_window.nml:147
        self.unmount_button.height = 2    # volumes_window.nml:148
        self.unmount_button.disabled = _bind(    # volumes_window.nml:156
            lambda _o: not self.allows('unmount')
        )
        self.unmount_button.command = UnmountVolume    # volumes_window.nml:157
        self.unmount_button.x = _bind(    # volumes_window.nml:150
            lambda _o: max(0, _o.parent.width - 13 - _o.width) if _o.parent.width < 82 else max(0, _o.parent.width - 35 - _o.width)
        )
        self.unmount_button.y = _bind(    # volumes_window.nml:151
            lambda _o: max(0, _o.parent.height - 3 - _o.height) if _o.parent.width < 82 else max(0, _o.parent.height - 1 - _o.height)
        )
        self.unmount_button.on_click = self.on_unmount_button_click    # volumes_window.nml:145

        self.eject_button.text = _bind(    # volumes_window.nml:161
            lambda _o: _tr('~E~ject'),
            yielding=True,
        )
        self.eject_button.width = 10    # volumes_window.nml:162
        self.eject_button.height = 2    # volumes_window.nml:163
        self.eject_button.disabled = _bind(lambda _o: not self.allows('eject'))    # volumes_window.nml:171
        self.eject_button.command = EjectVolume    # volumes_window.nml:172
        self.eject_button.x = _bind(    # volumes_window.nml:165
            lambda _o: max(0, _o.parent.width - 2 - _o.width) if _o.parent.width < 82 else max(0, _o.parent.width - 24 - _o.width)
        )
        self.eject_button.y = _bind(    # volumes_window.nml:166
            lambda _o: max(0, _o.parent.height - 3 - _o.height) if _o.parent.width < 82 else max(0, _o.parent.height - 1 - _o.height)
        )
        self.eject_button.on_click = self.on_eject_button_click    # volumes_window.nml:160

        self.go_button.text = _bind(lambda _o: _tr('~G~o'), yielding=True)    # volumes_window.nml:176
        self.go_button.default = True    # volumes_window.nml:177
        self.go_button.width = 10    # volumes_window.nml:178
        self.go_button.height = 2    # volumes_window.nml:179
        self.go_button.x = _bind(    # volumes_window.nml:181
            lambda _o: max(0, _o.parent.width - 13 - _o.width)
        )
        self.go_button.y = _bind(    # volumes_window.nml:182
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )

        async def _on_click(event):    # volumes_window.nml:183
            await self.go()
            return True
        self.go_button.on_click = _on_click

        self.close_button.text = _bind(lambda _o: _tr('Close'), yielding=True)    # volumes_window.nml:187
        self.close_button.width = 10    # volumes_window.nml:188
        self.close_button.height = 2    # volumes_window.nml:189
        self.close_button.x = _bind(    # volumes_window.nml:191
            lambda _o: max(0, _o.parent.width - 2 - _o.width)
        )
        self.close_button.y = _bind(    # volumes_window.nml:192
            lambda _o: max(0, _o.parent.height - 1 - _o.height)
        )

        async def _on_click(event):    # volumes_window.nml:193
            self.request_close()
            return True
        self.close_button.on_click = _on_click

        self.volumes_menu.text = _bind(    # volumes_window.nml:199
            lambda _o: _tr('~V~olumes'),
            yielding=True,
        )
        self.volumes_menu.after = 'File'    # volumes_window.nml:199
        self.volumes_menu.tooltip = _bind(    # volumes_window.nml:201
            lambda _o: _tr('Mount, unmount and eject volumes'),
            yielding=True,
        )

        _w1.text = _bind(lambda _o: _tr('~R~e-read'), yielding=True)    # volumes_window.nml:202
        _w1.command = Rescan    # volumes_window.nml:202

        _w2.text = _bind(lambda _o: _tr('~S~how all mounts'), yielding=True)    # volumes_window.nml:203
        _w2.command = ToggleHidden    # volumes_window.nml:203
        _w2.tooltip = _bind(    # volumes_window.nml:204
            lambda _o: _tr("Show the kernel's own file systems too"),
            yielding=True,
        )

        _w4.text = _bind(lambda _o: _tr('~M~ount'), yielding=True)    # volumes_window.nml:206
        _w4.command = MountVolume    # volumes_window.nml:206
        _w4.key = 'F5'    # volumes_window.nml:206

        _w5.text = _bind(lambda _o: _tr('~U~nmount'), yielding=True)    # volumes_window.nml:207
        _w5.command = UnmountVolume    # volumes_window.nml:207
        _w5.key = 'F6'    # volumes_window.nml:207

        _w6.text = _bind(lambda _o: _tr('~E~ject'), yielding=True)    # volumes_window.nml:208
        _w6.command = EjectVolume    # volumes_window.nml:208
        _w6.key = 'F7'    # volumes_window.nml:208

        _w8.text = _bind(lambda _o: _tr('Mount ~i~mage...'), yielding=True)    # volumes_window.nml:210
        _w8.command = MountImage    # volumes_window.nml:210
        _w8.tooltip = _bind(    # volumes_window.nml:211
            lambda _o: _tr('A disk image file (.iso, .img): attached read-only and mounted'),
            yielding=True,
        )

        _w9.text = _bind(lambda _o: _tr('Unmount ima~g~e'), yielding=True)    # volumes_window.nml:212
        _w9.command = UnmountImage    # volumes_window.nml:212
        _w9.tooltip = _bind(    # volumes_window.nml:213
            lambda _o: _tr('The disk image this volume is on: every file system of it unmounted, and detached'),
            yielding=True,
        )

        _w11.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # volumes_window.nml:215
        _w11.command = CloseWindow    # volumes_window.nml:215
