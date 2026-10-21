"""F3's *Markdown* reading: ``navigator/lib/viewer/markdown.py`` and the viewer rendering it."""

from __future__ import annotations

import pytest

from conftest import IDLE, FakeTerminal, Until, run_app
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

import navigator.lib.viewer as viewer_model
from navigator.__main__ import Navigator
from navigator.lib.viewer import ViewSearch
from navigator.lib.viewer.markdown import render
from navigator.settings import SETTINGS
from navigator.widgets.viewer.commands import SwitchRendered, Unwrap


def texts(source: str, width: int = 40, **kwargs) -> list[str]:
    return [row.text for row in render(source.encode(), width, **kwargs).rows]


def classes_at(layout, row: int, column: int) -> tuple[str, ...]:
    return layout.rows[row].cells[column][1]


# -- the layout ----------------------------------------------------------------


def test_headings_lose_their_marks_and_the_first_two_are_underlined():
    assert texts("# One\n\n## Two\n\n### Three\n") == [
        "One", "═══", "", "Two", "───", "", "Three",
    ]
    layout = render(b"# One\n", 40)
    assert {"heading", "h1"} <= set(classes_at(layout, 0, 0))


def test_ascii_draws_with_ascii():
    assert texts("# One\n\n- a\n\n---\n", 10, unicode=False) == ["One", "===", "", "* a", "", "-" * 10]


def test_a_paragraph_is_joined_and_wrapped_at_blanks():
    assert texts("one two\nthree four five six\n", 14) == ["one two three", "four five six"]


def test_a_word_longer_than_a_line_is_cut():
    assert texts("abcdefghij\n", 4) == ["abcd", "efgh", "ij"]


def test_emphasis_code_and_links_are_classes_and_the_link_keeps_its_url():
    layout = render(b"*a* **b** ~~c~~ `d` [e](http://x.org)\n", 40)
    row = layout.rows[0]
    assert row.text == "a b c d e"
    assert "emph" in row.cells[0][1] and "strong" in row.cells[2][1]
    assert "strike" in row.cells[4][1] and "code" in row.cells[6][1]
    assert "link" in row.cells[8][1] and row.cells[8][2] == "http://x.org"


def test_lists_nest_tight_without_blank_rows_and_tasks_are_boxes():
    assert texts("Intro\n\n- one\n  - inner\n- [x] done\n- [ ] todo\n\n1. first\n2. second\n") == [
        "Intro", "", "• one", "  • inner", "☒ done", "☐ todo", "", "1. first", "2. second",
    ]


def test_a_loose_list_keeps_a_blank_row_between_items():
    assert texts("- one\n\n- two\n") == ["• one", "", "• two"]


def test_a_quote_has_a_gutter_on_every_row():
    assert texts("> one\n>\n> two\n") == ["│ one", "│", "│ two"]


def test_a_code_block_is_indented_unwrapped_and_coloured_by_its_language():
    layout = render(b"```python\ndef f():\n    return 1\n```\n", 20)
    assert [row.text.rstrip() for row in layout.rows] == ["  def f():", "      return 1"]
    assert "keyword" in classes_at(layout, 0, 2) and "token" in classes_at(layout, 0, 2)
    # Each line at its own source line, the one after the fence first.
    assert [row.src for row in layout.rows] == [10, 19]


def test_a_table_is_drawn_in_box_characters_and_aligned():
    rows = texts("| Name | N |\n|------|--:|\n| a | 1 |\n| bb | 22 |\n")
    assert rows == [
        "┌──────┬────┐",
        "│ Name │  N │",
        "├──────┼────┤",
        "│ a    │  1 │",
        "│ bb   │ 22 │",
        "└──────┴────┘",
    ]


def test_a_table_too_wide_is_shrunk_and_its_cells_wrap():
    rows = texts("| a | b |\n|---|---|\n| one two three | x |\n", 16)
    assert all(len(row) <= 16 for row in rows)
    assert any("three" in row for row in rows)


def test_rows_know_the_source_line_their_block_starts_on():
    source = b"# Head\n\nSome text\nmore text\n\n- item\n"
    layout = render(source, 6)
    starts = {row.text: row.src for row in layout.rows if row.text}
    assert starts["Head"] == 0
    assert starts["Some"] == starts["more"] == source.index(b"Some")
    assert starts["• item"] == source.index(b"- item")
    # An offset anywhere in the paragraph finds its first row.
    first = layout.row_for(source.index(b"more"))
    assert layout.rows[first].text == "Some"


def test_an_html_comment_is_hidden_and_other_html_shown():
    assert texts("one\n\n<!-- note -->\n\n<div>two</div>\n") == ["one", "", "<div>two</div>"]


def test_a_wide_character_takes_two_columns():
    layout = render("漢字 x\n".encode(), 40)
    assert [c for c, _, _ in layout.rows[0].cells] == ["漢", "", "字", "", " ", "x"]


# -- the window ----------------------------------------------------------------


DOC = (
    "# Title\n\n"
    + "".join(f"Paragraph number {n:02} has a few words in it.\n\n" for n in range(40))
    + "## The end\n"
)


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "dir").mkdir()
    (tmp_path / "readme.md").write_text(DOC)
    return tmp_path


def navigator(path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def screen(app) -> ScreenBuffer:
    from conftest import settle

    buffer = ScreenBuffer(80, 24)
    app.shell.layout(80, 24)
    settle()
    app.shell.render_tree(buffer)
    return buffer


def row_of(buffer: ScreenBuffer, y: int) -> str:
    return "".join(buffer.get(x, y)[0] or " " for x in range(buffer.width))


def inside(buffer: ScreenBuffer, y: int) -> str:
    """A row inside the window's frame, trimmed."""
    return row_of(buffer, y)[1:-1].strip()


def opened(app):
    from navigator.widgets.viewer.file_window import FileWindow

    window = app.shell.desktop.active_window
    return window if isinstance(window, FileWindow) else None


RENDERED = Until(lambda a: opened(a) is not None and opened(a).viewer.rendering)


def test_f3_renders_a_markdown_file_and_shift_f4_shows_its_source(files):
    app = navigator(files)
    seen = {}
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, RENDERED,
        lambda a: seen.update(rendered=screen(a)),
        KeyEvent("pagedown"),
        lambda a: seen.update(top=opened(a).viewer.top, row=opened(a).viewer.render_row),
        KeyEvent("f4", shift=True), IDLE,
        lambda a: seen.update(source=screen(a), source_top=opened(a).viewer.top,
                              rendering=opened(a).viewer.rendering),
    ])
    assert inside(seen["rendered"], 2) == "Title"
    assert "═════" in row_of(seen["rendered"], 3)
    assert "{Markdown}" in row_of(seen["rendered"], 21)
    assert seen["row"] > 0 and seen["top"] > 0
    # The source, from the block that was on top.
    assert not seen["rendering"]
    assert seen["source_top"] == seen["top"]
    assert inside(seen["source"], 2).startswith("Paragraph number")
    # Still there, struck through: a click puts the rendering back.
    assert "{Markdown}" in row_of(seen["source"], 21)


def test_the_view_menu_ticks_markdown_and_hex_greys_it_and_wrap(files):
    app = navigator(files)
    seen = []

    def look(a):
        window = opened(a)
        seen.append((window.checks(SwitchRendered()), a.command_enabled(SwitchRendered()),
                     a.command_enabled(Unwrap())))

    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, RENDERED, look,
        KeyEvent("f4"), IDLE, look,
    ])
    # Rendering: ticked, enabled, Wrap greyed; in hex it is greyed itself.
    assert seen[0] == (True, True, False)
    assert seen[1][1] is False


def test_the_setting_off_opens_the_source(files, monkeypatch):
    monkeypatch.setattr(SETTINGS.viewer, "render_markdown", False)
    app = navigator(files)
    seen = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE,
                  lambda a: seen.append((opened(a).viewer.rendered, inside(screen(a), 2)))])
    assert seen[0][0] is False and seen[0][1] == "# Title"


def test_a_search_lands_on_the_rendered_block_and_marks_the_words(files, monkeypatch):
    monkeypatch.setattr(viewer_model, "last_search", ViewSearch("number 30"))
    app = navigator(files)
    seen = {}

    def look(a):
        viewer = opened(a).viewer
        seen.update(row=viewer.render_layout.rows[viewer.render_row].text,
                    marks=viewer._render_marks(viewer.render_layout), layout=viewer.render_layout,
                    hit=viewer.hit)

    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, RENDERED,
        KeyEvent("f7", shift=True), Until(lambda a: opened(a).viewer.hit is not None),
        look,
    ], settle=0.05)
    assert seen["hit"] is not None
    assert seen["row"].startswith("Paragraph number 30")
    marked = sorted(seen["marks"])
    row = seen["layout"].rows[marked[0][0]]
    assert "".join(row.cells[c][0] for _, c in marked) == "number 30"


def test_the_choice_is_kept_in_the_view_history(files):
    from navigator.models.view_record import ViewRecord

    SETTINGS.interface.track_viewing = True
    app = navigator(files)
    seen = []
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, RENDERED,
        KeyEvent("f4", shift=True), IDLE, KeyEvent("escape"), IDLE,
        KeyEvent("f3"), IDLE,
        lambda a: seen.append(opened(a).viewer.rendered),
    ])
    assert ViewRecord.find(files / "readme.md").rendered == "off"
    assert seen == [False]


def test_the_quick_view_renders_too(files):
    app = navigator(files)
    seen = []
    run_app(app, [
        KeyEvent("end"), KeyEvent("q", ctrl=True),
        Until(lambda a: a.manager.quick.viewer.rendering),
        lambda a: seen.append(a.manager.quick.viewer.render_layout.rows[0].text),
    ])
    assert seen == ["Title"]


def click_mark(app):
    from navkit.events import MouseClickEvent

    mark = opened(app).md_mark
    ox, oy = mark.offset()
    x, y = ox + mark.x + 1, oy + mark.y
    app.post_event(MouseClickEvent(x=x, y=y, button="left", action="press"))
    app.post_event(MouseClickEvent(x=x, y=y, button="left", action="release"))


def test_a_click_on_the_mark_switches_it_and_off_it_is_struck_through(files):
    app = navigator(files)
    seen = []

    def look(a):
        mark = opened(a).md_mark
        buffer = screen(a)
        ox, oy = mark.offset()
        text = "".join(buffer.get(ox + mark.x + i, oy + mark.y)[0] for i in range(mark.width))
        seen.append((opened(a).viewer.rendering, text,
                     buffer.get(ox + mark.x + 1, oy + mark.y)[1].strike))

    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, RENDERED, look,
        click_mark, IDLE, look,
        click_mark, RENDERED, look,
    ])
    assert seen[0] == (True, "{Markdown}", False)
    assert seen[1] == (False, "{Markdown}", True)
    assert seen[2] == (True, "{Markdown}", False)


def test_no_mark_for_a_file_the_masks_do_not_name(files):
    (files / "zz.txt").write_text("plain\n")
    app = navigator(files)
    seen = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE,
                  lambda a: seen.append((opened(a).viewer.render_mark, opened(a).md_mark.width))])
    assert seen == [("", 0)]


def test_strike_is_sgr_9():
    from navkit.style import Style

    assert Style(strike=True).sgr() == "\x1b[0;9m"
