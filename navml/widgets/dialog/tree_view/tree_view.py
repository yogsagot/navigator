"""A tree of named nodes, drawn and driven the way DOS Navigator's
``TTreeView`` is (``TREE.PAS``).

**The rows are a flat list**, as DOS Navigator's ``DC`` collection is: the
visible nodes depth first, each knowing its level.  So the tree is a
:class:`~navml.widgets.dialog.list_viewer.ListViewer` -- its frame, its scroll
bar on the frame, its cursor and its wheel -- whose items are those rows,
re-flattened whenever a branch opens or closes.  A node is data, as a listing
row is, never a widget.

**Nodes load lazily.**  A :class:`TreeNode` holds a name, whatever the program
hangs on it, and either its children or a *loader* that produces them the
first time the branch is opened.  DOS Navigator read a drive's whole tree up
front, which a filesystem rooted at ``/`` cannot afford; whether an unopened
node has children at all is asked only of a row about to be painted, and
remembered.

**Every measurement is ``TTreeView.Draw``'s**, with DOS Navigator's column 0
at the first column inside the frame:

* Level 0 -- the root -- starts at column 2, and each level indents three.
* An ancestor that still has siblings below draws ``│`` in its column.
* A node's branch is ``├───``, or ``└───`` for a last child.  In the
  collapsible view one with children is ``├─[+] `` or ``├─[-] ``; in the
  expanded view -- ``collapsible`` off -- it is ``├──┬``.
* **The cursor is `` name `` in the cursor colour, begun one column early**,
  over the last cell of its branch.  The line under the cursor is not filled,
  as a listing's is: only the name is marked.
* The view scrolls sideways to keep the cursor's name in sight.

The seven colours are ``TTreeView``'s: the lines and the ground are the
widget's own style (*Normal tree*), and the ``node`` part takes ``:selected``
for the cursor -- *Selected node* while the tree has the keyboard, *Selected
passive* while it has not, which a sheet says with the owner's ``:focused``.

**The keys are ``TTreeView.HandleCommand``'s, but for two.**  Left and
Backspace go to the parent node, and Backspace closes it behind them; Right
opens the branch under the cursor and goes to its first child, or down a row
when it has none -- where ``TTreeView`` moved Left and Right up and down,
which duplicated the arrows beside them.
Space, ``+`` and ``-`` open or close the branch under the cursor; ``*`` opens
every branch already read; typing searches forward for a name starting with
what was typed; Enter emits :class:`ChosenEvent`.  A click on the ``[+]`` of a
row opens it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from navkit import glyphs as glyphs_module
from navkit.events import Event, KeyEvent, MouseClickEvent
from navkit.reactive import computed, effect, reactive
from navkit.screen import Surface
from navkit.style import Style

from navml.widgets.dialog.list_viewer import ListViewer

#: Produces a node's children, the first time they are asked for.
Loader = Callable[["TreeNode"], Iterable["TreeNode"]]


class TreeNode:
    """One named node, its data, and its children or the means to read them."""

    def __init__(
        self,
        name: str,
        children: Iterable[TreeNode] | None = None,
        *,
        loader: Loader | None = None,
        probe: Callable[[TreeNode], bool] | None = None,
        data: Any = None,
        expanded: bool = False,
    ) -> None:
        self.name = name
        self.data = data
        self.expanded = expanded
        self.parent: TreeNode | None = None
        self.loader = loader
        #: Answers "has it any children?" without reading them all, for a node
        #: that has not been opened.  Without one, an unopened node with a
        #: loader is assumed to have some until it is opened and found empty.
        self.probe = probe
        self._children: list[TreeNode] | None = None
        self._has_children: bool | None = None
        if children is not None or loader is None:
            self.set_children(children or [])

    @property
    def loaded(self) -> bool:
        return self._children is not None

    def children(self) -> list[TreeNode]:
        """The children, read now if they have not been."""
        if self._children is None:
            try:
                found = list(self.loader(self)) if self.loader is not None else []
            except OSError:
                found = []
            self.set_children(found)
        return self._children  # type: ignore[return-value]

    def set_children(self, children: Iterable[TreeNode]) -> None:
        self._children = list(children)
        for child in self._children:
            child.parent = self
        self._has_children = bool(self._children)

    def forget(self) -> None:
        """Drop the children read so far, to be read again when next asked."""
        if self.loader is not None:
            self._children = None
            self._has_children = None

    def has_children(self) -> bool:
        """Whether there is anything to open, asked as cheaply as possible."""
        if self._has_children is None:
            if self.probe is not None:
                try:
                    self._has_children = bool(self.probe(self))
                except OSError:
                    self._has_children = False
            else:
                self._has_children = True
        return self._has_children

    def names(self) -> list[str]:
        """The names from the root down to this node."""
        node, found = self, []
        while node is not None:
            found.append(node.name)
            node = node.parent
        return found[::-1]

    def __repr__(self) -> str:
        return f"TreeNode({'/'.join(self.names())!r})"


@dataclass(frozen=True)
class TreeRow:
    """A node as the flat list shows it: where it is, and what to draw left of it."""

    node: TreeNode
    level: int
    #: Whether a sibling follows this node, which picks ``├`` over ``└``.
    more: bool
    #: For each ancestor level from 1 to ``level - 1``, whether that ancestor
    #: has a sibling below it -- where ``│`` continues past this row.
    rails: tuple[bool, ...]

    def __str__(self) -> str:
        return self.node.name


@dataclass(frozen=True, slots=True)
class ChosenEvent(Event):
    """Enter on a node, or a double click.  Reaches ``on_chosen``."""

    node: Any = None


class TreeView(ListViewer):
    """The rows of a :class:`TreeNode` tree, with branches drawn between them."""

    emits = (ChosenEvent,)

    #: The node names are painted in this part; ``:selected`` for the cursor.
    parts = ("node",)

    #: The tree.  Assigning another one shows it from the top.
    root: Any = reactive(None)
    #: Whether branches open and close (``[+]`` and ``[-]``), or the whole tree
    #: is always shown (``┬``) -- ``TTreeView``'s ``Parital``.
    collapsible: bool = reactive(True)
    #: Bumped whenever a branch opens, closes or is re-read: the node model is
    #: not reactive, and this one counter stands for all of it.
    revision: int = reactive(0)
    #: What has been typed of a name being searched for, or "" while not.
    search: str = reactive("")

    def mounted(self) -> None:
        # Before ListViewer's two: the rows have to exist before a cursor can
        # be clamped onto them.
        effect(self, TreeView._flatten)
        super().mounted()

    # -- the rows ------------------------------------------------------------------

    def _flatten(self) -> None:
        _ = self.revision
        root, collapsible = self.root, self.collapsible
        rows: list[TreeRow] = []

        def walk(node: TreeNode, level: int, more: bool, rails: tuple[bool, ...]) -> None:
            rows.append(TreeRow(node, level, more, rails))
            if collapsible and not node.expanded:
                return
            children = node.children()
            inner = rails + ((more,) if level >= 1 else ())
            for index, child in enumerate(children):
                walk(child, level + 1, index < len(children) - 1, inner)

        if root is not None:
            walk(root, 0, False, ())
        self.items = rows

    @computed
    def selected_node(self) -> TreeNode | None:
        row = self.selected
        return row.node if row is not None else None

    def index_of(self, node: TreeNode) -> int:
        """The row showing *node*, or -1 while a closed branch hides it."""
        for index, row in enumerate(self.items):
            if row.node is node:
                return index
        return -1

    # -- opening and closing ----------------------------------------------------------

    def refresh(self) -> None:
        """Re-flatten after the node model changed behind the view's back."""
        self.revision += 1

    def expand(self, node: TreeNode) -> None:
        if not node.expanded:
            node.expanded = True
            self.refresh()

    def collapse(self, node: TreeNode) -> None:
        """Close *node*; a cursor inside the closed branch moves onto it."""
        if not node.expanded:
            return
        inside = self.selected_node
        node.expanded = False
        while inside is not None and inside is not node:
            inside = inside.parent
        self.refresh()
        if inside is node:
            self.select(node)

    def toggle(self, node: TreeNode) -> None:
        """``CollapseBranch``: open a closed branch, close an open one."""
        if not self.collapsible:
            return
        if node.expanded:
            self.collapse(node)
        elif node.has_children():
            self.expand(node)
            if not node.children():
                self.refresh()

    def descend(self, node: TreeNode) -> None:
        """Open *node* and put the cursor on its first child, or on the next
        row when it has none."""
        children = node.children() if node.has_children() else []
        if children:
            self.select(children[0])
        else:
            # A node assumed to have children may have been read and found
            # empty, and its ``[+]`` has to go.
            self.refresh()
            self.move_cursor(1)

    def expand_all(self) -> None:
        """``*``: open every branch that has been read already.

        Not every branch there is -- a tree rooted at ``/`` would read the
        whole disk -- but every branch whose children are in hand.
        """
        def open_loaded(node: TreeNode) -> None:
            if node.loaded and node.children():
                node.expanded = True
                for child in node.children():
                    open_loaded(child)

        if self.root is not None:
            open_loaded(self.root)
            self.refresh()

    def select(self, node: TreeNode) -> None:
        """Put the cursor on *node*, opening every branch above it."""
        parent = node.parent
        changed = False
        while parent is not None:
            if not parent.expanded:
                parent.expanded = True
                changed = True
            parent = parent.parent
        if changed:
            self.refresh()
            self._flatten()
        index = self.index_of(node)
        if index >= 0:
            self.cursor = index

    def locate(self, names: Iterable[str]) -> TreeNode | None:
        """Find the node at the path *names* from the root and put the cursor on it.

        As far as the path goes: a name that is not there stops the walk, and
        the cursor lands on the deepest node that was found.
        """
        node = self.root
        if node is None:
            return None
        names = list(names)
        if names and names[0] == node.name:
            names = names[1:]
        for name in names:
            child = next((c for c in node.children() if c.name == name), None)
            if child is None:
                break
            node = child
        self.select(node)
        return node

    # -- geometry ------------------------------------------------------------------------

    def _chars(self) -> tuple[str, str, str, str, str]:
        """``├ └ ─ │ ┬`` -- always single, whatever frame the widget has."""
        tl, tr, bl, br, horizontal, vertical = glyphs_module.charset("single", self.glyphs)
        joins = glyphs_module.joins("single", self.glyphs)
        return joins[0], bl, horizontal, vertical, joins[2]

    def branch(self, row: TreeRow) -> str:
        """The branch drawn left of a row's name, as ``TTreeView.Draw`` builds it."""
        if row.level == 0:
            return ""
        tee, corner, horizontal, _, down = self._chars()
        start = tee if row.more else corner
        if row.node.has_children() and (not row.node.loaded or row.node.children()):
            if self.collapsible:
                mark = "-" if row.node.expanded else "+"
                return f"{start}{horizontal}[{mark}] "
            return f"{start}{horizontal}{horizontal}{down}"
        return start + horizontal * 3

    def name_column(self, row: TreeRow) -> int:
        """Where a row's name starts, in DOS Navigator's columns."""
        return 2 + 3 * max(0, row.level - 1) + len(self.branch(row))

    @computed
    def shift(self) -> int:
        """How far the rows are scrolled sideways: ``Delta.X``.

        Far enough that the cursor's name ends inside the view, and never so
        far that its own branch leaves it.
        """
        row = self.selected
        if row is None:
            return 0
        inner = max(1, self.inner_width)
        need = row.level * 3 + 6 + len(row.node.name)
        shift = max(0, need - inner)
        return max(0, min(shift, row.level * 3 - 4))

    # -- painting -------------------------------------------------------------------------

    def row_selected(self, index: int) -> bool:
        """Never: a tree marks the cursor's name, not the line it is on."""
        return False

    def render_row(self, surface: Surface, y: int, index: int, item: TreeRow) -> None:
        line_style = self.style
        _, _, _, vertical, _ = self._chars()
        shift, inset = self.shift, self.inset
        inner = self.inner_width

        def put(column: int, text: str, style: Style) -> None:
            x = column - shift
            if x + len(text) <= 0 or x >= inner:
                return
            if x < 0:
                text, x = text[-x:], 0
            surface.draw_text(inset + x, y, text, style, inner - x)

        column = 2
        for more in item.rails:
            if more:
                put(column, vertical, line_style)
            column += 3
        branch = self.branch(item)
        put(column, branch, line_style)
        name_at = column + len(branch)
        if index == self.cursor:
            put(name_at - 1, f" {item.node.name} ", self.part_style("node", selected=True))
        else:
            put(name_at, item.node.name, self.part_style("node"))

    def cursor_position(self) -> tuple[int, int] | None:
        """The caret sits after what has been typed, while a search is on."""
        row = self.selected
        if not self.search or row is None:
            return None
        row_y = self.inset + self.header + self.cursor - self.scroll
        return self.inset + self.name_column(row) - self.shift + len(self.search), row_y

    # -- keys and the mouse ---------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if self.inert:
            return False
        node = self.selected_node
        if event.char and event.is_printable and event.char in "+- " and not self.search:
            if node is not None:
                self.toggle(node)
            return True
        if event.char == "*" and not self.search:
            self.expand_all()
            return True
        if event.is_printable and event.char and event.char != " ":
            self._search(self.search + event.char, start=self.cursor)
            return True
        if event.matches("backspace") and self.search:
            self.search = self.search[:-1]
            return True
        if self.search:
            self.search = ""
            if event.matches("escape"):
                return True
        if event.matches("left") or event.matches("backspace"):
            if node is not None and node.parent is not None:
                if event.matches("backspace"):
                    # Closing the branch brings the cursor out onto it.
                    self.collapse(node.parent)
                else:
                    self.select(node.parent)
            return True
        if event.matches("right"):
            if node is not None:
                self.descend(node)
            return True
        return await super().on_key(event)

    def _search(self, text: str, start: int) -> None:
        """Move to the next row, from *start* on and round, whose name begins with *text*."""
        rows = self.items
        wanted = text.casefold()
        for step in range(len(rows)):
            index = (start + step) % len(rows)
            if rows[index].node.name.casefold().startswith(wanted):
                self.search = text
                self.cursor = index
                return

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """A press on a row's ``[+]`` opens it; anywhere else, as a list."""
        if (
            event.action == "press" and event.button == "left" and not self.inert
            and self.collapsible
        ):
            index = self.row_at(event.y)
            if index is not None:
                row = self.items[index]
                column = event.x - self.inset + self.shift
                start = 2 + 3 * max(0, row.level - 1) + 1
                if row.level > 0 and start <= column < start + 3:
                    self.focus()
                    self.cursor = index
                    self.toggle(row.node)
                    return True
        return await super().on_mouse_click(event)

    async def choose(self) -> bool:
        node = self.selected_node
        if node is None:
            return False
        await self.emit(ChosenEvent(node))
        return True
