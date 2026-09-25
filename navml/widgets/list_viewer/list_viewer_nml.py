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

from navkit.events import Event as _Event
from navkit.reactive import bind as _bind
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navml.widgets.control import Control    # list_viewer.nml:1
from navml.widgets.scroll_bar import ScrollBar    # list_viewer.nml:2

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
    items = _reactive(factory=lambda: [])    # list_viewer.nml:20

    #: Which row the cursor is on.
    cursor: int = _reactive(0)    # list_viewer.nml:23

    #: The first row shown.  Followed automatically; assign it only to jump.
    scroll: int = _reactive(0)    # list_viewer.nml:26

    #: A line under the top frame, or 0 for none.  ``Panel`` uses it for the
    #: column headings the original draws there.
    header: int = _reactive(0)    # list_viewer.nml:30

    #: Ids, annotated so the hand-written half completes them.
    bar: ScrollBar    # list_viewer.nml:38

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_bar_scroll(self, event: _Event) -> bool:    # list_viewer.nml:38
        """``bar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.bar = ScrollBar(parent=self)    # list_viewer.nml:37

        self.bar.x = _bind(lambda _o: _o.parent.width - 1)    # list_viewer.nml:39
        self.bar.y = 1    # list_viewer.nml:40
        self.bar.width = 1    # list_viewer.nml:41
        self.bar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # list_viewer.nml:42
        self.bar.value = _bind(lambda _o: _o.parent.cursor)    # list_viewer.nml:43
        self.bar.maximum = _bind(lambda _o: max(0, len(_o.parent.items) - 1))    # list_viewer.nml:44
        self.bar.page = _bind(lambda _o: max(1, _o.parent.rows - 1))    # list_viewer.nml:45
        self.bar.visible = _bind(    # list_viewer.nml:46
            lambda _o: _o.parent.error is None and len(_o.parent.items) > _o.parent.rows
        )
        self.bar.on_scroll = self.on_bar_scroll    # list_viewer.nml:38
