# navml: generated
"""Generated from ``label.nml``.

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

__navml_component__ = "Label"

__all__ = ["Label"]


class Label(_Component):
    """A line of text."""

    #: The document this class was generated from.
    __navml_source__ = "label.nml"

    text: str = _reactive('')    # label.nml:3
    align: str = _reactive('left')    # label.nml:4

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
