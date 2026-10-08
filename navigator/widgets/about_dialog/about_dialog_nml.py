# navml: generated
"""Generated from ``about_dialog.nml``.

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

from navml.component import Component as _Component
from navml.widgets.dialog.dialog import Dialog    # about_dialog.nml:1
from navigator.about import about_text, project_info    # about_dialog.nml:3

__navml_component__ = "AboutDialog"

__all__ = ["AboutDialog"]


class AboutDialog(Dialog, _Component):
    """≡ > About: DOS Navigator's ``MessageBoxAbout`` (``DNUTIL.PAS``).

    The original was a message box -- centred static text and an OK -- and so
    is this, built out of what ``Dialog`` already is: its ``message`` carries
    the text and ``buttons: "ok"`` hides the Cancel.  What the text says is
    ``pyproject.toml``'s, through :func:`navigator.about.project_info`, so the
    version, the licence and the author are written in one place.
    """

    #: The document this class was generated from.
    __navml_source__ = "about_dialog.nml"

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)

        self.modal_width = 52    # about_dialog.nml:13
        self.modal_height = 17    # about_dialog.nml:14
        self.title = _bind(lambda _o: _tr('About'), yielding=True)    # about_dialog.nml:15
        self.buttons = 'ok'    # about_dialog.nml:16
        self.prompt = about_text(project_info())    # about_dialog.nml:17
