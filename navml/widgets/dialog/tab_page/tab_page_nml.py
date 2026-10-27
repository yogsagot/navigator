# navml: generated
"""Generated from ``tab_page.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component

__navml_component__ = "TabPage"

__all__ = ["TabPage"]


class TabPage(_Component):
    """One page of a ``TabView``, written in the document that holds the view.

    A ``TabView`` takes any widget as a page and captions its tab with the
    page's ``title``; this is the page that is nothing more, for a dialog
    whose pages are laid out in its own markup rather than as components of
    their own -- so their ids stay the dialog's, as if there were no tabs.
    """

    #: The document this class was generated from.
    __navml_source__ = "tab_page.nml"

    #: The caption on its tab.
    title: str = _reactive('')    # tab_page.nml:9

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
