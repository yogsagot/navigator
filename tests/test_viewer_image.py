"""F3's *Image* reading: ``navigator/lib/viewer/image.py`` and the viewer
showing a picture on a kitty or sixel terminal."""

from __future__ import annotations

import dataclasses
import struct
import zlib

import pytest

from conftest import IDLE, FakeTerminal, Until, run_app
from navkit.capabilities import FULL
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.viewer import image
from navigator.settings import SETTINGS
from navigator.widgets.viewer.file_viewer import FileViewer


def make_png(width: int, height: int, rgb: tuple[int, int, int] = (200, 30, 30)) -> bytes:
    """A *width* x *height* PNG of one colour, made without Pillow."""
    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))

    row = b"\0" + bytes(rgb) * width
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(row * height))
            + chunk(b"IEND", b""))


PNG = make_png(64, 32)


# -- the model -----------------------------------------------------------------


def test_pictures_are_shown_by_their_name(monkeypatch):
    assert FileViewer.format_by_name("Photo.PNG") == "image"
    assert FileViewer.format_by_name("photo.jpeg") == "image"
    monkeypatch.setattr(SETTINGS.viewer, "render_images", False)
    assert FileViewer.format_by_name("photo.png") == ""


def test_a_png_s_size_is_read_from_its_header():
    assert image.png_size(PNG) == (64, 32)
    assert image.png_size(b"GIF89a" + b"\0" * 30) is None


def test_a_picture_fits_its_cells_with_its_aspect_kept_and_never_enlarged():
    # 1000x500 into 100x40 cells of 10x20: the width decides, 100 x 25.
    assert image.fit(1000, 500, 100, 40, (10, 20)) == (100, 25)
    # The height decides: 400 x 800 pixels.
    assert image.fit(500, 1000, 100, 40, (10, 20)) == (40, 40)
    # A 16x16 icon stays 16x16: two cells by one.
    assert image.fit(16, 16, 100, 40, (8, 16)) == (2, 1)
    # Unknown, a cell is taken as twice as tall as wide.
    assert image.fit(80, 80, 100, 40, None) == (10, 5)


def test_kitty_is_sent_a_png_as_it_is_without_pillow(monkeypatch):
    monkeypatch.setattr(image, "pillow", lambda: False)
    shown = image.decode(PNG, 80, 20, (8, 16), "kitty")
    assert shown.picture.png == PNG
    assert (shown.format, shown.width, shown.height) == ("PNG", 64, 32)
    assert (shown.picture.cols, shown.picture.rows) == (8, 2)
    assert image.can_show("a.png", "kitty") and not image.can_show("a.jpg", "kitty")
    assert not image.can_show("a.png", "sixel")
    with pytest.raises(ValueError):
        image.decode(b"\xff\xd8\xff\xe0 not really a jpeg", 80, 20, (8, 16), "kitty")
    with pytest.raises(ValueError):
        image.decode(PNG, 80, 20, (8, 16), "sixel")
    assert "navigator-fm[images]" in image.available()


def test_sixel_is_encoded_for_the_cells_it_takes():
    pytest.importorskip("PIL")
    shown = image.decode(PNG, 80, 20, (8, 16), "sixel")
    sixel = shown.picture.sixel
    assert sixel.startswith('\x1bP0;1;0q"1;1;64;32#0;2;')
    assert sixel.endswith("\x1b\\")
    assert (shown.picture.cols, shown.picture.rows) == (8, 2)


def test_pillow_reads_what_kitty_cannot_and_scales_it_down():
    PIL = pytest.importorskip("PIL.Image")
    import io

    out = io.BytesIO()
    PIL.new("RGB", (400, 200), (10, 200, 10)).save(out, "JPEG")
    shown = image.decode(out.getvalue(), 20, 20, (10, 20), "kitty")
    assert shown.format == "JPEG" and (shown.width, shown.height) == (400, 200)
    assert (shown.picture.cols, shown.picture.rows) == (20, 5)
    assert image.png_size(shown.picture.png) == (200, 100)


# -- the window ----------------------------------------------------------------


KITTY = dataclasses.replace(FULL, graphics="kitty", cell_px=(8, 16))


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "dir").mkdir()
    (tmp_path / "picture.png").write_bytes(PNG)
    return tmp_path


def opened(app):
    from navigator.widgets.viewer.file_window import FileWindow

    window = app.shell.desktop.active_window
    return window if isinstance(window, FileWindow) else None


SHOWN = Until(lambda a: opened(a) is not None and opened(a).viewer.showing_picture
              and bool(a._graphics.shown))


def test_f3_shows_a_picture_and_shift_f4_its_source(files):
    terminal = FakeTerminal(80, 24, info=KITTY)
    app = Navigator(files, files, terminal=terminal)
    seen = {}
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, SHOWN,
        lambda a: seen.update(id=opened(a).viewer.picture.picture.id, frames=len(terminal.frames),
                              shown=dict(a._graphics.shown)),
        KeyEvent("f4", shift=True), IDLE,
        lambda a: seen.update(after=dict(a._graphics.shown), rendered=opened(a).viewer.showing_picture),
    ])
    pid = seen["id"]
    painted = "".join(terminal.frames[: seen["frames"]])
    assert f"a=t,f=100,t=d,i={pid}" in painted and f"a=p,i={pid}" in painted
    assert pid in seen["shown"]
    assert seen["after"] == {} and not seen["rendered"]
    assert f"a=d,d=I,i={pid}" in "".join(terminal.frames[seen["frames"]:])


def test_a_menu_over_the_picture_hides_it(files):
    # Wide enough to fill the window, so the drop-down lands on it.
    (files / "picture.png").write_bytes(make_png(1280, 320))
    terminal = FakeTerminal(80, 24, info=KITTY)
    app = Navigator(files, files, terminal=terminal)
    seen = {}
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, SHOWN,
        lambda a: seen.update(shown=dict(a._graphics.shown)),
        KeyEvent("f10"), KeyEvent("down"), IDLE,
        lambda a: seen.update(menu=dict(a._graphics.shown)),
        KeyEvent("escape"), IDLE,
        lambda a: seen.update(back=dict(a._graphics.shown)),
    ])
    assert seen["shown"] and seen["back"] == seen["shown"]
    assert seen["menu"] == {}


def test_a_terminal_that_draws_no_pictures_shows_the_source(files):
    app = Navigator(files, files, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [
        KeyEvent("end"), KeyEvent("f3"), IDLE, Until(lambda a: opened(a) is not None),
        lambda a: seen.update(viewer=opened(a).viewer),
    ])
    viewer = seen["viewer"]
    assert viewer.render_format == "image"
    assert not viewer.can_render and not viewer.showing_picture and viewer.picture is None
    # View > Markup view, greyed, says why.
    assert viewer.render_refusal() == "This terminal draws no pictures"


def test_the_quick_view_shows_the_picture_under_the_cursor_and_lets_it_go(files):
    terminal = FakeTerminal(80, 24, info=KITTY)
    app = Navigator(files, files, terminal=terminal)
    seen = {}
    run_app(app, [
        KeyEvent("end"), KeyEvent("q", ctrl=True), IDLE,
        Until(lambda a: bool(a._graphics.shown)),
        lambda a: seen.update(shown=dict(a._graphics.shown), frames=len(terminal.frames)),
        KeyEvent("up"), IDLE, Until(lambda a: not a._graphics.shown),
    ])
    (pid,) = seen["shown"]
    x, _ = seen["shown"][pid]
    assert x >= 40  # in the passive panel's place, on the right
    assert f"a=d,d=I,i={pid}" in "".join(terminal.frames[seen["frames"]:])
