# navml: generated
"""Generated from ``edit_window.nml``.

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
from navigator.commands import SaveText    # edit_window.nml:1
from navigator.widgets.file_editor import FileEditor    # edit_window.nml:2
from navml.commands import CloseWindow    # edit_window.nml:3
from navml.widgets.dialog.scroll_bar import ScrollBar    # edit_window.nml:4
from navml.widgets.dialog.static_text import StaticText    # edit_window.nml:5
from navml.widgets.window import Window    # edit_window.nml:6

__navml_component__ = "EditWindow"

__all__ = ["EditWindow"]


class EditWindow(Window, _Component):
    """F4: DOS Navigator's ``TEditWindow`` (``MICROED.PAS``).

    A standard window titled ``Edit - `` and the file's path, the editor filling
    the inside of its frame, a vertical scroll bar on the right frame column, a
    horizontal one along the bottom frame, and ``TInfoLine`` over the bottom
    frame's left end -- the views ``TEditWindow.Init`` inserts, in the places it
    puts them.  **It opens zoomed**, as the viewer does.

    Both scroll bars and the info line show only while the window is active, as
    ``TFileEditor.SetState`` hid the bars and ``TInfoLine.Draw`` drew nothing.
    """

    #: The document this class was generated from.
    __navml_source__ = "edit_window.nml"

    #: ``StatusDef hcEditor``: what it captions.  The editing keys are the
    #: editor's own table, and Esc and Alt+F3 close the window, asking first
    #: about a text that has changed.
    keys = {    # edit_window.nml:24
        'escape': CloseWindow,    # edit_window.nml:25
        'alt+f3': CloseWindow,    # edit_window.nml:26
        'f2': SaveText,    # edit_window.nml:27
    }

    #: Ids, annotated so the hand-written half completes them.
    editor: FileEditor    # edit_window.nml:30
    vbar: ScrollBar    # edit_window.nml:38
    hbar: ScrollBar    # edit_window.nml:51
    info: StaticText    # edit_window.nml:64

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_vbar_scroll(self, event: _Event) -> bool:    # edit_window.nml:38
        """``vbar`` raised an event whose handler is ``on_scroll``."""
        return False

    async def on_hbar_scroll(self, event: _Event) -> bool:    # edit_window.nml:51
        """``hbar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.editor = FileEditor(parent=self)    # edit_window.nml:29
        self.vbar = ScrollBar(parent=self)    # edit_window.nml:37
        self.hbar = ScrollBar(parent=self)    # edit_window.nml:50
        self.info = StaticText(parent=self)    # edit_window.nml:63

        self.zoomed = True    # edit_window.nml:19

        self.editor.x = 1    # edit_window.nml:31
        self.editor.y = 1    # edit_window.nml:32
        self.editor.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # edit_window.nml:33
        self.editor.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # edit_window.nml:34

        self.vbar.visible = _bind(lambda _o: self.active)    # edit_window.nml:39
        self.vbar.x = _bind(lambda _o: _o.parent.width - 1)    # edit_window.nml:40
        self.vbar.y = 1    # edit_window.nml:41
        self.vbar.width = 1    # edit_window.nml:42
        self.vbar.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # edit_window.nml:43
        self.vbar.value = _bind(lambda _o: self.editor.line)    # edit_window.nml:44
        self.vbar.maximum = _bind(    # edit_window.nml:45
            lambda _o: max(0, self.editor.line_count - 1)
        )
        self.vbar.page = _bind(lambda _o: max(1, self.editor.height))    # edit_window.nml:46
        self.vbar.on_scroll = self.on_vbar_scroll    # edit_window.nml:38

        self.hbar.orientation = 'horizontal'    # edit_window.nml:52
        self.hbar.visible = _bind(lambda _o: self.active)    # edit_window.nml:53
        self.hbar.x = 24    # edit_window.nml:54
        self.hbar.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # edit_window.nml:55
        self.hbar.width = _bind(lambda _o: max(0, _o.parent.width - 26))    # edit_window.nml:56
        self.hbar.height = 1    # edit_window.nml:57
        self.hbar.value = _bind(lambda _o: self.editor.col)    # edit_window.nml:58
        self.hbar.maximum = _bind(lambda _o: max(255, self.editor.col))    # edit_window.nml:59
        self.hbar.page = _bind(lambda _o: max(1, self.editor.width))    # edit_window.nml:60
        self.hbar.on_scroll = self.on_hbar_scroll    # edit_window.nml:51

        self.info.visible = _bind(lambda _o: self.active)    # edit_window.nml:65
        self.info.x = 2    # edit_window.nml:66
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # edit_window.nml:67
        self.info.width = _bind(    # edit_window.nml:68
            lambda _o: min(len(self.editor.info_text), max(0, _o.parent.width - 4))
        )
        self.info.height = 1    # edit_window.nml:69
        self.info.text = _bind(lambda _o: self.editor.info_text)    # edit_window.nml:70
