#!/usr/bin/env python3
"""Paint Navigator headless and write its screens out as screenshots.

Run it from the repository root::

    ./venv/bin/python tools/screenshot.py

It paints every scene in :data:`SCENES`.  The first, ``desktop``, is the
README's, and writes two things, both of them text:

- ``docs/screenshot.svg``, every cell in the colours the theme gives it, so
  the README can show the desktop the way a terminal does.  Neither GitHub nor
  PyPI will colour Markdown -- both strip ``style=`` and raw escapes, and
  GitHub ignores an ```` ```ansi ```` fence -- so an SVG made of ``<text>`` and
  ``<rect>`` is the closest a README gets to a terminal.
- the same screen as plain characters, written into ``README.md`` between the
  ``<!-- screenshot:begin -->`` and ``<!-- screenshot:end -->`` markers.
  Nothing outside the markers is touched.

Every other scene is one of Help's pictures (the ``navigator-help`` skill has
the rules), cropped to the thing it shows and written twice into
``docs/en/shots/``:

- ``NAME.svg``, which the page's Markdown names and GitHub shows;
- ``NAME.ans``, the same cells as text with SGR colours, which Navigator's
  own help window reads in the SVG's place (:func:`as_ansi` has the grammar,
  ``navigator/lib/help/ansi.py`` the reader) and ``cat`` shows in a terminal.

``--check`` writes nothing and exits 1 if anything would change, which is what
to run after a change to anything a scene paints.  ``--only NAME`` paints one
scene; ``--no-readme`` leaves the desktop out, which is what the test runs
(``tests/test_screenshot.py``): the desktop shows the version, so a release
makes it stale, and the suite a release runs must not fail on that.

``--language CODE`` paints the scenes in another catalogue's language -- a
right-to-left one (``he``, ``ar``) mirrored, as ``nav --language he`` shows
it.  The desktop then writes only ``docs/screenshot-CODE.svg`` (the README's
picture and text block stay the English scene), and Help's pictures go to
``docs/CODE/shots/``.

The screen is the real one: the application is constructed as ``nav``
constructs it and rendered into a :class:`~navkit.screen.ScreenBuffer`, with
what would make it differ between runs pinned -- the directory it lists
(built here, with fixed sizes), the clock, the free space under each panel,
the shell the console would otherwise fork, and every setting and the
database, new for each scene (:func:`paint`).  This is the golden test's recipe
(``tests/test_nav.py``), applied to a directory worth looking at, with the
About box (≡ > About) open over it -- so the picture carries the version, and
a release makes ``--check`` stale until the screenshot is regenerated.

The panels are drawn in the simple mode, not the shipped default
(``[panel_defaults] view_mode = detailed``): a decision, so the picture keeps
DN's classic two-column look -- a change of default panel mode does not
change the screenshot.

This is an asset pipeline, like ``palconv.py``: nothing under ``navigator/``
imports it.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
import tempfile
import unicodedata
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from navkit.bidi import has_rtl  # noqa: E402
from navkit.capabilities import FULL, VGA_PALETTE, TerminalInfo, rgb_of  # noqa: E402
from navkit.glyphs import GLYPHS_UNICODE  # noqa: E402
from navkit.events import KeyEvent  # noqa: E402
from navkit.screen import ScreenBuffer, char_width  # noqa: E402
from navkit.style import RESET_SGR, Style  # noqa: E402

SVG = ROOT / "docs" / "screenshot.svg"
README = ROOT / "README.md"
BEGIN, END = "<!-- screenshot:begin -->", "<!-- screenshot:end -->"
IMAGE_URL = "https://raw.githubusercontent.com/yogsagot/navigator/master/docs/screenshot.svg"
DOCS = ROOT / "docs"

# What the panels list.  Sizes are fixed so the size column is; nothing reads
# a date, but they are pinned anyway so the scene is the same scene on disk.
TREE: dict[str, int | None] = {
    "bin": None,
    "docs": None,
    "src": None,
    "tests": None,
    ".gitignore": 214,
    "LICENSE": 1071,
    "Makefile": 2318,
    "README.md": 7482,
    "config.nss": 4096,
    "navigator.log": 183_552,
    "pyproject.toml": 1904,
    "setup.cfg": 612,
}
SUBTREE: dict[str, int | None] = {
    "navigator": None,
    "navkit": None,
    "navml": None,
    "__init__.py": 0,
    "app.py": 12_847,
    "console.py": 9_311,
    "screen.py": 18_205,
    "widgets.py": 22_596,
}
PINNED_TIME = datetime(1999, 12, 31, 23, 59).timestamp()

# What the files a scene opens say: a viewer, an editor and a comparison have
# nothing to show of a file of NULs.  Each is padded or cut to the size
# ``TREE`` gives its file, so no picture of a panel changes with the text.
APP_PY = '''"""The application: one loop, one screen, a tree of widgets."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

FRAME = 1 / 60  # seconds between two paints, at most


@dataclass
class Event:
    """Something that happened: a key, a click, a resize."""

    name: str
    handled: bool = False


@dataclass
class Application:
    title: str = "Navigator"
    queue: list[Event] = field(default_factory=list)
    running: bool = False

    def post(self, event: Event) -> None:
        self.queue.append(event)

    async def run(self) -> int:
        self.running = True
        while self.running:
            for event in self.take():
                await self.dispatch(event)
            self.paint()
            await asyncio.sleep(FRAME)
        return 0

    def take(self) -> list[Event]:
        batch, self.queue = self.queue, []
        return batch

    async def dispatch(self, event: Event) -> None:
        if event.name == "quit":
            self.running = False
        event.handled = True

    def paint(self) -> None:
        print(f"{self.title}: {len(self.queue)} waiting")
'''
LICENSE_TEXT = '''Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
'''
TEXTS: dict[str, str] = {"src/app.py": APP_PY, "LICENSE": LICENSE_TEXT}
PROMPT = (
    b"\x1b[01;38;2;85;255;85mjuris@juris-dev\x1b[00;38;2;255;255;255m:"
    b"\x1b[01;38;2;85;85;255m~/development/navigator\x1b[00;38;2;255;255;255m$ "
)


class HeadlessTerminal:
    """The surface :class:`~navkit.application.Application` needs of a tty.

    ``tests/conftest.py`` has the same thing for the suite; a tool does not
    import from ``tests/``.
    """

    def __init__(self, width: int, height: int, info: TerminalInfo):
        self.info = info
        self.size = (width, height)
        self.is_tty = False
        self.input_fd = -1

    def start(self) -> None: ...
    def stop(self) -> None: ...
    def set_title(self, title: str) -> None: ...
    def read(self, size: int = 0) -> bytes: return b""
    def write(self, text: str) -> None: ...
    def flush(self) -> None: ...


def sized(text: str, size: int) -> bytes:
    """*text* as exactly *size* bytes: cut, or its lines said again as comments."""
    data = text.encode()
    filler = b"".join(b"# " + line + b"\n" for line in data.splitlines() if line.strip())
    while len(data) < size:
        data += b"\n" + filler
    data = data[:size]
    # Whole lines: what is left of a cut one is blanks.
    cut = data.rfind(b"\n") + 1
    return data[:cut] + b" " * (size - cut - 1) + b"\n" if cut < size else data


def pinned(*paths: Path) -> None:
    """*paths* (and what a stage wrote under them) dated as the rest is."""
    for path in paths:
        for each in (*path.rglob("*"), path) if path.is_dir() else (path,):
            os.utime(each, (PINNED_TIME, PINNED_TIME))


def populate(directory: Path) -> None:
    def fill(where: Path, entries: dict[str, int | None]) -> None:
        for name, size in entries.items():
            path = where / name
            if size is None:
                path.mkdir()
            else:
                path.write_bytes(b"\0" * size)
            os.utime(path, (PINNED_TIME, PINNED_TIME))

    fill(directory, TREE)
    fill(directory / "src", SUBTREE)
    for name, text in TEXTS.items():
        path = directory / name
        path.write_bytes(sized(text, path.stat().st_size))
        os.utime(path, (PINNED_TIME, PINNED_TIME))
    # The modes too: the umask's otherwise, and the Attributes column shows them.
    for path in directory.rglob("*"):
        os.chmod(path, 0o755 if path.is_dir() else 0o644)
    # Filling a directory moved its time again: the *Current file* line on
    # ``src``'s ``..`` shows it.
    for path in (directory / "src", directory):
        os.utime(path, (PINNED_TIME, PINNED_TIME))


# -- the scenes ---------------------------------------------------------------


@dataclass(frozen=True)
class Scene:
    """One picture: what is opened over the pinned desktop, and how much of
    the screen is kept."""

    name: str
    #: Opens what the picture shows, over the running application.  It answers
    #: the widget to crop to (with its shadow), a rectangle ``(x, y, width,
    #: height)`` of the screen, or None for the whole screen.
    #: A dialog is started with ``asyncio.create_task(dialog.execute(app))``
    #: rather than through its command, which would need a key or a menu
    #: walk; outside a dispatch, ``execute`` is content to be awaited, and
    #: the task is cancelled with the app.
    stage: Callable[[Any], Awaitable[Any]]
    size: tuple[int, int] = (80, 24)


async def _about(app: Any) -> None:
    from navigator.widgets.about_dialog import AboutDialog

    asyncio.create_task(AboutDialog().execute(app))
    return None


async def _make_directory(app: Any) -> Any:
    from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog

    dialog = MkdirDialog()
    asyncio.create_task(dialog.execute(app))
    return dialog


async def _until(condition: Callable[[], Any], timeout: float = 3.0) -> None:
    """Wait for *condition*: what a window reads on a thread has landed.
    A fixed sleep would be a picture of whatever had landed by then."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not condition():
        if loop.time() > deadline:
            raise TimeoutError("a scene waited for what never came")
        await asyncio.sleep(0.01)


def _placed(app: Any, window: Any, width: int, height: int) -> Any:
    """*window*, open on the desktop already, un-zoomed and centred at *width*
    by *height*: narrow enough for a help page where what it shows allows."""
    desktop = app.shell.desktop
    if getattr(window, "zoomed", False):
        window.toggle_zoom()
    # No narrower than the window says it can be: its captions' width, in
    # a language of longer ones.
    width = max(width, getattr(window, "min_width", 0))
    window.width, window.height = min(width, desktop.width), min(height, desktop.height)
    window.x, window.y = (desktop.width - window.width) // 2, (desktop.height - window.height) // 2
    return window


def _selection(app: Any, name: str) -> tuple[Any, list[Any]]:
    """The left panel with its cursor on *name*, and that entry as a selection."""
    panel = app.manager.left
    names = [entry.name for entry in panel.items]
    panel.cursor = names.index(name)
    return panel, [panel.items[panel.cursor]]


def _dialog(app: Any, dialog: Any) -> Any:
    asyncio.create_task(dialog.execute(app))
    return dialog


async def _copy(app: Any) -> Any:
    from navigator.widgets.file_ops.copy_dialog import CopyDialog

    panel, entries = _selection(app, "README.md")
    dialog = _dialog(app, CopyDialog(entries=entries, here=panel.location, other=None))
    # A place that is nobody's: the other panel's is the scratch directory.
    dialog.target.value = "/srv/backup/"
    return dialog


async def _erase(app: Any) -> Any:
    from navigator.widgets.file_ops.delete_dialog import DeleteDialog

    panel, entries = _selection(app, "navigator.log")
    return _dialog(app, DeleteDialog(entries=entries, here=panel.location, trash=False))


async def _create_archive(app: Any) -> Any:
    from navigator.widgets.file_ops.archive_dialog import ArchiveDialog, archive_dialog

    # Every type to be had, whatever is installed here: a type whose program
    # is missing (7z, rar, zstd) is greyed and named under the box, which
    # made the picture another one on a machine without them.
    archive_dialog.archive.format_missing = lambda kind: None
    # And the password to be had for a zip, which 7-Zip encrypts: without it
    # the line and its caption are greyed.
    archive_dialog.archive.can_encrypt = lambda kind: kind in (("7z", ""), ("zip", ""), ("rar", ""))

    panel, entries = _selection(app, "docs")
    return _dialog(app, ArchiveDialog(entries=entries, here=panel.location, directory="/srv/backup", stem="docs"))


async def _extract(app: Any) -> Any:
    from navigator.widgets.file_ops.extract_dialog import ExtractDialog

    return _dialog(app, ExtractDialog(here=Path("."), other="/srv/backup"))


#: What the archive scene's zip holds, each dated as the rest is.
ZIP_FILES: dict[str, str] = {
    "release/README.md": LICENSE_TEXT * 8,
    "release/LICENSE": LICENSE_TEXT,
    "release/bin/nav": "#!/bin/sh\nexec python3 -m navigator \"$@\"\n",
    "release/src/app.py": APP_PY,
    "release/src/screen.py": APP_PY * 3,
    "release/docs/manual.txt": LICENSE_TEXT * 12,
}


async def _open_archive(app: Any) -> Any:
    import zipfile

    from navigator.lib.drives import Location, archive

    path = Path("src/release.zip")
    with zipfile.ZipFile(path, "w") as zipped:
        for name, text in ZIP_FILES.items():
            info = zipfile.ZipInfo(name, date_time=datetime.fromtimestamp(PINNED_TIME).timetuple()[:6])
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zipped.writestr(info, text)
    pinned(path)
    drive = archive.open_archive(Location.of(path.resolve()))
    panel = app.manager.right
    panel.cycle_view_mode()  # detailed: what an archive's columns are for
    panel.location = drive.at("/release")
    await _until(lambda: not app.busy and any(entry.name == "README.md" for entry in panel.items))
    panel.cursor = [entry.name for entry in panel.items].index("README.md")
    await asyncio.sleep(0.1)
    return panel


async def _trash(app: Any) -> Any:
    from navigator.lib.file_ops import trash

    # A Trash of nobody's: the home one in the scene's own scratch directory,
    # which goes with it (the left panel listing it is not in the picture),
    # and no mount's (those are the machine's).
    data = Path(".data").resolve()
    os.environ["XDG_DATA_HOME"] = str(data)
    trash._mounts = lambda: []
    home = trash.home_trash()
    (home / "files").mkdir(parents=True)
    (home / "info").mkdir()
    for name, size, original in (
        ("draft.txt", 2_048, "/home/user/project/docs/draft.txt"),
        ("old-build", None, "/home/user/project/old-build"),
        ("photo.jpg", 284_211, "/home/user/Pictures/photo.jpg"),
        ("notes.md", 7_482, "/home/user/notes.md"),
        ("report.pdf", 1_310_720, "/home/user/Documents/report.pdf"),
    ):
        path = home / "files" / name
        if size is None:
            path.mkdir()
            (path / "main.o").write_bytes(b"\0" * 40_960)
        else:
            path.write_bytes(b"\0" * size)
        (home / "info" / f"{name}.trashinfo").write_text(trash.info_text(original, PINNED_TIME))
    # The modes too: the umask's otherwise, and the Attr column shows them.
    for path in (home / "files").rglob("*"):
        os.chmod(path, 0o755 if path.is_dir() else 0o644)
    pinned(home)
    manager = app.manager
    panel = manager.right
    panel.cycle_view_mode()
    await manager.open_trash(panel, focus=False)
    await _until(lambda: not app.busy and any(entry.name == "notes.md" for entry in panel.items))
    # On a file, so the line under the listing says where it came from.
    panel.cursor = [entry.name for entry in panel.items].index("notes.md")
    await asyncio.sleep(0.1)
    return panel


async def _find_file(app: Any) -> Any:
    from navigator.widgets.manager.find_file_dialog import FindFileDialog

    dialog = _dialog(app, FindFileDialog())
    dialog.mask.value = "*.py"
    dialog.text.value = "TODO"
    return dialog


async def _select_group(app: Any) -> Any:
    from navigator.widgets.manager.select_dialog import SelectDialog

    dialog = _dialog(app, SelectDialog(select=True, invert=False))
    dialog.mask.value = "*.py;*.md"
    return dialog


async def _compare_directories(app: Any) -> Any:
    from navigator.widgets.manager.compare_dialog import CompareDialog

    return _dialog(app, CompareDialog())


async def _viewer_find(app: Any) -> Any:
    from navigator.widgets.viewer.viewer_find_dialog import ViewerFindDialog

    dialog = _dialog(app, ViewerFindDialog())
    dialog.what.value = "error"
    return dialog


async def _editor_replace(app: Any) -> Any:
    from navigator.lib.editor.search import SearchData
    from navigator.widgets.editor.find_dialog import FindDialog

    # A record of its own: the editor's is kept for the session.
    dialog = _dialog(app, FindDialog(word="colour", replace=True, data=SearchData()))
    dialog.new.value = "color"
    return dialog


async def _calculator(app: Any) -> Any:
    from navigator.widgets.shell.calculator_window import CalculatorWindow

    window = app.shell.desktop.open(CalculatorWindow())
    window.place()
    window.take_keyboard()
    window.line.focus()
    for char in "2*(3+4)":
        app.post_event(KeyEvent(char, char))
    return window


def _calculator_face(mode: str, expression: str) -> Callable[[Any], Awaitable[Any]]:
    """The calculator on its *mode* face, *expression* typed on its line."""

    async def stage(app: Any) -> Any:
        from navigator.widgets.shell.calculator_window import CalculatorWindow

        window = app.shell.desktop.open(CalculatorWindow())
        window.set_mode(mode, focus=False, save=False)
        window.place()
        window.take_keyboard()
        window.line.focus()
        await asyncio.sleep(0.05)
        for char in expression:
            app.post_event(KeyEvent(char, char))
        return window

    return stage


#: The page the help window shows in its picture: written here, not read from
#: ``docs/``, so editing a help page does not make the picture stale.
HELP_PAGE = """# Help on help

Help is a window of pages about what Navigator does. `F1` opens it on the page
about what you are doing.

## Keys

| Key | What it does |
|---|---|
| `Tab`, `Shift+Tab` | Choose the next or the previous link |
| `Enter` | Follow the link |
| `Alt+F1` | Go back to the page before |
| `Shift+F1` | The contents |
| `Esc` | Close Help |

See [Panels](panels.md) and [The viewer](viewer.md) for more.
"""


async def _help_window(app: Any) -> Any:
    from navigator.lib.help import pages
    from navigator.widgets.help.help_window import HelpWindow

    docs = Path(".help").resolve()
    (docs / "en").mkdir(parents=True)
    (docs / "en" / "help.md").write_text(HELP_PAGE)
    pages.root = lambda: docs
    window = HelpWindow("help.md")
    asyncio.create_task(window.execute(app))
    viewer = window.viewer
    await asyncio.sleep(0.05)
    await _until(lambda: viewer.layout is not None and viewer._wanted is None)
    await asyncio.sleep(0.05)
    return window


async def _margins(app: Any) -> Any:
    from navigator.widgets.editor.margins_dialog import MarginsDialog

    return _dialog(app, MarginsDialog((0, 72, 4)))


async def _go_to_line(app: Any) -> Any:
    from navigator.widgets.editor.goto_line_dialog import GotoLineDialog
    from navigator.widgets.editor.goto_line_dialog import goto_line_dialog

    # The last line asked for is kept for the session: this picture's own.
    goto_line_dialog._last["text"] = "120"
    return _dialog(app, GotoLineDialog())


async def _calendar(app: Any) -> Any:
    from navigator.widgets.shell.calendar_window import CalendarWindow

    desktop = app.shell.desktop
    window = desktop.open(CalendarWindow())
    width, height = window.size()
    window.width, window.height = min(width, desktop.width), min(height, desktop.height)
    window.x, window.y = (desktop.width - window.width) // 2, (desktop.height - window.height) // 2
    window.take_keyboard()
    return window


# -- the wide ones: 76 to 78 columns, and their shadow -------------------------

#: A screen these fit with their shadow.  The help window draws a picture
#: wider than its page and scrolls sideways to the rest.
WIDE = (84, 30)


async def _multi_rename(app: Any) -> Any:
    from navigator.lib.file_ops import multirename
    from navigator.widgets.file_ops.multi_rename_dialog import MultiRenameDialog, multi_rename_dialog

    # The rule is kept for the session: this picture's own.
    multi_rename_dialog._session["rule"] = multirename.Rule()
    panel = app.manager.left
    items = [multirename.Item(entry.name, panel.location, mtime=PINNED_TIME)
             for entry in panel.items if not entry.is_dir and entry.name != ".."]
    dialog = _dialog(app, MultiRenameDialog(items, {panel.location: {item.name for item in items}}))
    dialog.name_mask.value = "[N]-[C]"
    dialog.digits.value = "2"
    return dialog


async def _link_manager(app: Any) -> Any:
    from navigator.lib.drives.profiles import Entry
    from navigator.widgets.drives.link_manager import LinkManagerDialog

    # Nobody's servers: the database's are the machine's.
    entries = [
        Entry("backup", "sftp", "files.example.org", "backup", 22, "/srv/backup"),
        Entry("web", "sftp", "www.example.org", "deploy", 2222, "/var/www"),
        Entry("build", "sftp", "build.example.org", "ci", 22, "/home/ci"),
    ]
    dialog = _dialog(app, LinkManagerDialog(entries, family="sftp"))
    await asyncio.sleep(0.05)
    # The first one chosen, so the lines say what a connection is made of.
    dialog._choose(0)
    return dialog


async def _connect(app: Any) -> Any:
    from navigator.widgets.drives.connect_dialog import ConnectDialog
    from navigator.widgets.drives.connect_dialog.connect_dialog import ConnectRequest

    # Nobody's server, and no recent connections: the database's are the machine's.
    request = ConnectRequest("sftp", "files.example.org", "backup", 22, "/srv/backup", "backup")
    return _dialog(app, ConnectDialog(request))


async def _host_key(app: Any) -> Any:
    from navigator.widgets.drives.host_key_query import HostKeyQuery

    return _dialog(app, HostKeyQuery(
        host="files.example.org", key_type="ssh-ed25519",
        fingerprint="SHA256:4rQ7uZ0mJ2kLwYbX9cVnT1aEoP3sDgF5hK8iU6yR2Ow",
    ))


async def _port_forwards(app: Any) -> Any:
    from navigator.lib.drives.forwards import Forward
    from navigator.widgets.drives.forwards_dialog import ForwardsDialog

    return _dialog(app, ForwardsDialog([
        Forward("L", 5432, "", "db.internal", 5432),
        Forward("L", 8080, "", "localhost", 80),
        Forward("R", 9000, "", "localhost", 3000),
        Forward("D", 1080),
    ]))


async def _saved_links(app: Any) -> Any:
    from navigator.lib.drives.profiles import Entry
    from navigator.widgets.drives.links_dialog import LinksDialog

    # Nobody's links: the database's are the machine's.
    return _dialog(app, LinksDialog([
        Entry("backup", "sftp", "files.example.org", "backup", 22, "/srv/backup"),
        Entry("web", "sftp", "www.example.org", "deploy", 2222, "/var/www"),
        Entry("mirror", "ftp", "ftp.example.org", "anonymous", 21, "/pub"),
        Entry("office", "smb", "nas.example.org", "user", 445, "/shared"),
        Entry("assets", "s3", "s3.amazonaws.com", "", 443, "/example-assets"),
    ]))


async def _settings(app: Any) -> Any:
    from navigator.widgets.setup.settings_dialog import SettingsDialog

    # Confirmations: a page with nothing of the machine on it.  The tabs
    # along the top, whatever ``[interface] settings_tabs`` says.
    return _dialog(app, SettingsDialog(tab="confirmations", side="top"))


async def _colors(app: Any) -> Any:
    from navigator.lib.appearance.palette import entry_values
    from navigator.widgets.setup.colors_dialog import ColorsDialog

    # The theme the picture is painted in, nothing applied as it changes.
    dialog = _dialog(app, ColorsDialog(entry_values(app.shell.stylesheet.variables)))
    await asyncio.sleep(0.05)
    # The file panel's group, by its place among the groups (the names are
    # the language's), the third of its items under the cursor.
    group = next(index for index, (name, _) in enumerate(dialog.groups_of) if name == "File Panel")
    dialog.groups.cursor = group
    await asyncio.sleep(0.05)
    dialog.items.cursor = 2
    await asyncio.sleep(0.05)
    return dialog


def _settings_page(tab: str) -> Callable[[Any], Awaitable[Any]]:
    """The Settings box open on *tab*'s page, as ``_settings`` is on Confirmations."""

    async def stage(app: Any) -> Any:
        from navigator.settings import SETTINGS
        from navigator.widgets.setup.settings_dialog import SettingsDialog
        from navigator.widgets.setup.settings_dialog.settings_dialog import PAGES

        # The page's sections at their defaults: ``paint()`` pins some away
        # from them (no option strips, no git letters, simple panels) for the
        # pictures of the panels, and the page would show the pins.
        pins = {section: {field.name: getattr(getattr(SETTINGS, section), field.name)
                          for field in getattr(SETTINGS, section).fields()} for section in PAGES[tab]}
        for section in PAGES[tab]:
            getattr(SETTINGS, section).reset()
        # Country's *Example* is now, written as the choices say: the clock's
        # pinned moment instead.
        import types

        from navigator.widgets.setup.country_page import country_page

        moment = datetime(2026, 1, 1, 12, 34).timestamp()
        country_page.time = types.SimpleNamespace(time=lambda: moment)
        dialog = _dialog(app, SettingsDialog(tab=tab, side="top"))
        await asyncio.sleep(0.05)
        # The pins back once the page has read the defaults: the panels
        # behind the box are the other pictures' panels.
        for section, values in pins.items():
            for name, value in values.items():
                setattr(getattr(SETTINGS, section), name, value)
        return dialog

    return stage


async def _key_bindings(app: Any) -> Any:
    from navigator.lib.config import keybindings
    from navigator.widgets.setup.key_bindings_dialog import KeyBindingsDialog

    # The keys the code binds, not what a keybindings.ini made of them.
    found = keybindings.sections(type(app))
    return _dialog(app, KeyBindingsDialog(found, {section.name: section.defaults() for section in found}))


# -- the windows ----------------------------------------------------------------

#: A window as wide as a help page on an 80-column terminal, shadow and all.
PAGE = (66, 18)


async def _viewer(app: Any, mode: str = "text") -> Any:
    from navigator.lib.config.file_history import open_viewer

    window = await open_viewer(app.shell.desktop, Path("src/app.py"), mode)
    _placed(app, window, *PAGE)
    if mode == "text":
        await asyncio.sleep(0.05)  # a paint, which is what starts the colouring
        await _until(lambda: window.viewer._lex_stop is None and window.viewer.lexer_name)
    return window


async def _viewer_hex(app: Any) -> Any:
    return await _viewer(app, "hex")


NOTES_MD = """# Release notes

Navigator now reads **Markdown** as a page, with headings, lists, tables
and `code` laid out for the screen.

- The viewer shows pictures on a terminal that can draw them.
- `F1` opens Help on the page about what you are doing.

| Key | What it does |
|---|---|
| `Shift+F3` | The data tree of a JSON or YAML file |
| `Ctrl+Q` | Quick view in the other panel's place |
"""

CONFIG_JSON = """{
  "name": "navigator",
  "version": "1.0.0",
  "panels": {"left": "/home/user/project", "right": "/srv/backup", "view": "detailed"},
  "viewer": {"wrap": true, "tab_size": 8, "encodings": ["utf-8", "cp437", "koi8-r"]},
  "editor": {"auto_indent": true, "backups": false},
  "servers": [
    {"name": "backup", "host": "files.example.org", "port": 22},
    {"name": "web", "host": "www.example.org", "port": 2222}
  ]
}
"""

SALES_CSV = """Region,Quarter,Units,Revenue,Manager
North,Q1,1204,48160.00,Alice Moreau
North,Q2,1388,55520.00,Alice Moreau
South,Q1,982,39280.00,Bruno Silva
South,Q2,1101,44040.00,Bruno Silva
East,Q1,1530,61200.00,Chen Wei
East,Q2,1612,64480.00,Chen Wei
West,Q1,876,35040.00,Dana Novak
West,Q2,944,37760.00,Dana Novak
"""


async def _markup_view(app: Any) -> Any:
    from navigator.lib.config.file_history import open_viewer

    path = Path("notes.md")
    path.write_text(NOTES_MD)
    pinned(path)
    window = await open_viewer(app.shell.desktop, path, "text")
    _placed(app, window, *PAGE)
    viewer = window.viewer
    if not viewer.rendered:
        viewer.toggle_rendered()
    await asyncio.sleep(0.05)
    await _until(lambda: viewer.rendering)
    return window


async def _data_tree(app: Any) -> Any:
    from navigator.widgets.viewer.struct_window.struct_window import open_tree

    path = Path("config.json")
    path.write_text(CONFIG_JSON)
    pinned(path)
    window = await open_tree(app.shell.desktop, path)
    tree = window.tree
    # Two branches open, the cursor on one of them.
    for name in ("panels", "servers"):
        tree.expand(next(node for node in tree.root.children() if node.name.startswith(name)))
    await asyncio.sleep(0.05)
    tree.select(next(node for node in tree.root.children() if node.name.startswith("panels")))
    await asyncio.sleep(0.05)
    return _placed(app, window, *PAGE)


async def _table_view(app: Any) -> Any:
    from navigator.widgets.viewer.db_window.db_window import open_csv

    path = Path("sales.csv")
    path.write_text(SALES_CSV)
    pinned(path)
    window = await open_csv(app.shell.desktop, path)
    await asyncio.sleep(0.05)
    await _until(lambda: not app.busy)
    return _placed(app, window, *PAGE)


async def _quick_view(app: Any) -> Any:
    # The text alone, not padded to the listing's size: the panel that lists
    # it is not in the picture.
    Path("LICENSE").write_text(LICENSE_TEXT)
    pinned(Path("LICENSE"))
    _selection(app, "LICENSE")
    manager = app.manager
    manager.toggle_quick_view()
    quick = manager.quick
    await asyncio.sleep(0.1)
    await _until(lambda: not app.busy)
    await asyncio.sleep(0.1)
    return quick


async def _filter_lines(app: Any) -> Any:
    from navigator.lib.viewer.lines import LinePattern
    from navigator.widgets.viewer.filter_lines_dialog import FilterLinesDialog

    return _dialog(app, FilterLinesDialog(last=LinePattern("error")))


async def _editor(app: Any) -> Any:
    from navigator.lib.config.file_history import open_editor

    window = await open_editor(app.shell.desktop, Path("src/app.py"))
    _placed(app, window, *PAGE)
    await asyncio.sleep(0.05)
    await _until(lambda: window.editor._lex_stop is None and window.editor._lexed > 0)
    return window


def _pin_tree() -> None:
    """The directory tree from the scratch directory, called ``/project``:
    from ``/`` it is the machine's directories down to a random name."""
    from navigator.widgets.tree.change_dir_dialog import change_dir_dialog
    from navigator.widgets.tree.directory_tree import directory_tree

    def root(hidden: bool = True, at: Any = None) -> Any:
        node = directory_tree.directory_node(Path("."), "/project", hidden=hidden)
        node.expanded = True
        return node

    def walk(top: Any, place: Any) -> tuple[list[str], list[list[Any]], dict[int, Any]]:
        # Below the scratch directory, however the place was spelled.
        names = [part for part in Path(os.path.relpath(getattr(place, "local", place))).parts if part != "."]
        levels, here = [], top.data
        for name in names:
            levels.append(directory_tree._subdirectories(directory_tree.directory_node(here, hidden=top.show_hidden)))
            here = here / name
        return names, levels, {}

    directory_tree.directory_root = change_dir_dialog.directory_root = root
    directory_tree._walk_down = walk


async def _tree_window(app: Any) -> Any:
    from navigator.widgets.tree.tree_window import TreeWindow

    _pin_tree()
    window = app.shell.desktop.open(TreeWindow(start=Path("src")))
    _placed(app, window, *PAGE)
    window.take_keyboard()
    await asyncio.sleep(0.05)
    # Asked again now that the window is up, as the Change directory box is:
    # the cursor the first walk placed is not kept.
    window.tree.show(Path("src"))
    await _until(lambda: window.tree.root is not None and window.tree.root.loaded
                 and window.tree.selected_node is not None and window.tree.selected_node.name == "src")
    # Opened a level, so the picture shows a branch.
    window.tree.expand(window.tree.selected_node)
    await _until(lambda: window.tree.selected_node.loaded)
    await asyncio.sleep(0.05)
    return window


async def _tree_panel(app: Any) -> Any:
    _pin_tree()
    manager = app.manager
    tree = manager.tree
    tree.reload()  # the root it was made with is the machine's
    manager.toggle_tree()
    await _until(lambda: tree.root.loaded and len(tree._counts) > 0)
    return tree


async def _change_directory(app: Any) -> Any:
    from navigator.widgets.tree.change_dir_dialog import ChangeDirDialog

    _pin_tree()
    dialog = _dialog(app, ChangeDirDialog(start=Path("src")))
    await asyncio.sleep(0.05)
    # Asked again now that the box is up: the walk of four directories is
    # back before it is, and the cursor it placed is not kept.
    dialog._show(Path("src"))
    await _until(lambda: dialog.tree.selected_node is not None and dialog.tree.selected_node.name == "src")
    return dialog


#: Two versions of one directory, for the comparisons: what differs is one
#: file changed, one only on the left and one only on the right.
NOTES_OLD = "Release notes\n\n- The viewer shows pictures.\n- Copy asks before it overwrites.\n- F1 opens Help.\n"
NOTES_NEW = ("Release notes\n\n- The viewer shows pictures and tables.\n- Copy asks before it overwrites.\n"
             "- F1 opens Help on the page about what you are doing.\n- Ctrl+F5 sizes the Help window.\n")


def _two_versions() -> tuple[Path, Path]:
    old, new = Path("docs/old"), Path("docs/new")
    for where, notes, extra in ((old, NOTES_OLD, "todo.txt"), (new, NOTES_NEW, "keys.txt")):
        where.mkdir(parents=True)
        (where / "notes.txt").write_text(notes)
        (where / "readme.txt").write_text("The same on both sides.\n")
        (where / extra).write_text("Only here.\n")
    pinned(Path("docs"))
    # The changed file is the newer one on the right.
    os.utime(new / "notes.txt", (PINNED_TIME + 3600, PINNED_TIME + 3600))
    return old, new


async def _synchronize(app: Any) -> Any:
    from navigator.lib.file_ops import dirsync
    from navigator.lib.file_ops.dircompare import CompareRequest
    from navigator.widgets.manager.sync_window import SyncWindow

    old, new = _two_versions()
    request = CompareRequest(window=True)
    SyncWindow.tree_view = False
    window = SyncWindow(manager=app.manager, left=old, right=new, request=request,
                        rows=dirsync.walk(old, new, request), options=dirsync.SyncOptions())
    app.shell.desktop.open(window)
    window.take_keyboard()
    # All but the screen's width, so its shadow is in the picture.
    return _placed(app, window, 76, 14)


async def _compare_files(app: Any) -> Any:
    from navigator.widgets.viewer.diff_window import open_diff

    old, new = _two_versions()
    await open_diff(app.shell.desktop, old / "notes.txt", new / "notes.txt")
    window = app.shell.desktop.active_window
    return _placed(app, window, *PAGE)


# -- menus and lists --------------------------------------------------------------


def _popup(app: Any) -> Any:
    from navml.widgets.menu.popup_menu import PopupMenu

    return next((child for child in app.root.children if isinstance(child, PopupMenu)), None)


async def _user_menu(app: Any) -> Any:
    from navigator.lib.config import usermenu

    # The menu Navigator ships, not this user's, nor one in a directory above.
    shipped = ROOT / "navigator" / "assets" / "menu.ini"
    usermenu.find_menu = lambda start, want_global=False: (shipped, True)
    asyncio.create_task(app.shell.user_menu())
    await _until(lambda: _popup(app) is not None and _popup(app).boxes)
    return _popup(app).boxes[-1]


async def _window_list(app: Any) -> Any:
    from navigator.lib.config.file_history import open_editor, open_viewer
    from navigator.widgets.shell.calculator_window import CalculatorWindow
    from navml.widgets.window_manager import WindowManagerDialog

    desktop = app.shell.desktop
    desktop.open(CalculatorWindow()).place()
    await open_viewer(desktop, Path("LICENSE"), "text")
    await open_editor(desktop, Path("src/app.py"))
    return _dialog(app, WindowManagerDialog(desktop=desktop))


async def _command_palette(app: Any) -> Any:
    from navigator.widgets.shell.command_palette import CommandPalette

    from navigator.widgets.shell.command_palette import command_palette

    behind = app.focused
    # The first letters of F5's command as this language calls it: "copy".
    title = next(entry.title for entry in command_palette.gather(app, behind) if entry.key == "F5")
    dialog = _dialog(app, CommandPalette(behind=behind))
    await asyncio.sleep(0.05)
    for char in "".join(char for char in title if char.isalnum())[:4].lower():
        app.post_event(KeyEvent(char, char))
    return dialog


async def _file_dialog(app: Any) -> Any:
    from navml.widgets.dialog.file_dialog import FileDialog

    dialog = _dialog(app, FileDialog(directory="."))
    await asyncio.sleep(0.05)
    # Where it is: the scratch directory's random path otherwise.
    dialog.info.path = "/home/user/project/*"
    return dialog


async def _completion(app: Any) -> Any:
    from navigator.lib.system.subshell import CompletionsReady

    # The shell's answer to Tab, without a shell: the scene has none.
    shell = app.shell
    line = shell.command_line
    line.value, line.cursor = "cat s", 5
    shell.completions_ready(CompletionsReady("cat s", 5, 4, ("setup.cfg", "src/")))
    await _until(lambda: shell._completion_list is not None)
    await asyncio.sleep(0.05)
    box = shell._completion_list
    ox, oy = line.offset()
    # The list and the line it hangs over, the prompt's width and a little
    # more -- the whole width on a mirrored screen, where the list is on the
    # other side of a line that is typed left to right all the same.
    width = app.shell.width if app.rtl else 60
    return (0, box.y, width, oy + line.y + 1 - box.y)


#: What the console shows: two commands typed at ``PROMPT`` and their output,
#: as a shell would have written them.
CONSOLE_OUTPUT = (
    PROMPT + b"ls -l\r\n"
    b"total 236\r\n"
    b"drwxr-xr-x 2 user users   4096 Dec 31  1999 \x1b[01;34mbin\x1b[0m\r\n"
    b"drwxr-xr-x 4 user users   4096 Dec 31  1999 \x1b[01;34mdocs\x1b[0m\r\n"
    b"-rw-r--r-- 1 user users   1071 Dec 31  1999 LICENSE\r\n"
    b"-rw-r--r-- 1 user users   2318 Dec 31  1999 Makefile\r\n"
    b"-rw-r--r-- 1 user users 183552 Dec 31  1999 navigator.log\r\n"
    b"-rw-r--r-- 1 user users   7482 Dec 31  1999 README.md\r\n"
    b"drwxr-xr-x 6 user users   4096 Dec 31  1999 \x1b[01;34msrc\x1b[0m\r\n"
    + PROMPT + b"git status --short\r\n"
    b" \x1b[31mM\x1b[0m README.md\r\n"
    b" \x1b[31mM\x1b[0m src/app.py\r\n"
    b"\x1b[31m??\x1b[0m navigator.log\r\n"
)


async def _console(app: Any) -> Any:
    shell = app.shell
    shell.console.screen.feed(CONSOLE_OUTPUT)
    shell.console._changed()
    shell.toggle_console()
    await asyncio.sleep(0.1)
    return None


async def _command_window(app: Any) -> Any:
    from navigator.widgets.shell.terminal_view import TerminalView
    from navigator.widgets.shell.terminal_window import TerminalWindow

    # No ssh run: what it would have written, fed to the window's screen.
    TerminalView.start = lambda self: None
    window = app.shell.desktop.open(TerminalWindow("ssh backup@files.example.org"))
    _placed(app, window, *PAGE)
    window.take_keyboard()
    await asyncio.sleep(0.05)
    window.view.screen.feed(
        b"Linux files 6.12.0-amd64 #1 SMP Debian x86_64\r\n\r\n"
        b"Last login: Fri Dec 31 23:59:00 1999 from 192.0.2.10\r\n"
        b"\x1b[01;32mbackup@files\x1b[0m:\x1b[01;34m~\x1b[0m$ df -h /srv\r\n"
        b"Filesystem      Size  Used Avail Use% Mounted on\r\n"
        b"/dev/sdb1       1.8T  1.1T  644G  64% /srv\r\n"
        b"\x1b[01;32mbackup@files\x1b[0m:\x1b[01;34m~\x1b[0m$ "
    )
    window.view._changed()
    await asyncio.sleep(0.05)
    return window


async def _command_history(app: Any) -> Any:
    from navigator.widgets.shell.command_history_dialog import CommandHistoryDialog
    from navigator.widgets.shell.command_line.command_line import HISTORY_ID
    from navml.history import HISTORY

    for command in ("make test", "git status --short", "ls -l", "grep -rn TODO src",
                    "python -m navigator", "git log --oneline -5"):
        HISTORY.add(HISTORY_ID, command)
    HISTORY.pin(HISTORY_ID, "make test")
    return _dialog(app, CommandHistoryDialog())


# -- more dialogs -----------------------------------------------------------------

BACKUP = Path("/srv/backup")


async def _checksums(app: Any) -> Any:
    from navigator.widgets.file_ops.calculate_checksums_dialog import CalculateChecksumsDialog

    return _dialog(app, CalculateChecksumsDialog(directory_name="docs"))


async def _links(app: Any) -> Any:
    from navigator.widgets.file_ops.link_dialog import LinkDialog

    panel, entries = _selection(app, "README.md")
    return _dialog(app, LinkDialog(entries=entries, here=panel.location, other=BACKUP,
                                   relative=True, hard=False, can_hard=True))


async def _split(app: Any) -> Any:
    from navigator.widgets.file_ops.split_dialog import SplitDialog

    panel, _ = _selection(app, "navigator.log")
    dialog = _dialog(app, SplitDialog(name="navigator.log", here=panel.location, other=BACKUP))
    dialog.size.value = "64K"
    return dialog


async def _encryption(app: Any) -> Any:
    from navigator.lib.file_ops import encrypt
    from navigator.widgets.file_ops.encrypt_dialog import EncryptDialog

    # Both programs to be had, whatever is installed here.
    encrypt.available = lambda: encrypt.TOOLS
    return _dialog(app, EncryptDialog())


async def _file_attributes(app: Any) -> Any:
    from navigator.lib.file_ops import fileattr
    from navigator.widgets.file_ops.attr_dialog import AttrDialog

    panel, entries = _selection(app, "README.md")
    # What the dialog would ask the disk and the user database: nobody's.
    moment = int(PINNED_TIME)
    status = os.stat_result((0o100644, 0, 0, 1, 1000, 1000, 7482, moment, moment, moment))
    survey = fileattr.Survey(mode=0o644, uid=1000, gid=1000, mtime=PINNED_TIME, files=1, single=status,
                             xattrs_supported=True, flags_supported=True)
    facts = {
        "survey": survey, "user": "user", "users": ["user"], "can_chown_user": False,
        "group": "users", "groups": ["users", "staff"], "can_chown_group": True,
        "all_users": [], "all_groups": [], "names": {},
        "can_xattr": True, "can_flags": True, "can_chmod": True, "can_elevate": False,
    }
    return _dialog(app, AttrDialog(entries=entries, here=panel.location, facts=facts))


async def _uu_encode(app: Any) -> Any:
    from navigator.widgets.file_ops.uu_encode_dialog import UUEncodeDialog

    return _dialog(app, UUEncodeDialog(source=Path("README.md"), other=BACKUP))


async def _convert_text(app: Any) -> Any:
    from navigator.widgets.file_ops.convert_text_dialog import ConvertTextDialog

    return _dialog(app, ConvertTextDialog())


async def _filter(app: Any) -> Any:
    from navigator.lib.file_ops.advfilter import extensions
    from navigator.widgets.manager.filter_dialog import FilterDialog

    masks = extensions(app.manager.left.items)
    dialog = _dialog(app, FilterDialog(masks, 0))
    dialog.masks.marks = frozenset({masks.index("*.md"), masks.index("*.toml")})
    return dialog


async def _columns_setup(app: Any) -> Any:
    from navigator.widgets.manager.columns_dialog import ColumnsDialog

    return _dialog(app, ColumnsDialog(frozenset({"size", "date"})))


async def _make_list(app: Any) -> Any:
    from navigator.widgets.manager.make_list_dialog import MakeListDialog

    dialog = _dialog(app, MakeListDialog())
    dialog.action.value = "gzip -9 !.!"
    return dialog


async def _character_table(app: Any) -> Any:
    from navigator.widgets.shell.unicode_chart import UnicodeChart, unicode_chart

    dialog = _dialog(app, UnicodeChart(glyphs=GLYPHS_UNICODE))
    await asyncio.sleep(0.05)
    await _until(lambda: dialog.nerd in unicode_chart._indexes, timeout=10)
    return dialog


# -- what is the machine's, made up ---------------------------------------------
#
# Each of these replaces the function its window asks the machine through
# with one that answers the same thing everywhere -- the function its test
# replaces (``tests/test_processes.py`` and so on).


async def _process_list(app: Any) -> Any:
    from navigator.lib.system import processes
    from navigator.lib.system.processes import Process
    from navigator.widgets.shell.process_window import ProcessWindow

    mib = 1 << 20
    rows = [
        Process(1, 0, 0, "root", "S", 1, 12 * mib, 0, 0, 1, "systemd", "/sbin/init", cpu=0.0),
        Process(412, 1, 0, "root", "S", 1, 6 * mib, 0, 0, 2, "cron", "/usr/sbin/cron -f", cpu=0.0),
        Process(655, 1, 0, "root", "S", 3, 9 * mib, 0, 0, 3, "sshd", "sshd: /usr/sbin/sshd -D", cpu=0.0),
        Process(1204, 1, 1000, "user", "S", 1, 8 * mib, 0, 0, 4, "bash", "-bash", cpu=0.0),
        Process(1377, 1204, 1000, "user", "R", 4, 64 * mib, 0, 0, 5, "nav", "python -m navigator", cpu=3.1),
        Process(1502, 1204, 1000, "user", "S", 12, 310 * mib, 0, 0, 6, "make", "make -j4 test", cpu=41.5),
        Process(1519, 1502, 1000, "user", "R", 1, 122 * mib, 0, 0, 7, "pytest", "python -m pytest -q", cpu=97.8),
        Process(1620, 1, 33, "www-data", "S", 8, 48 * mib, 0, 0, 8, "nginx", "nginx: worker process", cpu=0.4),
    ]
    processes.Sampler.__call__ = lambda self: list(rows)
    window = app.shell.desktop.open(ProcessWindow())
    # Whose they are: the rows of user 1000 are *yours*.
    window.uid = window.processes.uid = 1000
    window.take_keyboard()
    await _until(lambda: window.processes.items)
    window.reload()
    await asyncio.sleep(0.1)
    return _placed(app, window, 76, 16)


async def _services(app: Any) -> Any:
    from navigator.lib.system import services
    from navigator.lib.system.services.common import Unit
    from navigator.settings import SETTINGS
    from navigator.widgets.shell.service_window import ServiceWindow

    units = [
        Unit("cron.service", "loaded", "active", "running", "enabled", "Regular background program processing"),
        Unit("cups.service", "loaded", "inactive", "dead", "disabled", "CUPS Scheduler"),
        Unit("nginx.service", "loaded", "active", "running", "enabled", "A high performance web server"),
        Unit("postgresql.service", "loaded", "failed", "failed", "enabled", "PostgreSQL RDBMS"),
        Unit("ssh.service", "loaded", "active", "running", "enabled", "OpenBSD Secure Shell server"),
        Unit("systemd-timesyncd.service", "loaded", "active", "running", "enabled", "Network Time Synchronization"),
        Unit("ufw.service", "loaded", "active", "exited", "enabled", "Uncomplicated firewall"),
    ]
    # The manager too, before the window asks which it is: the machine's otherwise.
    SETTINGS.services.manager = "systemd"
    services.gather = lambda user=False, all_types=False: list(units)
    window = app.shell.desktop.open(ServiceWindow())
    window.take_keyboard()
    await _until(lambda: window.units.items)
    return _placed(app, window, 76, 16)


async def _system_monitor(app: Any) -> Any:
    from navigator.lib.system import monitor
    from navigator.lib.system.monitor import Chip, Cpu, Memory, Snapshot, Temperature
    from navigator.widgets.shell.monitor_window import MonitorWindow, monitor_window

    gib = 1 << 30
    shown = Snapshot(
        Cpu(-1, 37.0),
        (Cpu(0, 62.0, 3400.0), Cpu(1, 18.0, 2200.0), Cpu(2, 55.0, 3400.0), Cpu(3, 13.0, 1800.0)),
        Memory(16 * gib, 9 * gib, 4 * gib, 4 * gib, 3 * gib, 11 * gib, 12 * gib),
        (Chip("k10temp", "", (Temperature("Tctl", 48.0), Temperature("Tccd1", 52.0, 70.0, 90.0))),),
    )
    monitor.Monitor.__call__ = lambda self: shown
    monitor_window.processors = lambda: 4
    window = app.shell.desktop.open(MonitorWindow())
    window.take_keyboard()
    await _until(lambda: window._shape is not None and not app.busy)
    await asyncio.sleep(0.1)
    return window


async def _system_information(app: Any) -> Any:
    from navigator.lib.system.sysinfo import SystemFacts
    from navigator.widgets.shell.system_info_dialog import SystemInfoDialog

    facts = SystemFacts(
        board=[("Machine type", "Example Works Model 7"), ("CPU", "Example 4-Core Processor"), ("CPUs", "4")],
        disks=[("sda", "500 GB"), ("nvme0n1", "1 TB")],
        memory=[("Total", "16 GB"), ("Available", "9 GB"), ("Swap", "4 GB")],
        other=[("OS", "Debian GNU/Linux 13"), ("Kernel", "6.12.0"), ("Host", "example"), ("Up", "3 days")],
    )
    return _dialog(app, SystemInfoDialog(facts))


async def _environment(app: Any) -> Any:
    from navigator.widgets.shell.environment_dialog import EnvironmentDialog

    return _dialog(app, EnvironmentDialog({
        "EDITOR": "vi", "HOME": "/home/user", "LANG": "en_US.UTF-8", "PAGER": "less",
        "PATH": "/usr/local/bin:/usr/bin:/bin", "SHELL": "/bin/bash", "TERM": "xterm-256color", "USER": "user",
    }))


async def _volumes(app: Any) -> Any:
    from navigator.lib.system import desktop, volumes
    from navigator.lib.system.volumes import Volume
    from navigator.widgets.shell.volumes_window import VolumesWindow

    gib = 1 << 30
    rows = [
        Volume("system", "ext4", "/", "/dev/sda2", 100 * gib, 40 * gib),
        Volume("home", "ext4", "/home", "/dev/sda3", 400 * gib, 212 * gib),
        Volume("STICK", "vfat", "/media/user/STICK", "/dev/sdb1", 16 * gib, 9 * gib),
    ]
    volumes.gather_all = lambda *args, **kwargs: list(rows)
    # No Mount, Unmount or Eject: whether there is a program for them is the machine's.
    desktop.volume_program = lambda: None
    window = app.shell.desktop.open(VolumesWindow())
    window.take_keyboard()
    await _until(lambda: window.volumes.items)
    return window


async def _directory_sizes(app: Any) -> Any:
    from navigator.lib.file_ops import dirusage
    from navigator.lib.file_ops.dirusage import UsageNode
    from navigator.widgets.shell.usage_window import UsageWindow

    # A tree written out, not read: what a file takes on the disk is the
    # file system's, and a directory's own size too.
    def tree(name: str, entries: dict[str, Any], parent: Any = None) -> Any:
        node = UsageNode(name, is_dir=True, size=4096, usage=4096, parent=parent)
        for child_name, value in entries.items():
            if isinstance(value, dict):
                child = tree(child_name, value, node)
            else:
                child = UsageNode(child_name, size=value, usage=-(-value // 4096) * 4096, parent=node)
            node.children.append(child)
            size, usage, items = child.counted()
            node.size, node.usage, node.items = node.size + size, node.usage + usage, node.items + items
        return node

    made = tree(".", {
        "src": {"navigator": {"panel.py": 412_000, "viewer.py": 268_000, "editor.py": 301_000},
                "navkit": {"screen.py": 96_000, "widget.py": 142_000}, "app.py": 12_847},
        "docs": {"manual.pdf": 2_400_000, "screenshot.svg": 181_000},
        "tests": {"test_panel.py": 88_000, "test_viewer.py": 64_000},
        "navigator.log": 183_552, "README.md": 7_482, "LICENSE": 1_071,
    })
    dirusage.scan = lambda location, job=None, **kwargs: made
    window = app.shell.desktop.open(UsageWindow(start=Path("."), manager=app.manager))
    window.take_keyboard()
    await _until(lambda: window.tree is not None and not window.scanning)
    window.title = "/home/user/project"
    return _placed(app, window, *PAGE)


async def _bookmarks(app: Any) -> Any:
    from navigator.lib.config import bookmarks

    # Directories every machine has, and no mounts: those are this one's.
    bookmarks.mounted_places = lambda *args, **kwargs: []
    for place in ("/etc", "/usr/share", "/var/log", "/tmp"):
        bookmarks.add_bookmark(Path(place))
    manager = app.manager
    asyncio.create_task(manager.choose_bookmark(manager.left, side="left", focus=False))
    await _until(lambda: _popup(app) is not None and _popup(app).boxes)
    return _popup(app).boxes[-1]


async def _game(app: Any) -> Any:
    from navigator.lib.utilities import tetris
    from navigator.widgets.game.game_window import GameWindow
    from navigator.widgets.game.game_window.game_window import HEIGHT, WIDTH

    desktop = app.shell.desktop
    window = desktop.open(GameWindow())
    width, height = min(WIDTH, desktop.width), min(HEIGHT, desktop.height)
    window.locate((desktop.width - width) // 2, (desktop.height - height) // 2, width, height)
    window.glass.focus()
    game = window.game
    # The same figures every time, a few of them down already, and none falling
    # while the picture is taken.
    game.rng.seed(7)
    game.new_game()
    for move in (-4, 3, -1, 5, -3):
        for _ in range(abs(move)):
            game.move(1 if move > 0 else -1)
        game.drop()
        game.fall()  # set down, and the next one in
    for _ in range(6):
        game.fall()
    game.tick = lambda hundredths: False
    return window


async def _panel_detailed(app: Any) -> Any:
    panel, _ = _selection(app, "README.md")
    panel.cycle_view_mode()
    return panel


async def _panel(app: Any) -> Any:
    panel, _ = _selection(app, "README.md")
    return panel


async def _info_panel(app: Any) -> Any:
    from navigator.lib.system import diskinfo

    # The disk, the machine and the file under the cursor, made up: each is
    # this machine's otherwise.
    gib = 1 << 30
    diskinfo.gather = lambda directory, **kwargs: diskinfo.DiskFacts(
        total=500 * gib, free=384 * gib, mount="/home", device="/dev/sda3", fs_type="ext4", label="home",
        memory_total=16 * gib, memory_available=9 * gib, memory_navigator=64 << 20,
    )
    diskinfo.stat_file = lambda path, name: diskinfo.FileFacts(
        atime=PINNED_TIME, ctime=PINNED_TIME, nlink=1, inode=1048577, mime="text/markdown",
    )
    _selection(app, "README.md")
    manager = app.manager
    manager.switch_view(manager.info)
    info = manager.info
    await _until(lambda: info.facts is not None and not app.busy)
    await asyncio.sleep(0.1)
    return info


async def _miller(app: Any) -> Any:
    from navigator.lib.drives import Location

    # Two levels down, so no column is of the scratch directory's parent
    # (the machine's /tmp) or titled with its random name; a file of text
    # under the cursor for the preview.
    navkit = Path("src/navkit")
    for name, text in (("screen.py", APP_PY), ("widget.py", APP_PY), ("events.py", LICENSE_TEXT)):
        (navkit / name).write_text(text)
    pinned(navkit)
    manager = app.manager
    manager.toggle_miller(Location.of(navkit.resolve()), "widget.py")
    await asyncio.sleep(0.2)
    await _until(lambda: not app.busy)
    await asyncio.sleep(0.1)
    # The columns, not the command line under them: its prompt is the
    # scratch directory's.
    miller = manager.miller
    ox, oy = miller.offset()
    return (ox + miller.x, oy + miller.y, miller.width, miller.height)


async def _find_duplicates(app: Any) -> Any:
    from navigator.widgets.manager.duplicates_dialog import DuplicatesDialog

    dialog = _dialog(app, DuplicatesDialog())
    dialog.mask.value = "*.jpg;*.png"
    return dialog


async def _panelize(app: Any) -> Any:
    from navigator.widgets.manager.panelize_dialog import PanelizeDialog

    return _dialog(app, PanelizeDialog(command="git ls-files --modified"))


async def _directory_history(app: Any) -> Any:
    from navigator.widgets.manager.dir_history_dialog import DirHistoryDialog
    from navigator.widgets.manager.dir_history_dialog.dir_history_dialog import HISTORY_ID
    from navml.history import HISTORY

    for place in ("/etc", "/var/log", "/home/user/project/src", "/home/user/project", "/usr/share/doc"):
        HISTORY.add(HISTORY_ID, place)
    return _dialog(app, DirHistoryDialog())


async def _file_menu(app: Any) -> Any:
    # By its place on the bar, not by Alt+F: the letter is the language's.
    menu = app.shell.menu
    menu.open(menu.entries().index(menu.file), drop=True)
    await asyncio.sleep(0.1)
    box = app.modal.boxes[-1]
    ox, oy = box.offset()
    # The bar's row over the box, as far as the box and its shadow reach.
    return (0, 0, ox + box.x + box.width + 2, oy + box.y + box.height + 1)


#: The first is the README's and is written where the README wants it; the
#: rest are Help's.  A Help scene shows nothing that changes between runs or
#: releases (no version, no date that is not pinned), and is cropped to what
#: it explains.  One wider than the help window's page (68 columns on an
#: 80-column terminal) is drawn all the same and scrolled to sideways, so
#: wide is for what cannot be narrower: the four boxes of 76 to 78 columns.
SCENES: tuple[Scene, ...] = (
    Scene("desktop", _about),
    Scene("make-directory", _make_directory),
    Scene("copy", _copy),
    Scene("erase", _erase),
    Scene("create-archive", _create_archive),
    Scene("find-file", _find_file),
    Scene("select-group", _select_group),
    Scene("compare-directories", _compare_directories),
    Scene("viewer-find", _viewer_find),
    Scene("editor-replace", _editor_replace),
    Scene("calculator", _calculator),
    Scene("calendar", _calendar),
    Scene("multi-rename", _multi_rename, size=WIDE),
    Scene("link-manager", _link_manager, size=WIDE),
    Scene("settings", _settings, size=WIDE),
    Scene("colors", _colors, size=(80, 30)),
    Scene("settings-system", _settings_page("system"), size=WIDE),
    Scene("settings-startup", _settings_page("startup"), size=WIDE),
    Scene("settings-interface", _settings_page("interface"), size=WIDE),
    Scene("settings-savers", _settings_page("savers"), size=WIDE),
    Scene("settings-country", _settings_page("country"), size=WIDE),
    Scene("settings-editor-viewer", _settings_page("editor_viewer"), size=WIDE),
    Scene("settings-viewer-types", _settings_page("viewer_types"), size=WIDE),
    Scene("settings-file-manager", _settings_page("file_manager"), size=WIDE),
    Scene("settings-drive-info", _settings_page("drive_info"), size=WIDE),
    Scene("settings-panel-defaults", _settings_page("panel_defaults"), size=WIDE),
    Scene("settings-column-defaults", _settings_page("column_defaults"), size=WIDE),
    Scene("settings-highlight-groups", _settings_page("highlight_groups"), size=WIDE),
    Scene("settings-remote", _settings_page("remote"), size=WIDE),
    Scene("settings-tools", _settings_page("tools"), size=WIDE),
    Scene("key-bindings", _key_bindings, size=WIDE),
    Scene("panel", _panel),
    Scene("panel-detailed", _panel_detailed, size=(120, 24)),
    Scene("viewer", _viewer),
    Scene("viewer-hex", _viewer_hex),
    Scene("editor", _editor),
    Scene("tree-panel", _tree_panel),
    Scene("change-directory", _change_directory),
    Scene("synchronize", _synchronize),
    Scene("compare-files", _compare_files),
    Scene("user-menu", _user_menu),
    Scene("window-list", _window_list),
    Scene("command-palette", _command_palette),
    Scene("file-dialog", _file_dialog),
    Scene("completion", _completion),
    Scene("checksums", _checksums),
    Scene("links", _links),
    Scene("split", _split),
    Scene("encryption", _encryption),
    Scene("file-attributes", _file_attributes),
    Scene("uu-encode", _uu_encode),
    Scene("convert-text", _convert_text),
    Scene("filter", _filter),
    Scene("columns-setup", _columns_setup),
    Scene("make-list", _make_list),
    Scene("character-table", _character_table),
    Scene("process-list", _process_list),
    Scene("services", _services),
    Scene("system-monitor", _system_monitor, size=(80, 34)),
    Scene("system-information", _system_information),
    Scene("environment", _environment),
    Scene("volumes", _volumes),
    Scene("directory-sizes", _directory_sizes),
    Scene("bookmarks", _bookmarks),
    Scene("game", _game, size=(80, 30)),
    # Taller than the rest: at 24 rows the File menu is cut and scrolls.
    Scene("file-menu", _file_menu, size=(80, 34)),
    Scene("info-panel", _info_panel, size=(80, 30)),
    Scene("miller", _miller),
    Scene("find-duplicates", _find_duplicates),
    Scene("panelize", _panelize),
    Scene("directory-history", _directory_history),
    Scene("markup-view", _markup_view),
    Scene("data-tree", _data_tree),
    Scene("table-view", _table_view),
    Scene("quick-view", _quick_view),
    Scene("filter-lines", _filter_lines),
    Scene("connect", _connect),
    Scene("host-key", _host_key),
    Scene("port-forwards", _port_forwards),
    Scene("saved-links", _saved_links),
    Scene("console", _console),
    Scene("command-window", _command_window),
    Scene("command-history", _command_history),
    Scene("extract", _extract),
    Scene("open-archive", _open_archive, size=(120, 24)),
    Scene("trash", _trash, size=(120, 24)),
    Scene("tree-window", _tree_window),
    Scene("help-window", _help_window),
    Scene("margins", _margins),
    Scene("go-to-line", _go_to_line),
    Scene("calculator-classic", _calculator_face("classic", "2*(3+4)")),
    Scene("calculator-scientific", _calculator_face("scientific", "sqrt(2)*sin(45)")),
    Scene("calculator-programming", _calculator_face("programming", "255*3+1")),
)
README_SCENE = SCENES[0]


def cropped(buffer: ScreenBuffer, widget: Any) -> ScreenBuffer:
    """The cells of *buffer* under *widget* and its shadow, or in the
    rectangle ``(x, y, width, height)`` given in its place.

    A widget is found wherever it is in the tree -- an overlay, a window on
    the desktop, a panel -- by its parents' places; on a mirrored screen the
    rectangle is mirrored with it.
    """
    if isinstance(widget, tuple):
        x, y, width, height = widget
        shadow = 0
    else:
        ox, oy = widget.offset()
        x, y, width, height = ox + widget.x, oy + widget.y, widget.width, widget.height
        shadow = 2 if widget.shadow else 0
    left = max(0, x)
    top = max(0, y)
    right = min(buffer.width, x + width + shadow)
    bottom = min(buffer.height, y + height + shadow // 2)
    if buffer.rtl:
        left, right = buffer.width - right, buffer.width - left
    piece = ScreenBuffer(right - left, bottom - top)
    piece.blit(buffer, 0, 0, left, top, right - left, bottom - top)
    return piece


def _pin_today() -> None:
    """The calendar's today, the clock's: the two modules that ask
    ``datetime.date.today()`` are given a ``datetime`` whose ``date`` answers
    the pinned day (the class itself cannot be patched)."""
    import datetime as real
    import types

    from navigator.widgets.shell.calendar_window import calendar_window
    from navml.widgets.dialog.date_button import date_button

    class AnyDate(type):
        # A reactive declared ``datetime.date`` is checked against this class
        # once the module's ``datetime`` is the pinned one: every date passes.
        def __instancecheck__(cls, value: object) -> bool:
            return isinstance(value, real.date)

    class Date(real.date, metaclass=AnyDate):
        @classmethod
        def today(cls) -> real.date:
            return real.date(2026, 1, 1)

    pinned = types.SimpleNamespace(**{name: getattr(real, name) for name in dir(real) if not name.startswith("__")})
    pinned.date = Date
    for module in (calendar_window, date_button):
        module.datetime = pinned


def paint(
    scene: Scene, theme: str, size: tuple[int, int] | None = None, language_code: str | None = None
) -> tuple[ScreenBuffer, TerminalInfo]:
    """*scene* as ``nav --theme THEME`` shows it in a tty of the scene's size
    (or *size*) -- in *language_code*'s catalogue, mirrored if it reads right
    to left -- cropped to what the scene keeps."""
    from navigator.__main__ import Navigator
    from navigator.lib.appearance.scheme import load_scheme
    from navigator.settings import SETTINGS
    from navigator.widgets.shell.clock import clock as clock_module
    from navigator.lib.drives import listing as listing_module
    from navigator.widgets.shell.console import Console

    from navigator.lib.config import file_history

    from navkit.database import DATABASE

    # A scene painted alone and one painted after the others are the same
    # picture: every setting at its default and an empty database each time,
    # whatever the scene before changed or kept (a panel's view, a history).
    SETTINGS.reset()
    DATABASE.open()
    clock_module.now = lambda: datetime(2026, 1, 1, 12, 34)
    # Whose files they are: the machine's user otherwise.
    listing_module._user_name = lambda uid: "user"
    listing_module._group_name = lambda gid: "users"
    # No strips of switches under a viewer or an editor either, and nothing
    # kept of one scene's file for the next: a scene painted alone and one
    # painted after the others are the same picture.
    SETTINGS.viewer.show_options = False
    SETTINGS.editor.show_options = False
    SETTINGS.interface.track_viewing = False
    SETTINGS.interface.track_editing = False
    SETTINGS.interface.store_viewer_position = False
    SETTINGS.interface.store_editor_position = False
    file_history.LAST_EDIT = None
    # The lists that read the machine are read once, by what a scene fakes.
    SETTINGS.processes.refresh = 0
    SETTINGS.services.refresh = 0
    SETTINGS.monitor.refresh = 0
    _pin_today()
    Console.start = lambda self, argv=None: None
    listing_module.free_space_of = lambda path: (412_316_860_416, "/")
    # The simple mode, whatever the shipped default: see the module docstring.
    SETTINGS.panel_defaults.view_mode = "simple"
    # No option strips on the panels' bottom frames: the picture is of the
    # file manager DN drew, not of the switches Navigator added to it.
    SETTINGS.file_manager.show_options = False
    # Nor git's letters and branch, whatever repository the directory is in.
    SETTINGS.file_manager.git_status = False
    # The unicode tier, not the Nerd one: whoever views the SVG has no Nerd
    # Font, and the icon gutter would be a column of replacement boxes.
    info = replace(FULL, palette=VGA_PALETTE, glyphs=GLYPHS_UNICODE)
    width, height = size or scene.size

    async def main() -> ScreenBuffer:
        app = Navigator(
            Path("."),
            Path("src"),
            load_scheme(theme),
            terminal=HeadlessTerminal(width, height, info),
        )
        task = asyncio.create_task(app.run_async())
        await asyncio.sleep(0.15)
        # Staged for the picture, and untrue on purpose: under a modal the key
        # bar is empty, since nothing the dialog binds carries a caption, and
        # most of the file panel's commands are greyed until they exist.  The
        # line is kept as the file panel shows it, every item enabled.
        bound = app.bindings()
        app.bindings = lambda start=None: bound
        # The shell's own prompt, as if it had printed one where the panel
        # is: Debian's default bash PS1, in xfce4-terminal's default colours
        # (its VGA palette, bold shown bright, a white foreground), spelled as RGB so the theme's
        # palette cannot repaint it.
        app.shell.console._prompted(PROMPT, app.shell._front_directory())
        # Every item enabled, whatever is installed here: a menu's greyed
        # entries would differ between machines (gpg, docker, a keyring).
        app.command_enabled = lambda command, *where: True
        keep = await scene.stage(app)
        await asyncio.sleep(0.15)
        buffer = ScreenBuffer(width, height)
        # Composed left to right and flipped on the way out, as the
        # application does a frame (Application._back, ScreenBuffer.mirrored).
        buffer.rtl = app.rtl
        app.shell.render_tree(buffer)
        if buffer.rtl:
            mirrored = buffer.mirrored()
            mirrored.rtl = True
            buffer = mirrored
        if keep is not None:
            buffer = cropped(buffer, keep)
        app.exit()
        await task
        return buffer

    home = Path.cwd()
    if language_code is not None:
        from navigator.lib.config import language

        language.install(Path(tempfile.gettempdir()) / "navigator-screenshot-none")
        language.apply(language_code)
    kept = os.environ.get("XDG_CONFIG_HOME")
    with tempfile.TemporaryDirectory() as scratch, tempfile.TemporaryDirectory() as config:
        populate(Path(scratch))
        os.chdir(scratch)
        # Nobody's configuration: highlight.ini, menu.ini and the viewers'
        # and editors' lists are read from here, and there are none.
        os.environ["XDG_CONFIG_HOME"] = config
        try:
            return asyncio.run(asyncio.wait_for(main(), 20)), info
        finally:
            os.chdir(home)
            if kept is None:
                del os.environ["XDG_CONFIG_HOME"]
            else:
                os.environ["XDG_CONFIG_HOME"] = kept


# -- plain text ---------------------------------------------------------------


def as_text(buffer: ScreenBuffer) -> str:
    rows = (
        "".join(buffer.get(x, y)[0] or "" for x in range(buffer.width)).rstrip()
        for y in range(buffer.height)
    )
    return "\n".join(rows) + "\n"


def readme_block(text: str, width: int, height: int) -> str:
    return (
        f"{BEGIN}\n"
        f"![Navigator, {width}x{height}]({IMAGE_URL})\n\n"
        "<details><summary>The same screen, as text</summary>\n\n"
        f"```text\n{text}```\n\n"
        "</details>\n"
        f"{END}"
    )


def with_block(readme: str, block: str) -> str:
    pattern = re.compile(re.escape(BEGIN) + ".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(readme):
        sys.exit(f"{README.name}: no {BEGIN} ... {END} markers to write between")
    return pattern.sub(lambda _: block, readme, count=1)


# -- colours ------------------------------------------------------------------

type RGB = tuple[int, int, int]


def resolved(style: Style, info: TerminalInfo) -> tuple[RGB, RGB]:
    """Foreground and background as a VGA text screen shows *style*: the
    palette, reverse and dim applied.  One answer for the SVG and the ``.ans``
    file, so the two are the same picture."""
    fg = VGA_PALETTE[7] if style.fg is None else rgb_of(info.adapt(style.fg))
    bg = VGA_PALETTE[0] if style.bg is None else rgb_of(info.adapt(style.bg))
    if style.reverse:
        fg, bg = bg, fg
    if style.dim:
        fg = ((fg[0] + bg[0]) // 2, (fg[1] + bg[1]) // 2, (fg[2] + bg[2]) // 2)
    return fg, bg


# -- ANSI ---------------------------------------------------------------------


def as_ansi(buffer: ScreenBuffer, info: TerminalInfo) -> str:
    """*buffer* as text a terminal paints and ``navigator/lib/help/ansi.py`` reads.

    The whole grammar, kept this small so the reader can be strict:

    - one line a screen row, each ended ``ESC[0m`` and a newline; no cursor
      movement and no other escape;
    - every run of cells that look alike is preceded by one ``ESC[0;...m``
      that says all of its look (:meth:`~navkit.style.Style.sgr` starts with
      a reset), never a change from the run before;
    - both colours are always there and always ``38;2;r;g;b``/``48;2;r;g;b``,
      resolved here exactly as the SVG's are -- the palette, reverse and dim
      already applied -- so the file means the same colours in any terminal
      and under any theme; of the attributes only bold (1), italic (3),
      underline (4) and strike (9) are left to say;
    - a wide character is written once, its second cell not at all.
    """
    lines = []
    for row in range(buffer.height):
        parts: list[str] = []
        last: Style | None = None
        owed = 0  # cells the last wide character still covers
        for x in range(buffer.width):
            char, style = buffer.get(x, row)
            if char == "" and owed:
                owed -= 1
                continue  # the second half of a wide character
            # A second half whose first was painted over (a clipped CJK
            # caption) is a blank, or the row would read a cell short.
            char = char or " "
            owed = char_width(char) - 1
            fg, bg = resolved(style, info)
            look = Style(
                fg=fg, bg=bg, bold=style.bold, italic=style.italic,
                underline=style.underline, strike=style.strike,
            )
            if look != last:
                parts.append(look.sgr())
                last = look
            parts.append(char)
        lines.append("".join(parts) + RESET_SGR + "\n")
    return "".join(lines)


# -- SVG ----------------------------------------------------------------------

CELL_W, CELL_H = 10, 20
FONT_SIZE = 16.5
BASELINE = 15
PAD = 12
GAP = 2  # half the distance between the two strokes of a double line
FONTS = "'DejaVu Sans Mono', 'Cascadia Mono', Menlo, Consolas, 'Liberation Mono', monospace"

_DIRECTIONS = {
    "UP": "u",
    "DOWN": "d",
    "LEFT": "l",
    "RIGHT": "r",
    "HORIZONTAL": "lr",
    "VERTICAL": "ud",
}
_WEIGHTS = {"LIGHT": 1, "SINGLE": 1, "DOUBLE": 2}
_SHADES = {"░": 0.25, "▒": 0.5, "▓": 0.75, "█": 1.0}
_HALVES = {"▀": (0, 0, 1, 0.5), "▄": (0, 0.5, 1, 0.5), "▌": (0, 0, 0.5, 1), "▐": (0.5, 0, 0.5, 1)}


def box_arms(char: str) -> dict[str, int] | None:
    """The arms of a single/double box-drawing character and their weights.

    Read off the Unicode name, which spells every one of them the same two
    ways: ``LIGHT DOWN AND RIGHT`` (one weight throughout) or ``DOWN SINGLE
    AND RIGHT DOUBLE`` (a weight per group).  Heavy, dashed and rounded
    pieces answer None and are left to the font.
    """
    if not "─" <= char <= "╿":
        return None
    words = unicodedata.name(char, "").removeprefix("BOX DRAWINGS ").split()
    arms: dict[str, int] = {}
    if words and words[0] in ("LIGHT", "DOUBLE"):
        weight = _WEIGHTS[words[0]]
        for word in words[1:]:
            if word == "AND":
                continue
            if word not in _DIRECTIONS:
                return None
            for arm in _DIRECTIONS[word]:
                arms[arm] = weight
        return arms or None
    pending: list[str] = []
    for word in words:
        if word in _DIRECTIONS:
            pending.append(_DIRECTIONS[word])
        elif word in _WEIGHTS and pending:
            for group in pending:
                for arm in group:
                    arms[arm] = _WEIGHTS[word]
            pending = []
        elif word != "AND":
            return None
    return arms if arms and not pending else None


def box_lines(arms: dict[str, int], x: float, y: float) -> list[tuple[float, float, float, float]]:
    """Line segments drawing *arms* in the cell whose corner is *x*, *y*.

    Drawn rather than left to the font because a font's box glyphs meet
    their neighbours only if its line height is exactly the cell's, which an
    SVG in somebody else's browser cannot promise.
    """
    cx, cy = x + CELL_W / 2, y + CELL_H / 2
    edge = {"u": y, "d": y + CELL_H, "l": x, "r": x + CELL_W}
    perpendicular = {"u": "lr", "d": "lr", "l": "ud", "r": "ud"}
    sign = {"u": -1, "d": 1, "l": -1, "r": 1}
    lines = []
    for arm, weight in arms.items():
        vertical = arm in "ud"
        centre = cy if vertical else cx
        if weight == 1:
            doubles = [p for p in perpendicular[arm] if arms.get(p) == 2]
            # Through a double crossing, stop at the near stroke; round a
            # double corner, reach the far one.
            start = centre + sign[arm] * GAP * (1 if len(doubles) == 2 else -1) if doubles else centre
            if vertical:
                lines.append((cx, start, cx, edge[arm]))
            else:
                lines.append((start, cy, edge[arm], cy))
            continue
        for side in perpendicular[arm]:
            offset = sign[side] * GAP
            # The stroke on a side a double arm leaves by turns the corner
            # there; otherwise it runs across to the far stroke.
            start = centre + sign[arm] * GAP if arms.get(side) == 2 else centre - sign[arm] * GAP
            if vertical:
                lines.append((cx + offset, start, cx + offset, edge[arm]))
            else:
                lines.append((start, cy + offset, edge[arm], cy + offset))
    return lines


def hex_of(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def colours(style: Style, info: TerminalInfo) -> tuple[str, str]:
    """Foreground and background as ``#rrggbb``, as a VGA text screen shows them."""
    fg, bg = resolved(style, info)
    return hex_of(fg), hex_of(bg)


def as_svg(buffer: ScreenBuffer, info: TerminalInfo) -> str:
    width, height = buffer.width * CELL_W, buffer.height * CELL_H
    backgrounds, strokes, texts = [], [], []
    for row in range(buffer.height):
        y = row * CELL_H
        cells = [buffer.get(x, row) for x in range(buffer.width)]
        painted = [colours(style, info) for _, style in cells]

        start = 0
        for x in range(1, buffer.width + 1):
            if x == buffer.width or painted[x][1] != painted[start][1]:
                backgrounds.append(
                    f'<rect x="{start * CELL_W}" y="{y}" width="{(x - start) * CELL_W}"'
                    f' height="{CELL_H}" fill="{painted[start][1]}"/>'
                )
                start = x

        run: list[str] = []
        run_start, run_key = 0, None

        def close_run(cells_each: int = 1) -> None:
            if not run:
                return
            fg, bold, italic, underline, strike = run_key
            attributes = f' fill="{fg}"'
            attributes += ' font-weight="bold"' if bold else ""
            attributes += ' font-style="italic"' if italic else ""
            decoration = " ".join(name for name, on in (("underline", underline), ("line-through", strike)) if on)
            attributes += f' text-decoration="{decoration}"' if decoration else ""
            # One <text> per word, each placed on its own cell: a renderer
            # that collapses spaces then has none to collapse, and
            # textLength pins every word to exactly the cells it covers.
            for word in re.finditer(r"\S+", "".join(run)):
                # The cells are in the order they are painted already (a
                # Hebrew scene's laid out by navkit.bidi): a renderer must not
                # turn a right-to-left word round a second time.
                override = ' unicode-bidi="bidi-override" direction="ltr"' if has_rtl(word.group()) else ""
                texts.append(
                    f'<text x="{(run_start + word.start() * cells_each) * CELL_W}" y="{y + BASELINE}"'
                    f' textLength="{len(word.group()) * cells_each * CELL_W}" lengthAdjust="spacingAndGlyphs"'
                    f"{override}{attributes}>{escape(word.group())}</text>"
                )

        x = 0
        while x < buffer.width:
            char, style = cells[x]
            fg, bg = painted[x]
            span = 2 if x + 1 < buffer.width and cells[x + 1][0] == "" else 1
            arms = box_arms(char)
            vector = arms is not None or char in _SHADES or char in _HALVES
            key = (fg, style.bold, style.italic, style.underline, style.strike)
            if vector or key != run_key or span == 2:
                close_run()
                # A drawn cell is no part of any run, so the next one starts
                # after it.
                run, run_start, run_key = [], x + (span if vector else 0), None if vector else key
            if arms is not None:
                for x1, y1, x2, y2 in box_lines(arms, x * CELL_W, y):
                    strokes.append(f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{fg}"/>')
            elif char in _SHADES:
                strokes.append(
                    f'<rect x="{x * CELL_W}" y="{y}" width="{CELL_W}" height="{CELL_H}"'
                    f' fill="{fg}" fill-opacity="{_SHADES[char]}"/>'
                )
            elif char in _HALVES:
                left, top, w, h = _HALVES[char]
                strokes.append(
                    f'<rect x="{x * CELL_W + left * CELL_W:g}" y="{y + top * CELL_H:g}"'
                    f' width="{w * CELL_W:g}" height="{h * CELL_H:g}" fill="{fg}"/>'
                )
            else:
                run.append(char or " ")
                if span == 2:
                    # A wide character is a run of its own, two cells long.
                    close_run(cells_each=2)
                    run, run_start, run_key = [], x + span, None
            x += span
        close_run()

    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width + 2 * PAD}"'
            f' height="{height + 2 * PAD}" viewBox="0 0 {width + 2 * PAD} {height + 2 * PAD}">',
            "<!-- generated by tools/screenshot.py; re-run it rather than editing this -->",
            f'<rect width="100%" height="100%" rx="8" fill="{hex_of(VGA_PALETTE[0])}"/>',
            f'<g transform="translate({PAD} {PAD})">',
            '<g shape-rendering="crispEdges">',
            *backgrounds,
            "</g>",
            f'<g font-family="{escape(FONTS)}" font-size="{FONT_SIZE}">',
            *texts,
            "</g>",
            '<g stroke-width="1.25" stroke-linecap="square">',
            *strokes,
            "</g>",
            "</g>",
            "</svg>",
            "",
        ]
    )


# -- the command line ---------------------------------------------------------


def shots_dir(language_code: str | None) -> Path:
    """Where a language's Help pictures go: ``docs/CODE/shots``."""
    return DOCS / (language_code or "en") / "shots"


def outputs_of(
    scene: Scene, theme: str, size: tuple[int, int] | None, language_code: str | None
) -> dict[Path, str]:
    """Every file *scene* writes, by path."""
    buffer, info = paint(scene, theme, size, language_code)
    if scene is not README_SCENE:
        where = shots_dir(language_code)
        return {
            where / f"{scene.name}.svg": as_svg(buffer, info),
            where / f"{scene.name}.ans": as_ansi(buffer, info),
        }
    if language_code is not None:
        return {SVG.with_name(f"screenshot-{language_code}.svg"): as_svg(buffer, info)}
    return {
        SVG: as_svg(buffer, info),
        README: with_block(
            README.read_text(encoding="utf-8"), readme_block(as_text(buffer), buffer.width, buffer.height)
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--theme", default="default", help="colour scheme (default: %(default)s)")
    parser.add_argument("--size", default=None, help="WIDTHxHEIGHT of the terminal (default: the scene's, 80x24)")
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 if anything would change")
    parser.add_argument(
        "--only", default=None, metavar="NAME", choices=[scene.name for scene in SCENES],
        help="paint this scene alone (%(choices)s)",
    )
    parser.add_argument(
        "--no-readme", action="store_true",
        help="leave the README's scene out: Help's pictures alone, which no release makes stale",
    )
    parser.add_argument(
        "--language", default=None, metavar="CODE",
        help="paint in this catalogue's language (he, ar mirrored): the desktop into docs/screenshot-CODE.svg "
             "instead of the README's English scene, Help's pictures into docs/CODE/shots/",
    )
    args = parser.parse_args(argv)
    size = None
    if args.size is not None:
        try:
            width, height = (int(part) for part in args.size.lower().split("x"))
        except ValueError:
            parser.error(f"--size wants WIDTHxHEIGHT, not {args.size!r}")
        size = (width, height)

    outputs: dict[Path, str] = {}
    for scene in SCENES:
        if args.only in (None, scene.name) and not (args.no_readme and scene is README_SCENE):
            outputs.update(outputs_of(scene, args.theme, size, args.language))
    stale = [path for path, text in outputs.items() if not path.exists() or path.read_text(encoding="utf-8") != text]
    if args.check:
        for path in stale:
            print(f"{path.relative_to(ROOT)} is out of date", file=sys.stderr)
        return 1 if stale else 0
    for path in stale:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(outputs[path], encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
