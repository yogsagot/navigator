# navml: generated
"""Generated from ``savers_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.events import Event as _Event
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button    # savers_dialog.nml:1
from navml.widgets.dialog.check_boxes import CheckBoxes    # savers_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # savers_dialog.nml:3
from navml.widgets.dialog.label import Label    # savers_dialog.nml:4
from navml.widgets.dialog.list_viewer import ListViewer    # savers_dialog.nml:5
from navml.widgets.dialog.radio_buttons import RadioButtons    # savers_dialog.nml:6

__navml_component__ = "SaversDialog"

__all__ = ["SaversDialog"]


class SaversDialog(Dialog, _Component):
    """Options > Configuration > Screen savers: DOS Navigator's ``TSaversDialog``

    (SETUPS.PAS), which DN built in code rather than in ``DN.DNR``.

    Its rectangles: the selected savers down the left, *Add* and *Remove*
    between, the available ones down the right, *Time* and *Use mouse* under
    them.  Two rows taller than DN's 57 by 22, so the library's OK and Cancel
    clear the *Time* buttons; Help is left out, having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "savers_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    chosen_caption: Label    # savers_dialog.nml:21
    chosen: ListViewer    # savers_dialog.nml:30
    join: Button    # savers_dialog.nml:39
    drop: Button    # savers_dialog.nml:48
    offered_caption: Label    # savers_dialog.nml:56
    offered: ListViewer    # savers_dialog.nml:65
    time_caption: Label    # savers_dialog.nml:73
    time: RadioButtons    # savers_dialog.nml:82
    mouse: CheckBoxes    # savers_dialog.nml:90

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_join_click(self, event: _Event) -> bool:    # savers_dialog.nml:39
        """``join`` raised an event whose handler is ``on_click``."""
        return False

    async def on_drop_click(self, event: _Event) -> bool:    # savers_dialog.nml:48
        """``drop`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.chosen_caption = Label(parent=self)    # savers_dialog.nml:20
        self.chosen = ListViewer(parent=self)    # savers_dialog.nml:29
        self.join = Button(parent=self)    # savers_dialog.nml:38
        self.drop = Button(parent=self)    # savers_dialog.nml:47
        self.offered_caption = Label(parent=self)    # savers_dialog.nml:55
        self.offered = ListViewer(parent=self)    # savers_dialog.nml:64
        self.time_caption = Label(parent=self)    # savers_dialog.nml:72
        self.time = RadioButtons(parent=self)    # savers_dialog.nml:81
        self.mouse = CheckBoxes(parent=self)    # savers_dialog.nml:89

        self.modal_width = 57    # savers_dialog.nml:16
        self.modal_height = 24    # savers_dialog.nml:17
        self.title = 'Screen Saver Setup'    # savers_dialog.nml:18

        self.chosen_caption.x = 2    # savers_dialog.nml:22
        self.chosen_caption.y = 2    # savers_dialog.nml:23
        self.chosen_caption.width = 17    # savers_dialog.nml:24
        self.chosen_caption.height = 1    # savers_dialog.nml:25
        self.chosen_caption.text = '~S~elected savers'    # savers_dialog.nml:26
        self.chosen_caption.link = _bind(lambda _o: self.chosen)    # savers_dialog.nml:27

        self.chosen.framed = False    # savers_dialog.nml:31
        self.chosen.x = 2    # savers_dialog.nml:32
        self.chosen.y = 3    # savers_dialog.nml:33
        self.chosen.width = 18    # savers_dialog.nml:34
        self.chosen.height = 10    # savers_dialog.nml:35

        self.join.text = '<───── ~A~dd'    # savers_dialog.nml:40
        self.join.x = 21    # savers_dialog.nml:41
        self.join.y = 6    # savers_dialog.nml:42
        self.join.width = 15    # savers_dialog.nml:43
        self.join.height = 2    # savers_dialog.nml:44
        self.join.on_click = self.on_join_click    # savers_dialog.nml:39

        self.drop.text = '~R~emove ──>'    # savers_dialog.nml:49
        self.drop.x = 21    # savers_dialog.nml:50
        self.drop.y = 8    # savers_dialog.nml:51
        self.drop.width = 15    # savers_dialog.nml:52
        self.drop.height = 2    # savers_dialog.nml:53
        self.drop.on_click = self.on_drop_click    # savers_dialog.nml:48

        self.offered_caption.x = 37    # savers_dialog.nml:57
        self.offered_caption.y = 2    # savers_dialog.nml:58
        self.offered_caption.width = 18    # savers_dialog.nml:59
        self.offered_caption.height = 1    # savers_dialog.nml:60
        self.offered_caption.text = 'A~v~ailable savers'    # savers_dialog.nml:61
        self.offered_caption.link = _bind(lambda _o: self.offered)    # savers_dialog.nml:62

        self.offered.framed = False    # savers_dialog.nml:66
        self.offered.x = 37    # savers_dialog.nml:67
        self.offered.y = 3    # savers_dialog.nml:68
        self.offered.width = 18    # savers_dialog.nml:69
        self.offered.height = 10    # savers_dialog.nml:70

        self.time_caption.x = 2    # savers_dialog.nml:74
        self.time_caption.y = 14    # savers_dialog.nml:75
        self.time_caption.width = 8    # savers_dialog.nml:76
        self.time_caption.height = 1    # savers_dialog.nml:77
        self.time_caption.text = '~T~ime'    # savers_dialog.nml:78
        self.time_caption.link = _bind(lambda _o: self.time)    # savers_dialog.nml:79

        self.time.x = 2    # savers_dialog.nml:83
        self.time.y = 15    # savers_dialog.nml:84
        self.time.width = 16    # savers_dialog.nml:85
        self.time.height = 5    # savers_dialog.nml:86
        self.time.items = ['~N~ever', '~1~ minute', '~2~ minutes', '~5~ minutes', '1~0~ minutes']    # savers_dialog.nml:87

        self.mouse.x = 20    # savers_dialog.nml:91
        self.mouse.y = 15    # savers_dialog.nml:92
        self.mouse.width = 35    # savers_dialog.nml:93
        self.mouse.height = 1    # savers_dialog.nml:94
        self.mouse.items = ['Use ~m~ouse to call saver']    # savers_dialog.nml:95
