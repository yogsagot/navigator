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
from navigator.widgets.console.console import prompt_cells

SHELLS = [
    pytest.param(name, marks=pytest.mark.skipif(
        shutil.which(name) is None, reason=f"{name} is not installed"))
    for name in ("bash", "zsh", "sh")
]


@pytest.fixture(autouse=True)
def home(tmp_path_factory, monkeypatch) -> Path:
    """A home of our own, whose rc files set the prompt DOS Navigator drew.

    The hook keeps whatever prompt the user's rc sets, so without this every
    expectation below would be the prompt of whoever runs the suite.
    """
    home = tmp_path_factory.mktemp("home")
    # Debian's /etc/bash.bashrc prints a sudo hint to a home without it.
    (home / ".sudo_as_admin_successful").touch()
    rc(home, bash="PS1='$PWD>'", zsh="PS1='%/>'")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("ZDOTDIR", raising=False)
    return home


def rc(home: Path, *, bash: str, zsh: str) -> None:
    (home / ".bashrc").write_text(bash + "\n")
    (home / ".zshrc").write_text(zsh + "\n")


def text(screen: ConsoleScreen) -> list[str]:
    return [line.rstrip() for line in screen.screen.display if line.strip()]


async def session(
    shell: str,
    commands: list[tuple[str, Path | None]],
    prompts: list[tuple[bytes, Path | None]] | None = None,
):
    """Run *commands* one after another and return the screen and what finished.

    Every prompt the shell prints is appended to *prompts*, if given.
    """
    screen = ConsoleScreen(80, 24)
    finished: list[tuple[int, Path | None]] = []
    done = asyncio.Event()

    def on_finished(status, cwd):
        finished.append((status, cwd))
        done.set()

    def on_prompt(data, cwd):
        if prompts is not None:
            prompts.append((data, cwd))

    subshell = Subshell(screen, shell=shutil.which(shell), on_finished=on_finished,
                        on_prompt=on_prompt)
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


HOOKED = [param for param in SHELLS if param.values[0] != "sh"]


@pytest.mark.parametrize("shell", HOOKED)
def test_the_prompt_is_the_user_s_own(shell, home, tmp_path):
    rc(home, bash=r"PS1='[\w] \$ '", zsh="PS1='[%~] %# '")
    prompts = []
    screen, _, _ = run(session(shell, [("echo hi", tmp_path)], prompts))
    sign = "$" if shell == "bash" else "%"
    assert prompts and prompts[-1][1] == tmp_path
    assert "".join(char for char, _ in prompt_cells(prompts[-1][0])) == f"[{tmp_path}] {sign} "
    # The same prompt is what the console log shows before the command.
    assert text(screen)[0] == f"[{tmp_path}] {sign} echo hi"


@pytest.mark.parametrize("shell", HOOKED)
def test_the_prompt_keeps_its_colours(shell, home, tmp_path):
    rc(home, bash=r"PS1='\[\e[32m\]ok\[\e[0m\]> '", zsh="PS1=$'%{\\e[32m%}ok%{\\e[0m%}> '")
    prompts = []
    run(session(shell, [("true", tmp_path)], prompts))
    cells = prompt_cells(prompts[-1][0])
    assert "".join(char for char, _ in cells) == "ok> "
    assert [style.fg for _, style in cells] == [2, 2, None, None]


def test_a_prompt_a_prompt_command_rebuilds_is_followed(home, tmp_path):
    if shutil.which("bash") is None:
        pytest.skip("bash is not installed")
    rc(home, bash="n=0; PROMPT_COMMAND='n=$((n+1)); PS1=\"p$n> \"'", zsh="")
    prompts = []
    screen, _, _ = run(session("bash", [("true", tmp_path), ("true", tmp_path)], prompts))
    shown = ["".join(char for char, _ in prompt_cells(data)) for data, _ in prompts]
    # The prompt after the last command may still be on its way when the
    # session stops: a command finishes at the D mark, before the prompt.
    assert shown[:2] == ["p1> ", "p2> "]
    assert text(screen) == ["p1> true", "p2> true"]


def test_the_last_line_of_a_multi_line_prompt_is_the_one_typed_on():
    cells = prompt_cells(b"\x1b[34mfirst line\r\nsecond> ")
    assert "".join(char for char, _ in cells) == "second> "
    # Colour set on the line above is still in force.
    assert cells[0][1].fg == 4


@pytest.mark.parametrize("shell", SHELLS)
def test_sync_moves_an_idle_shell_and_reprompts_there(shell, tmp_path):
    (tmp_path / "b").mkdir()

    async def go():
        screen = ConsoleScreen(80, 24)
        prompts: list[tuple[bytes, Path | None]] = []
        arrived = asyncio.Event()

        def on_prompt(data, cwd):
            prompts.append((data, cwd))
            arrived.set()

        subshell = Subshell(screen, shell=shutil.which(shell), on_prompt=on_prompt)
        try:
            # Asked before the shell is up: it is sent at the first prompt.
            subshell.sync(tmp_path / "b")
            subshell.start(tmp_path)
            while not prompts or prompts[-1][1] != tmp_path / "b":
                arrived.clear()
                await asyncio.wait_for(arrived.wait(), 10)
        finally:
            subshell.stop()
        return screen, prompts

    screen, prompts = run(go())
    assert prompts[-1][1] == tmp_path / "b"
    assert subshell_cd_left_no_trace(screen)


def subshell_cd_left_no_trace(screen: ConsoleScreen) -> bool:
    return not any("cd --" in line for line in text(screen))
