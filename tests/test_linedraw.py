"""Line drawing: DOS Navigator's ``DrawLine`` (MICROED.PAS), as a model and in the editor."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.editor.linedraw import DOWN, LEFT, RIGHT, drawn, without_arm
from navigator.settings import SETTINGS

# -- the model ---------------------------------------------------------------------------------


def test_the_pen_draws_its_way_and_turns_corners():
    assert drawn(" ", " ", " ", " ", double=False, direction=RIGHT, came=None) == "─"
    assert drawn(" ", " ", " ", "─", double=False, direction=DOWN, came=LEFT) == "┐"
    assert drawn(" ", " ", " ", " ", double=True, direction=DOWN, came=None) == "║"


def test_crossing_a_line_of_the_other_weight_makes_the_mixed_junction():
    assert drawn("║", " ", "║", " ", double=False, direction=RIGHT, came=LEFT) == "╫"
    assert drawn(" ", "─", " ", "─", double=True, direction=DOWN, came=None) == "╥"


def test_erasing_takes_an_arm_off_a_junction_and_leaves_a_line_alone():
    assert without_arm("┼", 8) == "├"
    assert without_arm("├", 2) == "│"
    assert without_arm("─", 2) is None
    assert without_arm("x", 2) is None


# -- in the editor -----------------------------------------------------------------------------


@pytest.fixture
def blank(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    SETTINGS.interface.store_editor_position = False
    (tmp_path / "dir").mkdir()
    (tmp_path / "text.txt").write_bytes(b"\n")
    return tmp_path


def draw(path, *keys):
    app = Navigator(path, path, terminal=FakeTerminal(80, 24))
    seen = []
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), lambda a: None, *keys,
                  lambda a: seen.append(a.shell.desktop.active_window.editor)])
    return seen[0]


def shift(key, times=1):
    return [KeyEvent(key, shift=True)] * times


def test_f4_and_shift_arrows_draw_a_box(blank):
    editor = draw(blank, KeyEvent("f4"), *shift("right", 4), *shift("down", 2),
                  *shift("left", 4), *shift("up", 2), *shift("right"))
    # "\n" is two lines; going down off the second adds a third, which has no ending.
    assert editor.document.encode().decode() == "┌───┐\n│   │\n└───┘"
    assert editor.info_text.endswith("{┼}")


def test_a_second_f4_draws_double_and_a_third_stops(blank):
    editor = draw(blank, KeyEvent("f4"), KeyEvent("f4"), *shift("right", 3))
    assert editor.document.encode().decode() == "═══\n"
    assert editor.info_text.endswith("{╬}")
    (blank / "text.txt").write_text("abc\n")
    editor = draw(blank, KeyEvent("f4"), KeyEvent("f4"), KeyEvent("f4"), *shift("right", 2))
    assert editor.draw_mode == 0 and editor.block_text == "ab"  # Shift+arrows mark again


def test_plain_arrows_only_move_and_down_adds_a_line(blank):
    editor = draw(blank, KeyEvent("f4"), KeyEvent("down"), KeyEvent("down"), KeyEvent("right"))
    assert editor.document.encode() == b"\n\n"  # a third line, added by the second Down
    assert (editor.line, editor.col) == (2, 1)


def test_ctrl_arrows_erase_and_trim_the_junction_beside(blank):
    (blank / "text.txt").write_text(" │ \n─┼─\n │ \n")
    editor = draw(blank, KeyEvent("f4"), KeyEvent("down"), KeyEvent("right", ctrl=True))
    # The cell (1, 0) is blanked and the cross loses its left arm.
    assert editor.document.encode().decode() == " │ \n ├─\n │ \n"


def test_ctrl_q_ctrl_m_switches_too_and_each_stroke_is_one_undo(blank):
    editor = draw(blank, KeyEvent("q", ctrl=True), KeyEvent("enter"), *shift("right", 2),
                  KeyEvent("backspace", alt=True))
    assert editor.draw_mode == 1
    assert editor.document.encode().decode() == "─\n"
