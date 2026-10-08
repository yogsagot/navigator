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
every branch already read; Enter emits :class:`ChosenEvent`.  A click on the
``[+]`` of a row opens it.

**The quick search is a path, not a scan** -- ``TTreeView``'s own
(``SearchForMask``).  Ctrl+S, or typing where ``type_to_search`` is on,
starts it; what is typed moves the cursor to the next row from it whose name
begins so (the panel's rule: case folded, ``*`` and ``?`` wildcards, a
character that would name nothing refused), and Ctrl+S again finds the next.
**``/`` descends**, as DN's ``\\`` did: the branch matched opens, the cursor
goes to its first child, and what is typed next is matched among that
branch's children alone -- so ``us/lo/bi`` walks to ``/usr/local/bin``,
reading the three directories it names and no other.  That is the answer to
the tree being lazy: the search never needs a branch nobody has opened,
because it opens the one it goes into.  ``/`` before anything is typed
searches from the root, Backspace past a ``/`` climbs back out, Esc ends it
where it stands, and any other key ends it and does its job -- Enter chooses,
as it did in DN's.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from navkit import glyphs as glyphs_module
from navkit.events import Event, KeyEvent, MouseClickEvent
from navkit.i18n import tr
from navkit.reactive import computed, effect, peek, reactive
from navkit.screen import Surface
from navkit.style import Style

from navml.background import Background, Outcome
from navml.widgets.dialog.commands import QuickSearch
from navml.quick_search import name_pattern
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


#: Where unopened nodes are probed, for a tree that probes off the loop.
_PROBES = Background("navml-probe", workers=4)


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
    keys = {"ctrl+s": QuickSearch}

    #: What has been typed of the name being searched for since the last
    #: ``/``, or None while the quick search is off.
    search: str | None = reactive(None)
    #: The node whose children the search is confined to, after a ``/``;
    #: None searches every row.
    search_scope: Any = reactive(None)
    #: One ``(scope, typed, node)`` per ``/``: the scope before it, what had
    #: been typed, and the node it went into -- what Backspace climbs back to.
    search_trail: tuple = reactive(())
    #: Whether a printable key starts a search, as in DOS Navigator's tree.
    #: Off where typing belongs to a command line, and Ctrl+S starts it there.
    type_to_search: bool = reactive(True)

    #: Whether a frameless tree puts the search's caret on the cursor's name.
    #: An owner that shows :meth:`search_label` on a frame of its own turns it
    #: off and places the caret there itself.
    caret_on_name = True

    #: Whether an unopened node's probe runs on a thread, for a tree whose
    #: probes may wait -- a directory on a dead mount.  The row shows ``[+]``
    #: until the answer is in, which is what a node with no probe shows.
    probe_in_background = False
    #: The nodes whose probe is on a thread now.
    _probing: set[TreeNode] | None = None

    def mounted(self) -> None:
        # Before ListViewer's two: the rows have to exist before a cursor can
        # be clamped onto them.
        effect(self, TreeView._flatten)
        super().mounted()
        effect(self, TreeView._end_search_unfocused)
        effect(self, TreeView._end_search_on_new_root)

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
        if self.node_has_children(row.node) and (not row.node.loaded or row.node.children()):
            if self.collapsible:
                mark = "-" if row.node.expanded else "+"
                return f"{start}{horizontal}[{mark}] "
            return f"{start}{horizontal}{horizontal}{down}"
        return start + horizontal * 3

    def node_has_children(self, node: TreeNode) -> bool:
        """:meth:`TreeNode.has_children`, for painting: never waits on a probe
        when :attr:`probe_in_background` says it may be slow."""
        if (not self.probe_in_background or node._has_children is not None
                or node.probe is None):
            return node.has_children()
        app = self.application
        if app is None or not app.is_running:
            return node.has_children()
        if self._probing is None:
            self._probing = set()
        if node not in self._probing:
            self._probing.add(node)
            _PROBES.run(self, node.probe, node,
                        done=lambda outcome, node=node: self._probed(node, outcome))
        return True

    def _probed(self, node: TreeNode, outcome: Outcome) -> None:
        if self._probing is not None:
            self._probing.discard(node)
        if node._has_children is None:
            try:
                node._has_children = bool(outcome.result())
            except OSError:
                node._has_children = False
            self.refresh()

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

    def search_label(self) -> str:
        """`` Search: us/lo/b `` while searching, else "": what a frame shows.

        The tree's own footer when it is framed; a frameless tree's owner may
        put it on a frame of its own, as the tree window does.
        """
        if self.search is None:
            return ""
        return tr(" Search: ") + f"{self.search_path} "

    def footer_text(self) -> str:
        """While searching, the path typed so far; otherwise the list's own."""
        return self.search_label() or super().footer_text()

    def cursor_position(self) -> tuple[int, int] | None:
        """While searching, the caret after what has been typed: on the footer
        when there is a frame to carry one, else on the cursor's name, as
        ``TTreeView.Draw`` put it."""
        text = self.search
        if text is None:
            return None
        if self.framed:
            footer = self.footer_text()
            x = self.label_x(footer) + len(tr(" Search: ")) + len(self.search_path)
            return min(x, self.width - 2), self.height - 1
        row = self.selected
        if row is None or not self.caret_on_name:
            return None
        row_y = self.inset + self.header + self.cursor - self.scroll
        return self.inset + self.name_column(row) - self.shift + len(text), row_y

    # -- the quick search -------------------------------------------------------------------

    @property
    def edits_text(self) -> bool:
        """True while searching, so a command line's Enter, Home, End and Tab
        step aside and reach the search, which ends on them."""
        return self.search is not None

    @computed
    def search_path(self) -> str:
        """Everything typed: each segment a ``/`` went through, then the current one."""
        return "".join(typed + "/" for _, typed, _ in self.search_trail) + (self.search or "")

    def start_search(self) -> None:
        """Ctrl+S: start searching, with nothing typed yet."""
        if self.search is None:
            self.search = ""

    def end_search(self) -> None:
        self.search = None
        self.search_scope = None
        self.search_trail = ()

    def _end_search_unfocused(self) -> None:
        """The search ends when the keyboard leaves the tree."""
        if not self.focus_within and peek(self, TreeView.search) is not None:
            self.end_search()

    def _end_search_on_new_root(self) -> None:
        """And when the tree is read again from a new root: its nodes are gone."""
        _ = self.root
        if peek(self, TreeView.search) is not None:
            self.end_search()

    def _find(self, text: str, start: int) -> int | None:
        """The first row from *start* on, wrapping, inside the search's scope,
        whose name *text* begins."""
        pattern = name_pattern(text)
        scope, rows = self.search_scope, self.items
        for step in range(len(rows)):
            index = (start + step) % len(rows)
            node = rows[index].node
            if (scope is None or node.parent is scope) and pattern.match(node.name):
                return index
        return None

    def _descend_search(self) -> None:
        """``/``: confine the search to the branch it matched, opened."""
        text = self.search or ""
        if text:
            node = self.selected_node
        elif not self.search_trail and self.search_scope is None:
            # ``/`` first: from the root, as DN's leading ``\`` was.
            node = self.root
        else:
            return
        if node is None or not node.has_children() or not node.children():
            return
        self.search_trail = self.search_trail + ((self.search_scope, text, node),)
        self.search_scope = node
        self.search = ""
        # Selecting a child opens its branch, and re-flattens at once.
        self.select(node.children()[0])

    def _search_key(self, event: KeyEvent) -> bool:
        """A key while searching: True if the search took it.

        Esc ends the search where it stands.  Any other key that is not the
        search's ends it too and is declined, so it goes on to do what it
        always does -- Down moves, Enter chooses.
        """
        text = self.search or ""
        if event.char == "/":
            self._descend_search()
            return True
        if event.is_printable and event.char:
            found = self._find(text + event.char, self.cursor)
            if found is not None:
                self.cursor = found
                self.search = text + event.char
            return True
        if event.matches("backspace"):
            if text:
                self.search = text[:-1]
            elif self.search_trail:
                scope, typed, node = self.search_trail[-1]
                self.search_trail = self.search_trail[:-1]
                self.search_scope = scope
                self.search = typed
                self.select(node)
            return True
        self.end_search()
        return event.matches("escape")

    async def on_quick_search(self, event: QuickSearch) -> bool:
        """Ctrl+S starts the search, and while one is on finds the next match."""
        if self.search is None:
            self.start_search()
        elif self.search:
            found = self._find(self.search, self.cursor + 1)
            if found is not None:
                self.cursor = found
        return True

    def enables(self, command: Any) -> bool:
        if isinstance(command, QuickSearch):
            return not self.inert
        return super().enables(command)

    # -- keys and the mouse ---------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if self.inert:
            return False
        if self.search is not None and self._search_key(event):
            return True
        node = self.selected_node
        if self.search is None and event.char and event.is_printable and event.char in "+- ":
            if node is not None:
                self.toggle(node)
            return True
        if event.char == "*" and event.is_printable:
            self.expand_all()
            return True
        if event.is_printable and event.char:
            if not self.type_to_search:
                return False
            self.start_search()
            return self._search_key(event)
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

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """A press on a row's ``[+]`` opens it; anywhere else, as a list."""
        if event.action == "press" and not event.is_wheel and self.search is not None:
            self.end_search()
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
