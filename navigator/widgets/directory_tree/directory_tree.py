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

from navml.widgets.dialog.tree_view import TreeNode, TreeView


def _subdirectories(node: TreeNode) -> list[TreeNode]:
    """A directory's subdirectories, in the panel's order: by name, case folded."""
    path: Path = node.data
    found = []
    with os.scandir(path) as scan:
        for item in scan:
            try:
                if item.is_dir():
                    found.append(item.name)
            except OSError:
                continue
    found.sort(key=str.lower)
    return [directory_node(path / name, name) for name in found]


def _has_subdirectory(node: TreeNode) -> bool:
    """Whether a directory holds any directory: reads only as far as the first."""
    with os.scandir(node.data) as scan:
        for item in scan:
            try:
                if item.is_dir():
                    return True
            except OSError:
                continue
    return False


def directory_node(path: Path, name: str | None = None) -> TreeNode:
    """A node for *path*, whose children are read when it is opened."""
    return TreeNode(
        name if name is not None else str(path),
        loader=_subdirectories,
        probe=_has_subdirectory,
        data=path,
    )


def directory_root() -> TreeNode:
    """The filesystem from ``/``, its first level open and nothing yet read below."""
    root = directory_node(Path("/"), "/")
    root.expanded = True
    return root


def show_path(tree: TreeView, path: Path) -> None:
    """Put *tree*'s cursor on *path*, opening every branch on the way down."""
    tree.locate(Path(path).resolve().parts)


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

    #: Rows kept under the tree for the path and the file count.
    INFO_ROWS = 2

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.root = directory_root()
        #: ``count_files`` per path, cleared by :meth:`reload`: counting runs
        #: when the cursor stops on a directory, not on every repaint.
        self._counts: dict[Path, tuple[int, int]] = {}

    @computed
    def rows(self) -> int:
        """The listing rows, less the two the info band takes."""
        return max(0, self.height - 2 - self.header - self.INFO_ROWS)

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
        self.root = directory_root()
        if here is not None:
            self.show(here)

    # -- painting --------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        super().render(surface)
        path = self.selected_path
        if path is None or self.height < 2 + self.INFO_ROWS:
            return
        if path not in self._counts:
            self._counts[path] = count_files(path)
        style, inner = self.part_style("info"), max(0, self.width - 2)
        top = self.height - 1 - self.INFO_ROWS
        text = str(path)
        if len(text) > inner - 1:
            text = "..." + text[-(inner - 4):] if inner > 4 else text[:inner]
        for offset, line in enumerate((text, files_line(*self._counts[path]))):
            surface.fill(1, top + offset, inner, 1, " ", style)
            surface.draw_text(2, top + offset, line, style, max(0, inner - 1))
