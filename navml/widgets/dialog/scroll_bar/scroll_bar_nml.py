# navml: generated
"""Generated from ``scroll_bar.nml``.

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

__navml_component__ = "ScrollBar"

__all__ = ["ScrollBar"]


class ScrollBar(_Component):
    """A bar showing where a view sits in something longer than itself.

    DOS Navigator's ``[35] Scroll bar page`` and ``[36] Scroll bar icons``, and
    Turbo Vision's ``TScrollBar``.  It paints its own arrows, track and thumb
    -- there are no child widgets in here, for the reason
    ``navkit/DESIGN.md``'s *Parts: listing rows do not become widgets* gives:
    one view, many cells, no per-cell objects.
    """

    #: The document this class was generated from.
    __navml_source__ = "scroll_bar.nml"

    #: ``vertical`` or ``horizontal``.
    orientation: str = _reactive('vertical')    # scroll_bar.nml:10

    #: Where the view starts, from 0 to ``maximum``.
    value: int = _reactive(0)    # scroll_bar.nml:13

    #: The largest ``value`` there is.  Zero means nothing to scroll, and the
    #: bar paints a full track with no thumb.
    maximum: int = _reactive(0)    # scroll_bar.nml:17

    #: How much one page-up or page-down moves, and how long the thumb is
    #: drawn relative to the track.
    page: int = _reactive(1)    # scroll_bar.nml:21

    #: How far one click on an arrow moves.
    step: int = _reactive(1)    # scroll_bar.nml:24

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
