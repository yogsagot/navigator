# navml: generated
"""Generated from ``menu_params_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog    # menu_params_dialog.nml:1
from navml.widgets.dialog.field import Field    # menu_params_dialog.nml:2
from navml.widgets.dialog.label import Label    # menu_params_dialog.nml:3

__navml_component__ = "MenuParamsDialog"

__all__ = ["MenuParamsDialog"]


class MenuParamsDialog(Dialog, _Component):
    """A user menu item's ``%3`` .. ``%9``: DOS Navigator's ``InputBox`` with

    ``dlMenuParams`` for its title and the item's ``<Title`` line, or
    ``dlMenuParamLabel``, for its caption -- on the row above the line, as
    ``InputBox`` put a label that would not fit beside it.
    """

    #: The document this class was generated from.
    __navml_source__ = "menu_params_dialog.nml"

    #: The caption: the item's ``<Title``, or DN's *Parameters*.
    caption: str = _reactive('~P~arameters')    # menu_params_dialog.nml:11

    #: Ids, annotated so the hand-written half completes them.
    caption_label: Label    # menu_params_dialog.nml:18
    entry: Field    # menu_params_dialog.nml:28

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.caption_label = Label(parent=self)    # menu_params_dialog.nml:17
        self.entry = Field(parent=self)    # menu_params_dialog.nml:27

        self.modal_width = 60    # menu_params_dialog.nml:13
        self.modal_height = 9    # menu_params_dialog.nml:14
        self.title = _bind(lambda _o: _tr('Menu Parameters'), yielding=True)    # menu_params_dialog.nml:15

        self.caption_label.x = 2    # menu_params_dialog.nml:19
        self.caption_label.y = 1    # menu_params_dialog.nml:20
        self.caption_label.width = _bind(    # menu_params_dialog.nml:21
            lambda _o: max(0, _o.parent.width - 4)
        )
        self.caption_label.height = 1    # menu_params_dialog.nml:22
        self.caption_label.text = _bind(lambda _o: self.caption)    # menu_params_dialog.nml:23
        self.caption_label.link = _bind(lambda _o: self.entry.entry)    # menu_params_dialog.nml:24

        self.entry.x = 2    # menu_params_dialog.nml:29
        self.entry.y = 2    # menu_params_dialog.nml:30
        self.entry.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # menu_params_dialog.nml:31
        self.entry.height = 1    # menu_params_dialog.nml:32
        self.entry.label_text = ''    # menu_params_dialog.nml:33
        self.entry.label_width = 0    # menu_params_dialog.nml:34
        self.entry.history_id = 'menu_params'    # menu_params_dialog.nml:35
