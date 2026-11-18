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
from navigator.widgets.viewer.commands import AddFilter, ChooseEncoding, ContinueSearch, GotoAddress, HexMode, ReverseSearch    # quick_viewer.nml:1
from navigator.widgets.viewer.commands import SaveViewAs, SearchAgain, SearchFor, SwitchRendered, Unwrap    # quick_viewer.nml:2
from navigator.widgets.viewer.file_viewer import FileViewer    # quick_viewer.nml:3
from navml.widgets.dialog.scroll_bar import ScrollBar    # quick_viewer.nml:4
from navigator.widgets.viewer.commands import SetViewFilter, SetViewMode    # quick_viewer.nml:5

__navml_component__ = "QuickViewer"

__all__ = ["QuickViewer"]


class QuickViewer(_Component):
    """Ctrl+Q: the file under the active panel's cursor, shown in the passive

    panel's place -- DOS Navigator's ``THFileViewer``, which ``SwitchView(dtView)``
    put where the other panel stood.

    The viewer is the F3 window's, framed the way a panel is framed because it
    stands where one stood.  ``ViewInsert`` gave it a ``TViewScroll`` on the
    frame's right column, shown only while the viewer is selected
    (``TFileViewer.SetState``); the bar here does the same, and so does the
    bottom frame's (a departure, as the F3 window's).
    """

    #: The document this class was generated from.
    __navml_source__ = "quick_viewer.nml"

    #: ``StatusDef hcView``'s keys while the keyboard is in here: DN's quick
    #: view was a ``TFileViewer`` (``THFileViewer``, ``HelpCtx := hcView``), and
    #: handled them as the F3 window's did (``viewer_host``).  Shift+F4 is the
    #: panels' *Edit...* (``cmXEditFile``), as hcView had it too.
    #: 
    #: A departure: a key hcView did not list -- F3, F8, the panels' Alt and
    #: Ctrl keys -- did nothing there; here it still reaches the panels, and
    #: the key bar says what it does.  Not bound: Shift+F2's *Store*, since the
    #: quick view never types over a byte, and Ctrl+F4's *Close*, which would
    #: close the file manager.
    keys = {    # quick_viewer.nml:34
        'f2': Unwrap,    # quick_viewer.nml:35
        'f4': HexMode,    # quick_viewer.nml:36
        'f5': GotoAddress,    # quick_viewer.nml:37
        'f6': AddFilter,    # quick_viewer.nml:38
        'f7': SearchFor,    # quick_viewer.nml:39
        'ctrl+f7': ReverseSearch,    # quick_viewer.nml:40
        'shift+f7': ContinueSearch,    # quick_viewer.nml:41
        'ctrl+l': SearchAgain,    # quick_viewer.nml:42
        'ctrl+enter': SearchAgain,    # quick_viewer.nml:43
        'shift+f3': SwitchRendered,    # quick_viewer.nml:45
        'shift+f5': SaveViewAs,    # quick_viewer.nml:46
        'shift+f6': ChooseEncoding,    # quick_viewer.nml:47
    }

    #: F1 while the keyboard is in the view (``Navigator.help_topic``).
    help_topic: str = _reactive('viewer.md#quick-view')    # quick_viewer.nml:18

    #: Columns left clear at each end of the top frame for the window's icons,
    #: as a panel leaves them.
    title_margin: int = _reactive(0)    # quick_viewer.nml:22

    #: Ids, annotated so the hand-written half completes them.
    viewer: FileViewer    # quick_viewer.nml:58
    bar: ScrollBar    # quick_viewer.nml:66
    hbar: ScrollBar    # quick_viewer.nml:84

    #: The commands this component handles itself.
    async def on_unwrap(self, event: _Any) -> bool:    # quick_viewer.nml:51
        """``Unwrap``."""
        self.viewer.toggle_wrap()
        return True

    async def on_hex_mode(self, event: _Any) -> bool:    # quick_viewer.nml:52
        """``HexMode``."""
        self.viewer.cycle_mode()
        return True

    async def on_add_filter(self, event: _Any) -> bool:    # quick_viewer.nml:53
        """``AddFilter``."""
        self.viewer.cycle_filter()
        return True

    async def on_set_view_mode(self, event: _Any) -> bool:    # quick_viewer.nml:54
        """``SetViewMode``."""
        self.viewer.set_mode(event.mode)
        return True

    async def on_set_view_filter(self, event: _Any) -> bool:    # quick_viewer.nml:55
        """``SetViewFilter``."""
        self.viewer.set_filter(event.filter)
        return True

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_bar_scroll(self, event: _Event) -> bool:    # quick_viewer.nml:66
        """``bar`` raised an event whose handler is ``on_scroll``."""
        return False

    async def on_hbar_scroll(self, event: _Event) -> bool:    # quick_viewer.nml:84
        """``hbar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.viewer = FileViewer(parent=self)    # quick_viewer.nml:57
        self.bar = ScrollBar(parent=self)    # quick_viewer.nml:65
        self.hbar = ScrollBar(parent=self)    # quick_viewer.nml:83

        self.viewer.x = 1    # quick_viewer.nml:60
        self.viewer.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # quick_viewer.nml:61
        self.viewer.y = 1    # quick_viewer.nml:62
        self.viewer.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # quick_viewer.nml:63

        self.bar.width = 1    # quick_viewer.nml:67
        self.bar.value = _bind(lambda _o: self.viewer.top)    # quick_viewer.nml:72
        self.bar.maximum = _bind(lambda _o: self.viewer.size)    # quick_viewer.nml:73
        self.bar.page = _bind(    # quick_viewer.nml:74
            lambda _o: max(1, self.viewer.width * self.viewer.height)
        )
        self.bar.visible = _bind(    # quick_viewer.nml:77
            lambda _o: self.viewer.focused and self.viewer.overflows
        )
        self.bar.x = _bind(lambda _o: max(0, _o.parent.width - _o.width))    # quick_viewer.nml:69
        self.bar.y = 1    # quick_viewer.nml:70
        self.bar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # quick_viewer.nml:71
        self.bar.on_scroll = self.on_bar_scroll    # quick_viewer.nml:66

        self.hbar.orientation = 'horizontal'    # quick_viewer.nml:85
        self.hbar.height = 1    # quick_viewer.nml:86
        self.hbar.value = _bind(lambda _o: self.viewer.x_delta)    # quick_viewer.nml:91
        self.hbar.maximum = _bind(    # quick_viewer.nml:92
            lambda _o: max(0, self.viewer.row_span - self.viewer.width)
        )
        self.hbar.page = _bind(lambda _o: max(1, self.viewer.width))    # quick_viewer.nml:93
        self.hbar.visible = _bind(    # quick_viewer.nml:94
            lambda _o: self.viewer.focused and self.viewer.row_span > self.viewer.width and (_o.width >= 4)
        )
        self.hbar.x = 2    # quick_viewer.nml:88
        self.hbar.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # quick_viewer.nml:89
        self.hbar.y = _bind(lambda _o: max(0, _o.parent.height - _o.height))    # quick_viewer.nml:90
        self.hbar.on_scroll = self.on_hbar_scroll    # quick_viewer.nml:84

        self._navml_built(__class__)
