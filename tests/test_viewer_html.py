"""F3's *HTML* reading: ``navigator/lib/viewer/html.py`` and the viewer rendering it."""

from __future__ import annotations

import pytest

from conftest import IDLE, FakeTerminal, Until, run_app
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.lib.viewer.html import render
from navigator.settings import SETTINGS


def texts(source: str, width: int = 40, **kwargs) -> list[str]:
    return [row.text for row in render(source.encode(), width, **kwargs).rows]


def cells_of(layout, text: str):
    """The cells of the first row holding *text*, from where it starts."""
    for row in layout.rows:
        at = row.text.find(text)
        if at >= 0:
            return row.cells[at:at + len(text)]
    raise AssertionError(f"{text!r} is not rendered")


# -- the layout ----------------------------------------------------------------


def test_the_title_heads_the_page_and_the_head_scripts_and_styles_are_not_shown():
    page = ("<html><head><meta charset=utf-8><title>A &amp; B</title><style>p{}</style>"
            "<script>var x = 1;</script></head><body><p>Text</p><script>no()</script></body></html>")
    assert texts(page) == ["A & B", "═════", "", "Text"]


def test_a_head_never_closed_ends_where_the_body_begins():
    assert texts("<head><title>T</title>\n<h1>One</h1><p>two") == ["T", "═", "", "One", "═══", "", "two"]


def test_blanks_run_together_and_a_paragraph_wraps():
    assert texts("<p>one   two\n\tthree four five six</p>", 14) == ["one two three", "four five six"]


def test_br_breaks_and_unclosed_paragraphs_end_at_the_next():
    assert texts("<p>a<br>b<p>c") == ["a", "b", "", "c"]


def test_lists_nest_with_unclosed_items_and_an_ordered_start():
    page = "<p>Intro<ul><li>one<li>two<ol start=3><li>three<li>four</ol><li>five</ul>"
    assert texts(page) == ["Intro", "", "• one", "• two", "  3. three", "  4. four", "• five"]


def test_a_quote_has_a_gutter_and_a_definition_is_indented():
    assert texts("<blockquote><p>one<p>two</blockquote>") == ["│ one", "│", "│ two"]
    assert texts("<dl><dt>Term<dd>Meaning</dl>") == ["Term", "  Meaning"]


def test_pre_keeps_its_blanks_and_is_coloured_by_its_language():
    layout = render(b'<pre class="language-python">\ndef f():\n    return 1\n</pre>', 20)
    assert [row.text.rstrip() for row in layout.rows] == ["  def f():", "      return 1"]
    assert "keyword" in layout.rows[0].cells[2][1] and "token" in layout.rows[0].cells[2][1]
    # Each line at its own source line, the one after <pre> first.
    assert [row.src for row in layout.rows] == [30, 39]


def test_a_language_on_the_code_inside_pre_counts_too():
    layout = render(b'<pre><code class="lang-python">x = 1</code></pre>', 20)
    assert "token" in layout.rows[0].cells[4][1]


def test_a_table_is_drawn_in_box_characters_with_a_header_and_alignment():
    page = ("<table><thead><tr><th>Name<th align=right>N</thead>"
            "<tr><td>a<td>1<tr><td>bb<td style='text-align: right'>22</table>")
    assert texts(page) == [
        "┌──────┬────┐",
        "│ Name │  N │",
        "├──────┼────┤",
        "│ a    │  1 │",
        "│ bb   │ 22 │",
        "└──────┴────┘",
    ]


def test_inline_elements_are_classes_and_a_link_keeps_its_url():
    layout = render(b'<p><b>a</b> <i>b</i> <s>c</s> <code>d</code> <a href="http://x.org">e</a> '
                    b'<img src="p.png" alt="pic"></p>', 40)
    assert layout.rows[0].text == "a b c d e [pic]"
    assert "strong" in cells_of(layout, "a")[0][1] and "emph" in cells_of(layout, "b")[0][1]
    assert "strike" in cells_of(layout, "c")[0][1] and "code" in cells_of(layout, "d")[0][1]
    link = cells_of(layout, "e")[0]
    assert "link" in link[1] and link[2] == "http://x.org"
    assert "image" in cells_of(layout, "[pic]")[0][1]


def test_a_rule_and_a_heading_level():
    assert texts("<h3>Three</h3><hr>", 10) == ["Three", "", "─" * 10]


def test_rows_know_the_source_line_of_the_tag_their_block_began_at():
    source = b"<h1>Head</h1>\n<p>\nSome text\n</p>\n<ul>\n<li>item\n</ul>\n"
    layout = render(source, 40)
    starts = {row.text: row.src for row in layout.rows if row.text and "═" not in row.text}
    assert starts["Head"] == 0
    assert starts["Some text"] == source.index(b"<p>")
    assert starts["• item"] == source.index(b"<li>")


def test_broken_html_does_not_raise():
    texts("<b><i>x</b></i></div></td><tr><li></ol><table><td>a")
    texts("<pre>never closed")
    texts("</p></p><p")


# -- the window ----------------------------------------------------------------


PAGE = (
    "<!DOCTYPE html>\n<html><head><title>The page</title></head><body>\n"
    + "".join(f"<p>Paragraph number {n:02} has a few words in it.</p>\n" for n in range(40))
    + "</body></html>\n"
)


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "dir").mkdir()
    (tmp_path / "page.html").write_text(PAGE)
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


def test_f3_renders_an_html_file_and_shift_f4_shows_its_source(files):
    app = navigator(files)
    seen = {}

    def look(name):
        def action(a):
            mark = opened(a).md_mark
            buffer = screen(a)
            ox, oy = mark.offset()
            seen[name] = (buffer, buffer.get(ox + mark.x + 1, oy + mark.y)[1].strike,
                          opened(a).viewer.render_format)
        return action

    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, RENDERED, look("rendered"),
        KeyEvent("f4", shift=True), IDLE, look("source"),
    ])
    rendered, struck, format = seen["rendered"]
    assert format == "html" and not struck
    assert inside(rendered, 2) == "The page"
    assert "{HTML}" in row_of(rendered, 21)
    source, struck, _ = seen["source"]
    # From the block that was on top, the title: its line, not the doctype's.
    assert inside(source, 2).startswith("<html><head><title>")
    assert "{HTML}" in row_of(source, 21) and struck


def test_the_html_setting_off_opens_the_source(files, monkeypatch):
    monkeypatch.setattr(SETTINGS.viewer, "render_html", False)
    app = navigator(files)
    seen = []
    run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE,
                  lambda a: seen.append((opened(a).viewer.rendered, inside(screen(a), 2)))])
    assert seen == [(False, "<!DOCTYPE html>")]


def test_the_strip_names_the_format(files):
    from dataclasses import replace

    from navkit.capabilities import FULL

    from navkit.glyphs import GLYPHS_ASCII, GLYPHS_UNICODE

    labels = []
    for glyphs in (GLYPHS_ASCII, GLYPHS_UNICODE):
        app = Navigator(files, files, terminal=FakeTerminal(80, 24, info=replace(FULL, glyphs=glyphs)))
        run_app(app, [KeyEvent("end"), KeyEvent("f3"), IDLE, RENDERED,
                      lambda a: labels.append(opened(a).options.items[-1].label())])
    # A word on a plain terminal, a symbol on a Unicode one.
    assert labels == ["HTML", "</>"]
