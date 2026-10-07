"""≡ > Game: DOS Navigator's *Navigator's game* (TETRIS.PAS)."""

from __future__ import annotations

import random
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator import tetris
from navigator.__main__ import Navigator
from navigator.settings import SETTINGS
from navigator.tetris import SHI, VIS, Game
from navigator.widgets.game.game_setup_dialog import GameSetupDialog
from navigator.widgets.game.game_window import GameWindow
from navigator.widgets.game.top_ten_dialog import TopTenDialog
from navigator.widgets.game.winner_dialog import WinnerDialog


def game(figure: int = 2, **kwargs) -> Game:
    """A game whose falling figure is *figure* (2 is the four-long bar)."""
    g = Game(rng=random.Random(1), **kwargs)
    g.current, g.cells = figure, list(tetris.FIGURES[figure])
    g.x, g.y = SHI // 2 - 2, 0
    return g


def test_the_glass_is_walled_and_floored():
    g = game()
    assert g.glass[(0, 0)] == 1 and g.glass[(0, SHI + 1)] == 1 and g.glass[(VIS, 5)] == 1
    assert all(g.glass[(row, col)] == 0 for row in range(VIS) for col in range(1, SHI + 1))
    assert g.level == 5 and g.delay == 25
    assert Game(pentix=True, rng=random.Random(2)).figures == 27


def test_the_walls_stop_a_move_and_a_turn_turns_in_its_square():
    g = game()
    while g.move(-1):
        pass
    assert min(col for _, col in g.falling()) == 1
    assert not g.rotate()  # against the wall the bar cannot lie down
    g = game()
    assert g.rotate()
    assert sorted(g.cells) == [(3, 1), (3, 2), (3, 3), (3, 4)]  # it lies down in its square
    square = game(3)
    before = sorted(square.falling())
    square.rotate()
    assert sorted(square.falling()) == before


def test_a_figure_set_down_scores_and_a_full_line_goes():
    g = game(2)
    for col in range(1, SHI + 1):
        if col != 5:
            g.glass[(VIS - 1, col)] = 9
    g.x = 5 - 2 - 1  # the bar's column (2) over column 5
    g.drop()
    g.fall()  # sets it down: one line taken
    assert g.lines == 1
    assert all(g.glass[(VIS - 1, col)] == 0 for col in range(1, SHI + 1) if col != 5)
    assert g.glass[(VIS - 1, 5)] != 0  # the bar's lower cells came down a row
    # ((Vis - y) * 2 + level * 6) for setting it -- it rests at y 14, its
    # cells from row 1 -- and (Vis - row) * 30 for the line.
    assert g.score == (VIS - 14) * 2 + 5 * 6 + (0 + VIS - (VIS - 1)) * 30


def test_the_preview_scores_seven_tenths():
    plain, shown = game(3), game(3, preview=True)
    for g in (plain, shown):
        g.drop()
        g.fall()
    assert shown.score == plain.score * 7 // 10


def test_lines_climb_the_levels():
    g = game(start_level=9)
    g.lines = 90 - (9 - 9) * 10 + 20
    g.drop()
    g.fall()
    assert g.level == 10 and g.delay == 4


def test_a_figure_that_does_not_fit_ends_the_game():
    g = game(3)
    g.y = VIS - 4  # resting on the floor
    for row in range(0, 4):
        for col in range(1, SHI):  # the last column open: no line is taken
            g.glass[(row, col)] = 9
    g.fall()  # set down there, and the next has no room at the top
    assert g.over and g.stopped
    g.pause()
    assert g.stopped  # an ended game does not go on


def test_the_clock_drops_a_row_once_the_delay_has_passed():
    g = game()
    assert not g.tick(20)
    assert g.tick(10) and g.y == 1
    g.pause()
    assert not g.tick(100) and g.y == 1


def test_the_top_ten_keeps_ten_best_first_and_a_tie_after():
    assert tetris.place_for("tetris", 0) is None
    assert tetris.place_for("tetris", 10) == 0
    for score in range(10, 120, 10):
        tetris.enter("tetris", f"p{score}", 1, 2, score)
    table = tetris.top_ten("tetris")
    assert len(table) == 10 and table[0].score == 110 and table[-1].score == 20
    assert tetris.place_for("tetris", 20) is None and tetris.place_for("tetris", 25) == 9
    tetris.enter("tetris", "tie", 1, 1, 110)
    assert [e.name for e in tetris.top_ten("tetris")[:2]] == ["p110", "tie"]
    assert tetris.top_ten("pentix") == []
    line = tetris.score_line(table[0], highlight=True)
    assert line == "~p110~" + "." * 26 + " ....1 ....2 .......110"


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    return tmp_path


def window_of(app) -> GameWindow | None:
    window = app.shell.desktop.active_window
    return window if isinstance(window, GameWindow) else None


def test_alt_f9_opens_one_game_and_its_keys_play_it(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 25))
    seen = {}

    def look(a):
        window = window_of(a)
        seen.update(focus=type(a.focused).__name__, x=window.game.x)

    run_app(app, [KeyEvent("f9", alt=True), Until(lambda a: window_of(a) is not None), look,
                  KeyEvent("left"), lambda a: seen.update(moved=window_of(a).game.x),
                  KeyEvent("f3"), lambda a: seen.update(paused=window_of(a).game.stopped),
                  KeyEvent("f9", alt=True), lambda a: seen.update(count=sum(
                      isinstance(w, GameWindow) for w in a.shell.desktop.windows())),
                  KeyEvent("escape"), lambda a: seen.update(after=window_of(a))])
    assert seen["focus"] == "Glass" and seen["moved"] == seen["x"] - 1
    assert seen["paused"] and seen["count"] == 1 and seen["after"] is None


def test_a_game_good_enough_asks_a_name_and_shows_the_top_ten(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 25))
    seen = {}

    def end_it(a):
        g = window_of(a).game
        g.score = 1234
        for row in range(VIS):
            for col in range(1, SHI):
                g.glass[(row, col)] = 9

    def name(a):
        a.modal.player.value = "Juris"

    run_app(app, [KeyEvent("f9", alt=True), Until(lambda a: window_of(a) is not None), end_it,
                  Until(lambda a: getattr(a.modal, "title", "") == "Information", timeout=3),
                  lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("enter"),
                  Until(lambda a: isinstance(a.modal, WinnerDialog)), name, KeyEvent("enter"),
                  Until(lambda a: isinstance(a.modal, TopTenDialog)),
                  lambda a: seen.update(lines=[l.text for l in a.modal.lines]), KeyEvent("enter"),
                  Until(lambda a: a.modal is None)], timeout=10)
    assert seen["prompt"].startswith("Game over")
    assert seen["lines"][0].startswith("~Juris~")
    assert tetris.top_ten("tetris")[0].name == "Juris"


def test_setup_starts_a_new_game_and_keeps_the_answer(place):
    app = Navigator(place, place, terminal=FakeTerminal(80, 25))

    def answer(a):
        a.modal.level.value = 0
        a.modal.game_style.value = 1
        a.modal.options.value = 1

    run_app(app, [KeyEvent("f9", alt=True), Until(lambda a: window_of(a) is not None), KeyEvent("f5"),
                  Until(lambda a: isinstance(a.modal, GameSetupDialog)), answer, KeyEvent("enter"),
                  Until(lambda a: a.modal is None)])
    game_now = window_of(app).game
    assert game_now.pentix and game_now.preview and game_now.level == 1
    assert SETTINGS.tetris.style == "pentix" and "style = pentix" in SETTINGS.path.read_text()
