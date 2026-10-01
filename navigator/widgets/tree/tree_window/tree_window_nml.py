# navml: generated
"""Generated from ``tree_window.nml``.

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
from navigator.widgets.manager.commands import Rescan    # tree_window.nml:1
from navigator.widgets.tree.directory_tree import DirectoryTree    # tree_window.nml:2
from navml.commands import CloseWindow    # tree_window.nml:3
from navml.widgets.window import Window    # tree_window.nml:4

__navml_component__ = "TreeWindow"

__all__ = ["TreeWindow"]


class TreeWindow(Window, _Component):
    """Disk > Directory tree: DOS Navigator's ``TTreeWindow`` (``TREE.PAS``).

    A standard window titled *Directory Tree* holding the collapsible tree and
    the two ``TTreeInfoView`` rows under it, the way ``TTreeWindow.Init``
    builds it: the tree fills the inside of the frame less those two rows, and
    its scroll bar stands on the frame's right edge.  ``DirectoryTree`` without
    a frame of its own is exactly that, sized one column into the frame.

    DOS Navigator 1.51 defined this window and never opened it -- its menu entry
    opened a new file manager instead -- so its size is ``Window``'s default and
    what Enter does is Navigator's: the file manager's active panel goes there.
    """

    #: The document this class was generated from.
    __navml_source__ = "tree_window.nml"

    #: ``TTreeWindow.HandleEvent``: Esc closes it.  Ctrl+R and Alt+R re-read
    #: the tree, as they re-read a panel.
    keys = {    # tree_window.nml:22
        'escape': CloseWindow,    # tree_window.nml:23
        'ctrl+r': Rescan,    # tree_window.nml:24
        'alt+r': Rescan,    # tree_window.nml:25
    }

    #: Ids, annotated so the hand-written half completes them.
    tree: DirectoryTree    # tree_window.nml:28

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_tree_chosen(self, event: _Event) -> bool:    # tree_window.nml:28
        """``tree`` raised an event whose handler is ``on_chosen``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.tree = DirectoryTree(parent=self)    # tree_window.nml:27

        self.title = 'Directory Tree'    # tree_window.nml:18

        self.tree.framed = False    # tree_window.nml:29
        self.tree.x = 1    # tree_window.nml:30
        self.tree.y = 1    # tree_window.nml:31
        self.tree.width = _bind(lambda _o: max(0, _o.parent.width - 1))    # tree_window.nml:32
        self.tree.height = _bind(lambda _o: max(0, _o.parent.height - 2))    # tree_window.nml:33
        self.tree.on_chosen = self.on_tree_chosen    # tree_window.nml:28
