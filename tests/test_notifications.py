"""Desktop notifications: focus reports, the OSC 9/777 sequences, notify-send,
the setting, and a long job's end told to a terminal in the background."""

from __future__ import annotations

import asyncio
import io
import threading

import pytest

from conftest import FakeTerminal, run_app, wait_until

from navkit import notify as navkit_notify
from navkit.application import Application
from navkit.capabilities import TerminalInfo
from navkit.events import FocusEvent, KeyEvent
from navkit.terminal import NOTIFY_MAX, Terminal, notify_osc
from navkit.widget import Widget

from navigator.lib.system import notify
from navigator.lib.system.background import BACKGROUND
from navigator.settings import SETTINGS
from navigator.widgets.file_ops.delete_dialog import DeleteDialog
from navigator.widgets.file_ops.delete_progress import DeleteProgress

from test_background_jobs import held_erase, put_cursor, run_shell, two, wait_for  # noqa: F401


# -- choosing a way ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({"TERM": "xterm-kitty"}, "osc9"),
        ({"TERM": "xterm-256color", "TERM_PROGRAM": "ghostty"}, "osc9"),
        ({"TERM": "xterm-256color", "TERM_PROGRAM": "WezTerm"}, "osc9"),
        ({"TERM": "xterm-256color", "WT_SESSION": "x"}, "osc9"),
        ({"TERM": "foot"}, "osc777"),
        ({"TERM": "rxvt-unicode-256color"}, "osc777"),
        ({"TERM": "xterm-256color"}, "none"),
        ({"TERM": "dumb", "KITTY_WINDOW_ID": "1"}, "none"),
        ({"TERM": "xterm-kitty", "NAVKIT_NOTIFY": "osc777"}, "osc777"),
        ({"TERM": "xterm-kitty", "NAVKIT_NOTIFY": "off"}, "none"),
    ],
)
def test_the_way_is_guessed_from_the_terminal(env, expected):
    assert TerminalInfo.detect(env).notifications == expected


def test_notify_send_is_the_fallback_on_a_local_desktop_only(tmp_path):
    program = tmp_path / "notify-send"
    program.write_text("#!/bin/sh\n")
    program.chmod(0o755)
    local = {"TERM": "xterm-256color", "DISPLAY": ":0", "PATH": str(tmp_path)}
    assert TerminalInfo.detect(local).notifications == "notify-send"
    assert TerminalInfo.detect({**local, "SSH_CONNECTION": "a b c d"}).notifications == "none"
    assert TerminalInfo.detect({**local, "DISPLAY": ""}).notifications == "none"
    assert TerminalInfo.detect({**local, "PATH": str(tmp_path / "nowhere")}).notifications == "none"


def test_focus_reports_are_asked_of_an_interactive_terminal():
    assert TerminalInfo.detect({"TERM": "xterm"}).focus_reports
    assert not TerminalInfo.detect({"TERM": "linux"}).focus_reports
    assert not TerminalInfo.detect({"TERM": "dumb"}).focus_reports
    assert not TerminalInfo.detect({"TERM": "xterm", "NAVKIT_FOCUS": "off"}).focus_reports


@pytest.mark.parametrize(
    ("setting", "detected", "expected"),
    [
        ("auto", "osc777", "osc777"),
        ("auto", "none", "none"),
        ("terminal", "osc777", "osc777"),
        ("terminal", "notify-send", "osc9"),
        ("notify-send", "osc9", "notify-send"),
        ("off", "osc9", "none"),
    ],
)
def test_the_setting_picks_the_way(setting, detected, expected):
    assert notify.method(setting, detected) == expected


# -- the sequences -------------------------------------------------------------------


def test_osc_9_and_777():
    assert notify_osc("osc9", "Copy", "Finished: a to b") == "\x1b]9;Copy: Finished: a to b\x07"
    assert notify_osc("osc777", "Co;py", "Finished; a") == "\x1b]777;notify;Co py;Finished; a\x07"
    assert notify_osc("none", "Copy", "x") == ""


def test_the_text_cannot_end_the_sequence_early():
    sequence = notify_osc("osc9", "a\x07b", "c\x1b]0;d\x9ce\nf")
    assert sequence == "\x1b]9;a b: c ]0;d e f\x07"
    long = notify_osc("osc777", "t", "x" * 1000)
    assert len(long) < 2 * NOTIFY_MAX
    # A leading digit would read as ConEmu's command.
    assert notify_osc("osc9", "", "4;1;50").startswith("\x1b]9;​4")


def test_inside_a_multiplexer_the_sequence_is_passed_through():
    tmux = notify_osc("osc9", "t", "b", multiplexer="tmux")
    assert tmux == "\x1bPtmux;\x1b\x1b]9;t: b\x07\x1b\\"
    assert notify_osc("osc9", "t", "b", multiplexer="screen") == "\x1bP\x1b]9;t: b\x07\x1b\\"


def test_the_terminal_writes_one_only_while_it_owns_the_screen():
    out = io.StringIO()
    terminal = Terminal(input_stream=io.StringIO(), output_stream=out, info=TerminalInfo(notifications="osc9"))
    assert not terminal.notify("t", "b")  # not started
    terminal.start()
    assert terminal.notify("t", "b")
    assert "\x1b]9;t: b\x07" in out.getvalue()
    assert terminal.notify("t", "b", kind="osc777")
    assert "\x1b]777;notify;t;b\x07" in out.getvalue()
    terminal.suspend()
    assert not terminal.notify("t", "b")
    terminal.resume()
    terminal.stop()
    off = Terminal(input_stream=io.StringIO(), output_stream=io.StringIO(), info=TerminalInfo())
    off.start()
    assert not off.notify("t", "b")
    off.stop()


def test_notify_send_runs_on_the_loop(monkeypatch):
    calls = []

    class Process:
        async def wait(self):
            return 0

    async def spawn(*argv, **kwargs):
        calls.append((argv, kwargs.get("stdin")))
        return Process()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)

    async def main():
        app = Application(Widget(), terminal=FakeTerminal())
        app._loop = asyncio.get_running_loop()
        assert navkit_notify.send(app, "Copy", "Finished", "notify-send", app_name="Navigator")
        await wait_until(lambda: bool(calls))

    asyncio.run(main())
    assert calls[0][0] == ("notify-send", "--app-name=Navigator", "--", "Copy", "Finished")


def test_notify_send_missing_is_no_error(monkeypatch):
    async def spawn(*argv, **kwargs):
        raise FileNotFoundError(argv[0])

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)

    async def main():
        await navkit_notify._notify_send("t", "b", "Navigator")

    asyncio.run(main())


# -- the application -----------------------------------------------------------------


def test_a_focus_report_is_kept_and_offered_to_no_widget():
    offered = []

    class Root(Widget):
        async def on_event(self, event):
            offered.append(event)

    app = Application(Root(), terminal=FakeTerminal())
    seen = []
    run_app(app, [
        lambda a: seen.append(a.terminal_focused),
        FocusEvent(False),
        lambda a: seen.append(a.terminal_focused),
        FocusEvent(True),
        lambda a: seen.append(a.terminal_focused),
    ])
    assert seen == [None, False, True]
    assert not any(isinstance(event, FocusEvent) for event in offered)


# -- a long job's end ----------------------------------------------------------------


@pytest.fixture
def notifications_setting():
    keep = SETTINGS.system.notifications
    yield
    SETTINGS.system.notifications = keep


def erase_and_wait(a, b, monkeypatch, focused, *, told, question=False):
    """An erase held until the box is sent away (or its question waits), then
    let finish: what the terminal had been told while the question waited, and
    by the end.  *told* is how many the caller expects by the end: they are
    waited for, not slept for, since the last is sent after the job's thread
    ends -- later still on a loaded machine.  None expected cannot be waited
    for, so a short settle stands in; a slow one could only make that pass."""
    release = threading.Event()
    answers: list = []
    ask_now = threading.Event()
    held_erase(monkeypatch, release, question="is it?" if question else None, answers=answers, ask_now=ask_now)

    async def steps(app, shell):
        app.terminal.info = TerminalInfo(notifications="osc9")
        manager = shell.manager

        async def answer(q, *, quiet=False):
            return "yes"

        manager._answer_erase_question = answer
        put_cursor(manager.left, "one.txt")
        app.post_event(KeyEvent("f8"))
        await wait_for(lambda: isinstance(app.modal, DeleteDialog))
        app.post_event(KeyEvent("enter"))
        await wait_for(lambda: isinstance(app.modal, DeleteProgress))
        if focused is not None:
            app.post_event(FocusEvent(focused))
        if question:
            # Sent away, so the question waits for the box and is told of.
            app.post_event(KeyEvent("enter"))
            await wait_for(lambda: bool(BACKGROUND.jobs))
            ask_now.set()
            await wait_for(lambda: BACKGROUND.asking)
            await wait_for(lambda: bool(app.terminal.notifications))
            asked = list(app.terminal.notifications)
            BACKGROUND.recall()
            await wait_for(lambda: bool(answers))
        else:
            asked = []
        release.set()
        await wait_for(lambda: app.modal is None and not BACKGROUND.jobs)
        if told:
            await wait_for(lambda: len(app.terminal.notifications) >= told)
        else:
            await asyncio.sleep(0.1)
        return asked, list(app.terminal.notifications)

    return run_shell(a, b, steps)


def test_a_long_job_tells_a_terminal_in_the_background_it_ended(two, monkeypatch, notifications_setting):
    a, b = two
    SETTINGS.system.notifications = "auto"
    _, told = erase_and_wait(a, b, monkeypatch, focused=False, told=1)
    assert told == [("Erase", "Finished: Erase one.txt", "osc9")]


@pytest.mark.parametrize("focused", [True, None])
def test_a_watched_or_unknown_terminal_is_not_told(two, monkeypatch, notifications_setting, focused):
    a, b = two
    SETTINGS.system.notifications = "auto"
    assert erase_and_wait(a, b, monkeypatch, focused=focused, told=0)[1] == []


def test_off_tells_no_one(two, monkeypatch, notifications_setting):
    a, b = two
    SETTINGS.system.notifications = "off"
    assert erase_and_wait(a, b, monkeypatch, focused=False, told=0)[1] == []


def test_a_question_waiting_is_told_of_once(two, monkeypatch, notifications_setting):
    a, b = two
    SETTINGS.system.notifications = "terminal"
    asked, told = erase_and_wait(a, b, monkeypatch, focused=False, question=True, told=2)
    assert asked == [("Erase", "Waiting for an answer: Erase one.txt", "osc9")]
    assert told == asked + [("Erase", "Finished: Erase one.txt", "osc9")]


def test_the_communications_page_sets_it(notifications_setting):
    from navigator.widgets.setup.communications_page import CommunicationsPage

    SETTINGS.system.notifications = "notify-send"
    page = CommunicationsPage()
    assert page.notifications.value == 2
    page.notifications.value = 3
    system = page.accept()["system"]
    assert system["notifications"] == "off" and system["desktop_vfs"] == SETTINGS.system.desktop_vfs
