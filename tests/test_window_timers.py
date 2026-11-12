"""The windows that refresh on a clock do it with a ``Timer`` child.

Each window's ``ticker`` follows its ``[...] refresh`` setting, so a new
value is taken at once rather than the next time the window opens, and 0
stops it.  The game's clock is a ``Timer`` at ``tetris.TICK``.
"""

from __future__ import annotations

import pytest

from navigator.lib.utilities import tetris
from navigator.settings import SETTINGS


@pytest.fixture
def restore():
    saved = (SETTINGS.monitor.refresh, SETTINGS.processes.refresh)
    yield
    SETTINGS.monitor.refresh, SETTINGS.processes.refresh = saved


def test_the_monitor_s_ticker_follows_its_setting(restore):
    from navigator.widgets.shell.monitor_window import MonitorWindow

    SETTINGS.monitor.refresh = 3
    window = MonitorWindow()
    assert window.ticker.interval == 3000
    SETTINGS.monitor.refresh = 0
    assert window.ticker.interval == 0


def test_the_process_list_s_ticker_follows_its_setting(restore):
    from navigator.widgets.shell.process_window import ProcessWindow

    SETTINGS.processes.refresh = 2
    window = ProcessWindow()
    assert window.ticker.interval == 2000
    SETTINGS.processes.refresh = 5
    assert window.ticker.interval == 5000


def test_the_game_s_clock_is_a_timer_at_tick():
    from navigator.widgets.game.game_window import GameWindow

    assert GameWindow().clock.interval == round(tetris.TICK * 1000)
