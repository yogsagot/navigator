# navml: generated
"""Generated from ``key_capture_dialog.nml``.

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
from navml.widgets.dialog.dialog import Dialog    # key_capture_dialog.nml:1
from navml.widgets.dialog.static_text import StaticText    # key_capture_dialog.nml:2
from navigator.widgets.setup.key_capture_dialog.key_catcher import KeyCatcher    # key_capture_dialog.nml:3

__navml_component__ = "KeyCaptureDialog"

__all__ = ["KeyCaptureDialog"]


class KeyCaptureDialog(Dialog, _Component):
    """Key bindings' *Press a key*: whatever is pressed is the key to bind, two in

    a row a chord; Enter takes it and Esc leaves it.  Not DOS Navigator's,
    which had no key editor.
    """

    #: The document this class was generated from.
    __navml_source__ = "key_capture_dialog.nml"

    #: Ids, annotated so the hand-written half completes them.
    hint: StaticText    # key_capture_dialog.nml:14
    catcher: KeyCatcher    # key_capture_dialog.nml:22

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.hint = StaticText(parent=self)    # key_capture_dialog.nml:13
        self.catcher = KeyCatcher(parent=self)    # key_capture_dialog.nml:21

        self.modal_width = 44    # key_capture_dialog.nml:9
        self.modal_height = 9    # key_capture_dialog.nml:10
        self.title = 'Press a key'    # key_capture_dialog.nml:11

        self.hint.x = 2    # key_capture_dialog.nml:15
        self.hint.y = 2    # key_capture_dialog.nml:16
        self.hint.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # key_capture_dialog.nml:17
        self.hint.height = 2    # key_capture_dialog.nml:18
        self.hint.text = 'Press the key, or two for a chord.\nEnter takes it, Esc cancels.'    # key_capture_dialog.nml:19

        self.catcher.x = 3    # key_capture_dialog.nml:23
        self.catcher.y = 5    # key_capture_dialog.nml:24
        self.catcher.width = _bind(lambda _o: max(0, _o.parent.width - 6))    # key_capture_dialog.nml:25
        self.catcher.height = 1    # key_capture_dialog.nml:26
