#!/usr/bin/env python3
"""Navigator -- a recreation of DOS Navigator for POSIX terminals.

This is the application entry point.  For now it is a thin shell over navkit:
a menu bar, two directory panels and the function key bar, drawn by hand.  As
navml grows, these screens move into ``*.nml`` markup and this module keeps
only the event handlers.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from navkit.application import Application
from navkit.events import KeyEvent, MouseEvent
from navkit.screen import ScreenBuffer
from navkit.style import BLACK, BLUE, CYAN, LIGHT_CYAN, RED, WHITE, Style
from navkit.widget import Widget

PANEL = Style(fg=LIGHT_CYAN, bg=BLUE)
PANEL_TEXT = Style(fg=LIGHT_CYAN, bg=BLUE)
PANEL_DIR = Style(fg=WHITE, bg=BLUE, bold=True)
PANEL_TITLE = Style(fg=BLACK, bg=CYAN)
PANEL_TITLE_DIM = Style(fg=LIGHT_CYAN, bg=BLUE)
CURSOR = Style(fg=BLACK, bg=CYAN)
MENU = Style(fg=BLACK, bg=CYAN)
MENU_HOTKEY = Style(fg=RED, bg=CYAN)
KEYBAR_NUMBER = Style(fg=WHITE, bg=BLACK)
KEYBAR_LABEL = Style(fg=BLACK, bg=CYAN)
DESKTOP = Style(fg=CYAN, bg=BLACK)

MENU_ITEMS = ["Left", "Files", "Commands", "Options", "Right"]
FUNCTION_KEYS = [
    "Help",
    "Menu",
    "View",
    "Edit",
    "Copy",
    "RenMov",
    "Mkdir",
    "Delete",
    "PullDn",
    "Quit",
]


class DirEntry:
    """One line in a panel: a name, whether it is a directory, and its size."""

    __slots__ = ("name", "is_dir", "size")

    def __init__(self, name: str, is_dir: bool, size: int):
        self.name = name
        self.is_dir = is_dir
        self.size = size

    @property
    def sort_key(self) -> tuple:
        # ".." first, then directories, then files -- as in the original.
        return (self.name != "..", not self.is_dir, self.name.lower())

    @property
    def display_size(self) -> str:
        if self.name == "..":
            return " UP--DIR"
        if self.is_dir:
            return "     DIR"
        size = float(self.size)
        for unit in ("", "K", "M", "G", "T"):
            if size < 1024 or unit == "T":
                return f"{self.size:>8}" if not unit else f"{size:>7.0f}{unit}"
            size /= 1024
        return f"{self.size:>8}"


class Panel(Widget):
    """A file listing panel with a frame, a header and a cursor."""

    def __init__(self, path: Path, **kwargs):
        super().__init__(style=PANEL, **kwargs)
        self.path = path
        self.entries: list[DirEntry] = []
        self.cursor = 0
        self.scroll = 0
        self.active = False
        self.error: str | None = None
        self.reload()

    # -- model ---------------------------------------------------------------

    def reload(self) -> None:
        """Re-read the directory this panel shows."""
        entries: list[DirEntry] = []
        self.error = None
        if self.path != self.path.parent:
            entries.append(DirEntry("..", True, 0))
        try:
            with os.scandir(self.path) as scan:
                for item in scan:
                    try:
                        is_dir = item.is_dir()
                        size = 0 if is_dir else item.stat().st_size
                    except OSError:
                        is_dir, size = False, 0
                    entries.append(DirEntry(item.name, is_dir, size))
        except OSError as exc:
            self.error = exc.strerror or str(exc)
        entries.sort(key=lambda entry: entry.sort_key)
        self.entries = entries
        self.cursor = 0
        self.scroll = 0
        self.invalidate()

    @property
    def rows(self) -> int:
        """How many listing lines fit between the top and bottom frame."""
        return max(0, self.height - 2)

    @property
    def selected(self) -> DirEntry | None:
        if 0 <= self.cursor < len(self.entries):
            return self.entries[self.cursor]
        return None

    def move_cursor(self, delta: int) -> None:
        if not self.entries:
            return
        self.cursor = max(0, min(len(self.entries) - 1, self.cursor + delta))
        if self.cursor < self.scroll:
            self.scroll = self.cursor
        elif self.cursor >= self.scroll + self.rows:
            self.scroll = self.cursor - self.rows + 1
        self.invalidate()

    def enter(self) -> None:
        """Descend into the selected directory."""
        entry = self.selected
        if entry is None or not entry.is_dir:
            return
        previous = self.path.name
        self.path = (self.path / entry.name).resolve()
        self.reload()
        if entry.name == "..":
            # Put the cursor back on the directory we came out of.
            for index, item in enumerate(self.entries):
                if item.name == previous:
                    self.move_cursor(index)
                    break

    # -- painting ------------------------------------------------------------

    def render(self, buffer: ScreenBuffer) -> None:
        buffer.draw_box(
            self.x,
            self.y,
            self.width,
            self.height,
            PANEL,
            double=self.active,
            fill=" ",
        )
        self._render_title(buffer)
        self._render_entries(buffer)
        self._render_footer(buffer)

    def _render_title(self, buffer: ScreenBuffer) -> None:
        title = str(self.path)
        room = max(1, self.width - 4)
        if len(title) > room:
            title = "..." + title[-(room - 3) :]
        label = f" {title} "
        style = PANEL_TITLE if self.active else PANEL_TITLE_DIM
        buffer.draw_text(
            self.x + max(1, (self.width - len(label)) // 2), self.y, label, style
        )

    def _render_entries(self, buffer: ScreenBuffer) -> None:
        if self.error is not None:
            buffer.draw_text(
                self.x + 2, self.y + 2, self.error, PANEL_TEXT, self.width - 4
            )
            return
        name_width = max(1, self.width - 12)
        for row in range(self.rows):
            index = self.scroll + row
            if index >= len(self.entries):
                break
            entry = self.entries[index]
            selected = index == self.cursor and self.active
            style = CURSOR if selected else (PANEL_DIR if entry.is_dir else PANEL_TEXT)
            y = self.y + 1 + row
            if selected:
                buffer.fill(self.x + 1, y, self.width - 2, 1, " ", style)
            buffer.draw_text(self.x + 1, y, entry.name, style, name_width)
            buffer.draw_text(
                self.x + self.width - 9, y, entry.display_size, style, 8
            )

    def _render_footer(self, buffer: ScreenBuffer) -> None:
        entry = self.selected
        summary = f" {len(self.entries)} items "
        if entry is not None:
            summary = f" {entry.name} "
        room = max(1, self.width - 4)
        if len(summary) > room:
            summary = summary[: room - 1] + " "
        buffer.draw_text(
            self.x + max(1, (self.width - len(summary)) // 2),
            self.y + self.height - 1,
            summary,
            PANEL,
        )


class MenuBar(Widget):
    """The pull-down menu bar across the top of the screen."""

    def render(self, buffer: ScreenBuffer) -> None:
        buffer.fill(self.x, self.y, self.width, 1, " ", MENU)
        column = self.x + 1
        for item in MENU_ITEMS:
            buffer.draw_text(column, self.y, item[0], MENU_HOTKEY)
            buffer.draw_text(column + 1, self.y, item[1:], MENU)
            column += len(item) + 2


class KeyBar(Widget):
    """The F1..F10 hint bar across the bottom of the screen."""

    def render(self, buffer: ScreenBuffer) -> None:
        buffer.fill(self.x, self.y, self.width, 1, " ", KEYBAR_LABEL)
        slot = max(3, self.width // len(FUNCTION_KEYS))
        for index, label in enumerate(FUNCTION_KEYS):
            column = self.x + index * slot
            if column >= self.x + self.width:
                break
            number = str(index + 1)
            buffer.draw_text(column, self.y, number, KEYBAR_NUMBER)
            buffer.draw_text(
                column + len(number),
                self.y,
                label.ljust(slot - len(number)),
                KEYBAR_LABEL,
                slot - len(number),
            )


class Manager(Widget):
    """The Navigator desktop: menu bar, two panels and the key bar."""

    def __init__(self, left: Path, right: Path):
        super().__init__(style=DESKTOP)
        self.menu = MenuBar(style=MENU)
        self.left = Panel(left)
        self.right = Panel(right)
        self.keybar = KeyBar(style=KEYBAR_LABEL)
        for child in (self.menu, self.left, self.right, self.keybar):
            self.add(child)
        self.left.active = True

    @property
    def active_panel(self) -> Panel:
        return self.left if self.left.active else self.right

    def switch_panel(self) -> None:
        self.left.active, self.right.active = self.right.active, self.left.active
        self.invalidate()

    def layout(self, width: int, height: int) -> None:
        self.width, self.height = width, height
        self.menu.x, self.menu.y = 0, 0
        self.menu.width, self.menu.height = width, 1
        self.keybar.x, self.keybar.y = 0, max(1, height - 1)
        self.keybar.width, self.keybar.height = width, 1

        body_height = max(3, height - 2)
        half = width // 2
        self.left.x, self.left.y = 0, 1
        self.left.width, self.left.height = half, body_height
        self.right.x, self.right.y = half, 1
        self.right.width, self.right.height = width - half, body_height

    def render(self, buffer: ScreenBuffer) -> None:
        buffer.fill(self.x, self.y, self.width, self.height, " ", DESKTOP)


class Navigator(Application):
    """The file manager application."""

    def __init__(self, left: Path, right: Path):
        super().__init__(root=Manager(left, right), title="Navigator", background=DESKTOP)

    @property
    def manager(self) -> Manager:
        assert isinstance(self.root, Manager)
        return self.root

    def on_key(self, event: KeyEvent) -> bool:
        manager = self.manager
        panel = manager.active_panel

        if event.matches("f10", "ctrl+q"):
            self.exit()
        elif event.matches("tab"):
            manager.switch_panel()
        elif event.matches("up"):
            panel.move_cursor(-1)
        elif event.matches("down"):
            panel.move_cursor(1)
        elif event.matches("pageup"):
            panel.move_cursor(-max(1, panel.rows - 1))
        elif event.matches("pagedown"):
            panel.move_cursor(max(1, panel.rows - 1))
        elif event.matches("home"):
            panel.move_cursor(-len(panel.entries))
        elif event.matches("end"):
            panel.move_cursor(len(panel.entries))
        elif event.matches("enter"):
            panel.enter()
        elif event.matches("ctrl+r"):
            panel.reload()
        else:
            return False
        return True

    def on_mouse(self, event: MouseEvent) -> bool:
        manager = self.manager
        for panel in (manager.left, manager.right):
            if not panel.contains(event.x, event.y):
                continue
            if not panel.active:
                manager.switch_panel()
            if event.is_wheel:
                panel.move_cursor(-3 if event.button == "wheel_up" else 3)
            elif event.action == "press" and event.button == "left":
                row = event.y - panel.y - 1
                if 0 <= row < panel.rows:
                    panel.move_cursor(panel.scroll + row - panel.cursor)
            return True
        return False


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    left = Path(argv[0]).expanduser().resolve() if argv else Path.cwd()
    right = Path(argv[1]).expanduser().resolve() if len(argv) > 1 else left
    Navigator(left, right).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())