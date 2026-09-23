# navml: generated
"""Generated from ``list_viewer.nml``.

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
from navml.widgets.control import Control    # list_viewer.nml:1

__navml_component__ = "ListViewer"

__all__ = ["ListViewer"]


class ListViewer(Control, _Component):
    """A framed list with a cursor, a title and a footer.

    DOS Navigator's ``[57-60] List normal / focused / selected / divider``, and
    Turbo Vision's ``TListViewer``.  **It paints its own rows** -- there are no
    child widgets in here, for the reason ``navkit/DESIGN.md``'s *Parts:
    listing rows do not become widgets* settles by fidelity: "``TListViewer``
    draws its own items and picks a palette entry per item according to its
    state.  One view, many items, no per-item objects.  Rows were never objects
    in the original."

    ``items`` and ``cursor`` are properties a viewer **navigates**, so a
    document seeds them with a constructor keyword rather than binding them --
    the rule *A property a widget navigates cannot be bound* covers both.
    """

    #: The document this class was generated from.
    __navml_source__ = "list_viewer.nml"

    #: What is listed.  Replaced rather than mutated, because the reactive
    #: layer counts a change only when a collection is replaced.
    items = _reactive(factory=lambda: [])    # list_viewer.nml:19

    #: Which row the cursor is on.
    cursor: int = _reactive(0)    # list_viewer.nml:22

    #: The first row shown.  Followed automatically; assign it only to jump.
    scroll: int = _reactive(0)    # list_viewer.nml:25

    #: A line under the top frame, or 0 for none.  ``Panel`` uses it for the
    #: column headings the original draws there.
    header: int = _reactive(0)    # list_viewer.nml:29

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
