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
    return Navigator(home, home, terminal=FakeTerminal(80, 24))


def viewer(app):
    return app.modal.viewer


def on_page(name: str) -> Until:
    """Until the page *name* has been read and laid out."""
    return Until(lambda app: isinstance(app.modal, HelpWindow) and viewer(app).page == name
                 and viewer(app)._wanted is None and (viewer(app).layout is not None or viewer(app).problem))


def top_text(app) -> str:
    shown = viewer(app)
    return shown.layout.rows[shown.top].text


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
