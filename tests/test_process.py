"""Running a child on a pty this application owns.

``FakeTerminal`` cannot stand in here: the point of the module is a real fork
onto a real pty, so these tests use one.  They are the only tests in the suite
that start processes, and each one waits on the child's own exit rather than
on a timer.
"""

from __future__ import annotations

import asyncio
import os
import signal

import pytest

from navkit.console import ConsoleScreen
from navkit.events import KeyEvent
from navkit.process import MARKER, PtyProcess
from navkit.style import RED
from navkit.terminal import encode_key


def run(coro, timeout: float = 10.0):
    return asyncio.run(asyncio.wait_for(coro, timeout))


async def collect(argv, *, columns: int = 40, lines: int = 6, feed: bytes = b""):
    """Run *argv* to completion and return its console screen and the process."""
    console = ConsoleScreen(columns, lines)
    finished = asyncio.Event()
    process = PtyProcess(
        argv,
        columns=columns,
        lines=lines,
        on_output=console.feed,
        on_exit=lambda status: finished.set(),
    )
    process.start()
    if feed:
        process.write(feed)
    await finished.wait()
    return console, process


def text_of(console: ConsoleScreen, row: int) -> str:
    surface = console.surface
    return "".join(
        surface.get(x, row)[0] or " " for x in range(console.columns)
    ).rstrip()


def test_a_childs_output_arrives_as_cells():
    console, process = run(collect(["/bin/sh", "-c", "printf 'hello\\r\\n'"]))
    assert text_of(console, 0) == "hello"
    assert process.status == 0
    assert not process.is_running


def test_a_childs_colours_arrive_too():
    console, _ = run(
        collect(["/bin/sh", "-c", "printf '\\033[31mred\\033[0m\\r\\n'"])
    )
    assert text_of(console, 0) == "red"
    assert console.surface.get(0, 0)[1].fg == RED


def test_a_failing_child_reports_its_status():
    _, process = run(collect(["/bin/sh", "-c", "exit 3"]))
    assert os.waitstatus_to_exitcode(process.status) == 3


def test_a_child_that_cannot_be_executed_exits_rather_than_hanging():
    _, process = run(collect(["/nonexistent/definitely-not-a-program"]))
    assert os.waitstatus_to_exitcode(process.status) == 127


def test_the_child_is_told_it_is_running_inside_navigator():
    console, _ = run(collect(["/bin/sh", "-c", f"printf '%s\\r\\n' \"${MARKER}\""]))
    assert text_of(console, 0) == "1"


def test_the_child_is_told_how_big_its_terminal_is():
    console, _ = run(
        collect(["/bin/sh", "-c", "stty size 2>/dev/null || echo unavailable"],
                columns=40, lines=6)
    )
    # `stty size' prints rows then columns, which is the order TIOCSWINSZ
    # takes them in and the easiest pair to transpose.
    assert text_of(console, 0) in ("6 40", "unavailable")


def test_what_is_written_reaches_the_childs_stdin():
    console, _ = run(
        collect(["/bin/sh", "-c", "read line; printf 'got %s\\r\\n' \"$line\""],
                feed=b"typed\r")
    )
    assert "got typed" in "\n".join(text_of(console, y) for y in range(6))


def test_a_key_event_can_be_typed_at_a_child():
    console, _ = run(
        collect(["/bin/sh", "-c", "read line; printf 'got %s\\r\\n' \"$line\""],
                feed=encode_key(KeyEvent("h", "h")) + encode_key(KeyEvent("enter")))
    )
    assert "got h" in "\n".join(text_of(console, y) for y in range(6))


def test_resizing_signals_the_child():
    async def drive():
        console = ConsoleScreen(40, 6)
        finished = asyncio.Event()
        process = PtyProcess(
            # Report the size again whenever the kernel says it changed.
            ["/bin/sh", "-c", "trap 'stty size; exit 0' WINCH; sleep 5 & wait"],
            columns=40,
            lines=6,
            on_output=console.feed,
            on_exit=lambda status: finished.set(),
        )
        process.start()
        await asyncio.sleep(0.4)
        process.set_size(30, 9)
        await finished.wait()
        return console

    console = run(drive())
    printed = "\n".join(text_of(console, y) for y in range(6))
    assert "9 30" in printed


def test_a_child_can_be_terminated():
    async def drive():
        finished = asyncio.Event()
        process = PtyProcess(
            ["/bin/sh", "-c", "sleep 30"],
            on_exit=lambda status: finished.set(),
        )
        process.start()
        await asyncio.sleep(0.2)
        process.terminate()
        await finished.wait()
        return process

    process = run(drive())
    assert not process.is_running


def test_starting_twice_is_refused():
    async def drive():
        finished = asyncio.Event()
        process = PtyProcess(["/bin/sh", "-c", "exit 0"],
                             on_exit=lambda status: finished.set())
        process.start()
        with pytest.raises(RuntimeError):
            process.start()
        await finished.wait()

    run(drive())
