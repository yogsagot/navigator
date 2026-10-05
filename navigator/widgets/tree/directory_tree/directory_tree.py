"""The directory tree a panel can become: DOS Navigator's ``THTreeView``.

What Manager > Directory tree (Ctrl+T) puts in place of the passive panel.
It is :class:`~navml.widgets.dialog.tree_view.TreeView` over the filesystem,
rooted at ``/``, with the two rows ``TTreeInfoView`` kept under it: the path
of the directory under the cursor, and how many files it holds in how many
bytes -- ``12 files with 34,567 bytes``, as ``MakeDown`` wrote it.

**It reads lazily**, where DOS Navigator read the drive's whole tree on
opening: a branch is read when it is opened, and whether an unopened one has
anything in it is asked of the rows being painted.  ``THTreeView`` was the
collapsible kind already -- ``Parital`` on -- so the ``[+]`` and ``[-]`` it
draws are the original's, not a concession.  **It opens on the active
panel's directory**, every branch above it open, and follows the panel from
then on; what the panel does in return is ``Manager``'s to say.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from navkit.reactive import computed
from navkit.screen import Surface

from navml.background import Background, Outcome
from navml.widgets.dialog.tree_view import TreeNode, TreeView

#: Where the file counts under the tree are taken: a directory of a hundred
#: thousand files, or one on a dead mount, is counted without the screen
#: waiting for it.
_COUNTS = Background("nav-count", workers=2)


def _listed(name: str, hidden: bool) -> bool:
    """Whether a directory called *name* is listed: a dot-directory only if *hidden*."""
    return hidden or not name.startswith(".")


def _subdirectories(node: TreeNode) -> list[TreeNode]:
    """A directory's subdirectories, in the panel's order: by name, case folded."""
    path: Path = node.data
    hidden: bool = node.show_hidden
    found = []
    with os.scandir(path) as scan:
        for item in scan:
            if not _listed(item.name, hidden):
                continue
            try:
                if item.is_dir():
                    found.append(item.name)
            except OSError:
                continue
    found.sort(key=str.lower)
    return [directory_node(path / name, name, hidden=hidden) for name in found]


def _has_subdirectory(node: TreeNode) -> bool:
    """Whether a directory holds any directory: reads only as far as the first."""
    with os.scandir(node.data) as scan:
        for item in scan:
            if not _listed(item.name, node.show_hidden):
                continue
            try:
                if item.is_dir():
                    return True
            except OSError:
                continue
    return False


def directory_node(path: Path, name: str | None = None, *, hidden: bool = True) -> TreeNode:
    """A node for *path*, whose children are read when it is opened.

    *hidden* says whether dot-directories are listed below it, and is handed
    down to every node its loader makes -- the panel's ``show_hidden``.
    """
    node = TreeNode(
        name if name is not None else str(path),
        loader=_subdirectories,
        probe=_has_subdirectory,
        data=path,
    )
    node.show_hidden = hidden
    return node


def directory_root(hidden: bool = True) -> TreeNode:
    """The filesystem from ``/``, its first level open and nothing yet read below."""
    root = directory_node(Path("/"), "/", hidden=hidden)
    root.expanded = True
    return root


def show_path(tree: TreeView, path: Path) -> None:
    """Put *tree*'s cursor on *path*, opening every branch on the way down.

    **A dot-directory on the way is grafted in** when the tree hides them: a
    panel inside ``~/.config`` with its dot-files hidden still has a tree
    that can show where it is.  The graft is that one directory, not its
    dot-siblings, and it stays until the branch is read again.
    """
    node = tree.root
    if node is None:
        return
    names = list(Path(path).resolve().parts)
    if names and names[0] == node.name:
        names = names[1:]
    for name in names:
        children = node.children()
        child = next((c for c in children if c.name == name), None)
        if child is None:
            target = node.data / name
            if _listed(name, node.show_hidden) or not target.is_dir():
                break
            child = directory_node(target, name, hidden=node.show_hidden)
            node.set_children(sorted(children + [child], key=lambda c: c.name.lower()))
            tree.refresh()
        node = child
    tree.select(node)


def count_files(path: Path) -> tuple[int, int]:
    """How many files *path* holds directly, and their bytes together.

    What ``TDirRec`` carried as ``NumFiles`` and ``Size``: files only, and
    only this directory's own -- not its subdirectories'.
    """
    files = size = 0
    try:
        with os.scandir(path) as scan:
            for item in scan:
                try:
                    if not item.is_dir():
                        files += 1
                        size += item.stat().st_size
                except OSError:
                    continue
    except OSError:
        pass
    return files, size


def files_line(files: int, size: int) -> str:
    """``MakeDown``: ``3 files with 1,024 bytes``, ``1 file with 1 byte``."""
    head = "1 file with " if files == 1 else f"{files} files with "
    return head + ("1 byte" if size == 1 else f"{size:,} bytes")


class DirectoryTree(TreeView):
    """The filesystem as a tree, with the directory under the cursor described."""

    #: The two rows ``TTreeInfoView`` paints under the tree.
    parts = ("info",)

    #: Whether a branch has anything in it is asked on a thread: one stuck
    #: automount under ``/`` would otherwise stop the whole tree painting.
    probe_in_background = True

    #: Rows kept under the tree for the path and the file count.
    INFO_ROWS = 2

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: Whether dot-directories are listed -- the panel's ``show_hidden``,
        #: which whoever puts the tree up hands it through
        #: :meth:`set_show_hidden`.
        self.show_hidden = True
        self.root = directory_root()
        #: ``count_files`` per path, cleared by :meth:`reload`: counting runs
        #: when the cursor stops on a directory, not on every repaint -- and on
        #: a thread, the line left blank until the count is in.
        self._counts: dict[Path, tuple[int, int]] = {}
        self._counting: set[Path] = set()

    @computed
    def rows(self) -> int:
        """The listing rows, less the two the info band takes."""
        return max(0, self.height - 2 * self.inset - self.header - self.INFO_ROWS)

    @computed
    def selected_path(self) -> Path | None:
        node = self.selected_node
        return node.data if node is not None else None

    def show(self, path: Path) -> None:
        """Put the cursor on *path*, opening every branch on the way down."""
        show_path(self, path)

    def reload(self) -> None:
        """Read the tree again: ``Reread``, keeping the cursor where it was."""
        here = self.selected_path
        self._counts.clear()
        self._counting.clear()
        self.root = directory_root(self.show_hidden)
        if here is not None:
            self.show(here)

    def set_show_hidden(self, shown: bool) -> None:
        """List dot-directories or not, re-reading the tree if that changes it."""
        if shown != self.show_hidden:
            self.show_hidden = shown
            self.reload()

    # -- painting --------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        super().render(surface)
        path = self.selected_path
        inset = self.inset
        if path is None or self.height < 2 * inset + self.INFO_ROWS:
            return
        if path not in self._counts and path not in self._counting:
            self._counting.add(path)
            _COUNTS.run(self, count_files, path,
                        done=lambda outcome, path=path: self._counted(path, outcome))
        counted = self._counts.get(path)
        style, inner = self.part_style("info"), self.inner_width
        top = self.height - inset - self.INFO_ROWS
        text = str(path)
        if len(text) > inner - 1:
            text = "..." + text[-(inner - 4):] if inner > 4 else text[:inner]
        # ``TTreeInfoView.Draw`` starts its text one column in: ``B[1]``.
        count = files_line(*counted) if counted is not None else ""
        for offset, line in enumerate((text, count)):
            surface.fill(inset, top + offset, inner, 1, " ", style)
            surface.draw_text(inset + 1, top + offset, line, style, max(0, inner - 1))

    def _counted(self, path: Path, outcome: Outcome) -> None:
        if path in self._counting:
            self._counting.discard(path)
            self._counts[path] = outcome.result()
            app = self.application
            if app is not None and app.is_running:
                # Not when answered on the spot, from inside ``render``.
                self.invalidate()
