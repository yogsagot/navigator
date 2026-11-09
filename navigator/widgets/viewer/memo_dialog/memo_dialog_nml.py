# navml: generated
"""Generated from ``memo_dialog.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.events import Event as _Event
from navkit.i18n import tr as _tr
from navkit.reactive import bind as _bind

from navml.component import Component as _Component
from navigator.widgets.viewer.commands import AddFilter, ChooseEncoding, ContinueSearch, GotoAddress, HexMode, ReverseSearch    # memo_dialog.nml:1
from navigator.widgets.viewer.commands import SearchAgain, SearchFor, Unwrap    # memo_dialog.nml:2
from navigator.widgets.viewer.file_viewer import FileViewer    # memo_dialog.nml:3
from navml.widgets.dialog.dialog import Dialog    # memo_dialog.nml:4
from navml.widgets.dialog.scroll_bar import ScrollBar    # memo_dialog.nml:5

__navml_component__ = "MemoDialog"

__all__ = ["MemoDialog"]


class MemoDialog(Dialog, _Component):
    """F3 in the dBase viewer: DOS Navigator's ``ViewMemo`` (``DBVIEW.PAS``),

    *Memo view*.

    ``R.Assign(1,1,70,20)``, centred: a ``TNFileViewer`` on the memo from
    ``(2, 2)`` to ``(Size.X-2, Size.Y-4)``, its ``TViewScroll`` in the column
    after it, and OK.  The viewer is a ``TFileViewer`` with ``hcView``, so its
    keys are the viewer's while it has the keyboard -- handled by
    ``viewer_host``, as the F3 window's and the quick view's are.

    Not bound: Shift+F5's *Save as*, since a memo has no file of its own (the
    ``.fpt`` holds every record's) for it to be saved from, and Shift+F2's
    *Store*, since nothing is typed over.
    """

    #: The document this class was generated from.
    __navml_source__ = "memo_dialog.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # memo_dialog.nml:25
        'f2': Unwrap,    # memo_dialog.nml:26
        'f4': HexMode,    # memo_dialog.nml:27
        'f5': GotoAddress,    # memo_dialog.nml:28
        'f6': AddFilter,    # memo_dialog.nml:29
        'f7': SearchFor,    # memo_dialog.nml:30
        'ctrl+f7': ReverseSearch,    # memo_dialog.nml:31
        'shift+f7': ContinueSearch,    # memo_dialog.nml:32
        'ctrl+l': SearchAgain,    # memo_dialog.nml:33
        'ctrl+enter': SearchAgain,    # memo_dialog.nml:34
        'shift+f6': ChooseEncoding,    # memo_dialog.nml:35
    }

    #: Ids, annotated so the hand-written half completes them.
    viewer: FileViewer    # memo_dialog.nml:38
    bar: ScrollBar    # memo_dialog.nml:46

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_bar_scroll(self, event: _Event) -> bool:    # memo_dialog.nml:46
        """``bar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.viewer = FileViewer(parent=self)    # memo_dialog.nml:37
        self.bar = ScrollBar(parent=self)    # memo_dialog.nml:45

        self.modal_width = 69    # memo_dialog.nml:20
        self.modal_height = 19    # memo_dialog.nml:21
        self.title = _bind(lambda _o: _tr('Memo view'), yielding=True)    # memo_dialog.nml:22
        self.buttons = 'ok'    # memo_dialog.nml:23

        self.viewer.x = 2    # memo_dialog.nml:39
        self.viewer.y = 2    # memo_dialog.nml:40
        self.viewer.width = _bind(lambda _o: max(0, _o.parent.width - 4))    # memo_dialog.nml:41
        self.viewer.height = _bind(lambda _o: max(0, _o.parent.height - 6))    # memo_dialog.nml:42

        self.bar.x = _bind(lambda _o: _o.parent.width - 2)    # memo_dialog.nml:47
        self.bar.y = 2    # memo_dialog.nml:48
        self.bar.width = 1    # memo_dialog.nml:49
        self.bar.height = _bind(lambda _o: max(0, _o.parent.height - 6))    # memo_dialog.nml:50
        self.bar.value = _bind(lambda _o: self.viewer.top)    # memo_dialog.nml:51
        self.bar.maximum = _bind(lambda _o: self.viewer.size)    # memo_dialog.nml:52
        self.bar.page = _bind(    # memo_dialog.nml:53
            lambda _o: max(1, self.viewer.width * self.viewer.height)
        )
        self.bar.on_scroll = self.on_bar_scroll    # memo_dialog.nml:46
