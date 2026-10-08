# navml: generated
"""Generated from ``columns_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # columns_dialog.nml:1
from navml.widgets.dialog.check_boxes import CheckBoxes    # columns_dialog.nml:2
from navml.widgets.dialog.dialog import Dialog    # columns_dialog.nml:3
from navml.widgets.dialog.label import Label    # columns_dialog.nml:4

__navml_component__ = "ColumnsDialog"

__all__ = ["ColumnsDialog"]


class ColumnsDialog(Dialog, _Component):
    """Alt+K, Panel > Setup columns: DOS Navigator's ``dlgDiskParms`` (and, for a

    *Find:* listing, ``dlgFindParms``, whose last box is the path).

    *Show* and its boxes, OK, *Brief*, *Full* and Cancel, where DN had them
    down the right and along the bottom; the boxes are the detailed mode's
    columns -- POSIX's size, attributes, owner and date, where DN's were size,
    date, time and descriptions, which ``descript.ion`` went with.
    """

    #: The document this class was generated from.
    __navml_source__ = "columns_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    show_caption: Label    # columns_dialog.nml:19
    show: CheckBoxes    # columns_dialog.nml:28
    brief: Button    # columns_dialog.nml:37
    full: Button    # columns_dialog.nml:46
    pick: Button    # columns_dialog.nml:54
    abandon: Button    # columns_dialog.nml:63

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_brief_click(self, event: _Event) -> bool:    # columns_dialog.nml:37
        """``brief`` raised an event whose handler is ``on_click``."""
        return False

    async def on_full_click(self, event: _Event) -> bool:    # columns_dialog.nml:46
        """``full`` raised an event whose handler is ``on_click``."""
        return False

    async def on_pick_click(self, event: _Event) -> bool:    # columns_dialog.nml:54
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # columns_dialog.nml:63
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.show_caption = Label(parent=self)    # columns_dialog.nml:18
        self.show = CheckBoxes(parent=self)    # columns_dialog.nml:27
        self.brief = Button(parent=self)    # columns_dialog.nml:36
        self.full = Button(parent=self)    # columns_dialog.nml:45
        self.pick = Button(parent=self)    # columns_dialog.nml:53
        self.abandon = Button(parent=self)    # columns_dialog.nml:62

        self.modal_width = 40    # columns_dialog.nml:14
        self.modal_height = 13    # columns_dialog.nml:15
        self.title = _bind(lambda _o: _tr('Columns Setup'), yielding=True)    # columns_dialog.nml:16

        self.show_caption.x = 3    # columns_dialog.nml:20
        self.show_caption.y = 1    # columns_dialog.nml:21
        self.show_caption.width = 6    # columns_dialog.nml:22
        self.show_caption.height = 1    # columns_dialog.nml:23
        self.show_caption.text = _bind(lambda _o: _tr('Show'), yielding=True)    # columns_dialog.nml:24
        self.show_caption.link = _bind(lambda _o: self.show)    # columns_dialog.nml:25

        self.show.x = 3    # columns_dialog.nml:29
        self.show.y = 2    # columns_dialog.nml:30
        self.show.width = 20    # columns_dialog.nml:31
        self.show.height = 5    # columns_dialog.nml:32
        self.show.items = _bind(    # columns_dialog.nml:33
            lambda _o: [_tr('~S~ize'), _tr('~A~ttributes'), _tr('~O~wner'), _tr('~D~ate'), _tr('~P~ath')],
            yielding=True,
        )

        self.brief.text = _bind(lambda _o: _tr('~B~rief'), yielding=True)    # columns_dialog.nml:38
        self.brief.x = 26    # columns_dialog.nml:39
        self.brief.y = 2    # columns_dialog.nml:40
        self.brief.width = 11    # columns_dialog.nml:41
        self.brief.height = 2    # columns_dialog.nml:42
        self.brief.on_click = self.on_brief_click    # columns_dialog.nml:37

        self.full.text = _bind(lambda _o: _tr('~F~ull'), yielding=True)    # columns_dialog.nml:47
        self.full.x = 26    # columns_dialog.nml:48
        self.full.y = 5    # columns_dialog.nml:49
        self.full.width = 11    # columns_dialog.nml:50
        self.full.height = 2    # columns_dialog.nml:51
        self.full.on_click = self.on_full_click    # columns_dialog.nml:46

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # columns_dialog.nml:55
        self.pick.default = True    # columns_dialog.nml:56
        self.pick.x = 7    # columns_dialog.nml:57
        self.pick.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # columns_dialog.nml:58
        self.pick.width = 11    # columns_dialog.nml:59
        self.pick.height = 2    # columns_dialog.nml:60
        self.pick.on_click = self.on_pick_click    # columns_dialog.nml:54

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # columns_dialog.nml:64
        self.abandon.x = 20    # columns_dialog.nml:65
        self.abandon.y = _bind(lambda _o: max(0, _o.parent.height - 4))    # columns_dialog.nml:66
        self.abandon.width = 11    # columns_dialog.nml:67
        self.abandon.height = 2    # columns_dialog.nml:68
        self.abandon.on_click = self.on_abandon_click    # columns_dialog.nml:63
