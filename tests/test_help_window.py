"""F1 Help's window: DN's ``THelpWindow`` over Markdown pages."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, key_bar_hints, run_app
from navigator.__main__ import Navigator
from navigator.commands import Help
from navigator.lib.help import pages
from navigator.widgets.help.commands import GoBack
from navigator.widgets.help.help_window import HelpWindow
from navkit.events import KeyEvent, MouseClickEvent
from navkit.i18n import LOCALE
from navkit.screen import ScreenBuffer
from navkit.style import BLACK, BLUE, CYAN, WHITE, YELLOW

RUN = "\x1b[0;38;2;1;2;3;48;2;4;5;6m"
FILLER = "".join(f"Paragraph {n} of the page.\n\n" for n in range(30))

PAGES = {
    "en/README.md": (
        "# Contents\n\n"
        "Read [the other page](other.md), its [second part](other.md#second),\n"
        "[a site](https://example.org/) or [a page that is gone](gone.md).\n"
    ),
    "en/other.md": f"# Other\n\n[Back to the contents](README.md)\n\n{FILLER}## Second\n\nThe second part.\n\n{FILLER}",
    "en/help.md": "# Help on help\n\nThe keys.\n",
    "en/picture.md": "# Picture\n\n![A box](shots/box.svg)\n\nAfter it.\n",
    "en/shots/box.ans": f"{RUN}╔══╗\x1b[0m\n{RUN}╚══╝\x1b[0m\n",
    "lv/README.md": "# Saturs\n\nLatviski.\n",
}


@pytest.fixture
def app(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    for name, text in PAGES.items():
        path = docs / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    monkeypatch.setattr(pages, "root", lambda: docs)
    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)
    home = tmp_path / "home"
    home.mkdir()
    made = Navigator(home, home, terminal=FakeTerminal(80, 24))
    # These tests are about the mechanism, over pages of their own: the file
    # manager and the File menu name none of the shipped ones here.
    made.manager.help_topic = ""
    made.shell.menu.file.help_topic = ""
    return made


def viewer(app):
    return app.modal.viewer


def on_page(name: str) -> Until:
    """Until the page *name* has been read and laid out."""
    return Until(lambda app: isinstance(app.modal, HelpWindow) and viewer(app).page == name
                 and viewer(app)._wanted is None and (viewer(app).layout is not None or viewer(app).problem))


def top_text(app) -> str:
    shown = viewer(app)
    return shown.layout.rows[shown.top].text


def heading_shown(app, anchor: str) -> bool:
    """Whether the heading *anchor* names is on the screen: near a page's end
    it cannot be scrolled to the top."""
    shown = viewer(app)
    row = shown.layout.anchors[anchor]
    return shown.top <= row < shown.top + shown.height


def selected_text(app) -> str:
    shown = viewer(app)
    link = shown.links[shown.selected]
    return " ".join("".join(c[0] for c in shown.layout.rows[r].cells[a:b]) for r, a, b in link.spans)


def screen(app) -> ScreenBuffer:
    buffer = ScreenBuffer(80, 24)
    app.root.render_tree(buffer)
    return buffer


def test_f1_opens_help_on_the_contents_and_esc_closes_it(app):
    seen = []
    run_app(app, [
        KeyEvent("f1"),
        on_page("README.md"),
        lambda a: seen.append((type(a.modal), a.modal.title, a.modal.width, a.modal.height, top_text(a))),
        lambda a: seen.append(key_bar_hints(a)),
        KeyEvent("escape"),
        lambda a: seen.append(a.modal),
    ])
    assert seen[0] == (HelpWindow, "Help", 72, 20, "Contents")
    assert ("Tab", "Next topic") in seen[1] and ("Enter", "Go to reference") in seen[1]
    assert seen[2] is None


def test_tab_goes_round_the_links_of_help_and_passes_over_a_site(app):
    seen = []
    note = lambda a: seen.append(selected_text(a))
    run_app(app, [
        KeyEvent("f1"), on_page("README.md"), note,
        KeyEvent("tab"), note, KeyEvent("tab"), note, KeyEvent("tab"), note,
        KeyEvent("tab", shift=True), note,
        lambda a: seen.append([link.href for link in viewer(a).links]),
    ])
    assert seen[:5] == ["the other page", "second part", "a page that is gone", "the other page", "a page that is gone"]
    assert seen[5] == ["other.md", "other.md#second", "gone.md"]


def test_enter_follows_to_the_anchor_and_alt_f1_comes_back_to_the_place(app):
    seen = []
    run_app(app, [
        KeyEvent("f1"), on_page("README.md"),
        lambda a: seen.append(a.command_enabled(GoBack())),
        KeyEvent("tab"),
        KeyEvent("enter"), on_page("other.md"),
        lambda a: seen.append((top_text(a), len(viewer(a).history), a.command_enabled(GoBack()))),
        KeyEvent("f1", alt=True), on_page("README.md"),
        lambda a: seen.append((top_text(a), selected_text(a), viewer(a).history)),
        KeyEvent("f1", alt=True),  # nowhere further back: refused, nothing happens
        lambda a: seen.append(viewer(a).page),
    ])
    assert seen == [False, ("Second", 1, True), ("Contents", "second part", []), "README.md"]


def test_a_link_within_the_page_is_followed_without_reading_it_again(app, monkeypatch):
    reads = []
    real = pages.read
    monkeypatch.setattr(pages, "read", lambda name, language: reads.append(name) or real(name, language))
    seen = []
    run_app(app, [
        lambda a: a.spawn(HelpWindow("other.md").execute(a)), on_page("other.md"),
        lambda a: viewer(a).show("other.md#second"),
        lambda a: seen.append((top_text(a), len(viewer(a).history))),
        KeyEvent("f1", alt=True),
        lambda a: seen.append(top_text(a)),
    ])
    assert seen == [("Second", 1), "Other"]
    assert reads == ["other.md"]


def test_the_arrows_scroll_and_the_bar_shows_only_a_long_page(app):
    seen = []
    note = lambda a: seen.append((viewer(a).top, a.modal.bar.visible))
    run_app(app, [
        KeyEvent("f1"), on_page("README.md"), note,
        KeyEvent("down"), note,  # shorter than the window: nowhere to go
        lambda a: viewer(a).show("other.md"), on_page("other.md"), note,
        KeyEvent("down"), note, KeyEvent("pagedown"), note, KeyEvent("up"), note,
        KeyEvent("end"),
        lambda a: seen.append(viewer(a).top == viewer(a).total - viewer(a).height),
        KeyEvent("home"), note,
        lambda a: a.post_event(MouseClickEvent(a.modal.x + 5, a.modal.y + 5, "wheel_down")), note,
    ])
    assert seen == [(0, False), (0, False), (0, True), (1, True), (18, True), (17, True), True, (0, True), (3, True)]


def test_a_click_on_a_link_follows_it(app):
    seen = []

    def click(a):
        shown = viewer(a)
        row, start, _ = shown.links[1].spans[0]  # "second part"
        a.post_event(MouseClickEvent(a.modal.x + 2 + start, a.modal.y + 1 + row - shown.top, "left"))

    run_app(app, [
        KeyEvent("f1"), on_page("README.md"),
        click, on_page("other.md"),
        lambda a: seen.append(top_text(a)),
        # A click on plain text does nothing but take the keyboard.
        lambda a: a.post_event(MouseClickEvent(a.modal.x + 30, a.modal.y + 10, "left")),
        lambda a: seen.append(viewer(a).page),
    ])
    assert seen == ["Second", "other.md"]


def test_f1_inside_help_is_help_on_help_and_shift_f1_the_index(app):
    seen = []
    run_app(app, [
        KeyEvent("f1"), on_page("README.md"),
        KeyEvent("f1"), on_page("help.md"),
        lambda a: seen.append(top_text(a)),
        KeyEvent("f1", shift=True), on_page("README.md"),
        lambda a: seen.append((top_text(a), [place.page for place in viewer(a).history])),
    ])
    assert seen == ["Help on help", ("Contents", ["README.md", "help.md"])]


def test_a_page_that_is_not_there_says_so_and_the_way_back_still_works(app):
    seen = []
    run_app(app, [
        KeyEvent("f1"), on_page("README.md"),
        KeyEvent("tab"), KeyEvent("tab"), KeyEvent("enter"), on_page("gone.md"),
        lambda a: seen.append((viewer(a).problem, viewer(a).layout, a.modal.bar.visible)),
        lambda a: seen.append("There is no help page gone.md" in
                              "".join(screen(a).get(x, a.modal.y + 1)[0] for x in range(80))),
        KeyEvent("f1", alt=True), on_page("README.md"),
        lambda a: seen.append(selected_text(a)),
    ])
    assert seen == [("There is no help page gone.md", None, False), True, "a page that is gone"]


def test_alt_z_zooms_and_the_place_is_kept_at_the_new_width(app):
    seen = []
    note = lambda a: seen.append((a.modal.width, a.modal.height, viewer(a).layout.width, top_text(a)))
    relaid = lambda width: Until(lambda a: viewer(a).layout.width == width)
    run_app(app, [
        lambda a: a.spawn(HelpWindow("other.md#second").execute(a)), on_page("other.md"), note,
        KeyEvent("z", alt=True), relaid(76), note,
        KeyEvent("z", alt=True), relaid(68), note,
    ])
    assert seen == [(72, 20, 68, "Second"), (80, 22, 76, "Second"), (72, 20, 68, "Second")]


def test_a_picture_is_painted_in_its_own_colours(app):
    seen = []

    def look(a):
        buffer = screen(a)
        shown = viewer(a)
        row = next(index for index, r in enumerate(shown.layout.rows) if r.picture is not None)
        x, y = a.modal.x + 2, a.modal.y + 1 + row - shown.top
        seen.append([buffer.get(x + dx, y) for dx in range(4)])
        seen.append(buffer.get(x + 4, y)[1] == shown.style)

    run_app(app, [lambda a: a.spawn(HelpWindow("picture.md").execute(a)), on_page("picture.md"), look])
    chars = [char for char, _ in seen[0]]
    styles = {(style.fg, style.bg) for _, style in seen[0]}
    assert chars == list("╔══╗") and styles == {((1, 2, 3), (4, 5, 6))}
    assert seen[1]  # beside the picture, the page's own ground


def test_help_is_in_the_language_spoken_and_else_in_english(app):
    seen = []
    LOCALE.code = "lv"
    run_app(app, [
        KeyEvent("f1"), on_page("README.md"),
        lambda a: seen.append(top_text(a)),
        lambda a: viewer(a).show("help.md"), on_page("help.md"),
        lambda a: seen.append(top_text(a)),
    ])
    assert seen == ["Saturs", "Help on help"]


def test_the_colours_are_helps_own(app):
    seen = []

    def look(a):
        buffer = screen(a)
        window, shown = a.modal, viewer(a)
        heading = buffer.get(window.x + 2, window.y + 1)[1]
        text = buffer.get(window.x + 2, window.y + 4)[1]
        row, start, _ = shown.links[0].spans[0]
        chosen = buffer.get(window.x + 2 + start, window.y + 1 + row)[1]
        row, start, _ = shown.links[1].spans[0]
        link = buffer.get(window.x + 2 + start, window.y + 1 + row)[1]
        frame = buffer.get(window.x, window.y)[1]
        seen.append([(s.fg, s.bg) for s in (frame, heading, text, link, chosen)])

    run_app(app, [KeyEvent("f1"), on_page("README.md"), look])
    # CHelpColor: $3F frame and highlight, $30 text, $3E keyword, $1E selected keyword.
    assert seen == [[(WHITE, CYAN), (WHITE, CYAN), (BLACK, CYAN), (YELLOW, CYAN), (YELLOW, BLUE)]]


def test_f1_is_the_programs_while_one_has_the_keys(app, monkeypatch):
    seen = []
    run_app(app, [
        lambda a: seen.append(a.command_enabled(Help())),
        lambda a: monkeypatch.setattr(type(a.shell), "program_has_keys", property(lambda self: True)),
        lambda a: seen.append(a.command_enabled(Help())),
    ])
    assert seen == [True, False]


# -- F1 inside a dialog, and the topic ----------------------------------------


def test_f1_inside_a_dialog_opens_help_over_it_and_esc_goes_back_to_it(app):
    from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog

    seen = []
    run_app(app, [
        KeyEvent("f7"),
        Until(lambda a: isinstance(a.modal, MkdirDialog)),
        lambda a: setattr(a.modal, "help_topic", ""),  # its shipped page is not among this test's
        KeyEvent("f1"), on_page("README.md"),
        lambda a: seen.append(top_text(a)),  # a dialog naming no topic: the contents
        KeyEvent("escape"),
        lambda a: seen.append(type(a.modal)),
        lambda a: seen.append(a.focused is a.modal.entry.entry),  # the keyboard back where it was
        KeyEvent("escape"),
        lambda a: seen.append(a.modal),
    ])
    assert seen == ["Contents", MkdirDialog, True, None]


def test_a_dialog_names_its_topic(app):
    from navigator.widgets.file_ops.mkdir_dialog import MkdirDialog

    seen = []
    dialog = MkdirDialog()
    dialog.help_topic = "other.md#second"
    run_app(app, [
        lambda a: a.spawn(dialog.execute(a)),
        Until(lambda a: a.modal is dialog),
        lambda a: seen.append(a.help_topic()),
        KeyEvent("f1"), on_page("other.md"),
        lambda a: seen.append(top_text(a)),
    ])
    assert seen == ["other.md#second", "Second"]


def test_a_window_names_its_topic_and_the_nearest_one_wins(app):
    seen = []

    def name_it(a):
        from navml.widgets.window import Window

        window = a.focused
        while not isinstance(window, Window):
            window = window.parent
        window.help_topic = "other.md"
        seen.append(a.help_topic())
        a.focused.help_topic = "help.md"  # nearer the keyboard than the window
        seen.append(a.help_topic())
        del a.focused.help_topic

    run_app(app, [
        lambda a: seen.append(a.help_topic()),
        name_it,
        KeyEvent("f1"), on_page("other.md"),
        lambda a: seen.append(top_text(a)),
    ])
    assert seen == ["README.md", "other.md", "help.md", "Other"]


# -- F1 on a menu and on a popup ----------------------------------------------


def test_f1_on_an_open_menu_shows_the_highlighted_entrys_help_and_esc_goes_back(app):
    from navml.widgets.menu.menu_bar.menu_session import MenuSession

    seen = []

    def name_them(a):
        session = a.modal
        seen.append(type(session))
        seen.append(session.help_topic)  # nothing named yet
        a.shell.menu.file.help_topic = "other.md"
        seen.append(session.help_topic)  # the menu's, for any entry in it
        box = session.boxes[-1]
        box.entries()[box.current].help_topic = "other.md#second"
        seen.append(session.help_topic)  # the entry's own wins

    run_app(app, [
        KeyEvent("f10"), KeyEvent("right"), KeyEvent("enter"),  # File, dropped
        name_them,
        KeyEvent("f1"), on_page("other.md"),
        lambda a: seen.append(top_text(a)),
        KeyEvent("escape"),
        lambda a: seen.append((type(a.modal), len(a.modal.boxes))),  # the menu, still open
        KeyEvent("down"),
        lambda a: seen.append(a.modal.help_topic),
        KeyEvent("escape"),
        lambda a: seen.append(a.modal),
    ])
    assert seen == [MenuSession, "", "other.md", "other.md#second", "Second",
                    (MenuSession, 1), "other.md", None]


def test_f1_on_a_menu_naming_no_topic_shows_the_contents(app):
    seen = []
    run_app(app, [
        KeyEvent("f10"),
        KeyEvent("f1"), on_page("README.md"),
        lambda a: seen.append(top_text(a)),
    ])
    assert seen == ["Contents"]


def test_f1_on_a_popup_menu_asks_the_entry_then_the_popup_then_what_it_was_opened_for(app):
    from navml.widgets.menu.menu_item.menu_item import MenuItem
    from navml.widgets.menu.popup_menu import PopupMenu
    from navml.widgets.menu.sub_menu.sub_menu import SubMenu
    from navml.widgets.window import Window

    seen = []
    popups = []

    def open_one(topic=""):
        def start(a):
            menu = SubMenu()
            menu.add_item("~O~ne")
            menu.add_item("~T~wo")
            popups.append(PopupMenu(menu, 5, 5, behind=a.focused, help_topic=topic))
            a.spawn(popups[-1].execute(a))
        return start

    def window_of(a, widget):
        while not isinstance(widget, Window):
            widget = widget.parent
        return widget

    def ask(a):
        popup = popups[-1]
        seen.append(popup.help_topic)  # nobody names one
        window_of(a, popup.behind).help_topic = "other.md"
        seen.append(popup.help_topic)  # the window it was opened over
        popup.topic = "help.md"
        seen.append(popup.help_topic)  # its own
        box = popup.boxes[-1]
        box.entries()[box.current].help_topic = "other.md#second"
        seen.append(popup.help_topic)  # the highlighted entry's

    run_app(app, [
        open_one(), Until(lambda a: a.modal is popups[-1]),
        ask,
        KeyEvent("f1"), on_page("other.md"),
        lambda a: seen.append(top_text(a)),
        KeyEvent("escape"),
        lambda a: seen.append(a.modal is popups[-1]),
        KeyEvent("escape"),
    ])
    assert seen == ["", "other.md", "help.md", "other.md#second", "Second", True]


# -- Settings: a topic a page, and the dialog's own Help button ---------------


def test_f1_in_settings_shows_the_page_in_fronts_help_from_a_control_the_tabs_or_the_button():
    """Against the shipped pages: every tab of Settings names a section that is there."""
    from navigator.widgets.setup.settings_dialog import SettingsDialog
    from navigator.widgets.setup.settings_dialog.settings_dialog import PAGES

    import tempfile
    from pathlib import Path

    seen = []
    with tempfile.TemporaryDirectory() as home:
        app = Navigator(Path(home), Path(home), terminal=FakeTerminal(80, 24))
        dialog = SettingsDialog("confirmations")

        def topics(a):
            for name in PAGES:
                dialog.tabs.select(dialog.tabs.index_of(dialog.page(name)))
                seen.append(a.help_topic())  # from a control on the page
            dialog.tabs.select(dialog.tabs.index_of(dialog.page("country")))
            dialog.info.focus()
            seen.append(a.help_topic())  # from the Help button: the dialog's, the page in front's

        run_app(app, [
            lambda a: a.spawn(dialog.execute(a)), Until(lambda a: a.modal is dialog),
            topics,
            lambda a: a.spawn(dialog.info.press()),
            on_page("settings.md"),
            lambda a: seen.append(top_text(a)),
        ])
    assert seen[: len(PAGES)] == [
        "settings.md#system", "settings.md#startup", "settings.md#interface", "settings.md#confirmations",
        "settings.md#savers", "settings.md#country", "settings.md#editorviewer", "settings.md#viewer-types",
        "settings.md#file-panels", "settings.md#info-panel", "settings.md#panel-defaults", "settings.md#columns",
        "settings.md#highlight", "settings.md#communications", "settings.md#tools",
    ]
    assert seen[len(PAGES):] == ["settings.md#country", "Country"]


def test_f1_in_the_calculator_window_shows_its_page(tmp_path, monkeypatch):
    """A window's topic, against the shipped pages."""
    from navigator.widgets.manager.commands import Calculator

    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []
    run_app(app, [
        lambda a: a.spawn(a.run_command(Calculator)),
        Until(lambda a: a.help_topic() == "calculator.md"),
        KeyEvent("f1"), on_page("calculator.md"),
        lambda a: seen.append(top_text(a)),
    ])
    assert seen == ["The calculator"]


def test_the_librarys_boxes_get_their_topic_from_the_application(tmp_path, monkeypatch):
    """navml's Window list and file dialog name no page; ``topics.LIBRARY`` does,
    for them and for what derives from them.  Against the shipped pages."""
    from navigator.widgets.setup.palette_file_dialog import PaletteFileDialog
    from navml.widgets.dialog.file_dialog import FileDialog
    from navml.widgets.window_manager import WindowManagerDialog

    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []
    files = FileDialog(directory=str(tmp_path))
    run_app(app, [
        KeyEvent("0", alt=True),
        Until(lambda a: isinstance(a.modal, WindowManagerDialog)),
        lambda a: seen.append(a.help_topic()),
        lambda a: a.spawn(a.modal.helper.press()),  # its Help button asks as F1 does
        on_page("windows.md"),
        lambda a: seen.append(heading_shown(a, "window-list")),
        KeyEvent("escape"), KeyEvent("escape"),
        lambda a: a.spawn(files.execute(a)), Until(lambda a: a.modal is files),
        lambda a: seen.append(a.help_topic()),
        KeyEvent("f1"), on_page("dialogs.md"),
        lambda a: seen.append(heading_shown(a, "choosing-a-file")),
    ])
    assert seen == ["windows.md#window-list", True, "dialogs.md#choosing-a-file", True]
    from navigator.lib.help.topics import library_topic

    assert library_topic(PaletteFileDialog.__new__(PaletteFileDialog)) == "dialogs.md#choosing-a-file"
    assert library_topic(app) == ""


def test_the_main_windows_and_menus_name_their_pages(tmp_path, monkeypatch):
    """Against the shipped pages: the file manager, and the bar's File menu and one of its items."""
    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []

    def on_copy(a):
        box = a.modal.boxes[-1]
        entries = box.entries()
        box.current = next(i for i, entry in enumerate(entries) if getattr(entry, "text", "") == "~C~opy...")
        seen.append(a.help_topic())

    run_app(app, [
        lambda a: seen.append(a.help_topic()),
        KeyEvent("f1"), on_page("panels.md"),
        lambda a: seen.append(top_text(a)),
        KeyEvent("escape"),
        KeyEvent("f10"), KeyEvent("right"), KeyEvent("enter"),
        lambda a: seen.append(a.help_topic()),  # the File menu's
        on_copy,  # an item's own
    ])
    assert seen == ["panels.md", "Panels", "file-operations.md", "file-operations.md#copy-and-move"]
