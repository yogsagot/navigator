"""The list inside the *Synchronize* window: a row per path that differs.

A :class:`~navml.widgets.dialog.list_viewer.ListViewer` over
:class:`navigator.lib.file_ops.dirsync.SyncRow` items, laid out as Disk >
Volumes' list is (``VolumeList``): titles in the band under the top edge, a
``│`` between columns, the cursor bar across them.  The columns:

- the **status**: ``>`` on the left alone, ``<`` on the right alone, ``≠``
  on both and different, ``=`` the same, ``!`` a conflict;
- the **action**: ``→`` copied right, ``←`` copied left, ``✕`` deleted,
  blank left alone (``->``, ``<-`` and ``x`` in ASCII).  The arrows are the
  Arrows block's, not ``◄──``: many fonts set the geometric triangles lower
  than the box-drawing line beside them;
- the **path** below the two directories, a directory's ending in ``/``, cut
  at its start when it must be;
- each side's **size** and **date**, the time of day left to the footer,
  which gives both sides' in full -- or says why a conflict is one.

A row is styled by its status (``SyncList::row.only``, ``.differs``,
``.same``, ``.conflict``).

**The tree view** (Ctrl+T in the window, :attr:`SyncList.tree`) lists the same
rows under the directories both sides have (``dirsync.build_tree``), each a
:class:`Line`.  A directory shows what the rows beneath come to -- their
shared status, else ``≠``, and their shared action, else ``±`` -- and its
branch is drawn as the directory trees' are, single lines and DN's
``[+]``/``[-]``: not ``▸``/``▾``, which sit as badly in some fonts as ``◄``
did.  The path column is cut at its end there, so the branches stay.  Gray
``+``/``-`` and Enter open and close a directory, ``*`` opens them all; the
action keys are the window's, the same in both views.
"""

from __future__ import annotations

import stat
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from navkit.bidi import display_width, pad_cells
from navkit import glyphs as glyphs_module
from navkit.glyphs import GLYPHS_UNICODE
from navkit.events import KeyEvent
from navkit.i18n import tr, tr_n
from navkit.reactive import peek, reactive
from navkit.screen import Surface
from navkit.style import Style
from navml.widgets.dialog.list_viewer import ListViewer

from navigator.lib.config.country import date_text, stamp
from navigator.lib.file_ops import dirsync
from navigator.widgets.manager.panel.panel import fit_text, human_size

#: The fixed columns' widths; the path has the rest.
STATUS_WIDTH = 3
SIZE_WIDTH = 8
DATE_WIDTH = 12

_STATUS_MARK = {
    dirsync.LEFT_ONLY: ">", dirsync.RIGHT_ONLY: "<", dirsync.DIFFERS: "≠", dirsync.SAME: "=",
    dirsync.CONFLICT: "!",
}
_STATUS_CLASS = {
    dirsync.LEFT_ONLY: "only", dirsync.RIGHT_ONLY: "only", dirsync.DIFFERS: "differs", dirsync.SAME: "same",
    dirsync.CONFLICT: "conflict",
}
#: Each action's mark, in Unicode and in ASCII.
_ACTION_MARK = {
    dirsync.COPY_RIGHT: ("\u2192", "->"), dirsync.COPY_LEFT: ("\u2190", "<-"),
    dirsync.DELETE: ("✕", "x"), dirsync.SKIP: ("", ""), dirsync.MIXED: ("±", "*"),
}


#: What each action does, as a row's action column's tooltip -- given the row,
#: or None for a directory line.
_ACTION_TEXT = {
    dirsync.COPY_RIGHT: lambda row: (tr("Copied to the right, over the one there")
                                     if row is not None and row.right is not None else tr("Copied to the right")),
    dirsync.COPY_LEFT: lambda row: (tr("Copied to the left, over the one there")
                                    if row is not None and row.left is not None else tr("Copied to the left")),
    dirsync.DELETE: lambda row: (tr("Deleted from the left") if row is not None and row.left is not None
                                 else tr("Deleted from the right")),
    dirsync.SKIP: lambda row: tr("Left alone"),
    dirsync.MIXED: lambda row: tr("The rows beneath are not all set alike"),
}


@dataclass(frozen=True, slots=True)
class Line:
    """One line of the tree view: a directory (*node*) or a row, how deep it
    is, whether a sibling follows it, and for each level above whether the
    branch there goes on past it."""

    node: dirsync.DirNode | None
    row: dirsync.SyncRow | None
    depth: int
    more: bool
    rails: tuple[bool, ...]

    @property
    def path(self) -> PurePosixPath:
        return self.node.path if self.node is not None else self.row.path  # type: ignore[union-attr]


def path_of(item: Any) -> PurePosixPath:
    """The path an item of either view stands for."""
    return item.path


class SyncList(ListViewer):
    """What differs between two trees, a row a path, with what is to be done with each."""

    parts = ListViewer.parts + ("heading",)

    #: The tree view: directories as lines, the rows beneath them.
    tree: bool = reactive(False)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.header = 1
        #: The directories closed in the tree view; every other one is open.
        self.collapsed: frozenset[PurePosixPath] = frozenset()
        self._root: dirsync.DirNode | None = None
        self._show_same = False

    # -- what is listed ----------------------------------------------------------

    def show_rows(self, rows: list[dirsync.SyncRow], root: dirsync.DirNode | None, show_same: bool) -> None:
        """List *rows* -- in the tree view under *root*, their tree -- the
        same ones only with *show_same*, the cursor kept on its path."""
        current = self._current()
        self._root, self._show_same = root, show_same
        if peek(self, SyncList.tree) and root is not None:
            if current is not None:
                # Its directories opened, so it is still there to stand on.
                self.collapsed = frozenset(path for path in self.collapsed
                                           if path not in current.parents)
            self.items = self._lines(root)
        else:
            self.items = [row for row in rows if show_same or row.status != dirsync.SAME]
        self._put_cursor(current)

    def _current(self) -> PurePosixPath | None:
        """The cursor's path -- peeked: the window lists from an effect, which
        must not run again at every cursor move."""
        items, cursor = peek(self, ListViewer.items), peek(self, ListViewer.cursor)
        return path_of(items[cursor]) if 0 <= cursor < len(items) else None

    def _put_cursor(self, path: PurePosixPath | None) -> None:
        if path is None:
            return
        items, cursor = self.items, peek(self, ListViewer.cursor)
        if 0 <= cursor < len(items) and path_of(items[cursor]) == path:
            return  # where it was: an action changes a row, not the lines
        for index, item in enumerate(items):
            if path_of(item) == path:
                self.cursor = index
                return
        # Inside a directory just closed: onto the directory.
        for parent in path.parents:
            for index, item in enumerate(self.items):
                if path_of(item) == parent:
                    self.cursor = index
                    return

    def _lines(self, root: dirsync.DirNode) -> list[Line]:
        """The tree flattened: what is open, the same rows only with ``_show_same``."""
        show_same, collapsed = self._show_same, self.collapsed
        lines: list[Line] = []

        def walk(node: dirsync.DirNode, depth: int, rails: tuple[bool, ...]) -> None:
            entries: list[Any] = [child for _, child in sorted(node.dirs.items())
                                  if show_same or child.count]
            entries += [row for row in node.rows if show_same or row.status != dirsync.SAME]
            last = len(entries) - 1
            for index, entry in enumerate(entries):
                more = index < last
                if isinstance(entry, dirsync.DirNode):
                    lines.append(Line(entry, None, depth, more, rails))
                    if entry.path not in collapsed:
                        walk(entry, depth + 1, rails + (more,))
                else:
                    lines.append(Line(None, entry, depth, more, rails))

        walk(root, 0, ())
        return lines

    def _relist(self) -> None:
        if self.tree and self._root is not None:
            current = self._current()
            self.items = self._lines(self._root)
            self._put_cursor(current)

    def open_node(self, node: dirsync.DirNode, opened: bool) -> None:
        """Open or close *node*'s branch."""
        if opened == (node.path not in self.collapsed):
            return
        self.collapsed = self.collapsed - {node.path} if opened else self.collapsed | {node.path}
        self._relist()

    def open_all(self) -> None:
        if self.collapsed:
            self.collapsed = frozenset()
            self._relist()

    # -- the cursor's row ----------------------------------------------------------

    @property
    def selected_line(self) -> Line | None:
        item = self.selected
        return item if isinstance(item, Line) else None

    @property
    def selected_row(self) -> dirsync.SyncRow | None:
        """The row under the cursor, in either view; None on a directory."""
        item = self.selected
        return item.row if isinstance(item, Line) else item

    def selected_rows(self) -> list[dirsync.SyncRow]:
        """What an action at the cursor acts on: its row, or every row beneath its directory."""
        item = self.selected
        if isinstance(item, Line) and item.node is not None:
            return dirsync.rows_beneath(item.node)
        row = self.selected_row
        return [row] if row is not None else []

    def selected_allows(self, action: str) -> bool:
        """Whether an action at the cursor would change anything it may."""
        line = self.selected_line
        if line is not None and line.node is not None:
            return action == "default" or action in line.node.allowed
        row = self.selected_row
        return row is not None and (action == "default" or action in row.allowed)

    async def choose(self) -> bool:
        """Enter on a directory opens or closes it; on a row it is the window's."""
        line = self.selected_line
        if line is not None and line.node is not None:
            self.open_node(line.node, line.node.path in self.collapsed)
            return True
        return False

    async def on_key(self, event: KeyEvent) -> bool:
        """Gray ``+`` and ``-`` open and close the directory at the cursor -- or
        the one a row is in -- and ``*`` opens all, in the tree view."""
        line = self.selected_line
        if line is not None and not event.ctrl and not event.alt:
            node = line.node if line.node is not None else None
            if event.key in ("plus", "kp_plus") and node is not None:
                self.open_node(node, True)
                return True
            if event.key in ("-", "kp_minus"):
                if node is None or node.path in self.collapsed:
                    # A row, or a closed directory: its parent's branch.
                    parent = line.path.parent
                    target = self._node_at(parent)
                    if target is not None:
                        self.open_node(target, False)
                    return True
                self.open_node(node, False)
                return True
            if event.key in ("*", "kp_multiply"):
                self.open_all()
                return True
        return await super().on_key(event)

    def _node_at(self, path: PurePosixPath) -> dirsync.DirNode | None:
        node = self._root
        if node is None or not path.parts:
            return None
        for part in path.parts:
            node = node.dirs.get(part)
            if node is None:
                return None
        return node

    @property
    def ellipsis(self) -> str:
        return glyphs_module.ellipsis(self.glyphs)

    @property
    def divider_glyph(self) -> str:
        return glyphs_module.charset("single", self.glyphs)[5]

    def columns(self) -> list[tuple[int, int]]:
        """``(x, width)`` of each column, a divider's cell between two."""
        fixed = (STATUS_WIDTH, self.action_width, None, SIZE_WIDTH, DATE_WIDTH, SIZE_WIDTH, DATE_WIDTH)
        rest = max(0, self.inner_width - sum(width for width in fixed if width) - (len(fixed) - 1))
        spans: list[tuple[int, int]] = []
        x = self.inset
        for width in fixed:
            width = rest if width is None else width
            spans.append((x, width))
            x += width + 1
        return spans

    @property
    def action_width(self) -> int:
        """The action column: as wide as its widest mark in this glyph tier, a blank each side."""
        return max(len(self._action_mark(action)) for action in _ACTION_MARK) + 2

    def _status_mark(self, status: str) -> str:
        mark = _STATUS_MARK[status]
        return "#" if mark == "≠" and self.glyphs < GLYPHS_UNICODE else mark

    def _action_mark(self, action: str) -> str:
        unicode, ascii = _ACTION_MARK[action]
        return unicode if self.glyphs >= GLYPHS_UNICODE else ascii

    @staticmethod
    def _side(side: dirsync.Side | None) -> tuple[str, str]:
        if side is None:
            return "", ""
        size = tr("DIR") if side.kind == "dir" else human_size(side.size)
        return size, date_text(side.mtime) if side.mtime else ""

    def _branch(self, line: Line) -> str:
        """What is drawn left of a line's name: the rails above, its own branch."""
        tl, tr_, bl, br, horizontal, vertical = glyphs_module.charset("single", self.glyphs)
        tee = glyphs_module.joins("single", self.glyphs)[0]
        rails = "".join(f"{vertical} " if more else "  " for more in line.rails)
        return rails + (tee if line.more else bl) + horizontal

    def cells(self, item: Any) -> list[tuple[str, bool]]:
        """*item*'s text in each column, and whether it is right-aligned."""
        if isinstance(item, Line) and item.node is not None:
            node = item.node
            mark = "+" if node.path in self.collapsed else "-"
            path = f"{self._branch(item)}[{mark}] {node.name}/"
            return [(self._status_mark(node.status), False), (self._action_mark(node.action), False), (path, False),
                    ("", True), ("", False), ("", True), ("", False)]
        row = item.row if isinstance(item, Line) else item
        if isinstance(item, Line):
            path = f"{self._branch(item)}{row.path.name}" + ("/" if row.is_dir else "")
        else:
            path = str(row.path) + ("/" if row.is_dir else "")
        left_size, left_date = self._side(row.left)
        right_size, right_date = self._side(row.right)
        return [
            (self._status_mark(row.status), False), (self._action_mark(row.action), False), (path, False),
            (left_size, True), (left_date, False), (right_size, True), (right_date, False),
        ]

    def row_text(self, index: int, item: Any) -> str:
        return str(path_of(item))

    def row_style(self, index: int, item: Any) -> Style:
        status = item.node.status if isinstance(item, Line) and item.node is not None else \
            (item.row if isinstance(item, Line) else item).status
        return self.part_style("row", classes=(_STATUS_CLASS[status],), selected=self.row_selected(index))

    # -- tooltips --------------------------------------------------------------

    def tooltip_at(self, x: int, y: int) -> str:
        """What a cell leaves out: the status's reason, the action's meaning,
        the whole path, exact bytes and the whole time."""
        inside = self.inset <= x < self.inset + self.inner_width
        index = self.index_at(x, y) if inside else None
        if index is not None:
            for column, (left, width) in enumerate(self.columns()):
                if left <= x < left + width:
                    text = self.cell_tooltip(self.items[index], column, width - 2)
                    if text:
                        return text
                    break
        return super().tooltip_at(x, y)

    def _request(self) -> Any:
        """What the comparison asked: the window's ``CompareRequest``, or None."""
        widget = self.parent
        while widget is not None and getattr(widget, "request", None) is None:
            widget = widget.parent
        return widget.request if widget is not None else None

    def cell_tooltip(self, item: Any, column: int, room: int) -> str:
        """Column *column* of *item*, *room* cells wide, as a tooltip."""
        if isinstance(item, Line) and item.node is not None:
            node = item.node
            if column == 0:
                return tr_n("{n} difference beneath", "{n} differences beneath", node.count)
            if column == 1:
                return _ACTION_TEXT.get(node.action, lambda row: "")(None)
            if column == 2:
                return f"{node.path}/"
            return ""
        row = item.row if isinstance(item, Line) else item
        if column == 0:
            return self.status_reason(row)
        if column == 1:
            return _ACTION_TEXT[row.action](row)
        if column == 2:
            path = str(row.path) + ("/" if row.is_dir else "")
            return path if isinstance(item, Line) or len(path) > room else ""
        side = row.left if column in (3, 4) else row.right
        if side is None:
            return ""
        if column in (3, 5):
            if side.kind == "dir" or side.size < 1024:
                return ""
            return tr_n("{count} byte", "{count} bytes", side.size, count=f"{side.size:,}")
        return stamp(side.mtime) if side.mtime else ""

    def status_reason(self, row: dirsync.SyncRow) -> str:
        """What *row*'s status means, and for a difference, which of the
        checks the comparison asked for found one."""
        if row.error:
            return row.error
        if row.status == dirsync.LEFT_ONLY:
            return tr("Only on the left")
        if row.status == dirsync.RIGHT_ONLY:
            return tr("Only on the right")
        if row.status == dirsync.SAME:
            return tr("The same on both sides")
        left, right = row.left, row.right
        if row.status == dirsync.CONFLICT or left is None or right is None:
            kinds = {"file": tr("a file"), "dir": tr("a directory"), "link": tr("a link"),
                     "other": tr("a special file")}
            return tr("On the left {left}, on the right {right}: they cannot be compared, and are left alone").format(
                left=kinds.get(left.kind if left else "", ""), right=kinds.get(right.kind if right else "", ""))
        request = self._request()
        reasons = [tr("Different on the two sides")]
        if left.size != right.size:
            reasons.append(tr("Sizes {left} and {right} bytes").format(left=f"{left.size:,}", right=f"{right.size:,}"))
        if row.newer == "left":
            reasons.append(tr("The left one is newer"))
        elif row.newer == "right":
            reasons.append(tr("The right one is newer"))
        if request is not None and request.attributes and stat.S_IMODE(left.mode) != stat.S_IMODE(right.mode):
            reasons.append(tr("Permissions {left} and {right}").format(
                left=f"{stat.S_IMODE(left.mode):04o}", right=f"{stat.S_IMODE(right.mode):04o}"))
        if len(reasons) == 1 and request is not None and request.contents:
            reasons.append(tr("Their contents differ"))
        return "\n".join(reasons)

    def footer_text(self) -> str:
        """Why the row under the cursor is a conflict, or when each side was
        changed; on a directory, how many differences are beneath it."""
        line = self.selected_line
        if line is not None and line.node is not None:
            return " " + tr_n("{n} difference beneath", "{n} differences beneath", line.node.count) + " "
        item = self.selected_row
        if item is None:
            return ""
        if item.error:
            return f" {item.error} "
        times = [stamp(side.mtime) if side is not None and side.mtime else "-" for side in (item.left, item.right)]
        return f" {times[0]}  |  {times[1]} "

    def _cut_start(self, text: str, room: int) -> str:
        if len(text) <= room:
            return text
        marker = self.ellipsis
        if room > len(marker):
            return marker + text[-(room - len(marker)):]
        return text[-room:] if room > 0 else ""

    def render_header(self, surface: Surface) -> None:
        """The column titles, and the dividers from them down to the last row."""
        titles = ("", "", tr("Path"), tr("Left"), "", tr("Right"), "")
        top = self.inset
        bottom = top + self.header + self.rows
        right = self.inset + self.inner_width
        heading, divider = self.part_style("heading"), self.part_style("divider")
        spans = self.columns()
        for index, (title, (x, width)) in enumerate(zip(titles, spans)):
            shown = min(width, right - x)
            if shown <= 0:
                break
            title = title[:shown]
            surface.draw_text(x + (shown - display_width(title)) // 2, top, title, heading, shown)
            edge = x + width
            if index < len(spans) - 1 and edge < right:
                for y in range(top, bottom):
                    surface.draw_text(edge, y, self.divider_glyph, divider, 1)

    def render_row(self, surface: Surface, y: int, index: int, item: Any) -> None:
        style = self.row_style(index, item)
        right = self.inset + self.inner_width
        for column, ((text, flush_right), (x, width)) in enumerate(zip(self.cells(item), self.columns())):
            room = min(width, right - x) - 2
            if room <= 0:
                continue
            cut_start = column == 2 and not isinstance(item, Line)
            text = self._cut_start(text, room) if cut_start else fit_text(text, room, self.ellipsis)
            if flush_right:
                text = pad_cells(text, room, "right")
            surface.draw_text(x + 1, y, text, style, room)
