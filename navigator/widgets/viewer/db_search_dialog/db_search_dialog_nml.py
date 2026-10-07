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

from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navml.widgets.dialog.check_boxes import CheckBoxes    # db_search_dialog.nml:1
from navml.widgets.dialog.dialog import Dialog    # db_search_dialog.nml:2
from navml.widgets.dialog.field import Field    # db_search_dialog.nml:3
from navml.widgets.dialog.label import Label    # db_search_dialog.nml:4
from navml.widgets.dialog.radio_buttons import RadioButtons    # db_search_dialog.nml:5

__navml_component__ = "DBSearchDialog"

__all__ = ["DBSearchDialog"]


class DBSearchDialog(Dialog, _Component):
    """F7 in the dBase viewer: DOS Navigator's ``dlgDbFind`` -- the text, *Case

    sensitive*, the scope and the direction, in the resource's places.  A row
    taller than its 55 by 12 for this library's buttons; Help is left out.
    """

    #: The document this class was generated from.
    __navml_source__ = "db_search_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    text: Field    # db_search_dialog.nml:18
    options_caption: Label    # db_search_dialog.nml:28
    options: CheckBoxes    # db_search_dialog.nml:37
    scope_caption: Label    # db_search_dialog.nml:45
    scope: RadioButtons    # db_search_dialog.nml:54
    direction_caption: Label    # db_search_dialog.nml:62
    direction: RadioButtons    # db_search_dialog.nml:71

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.text = Field(parent=self)    # db_search_dialog.nml:17
        self.options_caption = Label(parent=self)    # db_search_dialog.nml:27
        self.options = CheckBoxes(parent=self)    # db_search_dialog.nml:36
        self.scope_caption = Label(parent=self)    # db_search_dialog.nml:44
        self.scope = RadioButtons(parent=self)    # db_search_dialog.nml:53
        self.direction_caption = Label(parent=self)    # db_search_dialog.nml:61
        self.direction = RadioButtons(parent=self)    # db_search_dialog.nml:70

        self.modal_width = 55    # db_search_dialog.nml:11
        self.modal_height = 13    # db_search_dialog.nml:12
        self.title = 'Search'    # db_search_dialog.nml:13
        self.buttons = 'ok-cancel'    # db_search_dialog.nml:14

        self.text.x = 2    # db_search_dialog.nml:19
        self.text.y = 2    # db_search_dialog.nml:20
        self.text.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # db_search_dialog.nml:21
        self.text.height = 1    # db_search_dialog.nml:22
        self.text.label_text = '~T~ext to search'    # db_search_dialog.nml:23
        self.text.label_width = 16    # db_search_dialog.nml:24
        self.text.history_id = 'dbsearch'    # db_search_dialog.nml:25

        self.options_caption.x = 3    # db_search_dialog.nml:29
        self.options_caption.y = 4    # db_search_dialog.nml:30
        self.options_caption.width = 8    # db_search_dialog.nml:31
        self.options_caption.height = 1    # db_search_dialog.nml:32
        self.options_caption.text = 'Options'    # db_search_dialog.nml:33
        self.options_caption.link = _bind(lambda _o: self.options)    # db_search_dialog.nml:34

        self.options.x = 12    # db_search_dialog.nml:38
        self.options.y = 4    # db_search_dialog.nml:39
        self.options.width = 20    # db_search_dialog.nml:40
        self.options.height = 1    # db_search_dialog.nml:41
        self.options.items = ['~C~ase sensitive']    # db_search_dialog.nml:42

        self.scope_caption.x = 5    # db_search_dialog.nml:46
        self.scope_caption.y = 6    # db_search_dialog.nml:47
        self.scope_caption.width = 6    # db_search_dialog.nml:48
        self.scope_caption.height = 1    # db_search_dialog.nml:49
        self.scope_caption.text = 'Scope'    # db_search_dialog.nml:50
        self.scope_caption.link = _bind(lambda _o: self.scope)    # db_search_dialog.nml:51

        self.scope.x = 12    # db_search_dialog.nml:55
        self.scope.y = 6    # db_search_dialog.nml:56
        self.scope.width = 21    # db_search_dialog.nml:57
        self.scope.height = 2    # db_search_dialog.nml:58
        self.scope.items = ['~I~n cursor field', '~A~ll fields']    # db_search_dialog.nml:59

        self.direction_caption.x = 35    # db_search_dialog.nml:63
        self.direction_caption.y = 4    # db_search_dialog.nml:64
        self.direction_caption.width = 10    # db_search_dialog.nml:65
        self.direction_caption.height = 1    # db_search_dialog.nml:66
        self.direction_caption.text = 'Direction'    # db_search_dialog.nml:67
        self.direction_caption.link = _bind(lambda _o: self.direction)    # db_search_dialog.nml:68

        self.direction.x = 35    # db_search_dialog.nml:72
        self.direction.y = 5    # db_search_dialog.nml:73
        self.direction.width = 18    # db_search_dialog.nml:74
        self.direction.height = 3    # db_search_dialog.nml:75
        self.direction.items = ['~F~orward', '~B~ackward', '~E~ntire scope']    # db_search_dialog.nml:76
