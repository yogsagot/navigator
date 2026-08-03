#!/usr/bin/env python3
"""Navigator -- a recreation of DOS Navigator for POSIX terminals.

The application entry point: ``python -m navigator``.  For now it is a thin
shell over navkit -- a menu bar, two directory panels and the function key
bar, drawn by hand.  As navml grows, these screens move into ``*.nml`` markup
and this module keeps only the event handlers.
"""

from __future__ import annotations

import argparse
import os
import sys
from importlib.resources import files
from pathlib import Path

from navkit.application import Application
from navkit.events import KeyEvent, MouseEvent
from navkit.reactive import bind, computed, effect, peek, reactive
from navkit.screen import Surface
from navkit.style import Style
from navkit.stylesheet import Stylesheet, parse_value, read, register_property
from navkit.widget import Widget

#: ``border`` is not a field of ``Style`` -- a box-drawing character set is an
#: input to a drawing operation, not an appearance a cell can carry -- so the
#: widget that reads it has to declare it before a sheet may name it.
register_property("border")

#: Where sheets live.  A directory rather than a single file because a theme is
#: nothing more than another ``.nss`` loaded after the default one, so this is
#: also where one would be dropped.
#:
#: Located through the package rather than by walking out from ``__file__``,
#: so it resolves the same from a source checkout, from an installed copy, and
#: whether this module is run as ``__main__`` or imported by name.
STYLES = Path(str(files("navigator.styles")))

#: What the screens are made of: the rules, in terms of variables it does not
#: define.  It does not parse on its own; a palette always follows it.
SCHEME_PATH = STYLES / "navigator.nss"

#: The palettes, one per colour scheme, each defining every variable the sheet
#: above reads.  They are DOS Navigator's own ``COLORS/*.PAL`` files decoded by
#: ``tools/palconv.py``, so retheming is picking one rather than writing one.
THEMES = STYLES / "themes"

#: The scheme DOS Navigator itself starts in -- ``DEFAULT.PAL``.
DEFAULT_THEME = "default"


def theme_names() -> list[str]:
    """Every theme that can be asked for by name."""
    return sorted(path.stem for path in THEMES.glob("*.nss"))


def load_scheme(theme: str = DEFAULT_THEME, *extra) -> Stylesheet:
    """The rules, with *theme*'s palette merged over them.

    Merged rather than concatenated: the palette is only variable definitions,
    and those resolve across sheets before any rule is read, so a palette needs
    no rules of its own and cannot accidentally out-specify one.

    *extra* is anything :func:`~navkit.stylesheet.read` accepts, loaded last --
    a path to a sheet of one's own, or a ``(name, text)`` pair.
    """
    path = THEMES / f"{theme}.nss"
    if not path.is_file():
        raise LookupError(
            f"no theme {theme!r}; there is " + ", ".join(theme_names())
        )
    return read(SCHEME_PATH, path, *extra)


def desktop_style(scheme: Stylesheet) -> Style:
    """What the buffer is cleared to before the tree paints over it.

    Read out of the scheme's variables rather than resolved against a widget,
    because :class:`~navkit.application.Application` clears the screen before
    any widget exists to ask.
    """
    variables = scheme.variables
    return Style(
        fg=parse_value("fg", variables.get("desktop-fg", "default"), variables),
        bg=parse_value("bg", variables.get("desktop-bg", "default"), variables),
    )


#: Parsed once, because a sheet is immutable and every desktop that does not
#: ask for a theme resolves against the same one.
SCHEME = load_scheme()

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
    """A file listing panel with a frame, a header and a cursor.

    The model is declarative: ``path`` is the only thing a command really
    assigns, and the listing, the cursor and the scroll offset follow it.  So
    the invariants -- the cursor sits on a row that exists, the scroll keeps
    it visible -- hold no matter which path changed the state, including a
    terminal resize, which the old imperative version got wrong.
    """

    path: Path = reactive(Path("."))
    entries: list[DirEntry] = reactive(factory=list)
    error: str | None = reactive(None)
    cursor: int = reactive(0)
    scroll: int = reactive(0)
    active: bool = reactive(False)
    #: Bumped to re-read a directory whose path has not changed.
    reload_token: int = reactive(0)

    def __init__(self, path: Path, **kwargs):
        super().__init__(**kwargs)
        #: Set by :meth:`enter` for the rescan that is about to happen, so the
        #: cursor can land on the directory we just climbed out of.
        self._return_to: str | None = None
        self.path = path
        # Declaration order is flush order: rebuild the listing, put the
        # cursor somewhere real, then scroll to it.
        effect(self, Panel._rescan)
        effect(self, Panel._clamp_cursor)
        effect(self, Panel._follow_cursor)

    # -- model ---------------------------------------------------------------

    def _rescan(self) -> None:
        """Re-read the directory, whenever the path or the token changes."""
        _ = self.reload_token  # read for the dependency; this is what Ctrl+R moves
        path = self.path
        entries: list[DirEntry] = []
        error: str | None = None
        if path != path.parent:
            entries.append(DirEntry("..", True, 0))
        try:
            with os.scandir(path) as scan:
                for item in scan:
                    try:
                        is_dir = item.is_dir()
                        size = 0 if is_dir else item.stat().st_size
                    except OSError:
                        is_dir, size = False, 0
                    entries.append(DirEntry(item.name, is_dir, size))
        except OSError as exc:
            error = exc.strerror or str(exc)
        entries.sort(key=lambda entry: entry.sort_key)

        self.entries = entries
        self.error = error
        target, self._return_to = self._return_to, None
        self.cursor = next(
            (index for index, item in enumerate(entries) if item.name == target), 0
        )
        self.scroll = 0

    def _clamp_cursor(self) -> None:
        """Keep the cursor on a row that exists, however the listing changed.

        Assigning what it also reads is allowed here: an effect's own writes
        are part of the run it is in and do not wake it again.
        """
        last = len(self.entries) - 1
        self.cursor = min(max(self.cursor, 0), last) if last >= 0 else 0

    def _follow_cursor(self) -> None:
        """Scroll just far enough to keep the cursor on screen.

        ``scroll`` is read with :func:`~navkit.reactive.peek` because this is
        the effect that assigns it; subscribing to it would be a loop.
        """
        cursor, rows = self.cursor, self.rows
        scroll = peek(self, Panel.scroll)
        if cursor < scroll:
            self.scroll = cursor
        elif cursor >= scroll + rows:
            self.scroll = cursor - rows + 1

    def reload(self) -> None:
        """Re-read the directory this panel shows."""
        self.reload_token += 1

    @computed
    def rows(self) -> int:
        """How many listing lines fit between the top and bottom frame."""
        return max(0, self.height - 2)

    @computed
    def selected(self) -> DirEntry | None:
        """The entry the cursor is on, if the listing has one."""
        if 0 <= self.cursor < len(self.entries):
            return self.entries[self.cursor]
        return None

    def move_cursor(self, delta: int) -> None:
        if not self.entries:
            return
        # Deliberately unclamped: _clamp_cursor owns that invariant.
        self.cursor += delta

    def enter(self) -> None:
        """Descend into the selected directory."""
        entry = self.selected
        if entry is None or not entry.is_dir:
            return
        # The rescan is deferred, so the cursor we want afterwards has to be
        # left behind as a note rather than applied on the next line.
        self._return_to = self.path.name if entry.name == ".." else None
        self.path = (self.path / entry.name).resolve()

    # -- painting ------------------------------------------------------------

    @computed
    def title_text(self) -> str:
        """The path across the top frame, clipped to fit."""
        title = str(self.path)
        room = max(1, self.width - 4)
        if len(title) > room:
            title = "..." + title[-(room - 3) :]
        return f" {title} "

    @computed
    def footer_text(self) -> str:
        """The selected name, or an item count when there is nothing to name."""
        entry = self.selected
        summary = f" {entry.name} " if entry else f" {len(self.entries)} items "
        room = max(1, self.width - 4)
        return summary[: room - 1] + " " if len(summary) > room else summary

    @computed
    def name_width(self) -> int:
        """How much of a listing line is left once the size column is taken."""
        return max(1, self.width - 12)

    def render(self, surface: Surface) -> None:
        surface.draw_box(
            0,
            0,
            self.width,
            self.height,
            self.style,
            double=self.style_property("border") == "double",
            fill=" ",
        )
        self._render_title(surface)
        self._render_entries(surface)
        self._render_footer(surface)

    def _render_title(self, surface: Surface) -> None:
        label = self.title_text
        style = self.part_style("title")
        surface.draw_text(max(1, (self.width - len(label)) // 2), 0, label, style)

    def _render_entries(self, surface: Surface) -> None:
        if self.error is not None:
            surface.draw_text(2, 2, self.error, self.part_style("error"), self.width - 4)
            return
        # Still an explicit limit: the name stops where the size column
        # begins, which is nearer than the edge the surface would clip at.
        name_width = self.name_width
        for row in range(self.rows):
            index = self.scroll + row
            if index >= len(self.entries):
                break
            entry = self.entries[index]
            # The cursor only shows on the panel that has focus, so the two
            # conditions are ANDed here rather than left to a ``:active``
            # selector: the row fill below is gated on the same answer.
            selected = index == self.cursor and self.active
            style = self.part_style(
                "row",
                classes=("directory",) if entry.is_dir else (),
                selected=selected,
            )
            y = 1 + row
            if selected:
                surface.fill(1, y, self.width - 2, 1, " ", style)
            surface.draw_text(1, y, entry.name, style, name_width)
            surface.draw_text(self.width - 9, y, entry.display_size, style, 8)

    def _render_footer(self, surface: Surface) -> None:
        summary = self.footer_text
        surface.draw_text(
            max(1, (self.width - len(summary)) // 2),
            self.height - 1,
            summary,
            self.part_style("footer"),
        )


class MenuBar(Widget):
    """The pull-down menu bar across the top of the screen."""

    def render(self, surface: Surface) -> None:
        label, hotkey = self.style, self.part_style("hotkey")
        surface.fill(0, 0, self.width, 1, " ", label)
        column = 1
        for item in MENU_ITEMS:
            surface.draw_text(column, 0, item[0], hotkey)
            surface.draw_text(column + 1, 0, item[1:], label)
            column += len(item) + 2


class KeyBar(Widget):
    """The F1..F10 hint bar across the bottom of the screen."""

    def render(self, surface: Surface) -> None:
        label_style, number_style = self.style, self.part_style("number")
        surface.fill(0, 0, self.width, 1, " ", label_style)
        slot = max(3, self.width // len(FUNCTION_KEYS))
        for index, label in enumerate(FUNCTION_KEYS):
            column = index * slot
            if column >= self.width:
                break
            number = str(index + 1)
            surface.draw_text(column, 0, number, number_style)
            surface.draw_text(
                column + len(number),
                0,
                label.ljust(slot - len(number)),
                label_style,
                slot - len(number),
            )


class Manager(Widget):
    """The Navigator desktop: menu bar, two panels and the key bar."""

    def __init__(self, left: Path, right: Path, scheme: Stylesheet = SCHEME):
        super().__init__()
        # The desktop brings its own look, so the tree is styled with or
        # without an application around it -- which is also what lets a single
        # panel be built and painted on its own.
        self._stylesheet = scheme
        self.menu = MenuBar()
        self.left = Panel(left)
        self.right = Panel(right)
        self.keybar = KeyBar()
        for child in (self.menu, self.left, self.right, self.keybar):
            self.add(child)
        self._place()
        self.left.active = True

    def _place(self) -> None:
        """Say how the desktop is divided, once, in terms of its own size.

        There is no ``layout`` method to go with this: every size that depends
        on the terminal is an expression, so a resize propagates by itself.
        This is the shape a ``*.nml`` file will compile to.
        """
        self.menu.x, self.menu.y = 0, 0
        self.menu.width = bind(lambda w: w.parent.width)
        self.menu.height = bind(lambda w: 1)

        self.keybar.x = 0
        self.keybar.y = bind(lambda w: max(1, w.parent.height - 1))
        self.keybar.width = bind(lambda w: w.parent.width)
        self.keybar.height = bind(lambda w: 1)

        self.left.x, self.left.y = 0, 1
        self.left.width = bind(lambda w: w.parent.width // 2)
        self.left.height = bind(lambda w: max(3, w.parent.height - 2))

        self.right.y = 1
        self.right.x = bind(lambda w: w.parent.width // 2)
        self.right.width = bind(lambda w: w.parent.width - w.parent.width // 2)
        self.right.height = bind(lambda w: max(3, w.parent.height - 2))

    @computed
    def active_panel(self) -> Panel:
        """Whichever panel currently has the cursor."""
        return self.left if self.left.active else self.right

    def switch_panel(self) -> None:
        self.left.active, self.right.active = self.right.active, self.left.active

    def render(self, surface: Surface) -> None:
        surface.fill(0, 0, self.width, self.height, " ", self.style)


class Navigator(Application):
    """The file manager application."""

    def __init__(self, left: Path, right: Path, scheme: Stylesheet = SCHEME, **kwargs):
        kwargs.setdefault("title", "Navigator")
        kwargs.setdefault("background", desktop_style(scheme))
        self.manager = Manager(left, right, scheme)
        super().__init__(root=self.manager, **kwargs)

    def on_key(self, event: KeyEvent) -> bool:
        manager = self.manager
        panel = manager.active_panel

        if event.matches("f10", "ctrl+q", "alt+x"):
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
    parser = argparse.ArgumentParser(prog="navigator", description=__doc__)
    parser.add_argument("left", nargs="?", help="the directory the left panel opens")
    parser.add_argument("right", nargs="?", help="the directory the right panel opens")
    parser.add_argument(
        "--theme", default=DEFAULT_THEME, metavar="NAME",
        help="a colour scheme from navigator/styles/themes (default: %(default)s)",
    )
    parser.add_argument(
        "--list-themes", action="store_true", help="print the theme names and exit",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    if args.list_themes:
        print("\n".join(theme_names()))
        return 0
    try:
        scheme = load_scheme(args.theme)
    except LookupError as exc:
        parser.error(str(exc))

    left = Path(args.left).expanduser().resolve() if args.left else Path.cwd()
    right = Path(args.right).expanduser().resolve() if args.right else left
    Navigator(left, right, scheme).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())