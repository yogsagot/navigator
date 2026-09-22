#!/usr/bin/env python3
"""Navigator -- a recreation of DOS Navigator for POSIX terminals.

The application entry point: ``python -m navigator``.  What is left here is the
command line, the terminal it hands to navkit, and the application hooks that
hold the keys meaning the same thing wherever the focus is.

Everything it paints lives in :mod:`navigator.widgets`, one module per screen,
and the sheet those screens resolve against in :mod:`navigator.scheme`.  The
split is not tidiness: this module is what the command runs, so it is already
in ``sys.modules`` as ``__main__`` and importing a widget *from* it would build
a second copy of everything in it.  A widget a document names has to be
importable by its own name, which is what ``manager.nml`` will need.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from importlib import metadata
from pathlib import Path

from navkit.application import Application
from navkit.capabilities import VGA_PALETTE, TerminalInfo
from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import tier_named
from navkit.stylesheet import Stylesheet
from navkit.terminal import Terminal, is_a_tty

from navigator import __version__
from navigator.scheme import DEFAULT_THEME, default_scheme, load_scheme, theme_names
from navigator.widgets.manager import Manager


class Navigator(Application):
    """The file manager application."""

    def __init__(
        self, left: Path, right: Path, scheme: Stylesheet | None = None, **kwargs
    ):
        scheme = scheme or default_scheme()
        kwargs.setdefault("title", "Navigator")
        self.manager = Manager(left, right, scheme)
        super().__init__(root=self.manager, **kwargs)

    async def on_stop(self) -> None:
        # The shell would otherwise outlive the terminal it was talking to.
        self.manager.console.stop()

    async def on_key(self, event: KeyEvent) -> bool:
        """Only the keys that mean the same thing wherever the focus is.

        An application hook runs before the widgets, which is what makes it
        the right place for exactly these and the wrong place for anything
        else: whatever is kept here is kept from the console, from the panels
        and from every dialog that has not been written yet.  Ctrl+O is the
        way in and out of the console, and F10 and Ctrl+Q are the way out of
        Navigator -- both of which have to work while a child program is
        eating every other keystroke.

        Everything else went to the widget that owns it: ``Console.on_key``
        for the console's scrollback and the child, ``Manager.on_key`` for
        moving about the panels and for Alt+X.
        """
        if event.matches("ctrl+o"):
            self.manager.toggle_console()
            return True
        if event.matches("f10", "ctrl+q"):
            self.exit()
            return True
        return False

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        manager = self.manager
        if manager.console_visible:
            if event.is_wheel and manager.console.contains(event.x, event.y):
                if event.button == "wheel_up":
                    manager.console.scroll_back()
                else:
                    manager.console.scroll_forward()
                return True
            return False
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


class PrintVersion(argparse.Action):
    """``--version``, printed verbatim.

    argparse's own ``version`` action runs the string through the help
    formatter, which word-wraps it to the terminal -- and the banner is mostly
    one long path, so on a narrow window it comes back broken across lines and
    cannot be copied out of a bug report.  Printing it directly is the whole
    of the difference.
    """

    def __init__(self, option_strings, dest, help=None):
        super().__init__(option_strings, dest, nargs=0, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        print(version_banner())
        parser.exit()


def version_banner() -> str:
    """What ``--version`` prints: the version, and *which copy* is running.

    The second half is the useful half.  Navigator can be installed three ways
    at once -- a system package under ``/usr/lib``, a pipx or ``pip --user``
    copy under ``~/.local``, and a checkout -- and ``~/.local/bin`` comes
    before ``/usr/bin`` on nearly every PATH, so the one that runs is often not
    the one that was just installed.  Printing the path turns that from a
    mystery into a glance, which is why ``pip --version`` has done it for
    years and why the format here follows it.

    The version itself prefers the distribution metadata over ``__version__``:
    they differ exactly when a checkout has been edited since it was
    installed, and metadata is absent precisely in the case where the source
    tree is the honest answer.
    """
    try:
        version = metadata.version("navigator-fm")
    except metadata.PackageNotFoundError:
        version = __version__
    here = Path(__file__).resolve().parent
    python = ".".join(str(n) for n in sys.version_info[:3])
    return f"nav {version} from {here} (python {python})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nav", description=__doc__)
    parser.add_argument("left", nargs="?", help="the directory the left panel opens")
    parser.add_argument("right", nargs="?", help="the directory the right panel opens")
    parser.add_argument(
        "--version", action=PrintVersion,
        help="print the version, and which copy of Navigator is running",
    )
    parser.add_argument(
        "--theme", default=DEFAULT_THEME, metavar="NAME",
        help="a colour scheme from navigator/styles/themes (default: %(default)s)",
    )
    parser.add_argument(
        "--list-themes", action="store_true", help="print the theme names and exit",
    )
    parser.add_argument(
        "--palette", choices=("dos", "terminal"), default=None,
        help="what a colour name in a theme means: the VGA register value DOS "
             "Navigator asked for (default), or whatever the terminal's own "
             "scheme paints for it",
    )
    parser.add_argument(
        "--glyphs", choices=("auto", "ascii", "unicode", "nerd"), default="auto",
        help="which characters the terminal's font can draw: `ascii' for plain "
             "+-| frames, `unicode' for box drawing, `nerd' to add a Nerd Font "
             "icon beside each name (default: detect)",
    )
    parser.add_argument(
        "--reprogram-palette", action="store_true",
        help="rewrite the terminal's sixteen colour registers to the DOS "
             "palette for as long as Navigator runs -- the only thing that "
             "helps on a terminal that names no other colours",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    if args.list_themes:
        print("\n".join(theme_names()))
        return 0
    try:
        scheme = load_scheme(args.theme)
    except LookupError as exc:
        parser.error(str(exc))

    # A theme that names its colours is transcribing a palette that left the
    # VGA registers alone, so `blue' means the value that adapter held and not
    # whatever this terminal calls blue -- which is why Navigator pins by
    # default where navkit, knowing nothing of DOS, does not.  Precedence runs
    # flag, then NAVKIT_PALETTE, then that default; `detect' handles the last
    # two, and an explicit flag is applied over its answer.
    info = TerminalInfo.detect(
        is_tty=is_a_tty(sys.stdin, sys.stdout), palette=VGA_PALETTE
    )
    if args.palette is not None:
        info = replace(
            info, palette=VGA_PALETTE if args.palette == "dos" else None
        )
    # Same three-step precedence for the character repertoire, and the same
    # reason for spelling it out: `detect' has already weighed NAVKIT_GLYPHS
    # against what it found, so the flag is applied over that answer.
    if args.glyphs != "auto":
        info = replace(info, glyphs=tier_named(args.glyphs, info.glyphs))
    terminal = Terminal(info=info, reprogram_palette=args.reprogram_palette)

    left = Path(args.left).expanduser().resolve() if args.left else Path.cwd()
    right = Path(args.right).expanduser().resolve() if args.right else left
    Navigator(left, right, scheme, terminal=terminal).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
