"""A stall is logged: the frame loop's busy marker and the watchdog over it."""

from __future__ import annotations

import asyncio
import time
from collections import deque

from navkit.application import Application, describe_event
from navkit.events import KeyEvent, MouseClickEvent, PasteEvent
from navigator.lib.system import errorlog

from conftest import RecordingWidget, run_app


def test_events_are_described_without_their_text():
    assert describe_event(KeyEvent("f5", ctrl=True)) == "key ctrl+f5"
    assert describe_event(PasteEvent("secret")) == "paste of 6 characters (terminal)"
    assert describe_event(MouseClickEvent(3, 4, "left")) == "MouseClickEvent left press at 3,4"


def test_the_loop_marks_a_batch_busy_and_remembers_the_input(terminal):
    app = Application(RecordingWidget(), terminal=terminal)
    seen = []

    async def handler(event):
        seen.append(app.handling_since is not None and app.handling)

    app.on_key = handler
    run_app(app, [KeyEvent("x", char="x"), MouseClickEvent(1, 1, "none", "move")])
    assert seen == ["key x"]
    assert app.handling_since is None
    assert [what for _, what in app.recent_events] == ["key x"]


class _App:
    def __init__(self):
        self.handling_since: float | None = None
        self.handling = "key f5"
        self.recent_events = deque([(time.time(), "key f5")])


def test_one_report_per_stall_and_one_when_it_ends(tmp_path, monkeypatch):
    log = open(tmp_path / "errors.log", "a+", encoding="utf-8")
    monkeypatch.setattr(errorlog, "_fault_file", log)
    app = _App()

    async def scenario():
        dog = errorlog.Watchdog(app, asyncio.get_running_loop(), threshold=0.1, poll=0.02)
        dog.start()
        app.handling_since = time.monotonic()
        await asyncio.sleep(0.4)  # the loop is free: a handler waiting
        app.handling_since = None
        await asyncio.sleep(0.1)
        app.handling_since = time.monotonic()
        time.sleep(1.5)  # the loop thread itself blocked
        app.handling_since = None
        await asyncio.sleep(0.1)
        dog.stop()

    asyncio.run(scenario())
    log.close()
    text = (tmp_path / "errors.log").read_text()
    assert text.count("STALL nav") == 2
    assert text.count("STALL ENDED") == 2
    assert "busy for" in text and "key f5" in text
    assert "a handler is waiting" in text and "Stack for" in text
    assert "it is blocked" in text
    assert "test_stall_watchdog.py" in text  # faulthandler's thread stacks


def test_no_watchdog_before_the_log_is_open(monkeypatch):
    monkeypatch.setattr(errorlog, "_fault_file", None)

    async def start(threshold):
        return errorlog.start_watchdog(_App(), threshold)

    assert asyncio.run(start(2)) is None


def test_system_setup_sets_the_stall_threshold():
    from navigator.settings import SETTINGS
    from navigator.widgets.setup.system_setup_dialog import SystemSetupDialog

    box = SystemSetupDialog()
    assert box.stall_report.value == "002"
    box.stall_report.value = "010"
    assert box.accept()["stall_report"] == 10
    box.stall_report.value = "000"
    assert box.accept()["stall_report"] == 0
    assert SETTINGS.system.stall_report == 2


def test_a_zero_threshold_reports_nothing(tmp_path, monkeypatch):
    log = open(tmp_path / "errors.log", "a+", encoding="utf-8")
    monkeypatch.setattr(errorlog, "_fault_file", log)
    app = _App()

    async def scenario():
        dog = errorlog.Watchdog(app, asyncio.get_running_loop(), threshold=0, poll=0.02)
        dog.start()
        app.handling_since = time.monotonic() - 10
        await asyncio.sleep(0.2)
        dog.stop()

    asyncio.run(scenario())
    log.close()
    assert (tmp_path / "errors.log").read_text() == ""
