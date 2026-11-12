# navml: generated
"""Generated from ``struct_window.nml``.

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
from navigator.widgets.viewer.commands import ContinueSearch, CopyPath, CopyValue, ExpandAll, SearchAgain, SearchFor, ViewTreeAsText    # struct_window.nml:1
from navigator.widgets.viewer.struct_window.data_tree import DataTree    # struct_window.nml:2
from navigator.widgets.manager.commands import EditNamed    # struct_window.nml:3
from navml.commands import CloseWindow    # struct_window.nml:4
from navml.widgets.menu.menu_item import MenuItem    # struct_window.nml:5
from navml.widgets.menu.menu_line import MenuLine    # struct_window.nml:6
from navml.widgets.menu.sub_menu import SubMenu    # struct_window.nml:7
from navml.widgets.window import Window    # struct_window.nml:8

__navml_component__ = "StructWindow"

__all__ = ["StructWindow"]


class StructWindow(Window, _Component):
    """F3's structured view: a JSON, YAML, TOML, XML or property-list file's data

    as a tree, Shift+F3 from the text and back (``FileWindow.as_tree``).  A
    departure, asked for -- DOS Navigator's viewer had bytes and lines only.

    Dressed as the directory tree window is: the tree fills the frame less a
    row, which is the path of the node under the cursor, and its scroll bar
    stands on the frame's right edge.
    """

    #: The document this class was generated from.
    __navml_source__ = "struct_window.nml"

    #: The keys this component binds, read through key_table().
    keys = {    # struct_window.nml:20
        'escape': CloseWindow,    # struct_window.nml:21
        'shift+f3': ViewTreeAsText,    # struct_window.nml:24
        'shift+f4': EditNamed,    # struct_window.nml:25
        'ctrl+insert': CopyPath,    # struct_window.nml:26
        'ctrl+shift+c': CopyValue,    # struct_window.nml:27
        'f7': SearchFor,    # struct_window.nml:28
        'shift+f7': ContinueSearch,    # struct_window.nml:29
        'ctrl+l': SearchAgain,    # struct_window.nml:30
    }

    #: Ids, annotated so the hand-written half completes them.
    tree: DataTree    # struct_window.nml:42
    data_menu: SubMenu    # struct_window.nml:53

    #: The commands this component handles itself.
    async def on_search_for(self, event: _Any) -> bool:    # struct_window.nml:34
        """``SearchFor``."""
        self.spawn(self.search_for())
        return True

    async def on_continue_search(self, event: _Any) -> bool:    # struct_window.nml:35
        """``ContinueSearch``."""
        self.spawn(self.search_again())
        return True

    async def on_search_again(self, event: _Any) -> bool:    # struct_window.nml:36
        """``SearchAgain``."""
        self.spawn(self.search_again())
        return True

    async def on_view_tree_as_text(self, event: _Any) -> bool:    # struct_window.nml:37
        """``ViewTreeAsText``."""
        self.spawn(self.as_text())
        return True

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_tree_chosen(self, event: _Event) -> bool:    # struct_window.nml:42
        """``tree`` raised an event whose handler is ``on_chosen``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.tree = DataTree(parent=self)    # struct_window.nml:41
        self.data_menu = SubMenu(parent=self)    # struct_window.nml:52
        _w1 = MenuItem(parent=self.data_menu)    # struct_window.nml:55
        _w2 = MenuLine(parent=self.data_menu)    # struct_window.nml:57
        _w3 = MenuItem(parent=self.data_menu)    # struct_window.nml:58
        _w4 = MenuItem(parent=self.data_menu)    # struct_window.nml:60
        _w5 = MenuLine(parent=self.data_menu)    # struct_window.nml:62
        _w6 = MenuItem(parent=self.data_menu)    # struct_window.nml:63
        _w7 = MenuItem(parent=self.data_menu)    # struct_window.nml:65
        _w8 = MenuItem(parent=self.data_menu)    # struct_window.nml:66
        _w9 = MenuLine(parent=self.data_menu)    # struct_window.nml:67
        _w10 = MenuItem(parent=self.data_menu)    # struct_window.nml:68

        self.title = _bind(lambda _o: _tr('Data'), yielding=True)    # struct_window.nml:18
        self.first_focus = _bind(lambda _o: self.tree)    # struct_window.nml:39

        self.tree.framed = False    # struct_window.nml:43
        self.tree.x = 1    # struct_window.nml:45
        self.tree.width = _bind(lambda _o: max(0, _o.parent.width - 1))    # struct_window.nml:46
        self.tree.y = 1    # struct_window.nml:47
        self.tree.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # struct_window.nml:48
        self.tree.on_chosen = self.on_tree_chosen    # struct_window.nml:42

        self.data_menu.text = _bind(lambda _o: _tr('~D~ata'), yielding=True)    # struct_window.nml:52
        self.data_menu.after = 'File'    # struct_window.nml:52
        self.data_menu.tooltip = _bind(    # struct_window.nml:54
            lambda _o: _tr('Copy, search and fold the tree'),
            yielding=True,
        )

        _w1.text = _bind(lambda _o: _tr('~T~ext view'), yielding=True)    # struct_window.nml:55
        _w1.command = ViewTreeAsText    # struct_window.nml:55
        _w1.key = 'Shift-F4'    # struct_window.nml:55
        _w1.tooltip = _bind(    # struct_window.nml:56
            lambda _o: _tr("The file's text, where the cursor's node is when that is known"),
            yielding=True,
        )

        _w3.text = _bind(lambda _o: _tr('Copy ~p~ath'), yielding=True)    # struct_window.nml:58
        _w3.command = CopyPath    # struct_window.nml:58
        _w3.tooltip = _bind(    # struct_window.nml:59
            lambda _o: _tr('The path of the node under the cursor, to the clipboard'),
            yielding=True,
        )

        _w4.text = _bind(lambda _o: _tr('Copy ~v~alue'), yielding=True)    # struct_window.nml:60
        _w4.command = CopyValue    # struct_window.nml:60
        _w4.tooltip = _bind(    # struct_window.nml:61
            lambda _o: _tr("The node's value -- a branch as text -- to the clipboard"),
            yielding=True,
        )

        _w6.text = _bind(lambda _o: _tr('~S~earch...'), yielding=True)    # struct_window.nml:63
        _w6.command = SearchFor    # struct_window.nml:63
        _w6.tooltip = _bind(    # struct_window.nml:64
            lambda _o: _tr('Find text in the keys and values; Ctrl+S finds a key as it is typed'),
            yielding=True,
        )

        _w7.text = _bind(lambda _o: _tr('Search ~a~gain'), yielding=True)    # struct_window.nml:65
        _w7.command = ContinueSearch    # struct_window.nml:65

        _w8.text = _bind(lambda _o: _tr('E~x~pand all'), yielding=True)    # struct_window.nml:66
        _w8.command = ExpandAll    # struct_window.nml:66

        _w10.text = _bind(lambda _o: _tr('~C~lose'), yielding=True)    # struct_window.nml:68
        _w10.command = CloseWindow    # struct_window.nml:68
