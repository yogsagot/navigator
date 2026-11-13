# navml: generated
"""Generated from ``db_search_dialog.nml``.

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
from navml.widgets.dialog.button import Button    # db_search_dialog.nml:1
from navml.widgets.dialog.button_row import ButtonRow    # db_search_dialog.nml:2
from navml.widgets.dialog.commands import Help    # db_search_dialog.nml:3
from navml.widgets.dialog.check_boxes import CheckBoxes    # db_search_dialog.nml:4
from navml.widgets.dialog.dialog import Dialog    # db_search_dialog.nml:5
from navml.widgets.dialog.field import Field    # db_search_dialog.nml:6
from navml.widgets.dialog.label import Label    # db_search_dialog.nml:7
from navml.widgets.dialog.radio_buttons import RadioButtons    # db_search_dialog.nml:8

__navml_component__ = "DBSearchDialog"

__all__ = ["DBSearchDialog"]


class DBSearchDialog(Dialog, _Component):
    """F7 in the dBase viewer: DOS Navigator's ``dlgDbFind`` -- the text, *Case

    sensitive*, the scope and the direction, in the resource's places.  A row
    taller than its 55 by 12 for this library's buttons.
    """

    #: The document this class was generated from.
    __navml_source__ = "db_search_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    text: Field    # db_search_dialog.nml:24
    options_caption: Label    # db_search_dialog.nml:36
    options: CheckBoxes    # db_search_dialog.nml:44
    scope_caption: Label    # db_search_dialog.nml:52
    scope: RadioButtons    # db_search_dialog.nml:60
    direction_caption: Label    # db_search_dialog.nml:68
    direction: RadioButtons    # db_search_dialog.nml:76
    pick: Button    # db_search_dialog.nml:94
    abandon: Button    # db_search_dialog.nml:99
    helper: Button    # db_search_dialog.nml:104

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_pick_click(self, event: _Event) -> bool:    # db_search_dialog.nml:94
        """``pick`` raised an event whose handler is ``on_click``."""
        return False

    async def on_abandon_click(self, event: _Event) -> bool:    # db_search_dialog.nml:99
        """``abandon`` raised an event whose handler is ``on_click``."""
        return False

    async def on_helper_click(self, event: _Event) -> bool:    # db_search_dialog.nml:104
        """``helper`` raised an event whose handler is ``on_click``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.text = Field(parent=self)    # db_search_dialog.nml:23
        self.options_caption = Label(parent=self)    # db_search_dialog.nml:35
        self.options = CheckBoxes(parent=self)    # db_search_dialog.nml:43
        self.scope_caption = Label(parent=self)    # db_search_dialog.nml:51
        self.scope = RadioButtons(parent=self)    # db_search_dialog.nml:59
        self.direction_caption = Label(parent=self)    # db_search_dialog.nml:67
        self.direction = RadioButtons(parent=self)    # db_search_dialog.nml:75
        _w1 = ButtonRow(parent=self)    # db_search_dialog.nml:84
        self.pick = Button(parent=_w1)    # db_search_dialog.nml:93
        self.abandon = Button(parent=_w1)    # db_search_dialog.nml:98
        self.helper = Button(parent=_w1)    # db_search_dialog.nml:103

        self.modal_width = 55    # db_search_dialog.nml:14
        self.modal_height = 13    # db_search_dialog.nml:15
        self.title = _bind(lambda _o: _tr('Search'), yielding=True)    # db_search_dialog.nml:16
        self.help_topic = 'viewer.md#searching-a-table'    # db_search_dialog.nml:17
        self.buttons = 'none'    # db_search_dialog.nml:18
        self.buttons_row = _bind(    # db_search_dialog.nml:20
            lambda _o: (self.pick, self.abandon, self.helper)
        )

        self.text.y = 2    # db_search_dialog.nml:25
        self.text.label_text = _bind(    # db_search_dialog.nml:29
            lambda _o: _tr('~T~ext to search'),
            yielding=True,
        )
        self.text.label_width = 16    # db_search_dialog.nml:30
        self.text.history_id = 'dbsearch'    # db_search_dialog.nml:31
        self.text.x = 2    # db_search_dialog.nml:27
        self.text.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # db_search_dialog.nml:28

        self.options_caption.x = 1    # db_search_dialog.nml:37
        self.options_caption.y = 4    # db_search_dialog.nml:38
        self.options_caption.width = 11    # db_search_dialog.nml:39
        self.options_caption.text = _bind(    # db_search_dialog.nml:40
            lambda _o: _tr('Options'),
            yielding=True,
        )
        self.options_caption.link = _bind(lambda _o: self.options)    # db_search_dialog.nml:41

        self.options.x = 12    # db_search_dialog.nml:45
        self.options.y = 4    # db_search_dialog.nml:46
        self.options.width = 20    # db_search_dialog.nml:47
        self.options.height = 1    # db_search_dialog.nml:48
        self.options.items = _bind(    # db_search_dialog.nml:49
            lambda _o: [_tr('~C~ase sensitive')],
            yielding=True,
        )

        self.scope_caption.x = 5    # db_search_dialog.nml:53
        self.scope_caption.y = 6    # db_search_dialog.nml:54
        self.scope_caption.width = 6    # db_search_dialog.nml:55
        self.scope_caption.text = _bind(lambda _o: _tr('Scope'), yielding=True)    # db_search_dialog.nml:56
        self.scope_caption.link = _bind(lambda _o: self.scope)    # db_search_dialog.nml:57

        self.scope.x = 12    # db_search_dialog.nml:61
        self.scope.y = 6    # db_search_dialog.nml:62
        self.scope.width = 21    # db_search_dialog.nml:63
        self.scope.height = 2    # db_search_dialog.nml:64
        self.scope.items = _bind(    # db_search_dialog.nml:65
            lambda _o: [_tr('~I~n cursor field'), _tr('~A~ll fields')],
            yielding=True,
        )

        self.direction_caption.x = 35    # db_search_dialog.nml:69
        self.direction_caption.y = 4    # db_search_dialog.nml:70
        self.direction_caption.width = 10    # db_search_dialog.nml:71
        self.direction_caption.text = _bind(    # db_search_dialog.nml:72
            lambda _o: _tr('Direction'),
            yielding=True,
        )
        self.direction_caption.link = _bind(lambda _o: self.direction)    # db_search_dialog.nml:73

        self.direction.x = 35    # db_search_dialog.nml:77
        self.direction.y = 5    # db_search_dialog.nml:78
        self.direction.width = 18    # db_search_dialog.nml:79
        self.direction.height = 3    # db_search_dialog.nml:80
        self.direction.items = _bind(    # db_search_dialog.nml:81
            lambda _o: [_tr('~F~orward'), _tr('~B~ackward'), _tr('~E~ntire scope')],
            yielding=True,
        )

        _w1.justify = 'start'    # db_search_dialog.nml:85
        _w1.button_width = 10    # db_search_dialog.nml:86
        _w1.spacing = 2    # db_search_dialog.nml:87
        _w1.x = 14# db_search_dialog.nml:89
        _w1.width = _bind(lambda _o: max(0, _o.parent.width - 14))    # db_search_dialog.nml:90
        _w1.y = _bind(lambda _o: max(0, _o.parent.height - 2 - _o.height))    # db_search_dialog.nml:91

        self.pick.text = _bind(lambda _o: _tr('O~K~'), yielding=True)    # db_search_dialog.nml:95
        self.pick.default = True    # db_search_dialog.nml:96
        self.pick.on_click = self.on_pick_click    # db_search_dialog.nml:94

        self.abandon.text = _bind(lambda _o: _tr('Cancel'), yielding=True)    # db_search_dialog.nml:100
        self.abandon.on_click = self.on_abandon_click    # db_search_dialog.nml:99

        self.helper.text = _bind(lambda _o: _tr('Help'), yielding=True)    # db_search_dialog.nml:105
        self.helper.command = Help    # db_search_dialog.nml:106
        self.helper.on_click = self.on_helper_click    # db_search_dialog.nml:104

        self._navml_built(__class__)
