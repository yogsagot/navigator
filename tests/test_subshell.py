"""The shell behind the command line, on a real pty.

Like ``test_process.py`` these fork: the integration is a conversation with a
real shell's prompt hook, and nothing short of one says whether the rc file
it is handed says what it means.  Each shell that is installed is exercised;
one that is not is skipped rather than faked.
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
from pathlib import Path

import pytest

from navkit.console import ConsoleScreen
from navigator.subshell import MARK, Subshell
from navigator.widgets.shell.console.console import prompt_cells

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


@pytest.mark.parametrize("shell", SHELLS)
def test_a_line_editor_s_variables_are_not_inherited(shell, tmp_path, monkeypatch):
    # `nav` run from atuin's search with enter_accept inherits these from the
    # bind -x binding, and bash-preexec would then never fire preexec.
    monkeypatch.setenv("READLINE_POINT", "0")
    monkeypatch.setenv("COMP_POINT", "0")
    run(session(shell, [('echo "${READLINE_POINT-unset} ${COMP_POINT-unset}" >out', tmp_path)]))
    assert (tmp_path / "out").read_text() == "unset unset\n"


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


def test_bash_preexec_s_installer_stays_the_last_prompt_command(home, tmp_path):
    # bash-preexec installs itself from the first prompt; anything run after
    # its installer there switches preexec off for the first command, which
    # atuin then never records.  This stands in for it: the installer notes
    # whether our prompt command has already run.
    if shutil.which("bash") is None:
        pytest.skip("bash is not installed")
    rc(home, bash=(
        "__bp_install_string=$'__bp_trap_string=x\\n__fake_install'\n"
        "__fake_install() { echo ${__nav_wrapped:+after} >~/installed; "
        "PROMPT_COMMAND=${PROMPT_COMMAND//$__bp_install_string/:}; }\n"
        "PROMPT_COMMAND=$'true\\n'\"$__bp_install_string\""
    ), zsh="")
    _, finished, _ = run(session("bash", [("false", tmp_path)]))
    assert (home / "installed").read_text() == "after\n"
    assert finished == [(1, tmp_path)]


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


async def completion(shell: str, line: str, point: int, cwd: Path):
    """Start *shell* in *cwd*, ask it to complete, and return the answer and the screen."""
    screen = ConsoleScreen(80, 24)
    answer: list[tuple[int, list[str]]] = []
    ready, got = asyncio.Event(), asyncio.Event()
    subshell = Subshell(screen, shell=shutil.which(shell),
                        on_prompt=lambda data, where: ready.set())
    try:
        subshell.start(cwd)
        await asyncio.wait_for(ready.wait(), 10)
        # Cleared before asking: the prompt after the answer can arrive in
        # the same read as the answer itself.
        ready.clear()
        assert subshell.complete(line, point, cwd,
                                 lambda start, found: (answer.append((start, found)), got.set()))
        await asyncio.wait_for(got.wait(), 10)
        # And the shell is back at its prompt, ready for a command.
        await asyncio.wait_for(ready.wait(), 10)
    finally:
        subshell.stop()
    return answer[0], screen


@pytest.mark.parametrize("shell", HOOKED)
def test_the_first_word_completes_to_a_command(shell, tmp_path):
    (start, found), _ = run(completion(shell, "ech", 3, tmp_path))
    assert start == 0 and "echo" in found


@pytest.mark.parametrize("shell", HOOKED)
def test_a_later_word_completes_to_a_file_where_the_command_would_run(shell, tmp_path):
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subway.txt").write_text("")
    (start, found), screen = run(completion(shell, "ls sub", 6, tmp_path))
    assert start == 3
    assert sorted(found) == ["subdir", "subway.txt"]
    # Asked silently: nothing of the query reached the console.
    assert not any("__nav_complete" in line for line in text(screen))


def test_a_complete_function_is_asked_for_its_command(home, tmp_path):
    if shutil.which("bash") is None:
        pytest.skip("bash is not installed")
    rc(home, bash="PS1='$ '\n_greet() { COMPREPLY=($(compgen -W 'hello help' -- \"$2\")); }\n"
                  "complete -F _greet greet", zsh="")
    (start, found), _ = run(completion("bash", "greet he", 8, tmp_path))
    assert start == 6 and sorted(found) == ["hello", "help"]


def test_the_query_stays_out_of_the_history(home, tmp_path):
    if shutil.which("bash") is None:
        pytest.skip("bash is not installed")
    run(completion("bash", "ech", 3, tmp_path))
    history = home / ".bash_history"
    assert not history.exists() or "__nav_complete" not in history.read_text()


def test_sh_cannot_complete(tmp_path):
    async def go():
        subshell = Subshell(ConsoleScreen(80, 24), shell=shutil.which("sh"))
        try:
            subshell.start(tmp_path)
            return subshell.can_complete, subshell.complete("ech", 3, tmp_path, lambda *a: None)
        finally:
            subshell.stop()

    assert run(go()) == (False, False)


@pytest.mark.parametrize("shell", HOOKED)
def test_two_queries_in_a_row_are_each_answered_their_own(shell, tmp_path):
    # Typing sends the next query before the last is answered; each answer
    # has to reach the one that asked it, not the latest.
    (tmp_path / "navml").mkdir()
    (tmp_path / "navml" / "widgets").mkdir()

    async def go():
        screen = ConsoleScreen(80, 24)
        ready, answers = asyncio.Event(), {}
        subshell = Subshell(screen, shell=shutil.which(shell),
                            on_prompt=lambda data, where: ready.set())
        try:
            subshell.start(tmp_path)
            await asyncio.wait_for(ready.wait(), 10)
            both = asyncio.Event()

            def answer(name):
                def got(start, found):
                    answers[name] = found
                    if len(answers) == 2:
                        both.set()
                return got

            subshell.complete("ls navm", 7, tmp_path, answer("first"))
            subshell.complete("ls navml/", 9, tmp_path, answer("second"))
            await asyncio.wait_for(both.wait(), 10)
        finally:
            subshell.stop()
        return answers

    answers = run(go())
    assert answers == {"first": ["navml"], "second": ["navml/widgets"]}


async def started(shell: str, cwd: Path, **callbacks):
    """A subshell at its first prompt, and the event its prompts set."""
    ready = asyncio.Event()
    on_prompt = callbacks.pop("on_prompt", None)

    def prompted(data, where):
        ready.set()
        if on_prompt is not None:
            on_prompt(data, where)

    subshell = Subshell(ConsoleScreen(80, 24), shell=shutil.which(shell),
                        on_prompt=prompted, **callbacks)
    subshell.start(cwd)
    await asyncio.wait_for(ready.wait(), 10)
    return subshell, ready


@pytest.mark.parametrize("shell", HOOKED)
def test_the_history_is_the_shell_s_own_newest_first(shell, home, tmp_path):
    histfile = home / ("hist." + shell)
    histfile.write_text("echo first\necho second\n")
    rc(home, bash=f"PS1='$ '; HISTFILE={histfile}; history -r",
       zsh=f"PS1='$ '; HISTFILE={histfile}; fc -R")

    async def go():
        subshell, _ = await started(shell, tmp_path)
        got = asyncio.Event()
        entries = []
        try:
            assert subshell.history(lambda found: (entries.extend(found), got.set()))
            await asyncio.wait_for(got.wait(), 10)
        finally:
            subshell.stop()
        return entries

    entries = run(go())
    assert entries[:2] == ["echo second", "echo first"]


def test_silent_lines_stay_out_of_the_history_without_ignorespace(home, tmp_path):
    # bash-preexec strips ignorespace from HISTCONTROL at its first prompt, so
    # the silent cd and the history query itself would otherwise be listed.
    if shutil.which("bash") is None:
        pytest.skip("bash is not installed")
    rc(home, bash="PS1='$ '; PROMPT_COMMAND='HISTCONTROL=${HISTCONTROL//ignorespace}'", zsh="")
    (tmp_path / "sub").mkdir()

    async def go():
        done = asyncio.Event()
        subshell, _ = await started("bash", tmp_path, on_finished=lambda *_: done.set())
        got = asyncio.Event()
        entries = []
        try:
            subshell.run("echo typed", tmp_path / "sub")   # a silent cd first
            await asyncio.wait_for(done.wait(), 10)
            assert subshell.history(lambda found: (entries.extend(found), got.set()))
            await asyncio.wait_for(got.wait(), 10)
        finally:
            subshell.stop()
        return entries

    assert run(go()) == ["echo typed"]


@pytest.mark.parametrize("shell", HOOKED)
def test_no_atuin_binding_means_readline_s_keys(shell, tmp_path):
    async def go():
        subshell, _ = await started(shell, tmp_path)
        subshell.stop()
        return subshell.up_binding, subshell.search_binding

    assert run(go()) == (None, None)


def fake_atuin(home: Path) -> Path:
    """An ``atuin`` that draws on the terminal and chooses ``chosen command``.

    atuin's own shell integration swaps descriptors, so what it chooses is
    written to its standard error and what it draws to its standard output.
    """
    bin_dir = home / "bin"
    bin_dir.mkdir(exist_ok=True)
    atuin = bin_dir / "atuin"
    atuin.write_text('#!/bin/sh\necho "FAKE ATUIN $ATUIN_QUERY"\necho "chosen command" >&2\n')
    atuin.chmod(0o755)
    return bin_dir


def test_an_atuin_up_binding_is_recognised_and_run(home, tmp_path, monkeypatch):
    if shutil.which("bash") is None:
        pytest.skip("bash is not installed")
    bin_dir = fake_atuin(home)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    rc(home, bash="PS1='$ '\n__atuin_history() { :; }\n"
                  "bind -x '\"\\e[A\": __atuin_history --shell-up-key-binding'\n"
                  "bind -x '\"\\C-r\": __atuin_history'", zsh="")
    finished = []

    async def go():
        subshell, ready = await started("bash", tmp_path,
                                        on_finished=lambda *a: finished.append(a))
        chosen = []
        try:
            bindings = subshell.up_binding, subshell.search_binding
            ready.clear()
            assert subshell.search_history("ls", ["--shell-up-key-binding"], chosen.append)
            assert subshell.busy  # the search has the keys while it runs
            await asyncio.wait_for(ready.wait(), 10)
        finally:
            subshell.stop()
        return bindings, chosen, subshell

    bindings, chosen, subshell = run(go())
    assert bindings == ("atuin", "atuin")
    assert chosen == ["chosen command"]
    assert not subshell.busy and finished == []  # no command finished
    shown = text(subshell.screen)
    assert "FAKE ATUIN ls" in shown
    assert not any("__nav_atuin" in line for line in shown)
