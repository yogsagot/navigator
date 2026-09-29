# navml: generated
"""Generated from ``file_window.nml``.

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

from navml.component import Component as _Component
from navigator.commands import AddFilter, CloseViewer, ContinueSearch, GotoAddress, HexMode    # file_window.nml:1
from navigator.commands import ReverseSearch, SearchAgain, SearchFor, Unwrap    # file_window.nml:2
from navigator.widgets.file_viewer import FileViewer    # file_window.nml:3
from navml.commands import CloseWindow    # file_window.nml:4
from navml.widgets.dialog.scroll_bar import ScrollBar    # file_window.nml:5
from navml.widgets.dialog.static_text import StaticText    # file_window.nml:6
from navml.widgets.window import Window    # file_window.nml:7

__navml_component__ = "FileWindow"

__all__ = ["FileWindow"]


class FileWindow(Window, _Component):
    """F3: DOS Navigator's ``TFileWindow`` (``FVIEWER.PAS``).

    A standard window titled with the file's path, the viewer filling the
    inside of its frame, ``TViewScroll`` on the right frame column and
    ``TViewInfo`` over the bottom one -- the three views ``TFileWindow.Init``
    inserts, in the places it puts them.

    **It opens zoomed**, where DN reused the last viewer's rectangle
    (``LastViewerBounds``) and filled the desktop only the first time.  Taken
    to match the file manager, which opens zoomed too; the zoom icon gives the
    window its own rectangle back.
    """

    #: The document this class was generated from.
    __navml_source__ = "file_window.nml"

    #: ``StatusDef hcView``, in its order: the plain row, then Ctrl's and
    #: Shift's.  What DN bound there and Navigator cannot do yet -- Shift+F2
    #: Store, Shift+F5 Save as, Shift+F6 XLat -- is left out, so the bar closes
    #: up round it.  Ctrl+L continues a search with no caption, as it did.
    #: F3 closes the viewer, as Midnight Commander's does -- not DN's, which
    #: bound nothing there -- and has no caption either, so the line is DN's.
    keys = {    # file_window.nml:29
        'escape': CloseWindow,    # file_window.nml:30
        'f3': CloseViewer,    # file_window.nml:31
        'f2': Unwrap,    # file_window.nml:32
        'f4': HexMode,    # file_window.nml:33
        'f5': GotoAddress,    # file_window.nml:34
        'f6': AddFilter,    # file_window.nml:35
        'f7': SearchFor,    # file_window.nml:36
        'ctrl+f7': ReverseSearch,    # file_window.nml:37
        'shift+f7': ContinueSearch,    # file_window.nml:38
        'ctrl+l': SearchAgain,    # file_window.nml:39
    }

    #: Ids, annotated so the hand-written half completes them.
    viewer: FileViewer    # file_window.nml:42
    bar: ScrollBar    # file_window.nml:52
    info: StaticText    # file_window.nml:63

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_bar_scroll(self, event: _Event) -> bool:    # file_window.nml:52
        """``bar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.viewer = FileViewer(parent=self)    # file_window.nml:41
        self.bar = ScrollBar(parent=self)    # file_window.nml:51
        self.info = StaticText(parent=self)    # file_window.nml:62

        self.zoomed = True    # file_window.nml:21

        self.viewer.x = 1    # file_window.nml:43
        self.viewer.y = 1    # file_window.nml:44
        self.viewer.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # file_window.nml:45
        self.viewer.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # file_window.nml:46

        self.bar.x = _bind(lambda _o: _o.parent.width - 1)    # file_window.nml:53
        self.bar.y = 1    # file_window.nml:54
        self.bar.width = 1    # file_window.nml:55
        self.bar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # file_window.nml:56
        self.bar.value = _bind(lambda _o: self.viewer.top)    # file_window.nml:57
        self.bar.maximum = _bind(lambda _o: self.viewer.size)    # file_window.nml:58
        self.bar.page = _bind(    # file_window.nml:59
            lambda _o: max(1, self.viewer.width * self.viewer.height)
        )
        self.bar.on_scroll = self.on_bar_scroll    # file_window.nml:52

        self.info.x = 1    # file_window.nml:64
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # file_window.nml:65
        self.info.width = _bind(    # file_window.nml:66
            lambda _o: min(len(self.viewer.info_text), max(0, _o.parent.width - 3))
        )
        self.info.height = 1    # file_window.nml:67
        self.info.text = _bind(lambda _o: self.viewer.info_text)    # file_window.nml:68
