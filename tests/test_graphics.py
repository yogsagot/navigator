"""Pictures on the terminal: ``navkit/graphics.py``, the stamps
``Surface.place_image`` leaves, the terminal's answers, and the frame."""

from __future__ import annotations

import base64
import dataclasses

from conftest import FakeTerminal, run_app
from navkit.application import Application
from navkit.capabilities import FULL, TerminalInfo
from navkit.events import TerminalReplyEvent
from navkit.graphics import (
    KITTY_CHUNK,
    KITTY_HIDE_ALL,
    GraphicsLayer,
    Picture,
    kitty_transmit,
    sixel_encode,
)
from navkit.screen import ScreenBuffer
from navkit.terminal import InputParser
from navkit.widget import Widget

# -- the escapes -----------------------------------------------------------------


def test_kitty_is_sent_a_png_in_chunks_with_no_answers():
    picture = Picture(2, 1, png=b"x" * (KITTY_CHUNK * 2))
    sent = kitty_transmit(picture)
    chunks = sent.split("\x1b\\")[:-1]
    assert len(chunks) == 3
    assert chunks[0].startswith(f"\x1b_Ga=t,f=100,t=d,i={picture.id},q=2,m=1;")
    assert chunks[1].startswith("\x1b_Gm=1,q=2;") and chunks[2].startswith("\x1b_Gm=0,q=2;")
    data = "".join(chunk.split(";", 1)[1] for chunk in chunks)
    assert base64.b64decode(data) == picture.png


def test_sixel_bands_runs_and_a_transparent_colour():
    # Four wide, seven tall: a band of six and a band of one; colour 0 left unset.
    pixels = bytes([0, 1, 1, 1, 1, 1] * 7)
    out = sixel_encode(pixels, 6, 7, [(0, 0, 0), (255, 255, 255)], transparent=0)
    assert out.startswith('\x1bP0;1;0q"1;1;6;7#0;2;0;0;0#1;2;100;100;100')
    assert out.endswith("\x1b\\")
    # The first band: one blank sixel, then five full ones as a run.
    assert "#1?!5~-" in out
    # The second band holds only the top row.
    assert out.endswith("#1?!5@\x1b\\")


def test_the_parser_reads_the_answers_and_waits_for_one_only_when_asked():
    parser = InputParser()
    # Late, but whole: still an answer, never typed.
    assert parser.feed(b"\x1b_Gi=31;OK\x1b\\") == [TerminalReplyEvent("graphics", text="i=31;OK")]
    # Unfinished while nothing is expected: Alt+_ and what follows.
    assert [(e.key, e.alt) for e in parser.feed(b"\x1b_Gx")] == [("_", True), ("g", False), ("x", False)]
    parser = InputParser()
    parser.answers_graphics = True
    events = parser.feed(b"\x1b_Gi=31;OK\x1b\\\x1b[6;20;10t\x1b[?62;4;22c")
    assert events == [
        TerminalReplyEvent("graphics", text="i=31;OK"),
        TerminalReplyEvent("cell", (20, 10)),
        TerminalReplyEvent("da1", (62, 4, 22)),
    ]


def test_alt_underscore_is_still_a_key_while_answers_are_awaited():
    parser = InputParser()
    parser.answers_graphics = True
    assert parser.feed(b"\x1b_") == []
    assert parser.pending_escape
    (event,) = parser.flush()
    assert (event.key, event.alt) == ("_", True)


def test_detect_asks_unless_told_or_behind_a_multiplexer():
    base = {"TERM": "xterm-256color", "LANG": "C.UTF-8"}
    assert TerminalInfo.detect(base).probe_graphics
    assert not TerminalInfo.detect({**base, "TMUX": "/tmp/tmux,1,0"}).probe_graphics
    told = TerminalInfo.detect({**base, "NAVKIT_GRAPHICS": "sixel"})
    assert (told.graphics, told.probe_graphics) == ("sixel", False)
    off = TerminalInfo.detect({**base, "NAVKIT_GRAPHICS": "none"})
    assert (off.graphics, off.probe_graphics) == ("", False)


# -- the frame -------------------------------------------------------------------


def placed(width=20, height=10, at=(2, 3), size=(4, 2), **kinds):
    buffer = ScreenBuffer(width, height)
    picture = Picture(*size, png=b"PNG", sixel="SIXEL", **kinds)
    buffer.view(1, 1, width - 2, height - 2).place_image(picture, *at)
    return buffer, picture


def test_a_picture_is_placed_once_where_its_stamps_are():
    buffer, picture = placed()
    layer = GraphicsLayer()
    before, after = layer.compose(buffer.placements, buffer, None, "kitty")
    assert before == ""
    assert after.endswith(f"\x1b[5;4H\x1b_Ga=p,i={picture.id},p=1,c=4,r=2,C=1,q=2\x1b\\")
    assert layer.shown == {picture.id: (3, 4)}
    assert layer.compose(buffer.placements, buffer, buffer, "kitty") == ("", "")


def test_a_picture_painted_over_is_hidden_and_comes_back():
    buffer, picture = placed()
    layer = GraphicsLayer()
    layer.compose(buffer.placements, buffer, None, "kitty")
    covered = ScreenBuffer(20, 10)
    covered.copy_from(buffer)
    covered.set_cell(5, 4, "x")
    before, after = layer.compose(covered.placements, covered, buffer, "kitty")
    assert before == f"\x1b_Ga=d,d=i,i={picture.id},q=2\x1b\\" and after == ""
    _, after = layer.compose(buffer.placements, buffer, covered, "kitty")
    assert "a=p" in after and "a=t" not in after  # its data is still there


def test_a_picture_clipped_by_its_view_is_not_shown():
    buffer, picture = placed(at=(16, 3))
    assert GraphicsLayer().compose(buffer.placements, buffer, None, "kitty") == ("", "")


def test_a_picture_no_longer_placed_is_freed():
    buffer, picture = placed()
    layer = GraphicsLayer()
    layer.compose(buffer.placements, buffer, None, "kitty")
    empty = ScreenBuffer(20, 10)
    before, _ = layer.compose(empty.placements, empty, buffer, "kitty")
    assert f"a=d,d=I,i={picture.id}" in before


def test_a_full_repaint_places_everything_again():
    buffer, picture = placed()
    layer = GraphicsLayer()
    layer.compose(buffer.placements, buffer, None, "kitty")
    before, after = layer.compose(buffer.placements, buffer, None, "kitty")
    assert before == KITTY_HIDE_ALL and "a=p" in after and "a=t" not in after


def test_a_mirrored_screen_places_it_where_its_cells_went():
    buffer, picture = placed()
    mirrored = buffer.mirrored()
    layer = GraphicsLayer()
    layer.compose(mirrored.placements, mirrored, None, "kitty")
    assert layer.shown == {picture.id: (20 - 3 - 4, 4)}


def test_sixel_is_written_again_and_its_cells_cleaned_when_it_goes():
    buffer, picture = placed()
    layer = GraphicsLayer()
    _, after = layer.compose(buffer.placements, buffer, None, "sixel")
    assert after == "\x1b[5;4HSIXEL"
    front = ScreenBuffer(20, 10)
    front.copy_from(buffer)
    empty = ScreenBuffer(20, 10)
    assert layer.compose(empty.placements, empty, front, "sixel") == ("", "")
    assert front.get(3, 4)[0] == "\0"  # rewritten by the diff


def test_sixel_keeps_off_the_last_line():
    buffer = ScreenBuffer(20, 10)
    buffer.place_image(Picture(4, 2, png=b"PNG", sixel="SIXEL"), 2, 8)
    assert GraphicsLayer().compose(buffer.placements, buffer, None, "sixel") == ("", "")
    assert GraphicsLayer().compose(buffer.placements, buffer, None, "kitty")[1]


# -- the application -------------------------------------------------------------


class Shows(Widget):
    def __init__(self, picture, **kwargs):
        super().__init__(**kwargs)
        self.picture = picture

    def render(self, surface):
        surface.place_image(self.picture, 1, 1)


class Cover(Widget):
    def render(self, surface):
        surface.fill(0, 0, self.width, self.height, "#")


KITTY = dataclasses.replace(FULL, graphics="kitty", cell_px=(8, 16))


def test_the_application_writes_a_picture_after_the_cells_and_hides_it_under_a_window():
    picture = Picture(3, 2, png=b"PNG")
    root = Widget()
    root.add(Shows(picture, x=0, y=0, width=10, height=5))
    cover = Cover(x=2, y=2, width=3, height=2)
    terminal = FakeTerminal(20, 8, info=KITTY)
    app = Application(root, terminal=terminal)

    def cover_it(a):
        root.add(cover)

    def uncover(a):
        root.remove(cover)

    marks = {}
    run_app(app, [
        lambda a: marks.update(first=len(terminal.frames)),
        cover_it,
        lambda a: marks.update(covered=len(terminal.frames)),
        uncover,
    ])
    frames = terminal.frames
    first = frames[0]
    assert first.index("a=t,f=100") > first.index("\x1b[2J")
    assert f"a=p,i={picture.id}" in first
    assert any(f"a=d,d=i,i={picture.id}" in frame for frame in frames[marks["first"]: marks["covered"]])
    assert f"a=p,i={picture.id}" in "".join(frames[marks["covered"]:])


def test_the_terminal_s_answers_set_the_protocol(monkeypatch):
    terminal = FakeTerminal(20, 8, info=dataclasses.replace(FULL, probe_graphics=True))
    app = Application(Widget(), terminal=terminal)
    app._graphics_answers = {}
    app._terminal_replied(TerminalReplyEvent("graphics", text="i=31;OK"))
    app._terminal_replied(TerminalReplyEvent("cell", (18, 9)))
    app._terminal_replied(TerminalReplyEvent("da1", (62, 4)))
    assert (terminal.info.graphics, terminal.info.cell_px, terminal.info.probe_graphics) == (
        "kitty", (9, 18), False)

    terminal = FakeTerminal(20, 8, info=dataclasses.replace(FULL, probe_graphics=True))
    app = Application(Widget(), terminal=terminal)
    app._graphics_answers = {}
    app._terminal_replied(TerminalReplyEvent("da1", (62, 4)))
    assert terminal.info.graphics == "sixel"
    app._terminal_replied(TerminalReplyEvent("graphics", text="i=31;OK"))  # too late
    assert terminal.info.graphics == "sixel"
