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
from navigator.widgets.shell.volume_list import VolumeList    # volumes_window.nml:2
from navml.commands import CloseWindow    # volumes_window.nml:3
from navml.widgets.dialog.button import Button    # volumes_window.nml:4
from navml.widgets.dialog.check_boxes import CheckBoxes    # volumes_window.nml:5
from navml.widgets.dialog.commands import SelectNext, SelectPrevious    # volumes_window.nml:6
from navml.widgets.window import Window    # volumes_window.nml:7

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
    own file systems as well.  Tab walks the controls, Alt and a marked letter
    takes one, as in a dialog.
    """

    #: The document this class was generated from.
    __navml_source__ = "volumes_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # volumes_window.nml:31
        'escape': CloseWindow,    # volumes_window.nml:32
        'ctrl+r': Rescan,    # volumes_window.nml:33
        'alt+r': Rescan,    # volumes_window.nml:34
        'ctrl+h': ToggleHidden,    # volumes_window.nml:35
        'tab': SelectNext,    # volumes_window.nml:36
        'shift+tab': SelectPrevious,    # volumes_window.nml:37
    }

    #: Ids, annotated so the hand-written half completes them.
    volumes: VolumeList    # volumes_window.nml:40
    everything: CheckBoxes    # volumes_window.nml:48
    go_button: Button    # volumes_window.nml:56
    close_button: Button    # volumes_window.nml:65

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_volumes_chosen(self, event: _Event) -> bool:    # volumes_window.nml:40
        """``volumes`` raised an event whose handler is ``on_chosen``."""
        return False

    async def on_go_button_click(self, event: _Event) -> bool:    # volumes_window.nml:56
        """``go_button`` raised an event whose handler is ``on_click``."""
        return False

    async def on_close_button_click(self, event: _Event) -> bool:    # volumes_window.nml:65
        """``close_button`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.volumes = VolumeList(parent=self)    # volumes_window.nml:39
        self.everything = CheckBoxes(parent=self)    # volumes_window.nml:47
        self.go_button = Button(parent=self)    # volumes_window.nml:55
        self.close_button = Button(parent=self)    # volumes_window.nml:64

        self.title = _bind(lambda _o: _tr('Volumes'), yielding=True)    # volumes_window.nml:29

        self.volumes.framed = False    # volumes_window.nml:41
        self.volumes.x = 1    # volumes_window.nml:42
        self.volumes.y = 1    # volumes_window.nml:43
        self.volumes.width = _bind(lambda _o: max(0, _o.parent.width - 1))    # volumes_window.nml:44
        self.volumes.height = _bind(lambda _o: max(0, _o.parent.height - 5))    # volumes_window.nml:45
        self.volumes.on_chosen = self.on_volumes_chosen    # volumes_window.nml:40

        self.everything.x = 2    # volumes_window.nml:49
        self.everything.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # volumes_window.nml:50
        self.everything.width = 22    # volumes_window.nml:51
        self.everything.height = 1    # volumes_window.nml:52
        self.everything.items = _bind(    # volumes_window.nml:53
            lambda _o: [_tr('~S~how all mounts')],
            yielding=True,
        )

        self.go_button.text = _bind(lambda _o: _tr('~G~o'), yielding=True)    # volumes_window.nml:57
        self.go_button.default = True    # volumes_window.nml:58
        self.go_button.x = _bind(lambda _o: max(0, _o.parent.width - 25))    # volumes_window.nml:59
        self.go_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # volumes_window.nml:60
        self.go_button.width = 10    # volumes_window.nml:61
        self.go_button.height = 2    # volumes_window.nml:62
        self.go_button.on_click = self.on_go_button_click    # volumes_window.nml:56

        self.close_button.text = _bind(lambda _o: _tr('Close'), yielding=True)    # volumes_window.nml:66
        self.close_button.x = _bind(lambda _o: max(0, _o.parent.width - 13))    # volumes_window.nml:67
        self.close_button.y = _bind(lambda _o: max(0, _o.parent.height - 3))    # volumes_window.nml:68
        self.close_button.width = 10    # volumes_window.nml:69
        self.close_button.height = 2    # volumes_window.nml:70
        self.close_button.on_click = self.on_close_button_click    # volumes_window.nml:65
