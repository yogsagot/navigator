"""The structured view's tree: navml's ``TreeView`` over a
:class:`navigator.lib.viewer.structured.Node` tree, each row ``key: value``
and a path line under the rows.

A ``TreeNode`` is made for a node only when its parent is opened (the loader),
and holds the model's node as its ``data``; the model makes its own children
the same way, so nothing below a closed branch exists.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from navkit.bidi import display_width
from navkit.reactive import computed, effect, peek
from navkit.screen import Surface, char_width
from navml.widgets.dialog.list_viewer import ListViewer
from navml.widgets.dialog.tree_view import TreeNode, TreeRow, TreeView

from navigator.lib.viewer import structured
from navigator.lib.viewer.structured import Node

#: The most nodes *Expand all* (``*``) opens: past it the tree is left as it
#: is and :meth:`DataTree.expand_all` says so, as a deep document would make
#: rows by the hundred thousand.
EXPAND_LIMIT = 5000

#: The most rows one value is wrapped onto: the rest is cut, with ``…``, and
#: is whole in the row's tooltip and in *Copy value*.
WRAP_ROWS = 40

#: The narrowest a value's column may be for its wrapped rows to hang under
#: it; narrower, they start under the key instead.
MIN_WRAP = 16


@dataclass(frozen=True)
class ValueRow(TreeRow):
    """A row more of a long value: its node's, under the value's first row.
    The cursor passes over it, and a click on it is on its node."""

    piece: int = 1

    def __str__(self) -> str:
        return ""


def wrap_line(text: str, first: int, width: int) -> list[str]:
    """*text* cut into rows *first* columns wide, then *width* -- at the last
    blank in a row's second half when there is one, else where it is full."""
    pieces: list[str] = []
    room = max(1, first)
    while True:
        used, cut = 0, len(text)
        for index, char in enumerate(text):
            used += char_width(char)
            if used > room:
                cut = max(1, index)
                break
        if cut >= len(text):
            pieces.append(text)
            return pieces
        blank = text.rfind(" ", 0, cut)
        if blank >= cut // 2 and blank > 0:
            cut = blank + 1
        pieces.append(text[:cut])
        text = text[cut:]
        room = max(1, width)


def _tree_node(node: Node) -> TreeNode:
    if node.container and node.count:
        return TreeNode(_name(node), loader=_load, probe=lambda tree_node: True, data=node)
    return TreeNode(_name(node), data=node)


def _load(tree_node: TreeNode) -> list[TreeNode]:
    return [_tree_node(child) for child in tree_node.data.children()]


def _name(node: Node) -> str:
    """What a row is called -- and what quick search matches: a key, an
    index, an element's or attribute's name; the root, its format."""
    if node.key is None:
        return {"json": "JSON", "yaml": "YAML", "toml": "TOML", "plist": "plist"}.get(node.format, "") \
            if node.kind != "element" else str(node.key)
    if node.kind == "attribute":
        return f"@{node.key}"
    return str(node.key)


def root_node(root: Node) -> TreeNode:
    """The tree's root, opened."""
    tree_node = _tree_node(root)
    tree_node.expanded = True
    return tree_node


class DataTree(TreeView):
    """A document's data, a row a node: the key, then a scalar's value, or a
    branch's count -- ``{3}`` for a mapping, ``[3]`` for a list, ``<3>`` for
    an element's attributes, text and elements."""

    #: The key, the ``:`` after it, a value by its kind, a branch's count,
    #: and the path line under the rows.
    parts = ("node", "punct", "string", "number", "bool", "null", "date", "tagged", "count", "info")

    #: The path line: one row under the tree.
    INFO_ROWS = 1

    @computed
    def rows(self) -> int:
        return max(0, self.height - 2 * self.inset - self.header - self.INFO_ROWS)

    def mounted(self) -> None:
        self._pieces_for: dict[tuple[int, int], tuple[list[str], bool]] = {}
        super().mounted()
        effect(self, DataTree._onto_first_row)

    # -- long values, wrapped -------------------------------------------------------------

    def _flatten(self) -> None:
        """The tree's rows, and after a long value's row the rows more it
        wraps onto (:class:`ValueRow`) -- as many as the width makes.  The
        cursor stays on the node it was on, however many rows came or went
        above it."""
        held = None
        before = peek(self, ListViewer.items)
        at = peek(self, ListViewer.cursor)
        if 0 <= at < len(before):
            held = before[at].node
        TreeView._flatten(self)
        width = self.inner_width
        rows: list[TreeRow] = []
        for row in self.items:
            rows.append(row)
            pieces, _ = self.pieces(row, width)
            rows.extend(ValueRow(row.node, row.level, row.more, row.rails, piece)
                        for piece in range(1, len(pieces)))
        self.items = rows
        if held is not None:
            index = self.index_of(held)
            if index >= 0:
                self.cursor = index

    def pieces(self, row: TreeRow, width: int) -> tuple[list[str], bool]:
        """A scalar's value as the rows it is painted on -- its own row's
        part first, after the key -- and whether ``WRAP_ROWS`` cut it.  A
        branch's is its count, on one row."""
        node = row.node.data
        if node is None or node.container:
            return [], False
        key = (id(row.node), width)
        found = self._pieces_for.get(key)
        if found is not None:
            return found
        if len(self._pieces_for) > 4096:
            self._pieces_for.clear()
        text = node.text[:structured.VALUE_LIMIT].replace("\t", " ")
        if node.kind == "string" and node.format != "xml":
            text = f'"{text}"'
        column = 2 + 3 * len(row.rails) + len(self.branch(row))
        value_at = column + display_width(row.node.name) + 2
        indent = value_at if width - value_at >= MIN_WRAP else column
        pieces: list[str] = []
        for number, line in enumerate(text.split("\n")):
            pieces.extend(wrap_line(line, width - (value_at if number == 0 else indent), width - indent))
        cut = len(pieces) > WRAP_ROWS or len(node.text) > structured.VALUE_LIMIT
        if len(pieces) > WRAP_ROWS:
            pieces = pieces[:WRAP_ROWS]
        if cut:
            pieces[-1] = pieces[-1][:-1] + "…" if pieces[-1] else "…"
        self._pieces_for[key] = (pieces, cut)
        return pieces, cut

    def _first_row(self, index: int) -> int:
        while index > 0 and isinstance(self.items[index], ValueRow):
            index -= 1
        return index

    def _onto_first_row(self) -> None:
        """A click, the scroll bar or a search that lands on a value's row
        more puts the cursor on its node's first row."""
        items, cursor = self.items, self.cursor
        if 0 <= cursor < len(items) and isinstance(items[cursor], ValueRow):
            self.cursor = self._first_row(cursor)

    def move_cursor(self, delta: int) -> None:
        """Up and Down pass over a value's rows more, to the next node's
        first row; and the rows of the node arrived on are brought into view."""
        items = self.items
        if not items or not delta:
            return
        step = 1 if delta > 0 else -1
        target = min(max(self.cursor + delta, 0), len(items) - 1)
        while 0 <= target < len(items) and isinstance(items[target], ValueRow):
            target += step
        if target >= len(items):
            target = self._first_row(len(items) - 1)
        target = max(0, target)
        self.cursor = target
        end = target
        while end + 1 < len(items) and isinstance(items[end + 1], ValueRow):
            end += 1
        rows = self.rows
        if rows and end >= self.scroll + rows:
            self.scroll = max(0, min(target, end - rows + 1))

    @computed
    def selected_data(self) -> Node | None:
        """The model's node under the cursor."""
        node = self.selected_node
        return node.data if node is not None else None

    def show(self, target: Node) -> None:
        """The cursor on *target*, every branch above it opened -- each
        ``TreeNode`` found by the model node it holds."""
        chain = []
        node: Node | None = target
        while node is not None:
            chain.append(node)
            node = node.parent
        chain.reverse()
        here = self.root
        if here is None or here.data is not chain[0]:
            return
        for wanted in chain[1:]:
            found = next((child for child in here.children() if child.data is wanted), None)
            if found is None:
                break
            here = found
        self.select(here)

    def expand_all(self) -> bool:
        """``*``, *Expand all*: every branch opened -- not only those read, as
        the directory tree's are, since a document is in memory -- when it
        holds no more than ``EXPAND_LIMIT`` nodes.  False when it holds more,
        and nothing is opened."""
        root = self.root
        if root is None:
            return True
        for count, _ in enumerate(structured.walk(root.data), 1):
            if count > EXPAND_LIMIT:
                return False
        # An alias's branch is opened once: one that holds itself would
        # otherwise open for ever.
        seen: set[int] = set()
        stack = [root]
        while stack:
            node = stack.pop()
            held = node.data
            if held is None or not held.container or structured.identity(held) in seen:
                continue
            seen.add(structured.identity(held))
            node.expanded = True
            stack.extend(node.children())
        self.refresh()
        return True

    # -- painting -------------------------------------------------------------------------

    def value_runs(self, row: TreeRow) -> list[tuple[str, str]]:
        """What follows a row's name, as ``(text, part)`` pieces: a branch's
        count, or ``: `` and the first of its value's rows."""
        node = row.node.data
        if node.container:
            brackets = {"object": "{}", "array": "[]", "element": "<>"}[node.kind]
            return [(f" {brackets[0]}{node.count}{brackets[1]}", "count")]
        pieces, _ = self.pieces(row, self.inner_width)
        return [(": ", "punct"), (pieces[0] if pieces else "", self.value_part(node))]

    def value_part(self, node: Node) -> str:
        return node.kind if node.kind in self.parts else "string"

    def render_row(self, surface: Surface, y: int, index: int, item: TreeRow) -> None:
        # The rails, the branch and the name, as the tree draws them; then
        # the value, in its kind's colour, after the name.
        if isinstance(item, ValueRow):
            self._render_more(surface, y, item)
            return
        super().render_row(surface, y, index, item)
        node = item.node.data
        if node is None:
            return
        shift, inset, inner = self.shift, self.inset, self.inner_width
        column = 2 + 3 * len(item.rails) + len(self.branch(item))
        # Right after the name: on the cursor's row, over the blank its
        # highlight pads the name with.
        at = column + display_width(item.node.name) - shift
        if at >= inner or at < 0:
            return
        runs = [(text, self.part_style(part)) for text, part in self.value_runs(item)]
        surface.draw_runs(inset + at, y, runs, max_width=inner - at)

    def _render_more(self, surface: Surface, y: int, item: ValueRow) -> None:
        """A value's row more: the rails carried down past it -- its own
        node's too when a sibling follows -- and its piece of the value,
        under the value's first row (or under the key, when that is narrow)."""
        _, _, _, vertical, _ = self._chars()
        shift, inset, inner = self.shift, self.inset, self.inner_width
        line = self.style

        def put(column: int, text: str, style: Any) -> None:
            x = column - shift
            if x + len(text) <= 0 or x >= inner:
                return
            if x < 0:
                text, x = text[-x:], 0
            surface.draw_text(inset + x, y, text, style, inner - x)

        column = 2
        for more in item.rails:
            if more:
                put(column, vertical, line)
            column += 3
        if item.level and item.more:
            put(column, vertical, line)
        pieces, _ = self.pieces(item, inner)
        if item.piece >= len(pieces):
            return
        branch = column + len(self.branch(item))
        value_at = branch + display_width(item.node.name) + 2
        indent = value_at if inner - value_at >= MIN_WRAP else branch
        x = indent - shift
        if 0 <= x < inner:
            surface.draw_runs(inset + x, y, [(pieces[item.piece], self.part_style(self.value_part(item.node.data)))],
                              max_width=inner - x)

    def row_tooltip(self, index: int, item: TreeRow) -> str:
        """A value cut at ``WRAP_ROWS``, whole -- or as much as a tooltip holds."""
        node = item.node.data
        if node is None or node.container:
            return super().row_tooltip(index, item) if not isinstance(item, ValueRow) else ""
        _, cut = self.pieces(item, self.inner_width)
        return node.text[:structured.VALUE_LIMIT] if cut else ""

    def path_text(self) -> str:
        node = self.selected_data
        return structured.path(node) if node is not None else ""

    def render(self, surface: Surface) -> None:
        super().render(surface)
        inset, inner = self.inset, self.inner_width
        if self.height < 2 * inset + self.INFO_ROWS:
            return
        style = self.part_style("info")
        y = self.height - inset - self.INFO_ROWS
        text = self.path_text()
        if display_width(text) > inner - 1:
            # The end is where the cursor is: keep it, lose the start.
            text = "…" + text[-(max(1, inner - 2)):]
        surface.fill(inset, y, inner, 1, " ", style)
        surface.draw_text(inset + 1, y, text, style, max(0, inner - 1))
