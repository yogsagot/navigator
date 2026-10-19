# navml: generated
"""Generated from ``savers_page.nml``.

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
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.button import Button    # savers_page.nml:1
from navml.widgets.dialog.check_boxes import CheckBoxes    # savers_page.nml:2
from navml.widgets.dialog.label import Label    # savers_page.nml:3
from navml.widgets.dialog.list_viewer import ListViewer    # savers_page.nml:4
from navml.widgets.dialog.radio_buttons import RadioButtons    # savers_page.nml:5

__navml_component__ = "SaversPage"

__all__ = ["SaversPage"]


class SaversPage(_Component):
    """Options > Configuration > Screen savers: DOS Navigator's ``TSaversDialog``

    (SETUPS.PAS), which DN built in code rather than in ``DN.DNR``.

    Its lists leave PgUp and PgDn to the tabs of *Settings* (``page_keys``):
    seven rows need no paging, and the keys mean the next page there.

    Its rectangles: the selected savers down the left, *Add* and *Remove*
    between, the available ones down the right, *Time* and *Use mouse* under
    them, as DN had them -- the lists three rows shorter than DN's, so the
    page is no taller than *Panel defaults* in *Settings*.  Help is left out,
    having nothing to show yet.
    """

    #: The document this class was generated from.
    __navml_source__ = "savers_page.nml"

    #: The caption on its tab, which *Settings* gives it.
    title: str = _reactive('')    # savers_page.nml:20

    #: Ids, annotated so the hand-written half completes them.
    chosen_caption: Label    # savers_page.nml:23
    chosen: ListViewer    # savers_page.nml:32
    join: Button    # savers_page.nml:42
    drop: Button    # savers_page.nml:51
    offered_caption: Label    # savers_page.nml:59
    offered: ListViewer    # savers_page.nml:68
    time_caption: Label    # savers_page.nml:77
    time: RadioButtons    # savers_page.nml:86
    mouse: CheckBoxes    # savers_page.nml:94

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_join_click(self, event: _Event) -> bool:    # savers_page.nml:42
        """``join`` raised an event whose handler is ``on_click``."""
        return False

    async def on_drop_click(self, event: _Event) -> bool:    # savers_page.nml:51
        """``drop`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.chosen_caption = Label(parent=self)    # savers_page.nml:22
        self.chosen = ListViewer(parent=self)    # savers_page.nml:31
        self.join = Button(parent=self)    # savers_page.nml:41
        self.drop = Button(parent=self)    # savers_page.nml:50
        self.offered_caption = Label(parent=self)    # savers_page.nml:58
        self.offered = ListViewer(parent=self)    # savers_page.nml:67
        self.time_caption = Label(parent=self)    # savers_page.nml:76
        self.time = RadioButtons(parent=self)    # savers_page.nml:85
        self.mouse = CheckBoxes(parent=self)    # savers_page.nml:93

        self.chosen_caption.x = 2    # savers_page.nml:24
        self.chosen_caption.y = 2    # savers_page.nml:25
        self.chosen_caption.width = 17    # savers_page.nml:26
        self.chosen_caption.height = 1    # savers_page.nml:27
        self.chosen_caption.text = _bind(    # savers_page.nml:28
            lambda _o: _tr('~S~elected savers'),
            yielding=True,
        )
        self.chosen_caption.link = _bind(lambda _o: self.chosen)    # savers_page.nml:29

        self.chosen.framed = False    # savers_page.nml:33
        self.chosen.page_keys = False    # savers_page.nml:34
        self.chosen.x = 2    # savers_page.nml:35
        self.chosen.y = 3    # savers_page.nml:36
        self.chosen.width = 18    # savers_page.nml:37
        self.chosen.height = 7    # savers_page.nml:38

        self.join.text = _bind(lambda _o: _tr('<───── ~A~dd'), yielding=True)    # savers_page.nml:43
        self.join.x = 21    # savers_page.nml:44
        self.join.y = 4    # savers_page.nml:45
        self.join.width = 15    # savers_page.nml:46
        self.join.height = 2    # savers_page.nml:47
        self.join.on_click = self.on_join_click    # savers_page.nml:42

        self.drop.text = _bind(lambda _o: _tr('~R~emove ──>'), yielding=True)    # savers_page.nml:52
        self.drop.x = 21    # savers_page.nml:53
        self.drop.y = 6    # savers_page.nml:54
        self.drop.width = 15    # savers_page.nml:55
        self.drop.height = 2    # savers_page.nml:56
        self.drop.on_click = self.on_drop_click    # savers_page.nml:51

        self.offered_caption.x = 37    # savers_page.nml:60
        self.offered_caption.y = 2    # savers_page.nml:61
        self.offered_caption.width = 18    # savers_page.nml:62
        self.offered_caption.height = 1    # savers_page.nml:63
        self.offered_caption.text = _bind(    # savers_page.nml:64
            lambda _o: _tr('A~v~ailable savers'),
            yielding=True,
        )
        self.offered_caption.link = _bind(lambda _o: self.offered)    # savers_page.nml:65

        self.offered.framed = False    # savers_page.nml:69
        self.offered.page_keys = False    # savers_page.nml:70
        self.offered.x = 37    # savers_page.nml:71
        self.offered.y = 3    # savers_page.nml:72
        self.offered.width = 18    # savers_page.nml:73
        self.offered.height = 7    # savers_page.nml:74

        self.time_caption.x = 2    # savers_page.nml:78
        self.time_caption.y = 11    # savers_page.nml:79
        self.time_caption.width = 8    # savers_page.nml:80
        self.time_caption.height = 1    # savers_page.nml:81
        self.time_caption.text = _bind(lambda _o: _tr('~T~ime'), yielding=True)    # savers_page.nml:82
        self.time_caption.link = _bind(lambda _o: self.time)    # savers_page.nml:83

        self.time.x = 2    # savers_page.nml:87
        self.time.y = 12    # savers_page.nml:88
        self.time.width = 16    # savers_page.nml:89
        self.time.height = 5    # savers_page.nml:90
        self.time.items = _bind(    # savers_page.nml:91
            lambda _o: [_tr('~N~ever'), _tr('~1~ minute'), _tr('~2~ minutes'), _tr('~5~ minutes'), _tr('1~0~ minutes')],
            yielding=True,
        )

        self.mouse.x = 20    # savers_page.nml:95
        self.mouse.y = 12    # savers_page.nml:96
        self.mouse.width = 35    # savers_page.nml:97
        self.mouse.height = 1    # savers_page.nml:98
        self.mouse.items = _bind(    # savers_page.nml:99
            lambda _o: [_tr('Use ~m~ouse to call saver')],
            yielding=True,
        )
