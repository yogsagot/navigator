"""The widget library: that every widget paints, and what each one does.

The first test here is the one that matters most and says least.  Two
components shipped for months unable to paint at all -- ``Dialog`` and
``FramedButton`` both unpacked a six-character charset into ``draw_box``'s
positional arguments and raised ``TypeError`` the moment anything rendered
them -- because nothing in the suite ever rendered a widget.  It is
parametrized over ``navml.widgets.__all__`` rather than over a list, so a
widget added next year is covered by it without anybody remembering.
"""

from __future__ import annotations

import pytest

import navml.widgets
from navkit.glyphs import GLYPHS_ASCII, GLYPHS_UNICODE
from navkit.screen import ScreenBuffer
from navkit.widget import Widget

#: Every component the library publishes, as classes.
WIDGETS = [
    (name, getattr(navml.widgets, name))
    for name in navml.widgets.__all__
]

#: Widget classes only.  ``__all__`` may also carry an event or a helper.
PAINTERS = [(name, cls) for name, cls in WIDGETS if isinstance(cls, type) and issubclass(cls, Widget)]

#: Sizes every widget has to survive.  The degenerate ones are the point:
#: ``draw_box`` returns early below 2x2 and a painter's arithmetic goes
#: negative around there, which is exactly where a widget stops clipping and
#: starts raising.
SIZES = [(24, 6), (40, 1), (1, 1), (0, 0), (3, 2)]


@pytest.mark.parametrize("name, cls", PAINTERS, ids=[n for n, _ in PAINTERS])
@pytest.mark.parametrize("width, height", SIZES, ids=[f"{w}x{h}" for w, h in SIZES])
def test_every_widget_paints(name, cls, width, height):
    """It renders, at every size, without raising."""
    widget = cls(width=width, height=height)
    widget.render(ScreenBuffer(width, height))


@pytest.mark.parametrize("name, cls", PAINTERS, ids=[n for n, _ in PAINTERS])
def test_every_widget_paints_inside_itself(name, cls):
    """A widget may not draw outside its own area.

    ``render_tree`` hands each widget a view of its own rectangle, so this is
    the buffer's guarantee rather than the widget's -- but a widget that
    assumes otherwise is one that looks right alone and wrong in a tree.
    """
    buffer = ScreenBuffer(30, 8)
    widget = cls(width=10, height=3)
    widget.render(buffer.view(2, 2, 10, 3))
    for y in range(8):
        for x in range(30):
            if 2 <= x < 12 and 2 <= y < 5:
                continue
            assert buffer.get(x, y)[0] == " ", f"{name} painted at {x},{y}"


@pytest.mark.parametrize("name, cls", PAINTERS, ids=[n for n, _ in PAINTERS])
def test_every_widget_degrades_to_ascii(name, cls, monkeypatch):
    """Nothing above ASCII reaches the buffer at ``GLYPHS_ASCII``.

    A widget owes both halves of the glyph question: a sheet says which set is
    *wanted* and the tier says which can be *shown*.  A widget that reads the
    first and not the second paints replacement boxes on a terminal that told
    us so.
    """
    widget = cls(width=24, height=6)
    monkeypatch.setattr(type(widget), "glyphs", property(lambda self: GLYPHS_ASCII))
    buffer = ScreenBuffer(24, 6)
    widget.render(buffer)
    for y in range(6):
        for x in range(24):
            char = buffer.get(x, y)[0]
            assert char == "" or ord(char) < 128, (
                f"{name} drew {char!r} at {x},{y} on an ASCII terminal"
            )


@pytest.mark.parametrize("name, cls", PAINTERS, ids=[n for n, _ in PAINTERS])
def test_every_widget_declares_the_parts_it_paints(name, cls):
    """A part name is only checkable where the class is, so check it here.

    Painting at a size big enough to reach every branch, with ``part_style``
    refusing anything undeclared -- so a widget that paints ``::titel`` fails
    here rather than silently taking its owner's colours for ever.
    """
    cls(width=24, height=6).render(ScreenBuffer(24, 6))
