# navml: generated
"""Generated from ``diff_window.nml``.

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
from navigator.widgets.manager.commands import Rescan    # diff_window.nml:1
from navigator.widgets.viewer.commands import CloseViewer, NextDifference, PreviousDifference    # diff_window.nml:2
from navigator.widgets.viewer.diff_view import DiffView    # diff_window.nml:3
from navml.commands import CloseWindow    # diff_window.nml:4
from navml.widgets.dialog.scroll_bar import ScrollBar    # diff_window.nml:5
from navml.widgets.dialog.static_text import StaticText    # diff_window.nml:6
from navml.widgets.menu.menu_item import MenuItem    # diff_window.nml:7
from navml.widgets.menu.menu_line import MenuLine    # diff_window.nml:8
from navml.widgets.menu.sub_menu import SubMenu    # diff_window.nml:9
from navml.widgets.window import Window    # diff_window.nml:10

__navml_component__ = "DiffWindow"

__all__ = ["DiffWindow"]


class DiffWindow(Window, _Component):
    """File > Compare files: two files side by side, line against line.

    **A departure**: DOS Navigator had no such window -- its only comparison
    of files said whether they were the same (``CompareFiles``, behind
    *Compare directories*).  This is Midnight Commander's ``mcdiff`` and meld's:
    the two files in two columns under their paths, what one lacks faced by a
    filler row, the differences coloured and marked.  Laid out as the viewer's
    window is (``FileWindow``): opened zoomed, the view inside the frame, the
    scroll bar on its right column and the info line over its bottom one.

    The keys are ``mcdiff``'s N and P and meld's Alt+Down and Alt+Up for the
    next and previous difference; F3 and Esc close it, as the viewer's; Ctrl+R
    and Alt+R compare the two files again, as they re-read a panel.
    """

    #: The document this class was generated from.
    __navml_source__ = "diff_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # diff_window.nml:28
        'escape': CloseWindow,    # diff_window.nml:29
        'f3': CloseViewer,    # diff_window.nml:30
        'n': NextDifference,    # diff_window.nml:31
        'alt+down': NextDifference,    # diff_window.nml:32
        'p': PreviousDifference,    # diff_window.nml:33
        'alt+up': PreviousDifference,    # diff_window.nml:34
        'ctrl+r': Rescan,    # diff_window.nml:35
        'alt+r': Rescan,    # diff_window.nml:36
    }

    #: Ids, annotated so the hand-written half completes them.
    view: DiffView    # diff_window.nml:39
    bar: ScrollBar    # diff_window.nml:47
    info: StaticText    # diff_window.nml:58
    compare_menu: SubMenu    # diff_window.nml:69

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_bar_scroll(self, event: _Event) -> bool:    # diff_window.nml:47
        """``bar`` raised an event whose handler is ``on_scroll``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.view = DiffView(parent=self)    # diff_window.nml:38
        self.bar = ScrollBar(parent=self)    # diff_window.nml:46
        self.info = StaticText(parent=self)    # diff_window.nml:57
        self.compare_menu = SubMenu(parent=self)    # diff_window.nml:68
        _w1 = MenuItem(parent=self.compare_menu)    # diff_window.nml:73
        _w2 = MenuItem(parent=self.compare_menu)    # diff_window.nml:76
        _w3 = MenuLine(parent=self.compare_menu)    # diff_window.nml:79
        _w4 = MenuItem(parent=self.compare_menu)    # diff_window.nml:80
        _w5 = MenuLine(parent=self.compare_menu)    # diff_window.nml:83
        _w6 = MenuItem(parent=self.compare_menu)    # diff_window.nml:84

        self.zoomed = True    # diff_window.nml:26

        self.view.x = 1    # diff_window.nml:40
        self.view.y = 1    # diff_window.nml:41
        self.view.width = _bind(lambda _o: max(0, _o.parent.width - 2))    # diff_window.nml:42
        self.view.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # diff_window.nml:43

        self.bar.x = _bind(lambda _o: _o.parent.width - 1)    # diff_window.nml:48
        self.bar.y = 2    # diff_window.nml:49
        self.bar.width = 1    # diff_window.nml:50
        self.bar.height = _bind(lambda _o: max(0, _o.parent.height - 3))    # diff_window.nml:51
        self.bar.value = _bind(lambda _o: self.view.top)    # diff_window.nml:52
        self.bar.maximum = _bind(lambda _o: self.view.last_top)    # diff_window.nml:53
        self.bar.page = _bind(lambda _o: self.view.page)    # diff_window.nml:54
        self.bar.on_scroll = self.on_bar_scroll    # diff_window.nml:47

        self.info.name = 'info'    # diff_window.nml:59
        self.info.x = 1    # diff_window.nml:60
        self.info.y = _bind(lambda _o: max(0, _o.parent.height - 1))    # diff_window.nml:61
        self.info.width = _bind(    # diff_window.nml:62
            lambda _o: min(len(self.view.info_text), max(0, _o.parent.width - 3))
        )
        self.info.height = 1    # diff_window.nml:63
        self.info.text = _bind(lambda _o: self.view.info_text)    # diff_window.nml:64

        self.compare_menu.text = _bind(    # diff_window.nml:70
            lambda _o: _tr('~C~ompare'),
            yielding=True,
        )
        self.compare_menu.tooltip = _bind(    # diff_window.nml:71
            lambda _o: _tr('Step through the differences'),
            yielding=True,
        )
        self.compare_menu.after = 'File'    # diff_window.nml:72

        _w1.text = _bind(lambda _o: _tr('~N~ext difference'), yielding=True)    # diff_window.nml:74
        _w1.command = NextDifference    # diff_window.nml:75

        _w2.text = _bind(    # diff_window.nml:77
            lambda _o: _tr('~P~revious difference'),
            yielding=True,
        )
        _w2.command = PreviousDifference    # diff_window.nml:78

        _w4.text = _bind(lambda _o: _tr('~C~ompare again'), yielding=True)    # diff_window.nml:81
        _w4.command = Rescan    # diff_window.nml:82

        _w6.text = _bind(lambda _o: _tr('C~l~ose'), yielding=True)    # diff_window.nml:85
        _w6.command = CloseWindow    # diff_window.nml:86
