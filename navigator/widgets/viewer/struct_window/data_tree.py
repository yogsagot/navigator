"""The structured view's tree: navml's ``TreeView`` over a
:class:`navigator.lib.viewer.structured.Node` tree, each row ``key: value``
and a path line under the rows.

A ``TreeNode`` is made for a node only when its parent is opened (the loader),
and holds the model's node as its ``data``; the model makes its own children
the same way, so nothing below a closed branch exists.
"""

from __future__ import annotations

from typing import Any

from navkit.bidi import display_width
from navkit.reactive import computed
from navkit.screen import Surface
from navml.widgets.dialog.tree_view import TreeNode, TreeRow, TreeView

from navigator.lib.viewer import structured
from navigator.lib.viewer.structured import Node

#: The most nodes *Expand all* (``*``) opens: past it the tree is left as it
#: is and :meth:`DataTree.expand_all` says so, as a deep document would make
#: rows by the hundred thousand.
EXPAND_LIMIT = 5000

#: The most characters of a value a row shows: the rest is cut, as the
#: cursor's value is whole on the path line's tooltip and in *Copy value*.
SHOWN_VALUE = 512


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

    def value_runs(self, node: Node) -> list[tuple[str, str]]:
        """What follows a row's name, as ``(text, part)`` pieces."""
        if node.container:
            brackets = {"object": "{}", "array": "[]", "element": "<>"}[node.kind]
            return [(f" {brackets[0]}{node.count}{brackets[1]}", "count")]
        text = node.text[:SHOWN_VALUE].replace("\n", "↵").replace("\t", " ")
        if node.kind == "string" and node.format != "xml":
            text = f'"{text}"'
        part = node.kind if node.kind in self.parts else "string"
        return [(": ", "punct"), (text, part)]

    def render_row(self, surface: Surface, y: int, index: int, item: TreeRow) -> None:
        # The rails, the branch and the name, as the tree draws them; then
        # the value, in its kind's colour, after the name.
        super().render_row(surface, y, index, item)
        node = item.node.data
        if node is None:
            return
        shift, inset, inner = self.shift, self.inset, self.inner_width
        column = 2 + 3 * len(item.rails) + len(self.branch(item))
        # Right after the name: on the cursor's row, over the blank its
        # highlight pads the name with.
        at = column + display_width(item.node.name) - shift
        if at >= inner:
            return
        runs = [(text, self.part_style(part)) for text, part in self.value_runs(node)]
        if at < 0:
            return
        surface.draw_runs(inset + at, y, runs, max_width=inner - at)

    def row_tooltip(self, index: int, item: TreeRow) -> str:
        """A value cut at the edge, whole -- or as much as a tooltip holds."""
        node = item.node.data
        if node is None or node.container:
            return super().row_tooltip(index, item)
        at = 2 + 3 * len(item.rails) + len(self.branch(item)) - self.shift
        width = display_width(item.node.name) + 2 + display_width(node.text[:SHOWN_VALUE]) + 2
        return node.text[:structured.VALUE_LIMIT] if at + width > self.inner_width else ""

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
