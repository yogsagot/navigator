# navml: generated
"""Generated from ``quick_viewer.nml``.

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
from navigator.widgets.file_viewer import FileViewer    # quick_viewer.nml:1
from navml.widgets.dialog.scroll_bar import ScrollBar    # quick_viewer.nml:2

__navml_component__ = "QuickViewer"

__all__ = ["QuickViewer"]


class QuickViewer(_Component):
    """Ctrl+Q: the file under the active panel's cursor, shown in the passive

    panel's place -- DOS Navigator's ``THFileViewer``, which ``SwitchView(dtView)``
    put where the other panel stood.

    The viewer is the F3 window's, framed the way a panel is framed because it
    stands where one stood.  ``ViewInsert`` gave it a ``TViewScroll`` on the
    frame's right column, shown only while the viewer is selected
    (``TFileViewer.SetState``); the bar here does the same.
    """

    #: The document this class was generated from.
    __navml_source__ = "quick_viewer.nml"

    #: Columns left clear at each end of the top frame for the window's icons,
    #: as a panel leaves them.
    title_margin: int = _reactive(0)    # quick_viewer.nml:15

    #: Ids, annotated so the hand-written half completes them.
    viewer: FileViewer    # quick_viewer.nml:18
    bar: ScrollBar    # quick_viewer.nml:25

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_bar_scroll(self, event: _Event) -> bool:    # quick_viewer.nml:25
        """``bar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.viewer = FileViewer(parent=self)    # quick_viewer.nml:17
        self.bar = ScrollBar(parent=self)    # quick_viewer.nml:24

        self.viewer.x = 1    # quick_viewer.nml:19
        self.viewer.y = 1    # quick_viewer.nml:20
        self.viewer.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # quick_viewer.nml:21
        self.viewer.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # quick_viewer.nml:22

        self.bar.x = _bind(lambda _o: _o.parent.width - 1)    # quick_viewer.nml:26
        self.bar.y = 1    # quick_viewer.nml:27
        self.bar.width = 1    # quick_viewer.nml:28
        self.bar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # quick_viewer.nml:29
        self.bar.value = _bind(lambda _o: self.viewer.top)    # quick_viewer.nml:30
        self.bar.maximum = _bind(lambda _o: self.viewer.size)    # quick_viewer.nml:31
        self.bar.page = _bind(    # quick_viewer.nml:32
            lambda _o: max(1, self.viewer.width * self.viewer.height)
        )
        self.bar.visible = _bind(lambda _o: self.viewer.focused)    # quick_viewer.nml:33
        self.bar.on_scroll = self.on_bar_scroll    # quick_viewer.nml:25
