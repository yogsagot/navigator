"""F3's *reStructuredText* reading: ``navigator/lib/viewer/rst.py`` and the viewer rendering it."""

from __future__ import annotations

import pytest

from conftest import IDLE, FakeTerminal, Until, run_app
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.lib.viewer.rst import render
from navigator.settings import SETTINGS


def texts(source: str, width: int = 40, **kwargs) -> list[str]:
    return [row.text.rstrip() for row in render(source.encode(), width, **kwargs).rows]


def cells_of(layout, text: str):
    for row in layout.rows:
        at = row.text.find(text)
        if at >= 0:
            return row.cells[at:at + len(text)]
    raise AssertionError(f"{text!r} is not rendered")


# -- the layout ----------------------------------------------------------------


def test_sections_are_headings_by_depth():
    source = "=====\nTitle\n=====\n\nOne\n===\n\nTwo\n---\n\nText.\n"
    assert texts(source) == ["Title", "═════", "", "One", "───", "", "Two", "", "Text."]
    layout = render(source.encode(), 40)
    assert {"heading", "h3"} <= set(cells_of(layout, "Two")[0][1])


def test_a_paragraph_is_joined_and_wrapped():
    assert texts("one two\nthree four five six\n", 14) == ["one two three", "four five six"]


def test_inline_markup_is_classes_and_a_link_keeps_its_url():
    layout = render(b"*a* **b** ``c`` `d <http://x.org>`_ `e`\n", 40)
    assert layout.rows[0].text == "a b c d e"
    assert "emph" in cells_of(layout, "a")[0][1] and "strong" in cells_of(layout, "b")[0][1]
    assert "code" in cells_of(layout, "c")[0][1]
    link = cells_of(layout, "d")[0]
    assert "link" in link[1] and link[2] == "http://x.org"
    # A title reference, the default role, is emphasis.
    assert "emph" in cells_of(layout, "e")[0][1]


def test_lists_nest_and_enumerate_in_their_own_kind():
    source = "Intro\n\n- one\n- two\n\n  - inner\n\n#. first\n#. second\n\na) x\nb) y\n\nii. r\niii. s\n"
    assert texts(source) == [
        "Intro", "", "• one", "• two", "  • inner", "", "1. first", "2. second", "", "a) x", "b) y",
        "", "ii. r", "iii. s",
    ]


def test_a_quote_an_admonition_and_definitions():
    assert texts("Text\n\n    quoted\n") == ["Text", "", "│ quoted"]
    assert texts(".. note:: Mind it.\n") == ["│ Note", "│ Mind it."]
    assert texts("term\n   meaning\n\n:field: value\n") == ["term", "  meaning", "", "field", "  value"]


def test_code_blocks_are_coloured_and_each_line_is_at_its_own_offset():
    source = b"Text\n\n.. code-block:: python\n\n   def f():\n       return 1\n\nAfter::\n\n   plain\n"
    layout = render(source, 30)
    code = [row for row in layout.rows if row.text.startswith("  ") and row.text.strip()]
    assert [row.text.rstrip() for row in code] == ["  def f():", "      return 1", "  plain"]
    assert "keyword" in code[0].cells[2][1] and "token" in code[0].cells[2][1]
    assert [row.src for row in code] == [source.index(b"   def"), source.index(b"       return"),
                                         source.index(b"   plain")]


def test_grid_and_simple_tables_are_drawn_in_box_characters():
    grid = "+------+----+\n| Name | N  |\n+======+====+\n| a    | 1  |\n+------+----+\n"
    simple = "====  ==\nName  N\n====  ==\na     1\n====  ==\n"
    expected = ["┌──────┬───┐", "│ Name │ N │", "├──────┼───┤", "│ a    │ 1 │", "└──────┴───┘"]
    assert texts(grid) == expected
    assert texts(simple) == expected


def test_a_transition_and_an_image():
    assert texts("A\n\n----\n\nB\n\n.. image:: p.png\n   :alt: pic\n", 10) == [
        "A", "", "─" * 10, "", "B", "", "[pic]",
    ]


def test_nothing_outside_the_file_is_read_and_errors_do_not_raise(tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("SECRET")
    shown = texts(f".. include:: {secret}\n\n.. raw:: html\n\n   <b>raw</b>\n\nText\n")
    assert "SECRET" not in " ".join(shown) and "raw" not in " ".join(shown)
    assert "Text" in shown
    texts("Title\n===\n\n`unclosed\n\n.. unknown-directive::\n\n- a\n * b\n")


# -- the window ----------------------------------------------------------------


DOC = "Title\n=====\n\n" + "".join(f"Paragraph number {n:02} has a few words in it.\n\n" for n in range(40))


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "dir").mkdir()
    (tmp_path / "readme.rst").write_text(DOC)
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
    return row_of(buffer, y)[1:-1].strip()


def opened(app):
    from navigator.widgets.viewer.file_window import FileWindow

    window = app.shell.desktop.active_window
    return window if isinstance(window, FileWindow) else None


RENDERED = Until(lambda a: opened(a) is not None and opened(a).viewer.rendering)


def test_f3_renders_a_rst_file_and_shift_f4_shows_its_source(files):
    app = navigator(files)
    seen = {}
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, RENDERED,
        lambda a: seen.update(rendered=screen(a), format=opened(a).viewer.render_format),
        KeyEvent("f4", shift=True), IDLE,
        lambda a: seen.update(source=screen(a)),
    ])
    assert seen["format"] == "rst"
    assert inside(seen["rendered"], 2) == "Title"
    assert "{reST}" in row_of(seen["rendered"], 21)
    assert inside(seen["source"], 2) == "Title"
    assert inside(seen["source"], 3) == "====="


def test_the_rst_setting_off_opens_the_source(files, monkeypatch):
    monkeypatch.setattr(SETTINGS.viewer, "render_rst", False)
    app = navigator(files)
    seen = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE,
                  lambda a: seen.append((opened(a).viewer.rendered, inside(screen(a), 3)))])
    assert seen == [(False, "=====")]
