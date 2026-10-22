"""F3's *PDF* reading: ``navigator/lib/viewer/pdf.py`` and the viewer rendering it."""

from __future__ import annotations

import pytest

from conftest import IDLE, FakeTerminal, Until, run_app
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.lib.viewer.pdf import render
from navigator.settings import SETTINGS
from navigator.widgets.viewer.file_viewer import FileViewer


def make_pdf(pages: list[list[str]]) -> bytes:
    """A PDF of *pages*, each a list of lines in Helvetica, one under another."""
    count = len(pages)
    # 1 catalog, 2 pages, 3 font, then a page and its contents for each.
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [" + b" ".join(f"{4 + 2 * n} 0 R".encode() for n in range(count))
        + f"] /Count {count} >>".encode(),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for n, lines in enumerate(pages):
        stream = b"BT /F1 12 Tf 14 TL 72 720 Td " + b" ".join(
            b"(" + line.encode("latin-1") + b") Tj T*" for line in lines) + b" ET"
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                       f"/Resources << /Font << /F1 3 0 R >> >> /Contents {5 + 2 * n} 0 R >>".encode())
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{offset:010} 00000 n \n".encode() for offset in offsets)
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


TWO_PAGES = make_pdf([["First page text"], ["Second page, which has", "two lines of text"]])


def texts(data: bytes, width: int = 40, **kwargs) -> list[str]:
    return [row.text for row in render(data, width, **kwargs).rows]


# -- the layout ----------------------------------------------------------------


def test_each_page_is_headed_and_ruled_off_from_the_last():
    assert texts(TWO_PAGES) == [
        "Page 1 of 2", "───────────", "", "First page text", "",
        "────────────────────────────────────────", "",
        "Page 2 of 2", "───────────", "", "Second page, which has two lines of text",
    ]


def test_a_page_wraps_to_the_width():
    rows = texts(TWO_PAGES, 20)
    assert rows[-3:] == ["Second page, which", "has two lines of", "text"]


def test_ascii_glyphs_when_unicode_is_off():
    rows = texts(TWO_PAGES, 20, unicode=False)
    assert rows[1] == "-----------"
    assert rows[5] == "-" * 20


def test_rows_point_into_the_file_in_order_so_the_scroll_bar_follows_the_pages():
    layout = render(TWO_PAGES, 40)
    srcs = [row.src for row in layout.rows]
    assert srcs == sorted(srcs)
    assert srcs[0] == 0 and srcs[-1] < len(TWO_PAGES)
    second = next(index for index, row in enumerate(layout.rows) if row.text == "Page 2 of 2")
    assert layout.row_for(layout.rows[second].src) == second


def test_a_file_that_is_not_a_pdf_raises_so_the_source_is_shown():
    with pytest.raises(Exception):
        render(b"just some text\n", 40)


def test_pdf_files_are_rendered_by_their_name(monkeypatch):
    assert FileViewer.format_by_name("Report.PDF") == "pdf"
    monkeypatch.setattr(SETTINGS.viewer, "render_pdf", False)
    assert FileViewer.format_by_name("report.pdf") == ""


# -- the window ----------------------------------------------------------------


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "dir").mkdir()
    (tmp_path / "paper.pdf").write_bytes(TWO_PAGES)
    return tmp_path


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


def test_f3_shows_a_pdf_s_text_and_shift_f4_its_source(files):
    app = Navigator(files, files, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, RENDERED,
        lambda a: seen.update(rendered=screen(a), format=opened(a).viewer.render_format),
        KeyEvent("f4", shift=True), IDLE,
        lambda a: seen.update(source=screen(a)),
    ])
    assert seen["format"] == "pdf"
    assert inside(seen["rendered"], 2) == "Page 1 of 2"
    assert "{PDF}" in row_of(seen["rendered"], 21)
    assert inside(seen["source"], 2) == "%PDF-1.4"
