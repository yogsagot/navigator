"""Utilities > Process list: reading ``/proc``, and the window that lists it."""

from __future__ import annotations

import errno
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from navkit.events import KeyEvent, MouseClickEvent

from conftest import Until, run_app

from navigator.lib.system import processes
from navigator.lib.system.processes import Process, Row


def stat_line(pid: int, comm: str, state: str = "S", ppid: int = 1, ticks: tuple[int, int] = (0, 0),
              started: int = 100, rss_pages: int = 10) -> str:
    # pid (comm) state ppid pgrp session tty tpgid flags minflt cminflt majflt cmajflt
    # utime stime cutime cstime priority nice threads itreal starttime vsize rss ...
    fields = [state, ppid, 1, 1, 0, -1, 0, 0, 0, 0, 0, ticks[0], ticks[1], 0, 0, 20, 0, 1, 0,
              started, 4096 * 100, rss_pages]
    return f"{pid} ({comm}) " + " ".join(str(field) for field in fields) + " 0 0 0\n"


def fake_proc(root: Path, entries: list[dict]) -> Path:
    """A ``/proc`` with one directory per entry and a ``stat`` of the machine."""
    root.mkdir(exist_ok=True)
    (root / "stat").write_text("cpu  100 0 100 800 0 0 0 0 0 0\nbtime 1700000000\n")
    (root / "self").mkdir(exist_ok=True)
    (root / "self" / "stat").write_text("1 (x) S\n")
    for entry in entries:
        where = root / str(entry["pid"])
        where.mkdir()
        (where / "stat").write_text(stat_line(entry["pid"], entry.get("comm", "x"), entry.get("state", "S"),
                                              entry.get("ppid", 1), entry.get("ticks", (0, 0)),
                                              entry.get("started", 100)))
        (where / "status").write_text(f"Name:\t{entry.get('comm', 'x')}\nUid:\t{entry.get('uid', 0)}\t0\t0\t0\n")
        (where / "cmdline").write_bytes(b"\0".join(word.encode() for word in entry.get("argv", [])))
    return root


def test_a_name_holding_spaces_and_a_parenthesis_is_read_whole(tmp_path):
    proc = fake_proc(tmp_path / "proc", [{"pid": 42, "comm": "odd) name (x", "argv": ["/bin/odd", "-v"],
                                          "uid": os.getuid(), "ticks": (3, 4)}])
    found = processes.read(42, proc)
    assert found is not None
    assert found.name == "odd) name (x"
    assert found.command == "/bin/odd -v"
    assert found.ticks == 7
    assert found.uid == os.getuid()
    assert found.rss == 10 * processes.PAGE_SIZE


def test_a_kernel_thread_has_its_name_in_brackets_and_a_vanished_one_is_left_out(tmp_path):
    proc = fake_proc(tmp_path / "proc", [{"pid": 2, "comm": "kthreadd", "ppid": 0}, {"pid": 7}])
    (proc / "7" / "stat").unlink()
    found = processes.gather(proc)
    assert [each.pid for each in found] == [2]
    assert found[0].command == "[kthreadd]"
    assert found[0].kernel_thread


def test_cpu_share_is_the_ticks_since_the_last_read_over_the_machines(tmp_path):
    def process(ticks: int, started: int = 100) -> Process:
        return Process(5, 1, 0, "root", "R", 1, 0, 0, ticks, started, "busy", "busy")

    sampler = processes.Sampler(tmp_path)
    assert sampler.sample([process(10)], machine=1000, cpus=4)[0].cpu == 0.0
    assert sampler.sample([process(60)], machine=1200, cpus=4)[0].cpu == pytest.approx(100.0)
    # Its number given to another: nothing to compare with.
    assert sampler.sample([process(500, started=999)], machine=1400, cpus=4)[0].cpu == 0.0


def test_the_tree_puts_children_under_parents_and_an_orphan_at_the_root():
    def process(pid: int, ppid: int, command: str) -> Process:
        return Process(pid, ppid, 0, "root", "S", 1, 0, 0, 0, 0, command, command)

    rows = processes.tree([process(1, 0, "init"), process(30, 1, "b"), process(20, 1, "a"),
                           process(21, 20, "a1"), process(99, 77, "orphan")], by="command")
    assert [(row.process.pid, row.depth, row.last) for row in rows] == [
        (1, 0, False), (20, 1, False), (21, 2, True), (30, 1, True), (99, 0, True)]
    assert rows[2].rails == (True,)


def test_ordered_sorts_by_each_key_and_breaks_ties_by_number():
    a = Process(3, 1, 0, "zed", "S", 1, 500, 0, 0, 0, "a", "alpha", cpu=1.0)
    b = Process(1, 1, 0, "amy", "R", 1, 900, 0, 0, 0, "b", "Beta", cpu=5.0)
    c = Process(2, 1, 0, "amy", "S", 1, 100, 0, 0, 0, "c", "gamma", cpu=1.0)
    assert [p.pid for p in processes.ordered([a, b, c], "pid", False)] == [1, 2, 3]
    assert [p.pid for p in processes.ordered([a, b, c], "user", False)] == [1, 2, 3]
    assert [p.pid for p in processes.ordered([a, b, c], "memory", True)] == [1, 3, 2]
    assert [p.pid for p in processes.ordered([a, b, c], "cpu", True)] == [1, 2, 3]
    assert [p.pid for p in processes.ordered([a, b, c], "command", False)] == [3, 1, 2]


def test_send_refuses_init_and_navigator_itself():
    for pid in (1, 0, os.getpid()):
        with pytest.raises(PermissionError):
            processes.send(pid, 0)


def test_a_signal_reaches_a_child_and_not_one_whose_number_was_given_again():
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        found = processes.read(child.pid)
        assert found is not None
        with pytest.raises(ProcessLookupError):
            processes.signal_process(Process(**{**found.__dict__, "started": found.started + 1}), signal.SIGTERM)
        assert child.poll() is None
        processes.signal_process(found, signal.SIGTERM)
        assert child.wait(timeout=5) == -signal.SIGTERM
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()


def test_details_tell_the_parent_and_the_start_time(tmp_path):
    proc = fake_proc(tmp_path / "proc", [{"pid": 1, "comm": "init"}, {"pid": 8, "comm": "sh", "argv": ["sh"]}])
    lines = dict(processes.details(8, proc))
    assert lines["Parent"] == "1 init"
    assert lines["Command"] == "sh"
    assert lines["Started"].startswith("2023-11-1")
    with pytest.raises(ProcessLookupError):
        processes.details(9, proc)


# -- the window --------------------------------------------------------------


def fake_processes() -> list[Process]:
    me, root = os.getuid(), 0 if os.getuid() else 4242
    return [
        Process(1, 0, root, "root", "S", 1, 10 << 20, 0, 0, 1, "init", "/sbin/init"),
        Process(300, 1, me, "me", "S", 1, 50 << 20, 0, 0, 2, "bash", "/bin/bash"),
        Process(310, 300, me, "me", "R", 1, 200 << 20, 0, 0, 3, "vim", "vim notes.txt"),
        Process(200, 1, root, "root", "S", 1, 5 << 20, 0, 0, 4, "cron", "/usr/sbin/cron -f"),
    ]


def process_run(where, monkeypatch, *actions):
    from test_nav import navigator

    from navigator.settings import SETTINGS

    monkeypatch.setattr(processes, "gather", lambda proc=processes.PROC: fake_processes())
    monkeypatch.setattr(SETTINGS.processes, "refresh", 0)
    app = navigator(where)

    def open_it(a):
        from navigator.widgets.shell.commands import OpenProcessWindow

        a.spawn(a.run_command(OpenProcessWindow))

    def listed(a):
        window = a.shell.desktop.active_window
        return getattr(window, "processes", None) is not None and bool(window.processes.items)

    run_app(app, [open_it, Until(listed), *actions, lambda a: None])
    return app


def pids(a) -> list[int]:
    return [row.process.pid for row in a.shell.desktop.active_window.processes.items]


def test_the_window_lists_by_number_and_the_sort_keys_turn_round_when_pressed_again(tmp_path, monkeypatch):
    seen = []
    look = lambda a: seen.append(pids(a))  # noqa: E731
    process_run(tmp_path, monkeypatch, look, KeyEvent("z", ctrl=True), look, KeyEvent("z", ctrl=True), look,
                KeyEvent("n", ctrl=True), look)
    assert seen[0] == [1, 200, 300, 310]
    assert seen[1] == [310, 300, 1, 200]
    assert seen[2] == [200, 1, 300, 310]
    assert seen[3] == [300, 1, 200, 310]


def test_a_click_on_a_title_sorts_by_its_column(tmp_path, monkeypatch):
    seen = []

    def click_memory(a):
        listing = a.shell.desktop.active_window.processes
        x, _ = listing.columns()[4]
        ox, oy = listing.offset()
        a.post_event(MouseClickEvent(ox + listing.x + x + 2, oy + listing.y + listing.inset, "left", "press"))

    process_run(tmp_path, monkeypatch, click_memory,
                lambda a: seen.append((pids(a), a.shell.desktop.active_window.sort)))
    assert seen == [([310, 300, 1, 200], "memory")]


def test_the_cursor_stays_on_its_process_when_read_again_and_the_tree_and_mine_only_boxes_list_again(
        tmp_path, monkeypatch):
    seen = []

    def to_vim(a):
        listing = a.shell.desktop.active_window.processes
        listing.cursor = pids(a).index(310)

    def look(a):
        window = a.shell.desktop.active_window
        seen.append((pids(a), window.processes.selected.process.pid,
                     [window.processes.branch(row) for row in window.processes.items]))

    process_run(tmp_path, monkeypatch, to_vim, KeyEvent("r", ctrl=True), look,
                KeyEvent("t", ctrl=True), look, KeyEvent("h", ctrl=True), look)
    assert seen[0][:2] == ([1, 200, 300, 310], 310)
    assert seen[1][:2] == ([1, 200, 300, 310], 310)
    assert seen[1][2] == ["", "├─", "└─", "  └─"]
    assert seen[2][:2] == ([300, 310], 310)


def test_typing_searches_and_f3_shows_the_details(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(processes, "details", lambda pid, proc=processes.PROC: [("Process", str(pid))])
    process_run(tmp_path, monkeypatch, KeyEvent("c", char="c"), KeyEvent("r", char="r"),
                lambda a: seen.append(a.shell.desktop.active_window.processes.selected.process.pid),
                KeyEvent("escape"), KeyEvent("f3"), Until(lambda a: a.modal is not None),
                lambda a: seen.append(type(a.modal).__name__), KeyEvent("enter"))
    assert seen == [200, "Dialog"]


def test_f8_asks_then_sends_sigterm_and_a_refusal_offers_as_root(tmp_path, monkeypatch):
    from navigator.lib.system import elevate
    from navigator.widgets.file_ops import as_root

    sent = []
    asked = []

    def refuse(process, sig):
        sent.append((process.pid, sig))
        raise PermissionError(errno.EPERM, "Operation not permitted")

    async def no_root(app, message, **kwargs):
        asked.append(message)
        return False

    monkeypatch.setattr(processes, "signal_process", refuse)
    monkeypatch.setattr(elevate.ELEVATION, "available", lambda: True)
    monkeypatch.setattr(as_root, "ask_as_root", no_root)

    def to_cron(a):
        a.shell.desktop.active_window.processes.cursor = pids(a).index(200)

    process_run(tmp_path, monkeypatch, to_cron, KeyEvent("f8"), Until(lambda a: a.modal is not None),
                KeyEvent("enter"), Until(lambda a: bool(asked)))
    assert sent == [(200, signal.SIGTERM)]
    assert "200" in asked[0] and "cron" in asked[0]


def test_init_is_not_offered_a_signal(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(processes, "signal_process", lambda process, sig: seen.append("sent"))

    def look(a):
        window = a.shell.desktop.active_window
        seen.append((window.processes.selected.process.pid, window.allows("signal"),
                     window.refusal(window.processes.selected and __import__(
                         "navigator.widgets.shell.commands", fromlist=["KillProcess"]).KillProcess())))

    process_run(tmp_path, monkeypatch, look, KeyEvent("f8"), lambda a: seen.append(a.modal))
    assert seen[0][:2] == (1, False) and seen[0][2]
    assert seen[1:] == [None]


# -- the root helper ---------------------------------------------------------


def test_the_helpers_kill_signals_a_child_and_refuses_init():
    from navigator.lib.system import roothelper

    helper = roothelper._Helper()
    assert "kill" in roothelper.OPS
    with pytest.raises(OSError) as refused:
        helper.kill(1, 0)
    assert refused.value.errno == errno.EPERM
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        helper.kill(child.pid, signal.SIGTERM)
        assert child.wait(timeout=5) == -signal.SIGTERM
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()


def test_a_refused_signal_is_sent_by_the_root_helper(tmp_path, monkeypatch):
    """The helper runs as the user here, so it may signal the user's own child:
    refused once by the window's own ``kill``, sent by the helper's."""
    from navigator.lib.drives import root, unmount
    from navigator.lib.system import elevate
    from navigator.widgets.file_ops import as_root

    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    found = processes.read(child.pid)
    assert found is not None
    asked = []

    def refuse(pid, sig):
        raise PermissionError(errno.EPERM, "Operation not permitted")

    async def yes(app, message, **kwargs):
        asked.append(message)
        return await as_root.open_root(app)

    monkeypatch.setattr(processes, "send", refuse)
    monkeypatch.setattr(as_root, "ask_as_root", yes)
    monkeypatch.setattr(as_root, "untrusted_code", lambda: None)
    elevate.ELEVATION.command = [sys.executable, "-I", "-c", elevate._BOOT]
    try:
        from navigator.widgets.shell.commands import SendSignal

        # The window lists the child alone, so the cursor is on it.
        monkeypatch.setitem(globals(), "fake_processes", lambda: [found])
        process_run(tmp_path, monkeypatch, lambda a: a.spawn(a.run_command(SendSignal(int(signal.SIGTERM)))),
                    Until(lambda a: child.poll() is not None, timeout=10))
        assert child.wait(timeout=5) == -signal.SIGTERM
        assert asked
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()
        root._HOLDERS.clear()
        unmount(root.ROOT_SITE)
        elevate.ELEVATION.close()
        elevate.ELEVATION.command = None
