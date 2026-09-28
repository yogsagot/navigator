"""The shell behind the command line, on a real pty.

Like ``test_process.py`` these fork: the integration is a conversation with a
real shell's prompt hook, and nothing short of one says whether the rc file
it is handed says what it means.  Each shell that is installed is exercised;
one that is not is skipped rather than faked.
"""

from __future__ import annotations

import asyncio
import re
import shutil
from pathlib import Path

import pytest

from navkit.console import ConsoleScreen
from navigator.subshell import MARK, Subshell

SHELLS = [
    pytest.param(name, marks=pytest.mark.skipif(
        shutil.which(name) is None, reason=f"{name} is not installed"))
    for name in ("bash", "zsh", "sh")
]


def text(screen: ConsoleScreen) -> list[str]:
    return [line.rstrip() for line in screen.screen.display if line.strip()]


async def session(shell: str, commands: list[tuple[str, Path | None]]):
    """Run *commands* one after another and return the screen and what finished."""
    screen = ConsoleScreen(80, 24)
    finished: list[tuple[int, Path | None]] = []
    done = asyncio.Event()

    def on_finished(status, cwd):
        finished.append((status, cwd))
        done.set()

    subshell = Subshell(screen, shell=shutil.which(shell), on_finished=on_finished)
    try:
        for command, cwd in commands:
            done.clear()
            subshell.run(command, cwd)
            await asyncio.wait_for(done.wait(), 10)
    finally:
        subshell.stop()
    return screen, finished, subshell


def run(coro):
    return asyncio.run(coro)


@pytest.mark.parametrize("shell", SHELLS)
def test_a_command_finishes_with_its_status_and_directory(shell, tmp_path):
    screen, finished, _ = run(session(shell, [("echo hi; false", tmp_path)]))
    assert finished == [(1, tmp_path)]
    # The prompt the shell printed and was held back, then its echo, then the
    # output -- DOS Navigator's `DosWrite(ActiveDir + '>' + S)`.
    assert text(screen) == [f"{tmp_path}>echo hi; false", "hi"]


@pytest.mark.parametrize("shell", SHELLS)
def test_a_cd_on_the_command_line_is_reported(shell, tmp_path):
    (tmp_path / "sub").mkdir()
    _, finished, _ = run(session(shell, [("cd sub", tmp_path)]))
    assert finished == [(0, tmp_path / "sub")]


@pytest.mark.parametrize("shell", SHELLS)
def test_the_panel_s_directory_reaches_the_shell_silently(shell, tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    screen, finished, _ = run(session(shell, [
        ("pwd", tmp_path / "a"),
        ("pwd", tmp_path / "b"),   # a different directory: a silent cd first
    ]))
    assert [cwd for _, cwd in finished] == [tmp_path / "a", tmp_path / "b"]
    # Nothing of the cd is on the screen: not its echo, not a second prompt.
    assert text(screen) == [
        f"{tmp_path / 'a'}>pwd", str(tmp_path / "a"),
        f"{tmp_path / 'b'}>pwd", str(tmp_path / "b"),
    ]


@pytest.mark.parametrize("shell", SHELLS)
def test_a_line_with_a_tab_in_it_is_not_completed(shell, tmp_path):
    screen, finished, _ = run(session(shell, [("printf '%s|' a\tb", tmp_path)]))
    assert finished[0][0] == 0
    assert "a|b|" in text(screen)[-1]


def test_a_shell_that_exits_finishes_the_command(tmp_path):
    # No prompt comes back, so the command is finished by the exit instead,
    # with the wait status -- and the next command starts another shell.
    _, finished, subshell = run(session("sh", [("exit 3", tmp_path)]))
    assert finished == [(3 << 8, tmp_path)]
    assert not subshell.is_running


def detached(finished: list) -> Subshell:
    """A subshell that never forks, listening for marks with the nonce ``n``."""
    subshell = Subshell(ConsoleScreen(40, 5),
                        on_finished=lambda s, c: finished.append((s, c)))
    subshell._marks = re.compile(
        rb"\x1b\]%d;n;([ABD])(?:;([^\x07\x1b]*))?(?:\x07|\x1b\\)" % MARK
    )
    subshell.busy = True
    return subshell


def test_a_mark_split_across_two_reads_is_still_a_mark():
    finished = []
    subshell = detached(finished)
    screen = subshell.screen
    mark = b"\x1b]%d;n;D;0;/tmp\x07" % MARK
    subshell._on_output(b"out\r\n" + mark[:9])
    assert finished == []
    subshell._on_output(mark[9:])
    assert finished == [(0, Path("/tmp"))]
    assert text(screen) == ["out"]


def test_a_mark_with_the_wrong_nonce_is_only_output():
    finished = []
    subshell = detached(finished)
    subshell._on_output(b"\x1b]%d;forged;D;0;/tmp\x07" % MARK)
    assert finished == []
    assert subshell.busy
