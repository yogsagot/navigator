"""The shell behind the command line: one, long-lived, and never shown its prompt.

DOS Navigator ran each command line by quitting to its loader, which handed the
string to ``COMSPEC /C`` and restarted the file manager afterwards
(``RUNCMD.INC``'s ``ExecString``, ``DN.ASM``).  The current directory survived
the round trip because DOS kept it globally, so a ``cd`` typed on the command
line moved the panel the file manager came back to.  A POSIX process cannot
change its parent's directory, so the nearest thing that keeps that property is
a shell that outlives every command: the user's ``$SHELL``, on the console's
pty, with their own rc files loaded -- aliases, functions and variables
included -- and one hook added after them.

**The hook is how the shell talks back.**  Before every prompt it prints a
private OSC carrying the last command's status and the shell's ``$PWD``, and it
brackets the prompt itself between two more.  So Navigator learns

* *when a command finished*, which is when the panels come back;
* *where the shell is*, which is how a typed ``cd`` moves the active panel;
* *which bytes are the prompt*, which are **held back** rather than painted.
  The command line is the prompt the user types at; a second one sitting in the
  console would be a lie about where the keys go.  The held-back prompt is
  painted only when a command is sent, immediately before the shell echoes
  it, so the console log reads ``/home/user>ls`` -- which is what DOS
  Navigator's ``DosWrite(ActiveDir + '>' + S)`` left on the user screen.

Each mark is ``ESC ] 6973 ; <nonce> ; <kind> [; <data>] BEL``.  The nonce is
random per shell, so a program that happens to print something mark-shaped --
a nested shell with the same rc, a ``cat`` of this file -- cannot forge a
finished command.  A mark with a foreign nonce is not a mark and goes to the
screen, where the emulator drops an OSC it does not know.

**The directory flows both ways.**  The shell tells Navigator where it is after
every command; Navigator tells the shell where the active panel is before one,
with a *silent* ``cd``: a leading space keeps it out of the history, and
everything the shell prints until its next prompt is swallowed.  Only when the
two differ, so an ordinary command costs no extra round trip.
"""

from __future__ import annotations

import os
import re
import secrets
import shlex
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from navkit.console import ConsoleScreen
from navkit.events import Event
from navkit.process import PtyProcess

#: The OSC number the marks are carried under.  Private: no terminal assigns it.
MARK = 6973

#: Bracketed paste on and off, as the shell's line editor announces them.
_PASTE_ON = b"\x1b[?2004h"
_PASTE_OFF = b"\x1b[?2004l"


@dataclass(frozen=True, slots=True)
class CommandFinished(Event):
    """The shell is back at its prompt after a command the command line sent.

    Posted to the application rather than called from the pty's reader, so
    whatever it changes -- the panels coming back, the focus, a panel's
    directory -- is dispatched and painted with a batch like any keystroke.
    """

    status: int
    cwd: Path | None


def _bash_rc(nonce: str) -> str:
    # $? is caught first and the mark printed last, so a prompt command the
    # user's rc installed -- starship, a git prompt -- neither clobbers the
    # status nor rewrites PS1 after us.  PROMPT_COMMAND may be an array in
    # bash 5.1 and later, and appending to an array's first element would put
    # the other elements after the mark.
    mark = f"\\033]{MARK};{nonce}"
    return f"""\
[ -r /etc/bash.bashrc ] && . /etc/bash.bashrc
[ -r ~/.bashrc ] && . ~/.bashrc
__nav_prompt() {{
    local p=${{PWD//\\\\/\\\\\\\\}}
    p=${{p//\\$/\\\\\\$}}
    p=${{p//\\`/\\\\\\`}}
    printf '{mark};D;%s;%s\\007' "$__nav_status" "$PWD"
    PS1="\\[{mark};A\\007\\]$p>\\[{mark};B\\007\\]"
    PS2=''
}}
if [[ "$(declare -p PROMPT_COMMAND 2>/dev/null)" == "declare -a"* ]]; then
    PROMPT_COMMAND=('__nav_status=$?' "${{PROMPT_COMMAND[@]}}" __nav_prompt)
else
    PROMPT_COMMAND="__nav_status=\\$?;${{PROMPT_COMMAND:+$PROMPT_COMMAND;}}__nav_prompt"
fi
HISTCONTROL="ignorespace${{HISTCONTROL:+:$HISTCONTROL}}"
"""


def _zsh_env() -> str:
    # zsh reads every startup file from $ZDOTDIR, so it is pointed here and
    # each of these reads the user's own from where it really is.
    return """\
__nav_zdotdir=$ZDOTDIR
ZDOTDIR=${NAV_USER_ZDOTDIR:-$HOME}
[[ -r $ZDOTDIR/.zshenv ]] && source $ZDOTDIR/.zshenv
NAV_USER_ZDOTDIR=$ZDOTDIR
ZDOTDIR=$__nav_zdotdir
"""


def _zsh_rc(nonce: str) -> str:
    mark = f"\\e]{MARK};{nonce}"
    return f"""\
ZDOTDIR=$NAV_USER_ZDOTDIR
unset NAV_USER_ZDOTDIR __nav_zdotdir
[[ -r $ZDOTDIR/.zshrc ]] && source $ZDOTDIR/.zshrc
[[ $ZDOTDIR == $HOME ]] && unset ZDOTDIR
__nav_status() {{ __nav_s=$? }}
__nav_prompt() {{
    printf '{mark};D;%s;%s\\a' "$__nav_s" "$PWD"
    PS1=$'%{{{mark};A\\a%}}%/>%{{{mark};B\\a%}}'
    PS2='' RPS1='' RPROMPT=''
}}
precmd_functions=(__nav_status $precmd_functions __nav_prompt)
setopt HIST_IGNORE_SPACE
"""


def _sh_rc(nonce: str) -> str:
    # No prompt hook in a POSIX shell, so the mark lives in PS1 itself, which
    # every shell here expands parameters in.  One that does not reports a
    # status that is not a number and a directory that is not absolute, and
    # both are ignored rather than trusted.
    esc, bel = "\033", "\007"
    mark = f"{esc}]{MARK};{nonce}"
    return (
        f"PS1='{mark};D;$?;$PWD{bel}{mark};A{bel}$PWD>{mark};B{bel}'\n"
        "PS2=''\n"
    )


def shell_argv(shell: str, directory: Path, nonce: str) -> tuple[list[str], dict[str, str]]:
    """The command line and extra environment that start *shell* with the hook.

    The rc files are written into *directory*.  bash and zsh are integrated in
    their own terms; anything else -- fish, tcsh -- has no hook written for
    it, so bash stands in if it is installed and a POSIX ``sh`` otherwise.
    """
    name = Path(shell).name
    if name not in ("bash", "zsh", "sh", "dash"):
        shell = shutil.which("bash") or "/bin/sh"
        name = Path(shell).name
    if name == "bash":
        rc = directory / "bashrc"
        rc.write_text(_bash_rc(nonce))
        return [shell, "--rcfile", str(rc), "-i"], {}
    if name == "zsh":
        (directory / ".zshenv").write_text(_zsh_env())
        (directory / ".zshrc").write_text(_zsh_rc(nonce))
        env = {"ZDOTDIR": str(directory)}
        if "ZDOTDIR" in os.environ:
            env["NAV_USER_ZDOTDIR"] = os.environ["ZDOTDIR"]
        return [shell, "-i"], env
    rc = directory / "shrc"
    rc.write_text(_sh_rc(nonce))
    return [shell, "-i"], {"ENV": str(rc)}


class Subshell:
    """The user's shell on a pty, driven by the command line.

    *screen* is the console's; everything the shell prints goes there except
    the marks and the prompt.  *on_output* is called after anything reached
    the screen, which is the console bumping its revision.  *on_finished* is
    called with the status and the shell's directory when a command the
    command line sent is done; *on_exit* when the shell itself goes, after
    which the next command starts another.
    """

    def __init__(
        self,
        screen: ConsoleScreen,
        *,
        shell: str | None = None,
        on_output: Callable[[], None] | None = None,
        on_finished: Callable[[int, Path | None], None] | None = None,
        on_exit: Callable[[int], None] | None = None,
    ):
        self.screen = screen
        self.shell = shell or os.environ.get("SHELL") or "/bin/sh"
        self.on_output = on_output
        self.on_finished = on_finished
        self.on_exit = on_exit
        self.process: PtyProcess | None = None
        #: Where the shell last said it was, or None before its first prompt.
        self.cwd: Path | None = None
        #: The status of the last command, as the shell reported it.
        self.status = 0
        #: A command the command line sent is running.
        self.busy = False
        self._nonce = ""
        self._marks: re.Pattern[bytes] | None = None
        self._directory: str | None = None
        #: Bytes that may be the start of a mark, kept for the next read.
        self._tail = b""
        #: Inside the prompt, between the A and B marks.
        self._in_prompt = False
        #: The last prompt the shell printed, held back from the screen.
        self._prompt = b""
        #: The shell is at its prompt, reading.
        self._ready = False
        #: Swallow everything until the next D mark: a silent ``cd`` is running.
        self._silent = False
        #: What to send once the shell is ready: ``(text, silent)``.
        self._queue: list[tuple[str, bool]] = []
        self._paste = False

    @property
    def is_running(self) -> bool:
        return self.process is not None and self.process.is_running

    # -- the process ---------------------------------------------------------

    def start(self, cwd: Path | None = None, columns: int = 80, lines: int = 24) -> None:
        """Start the shell if it is not running already."""
        if self.is_running:
            return
        self._cleanup()
        self._nonce = secrets.token_hex(8)
        self._marks = re.compile(
            rb"\x1b\]%d;%s;([ABD])(?:;([^\x07\x1b]*))?(?:\x07|\x1b\\)"
            % (MARK, self._nonce.encode())
        )
        self._directory = tempfile.mkdtemp(prefix="navigator-shell-")
        argv, extra = shell_argv(self.shell, Path(self._directory), self._nonce)
        env = dict(os.environ)
        env.update(extra)
        self._tail, self._prompt = b"", b""
        self._in_prompt = self._ready = self._silent = self.busy = self._paste = False
        self.process = PtyProcess(
            argv,
            cwd=cwd,
            env=env,
            columns=columns,
            lines=lines,
            on_output=self._on_output,
            on_exit=self._on_exit,
        )
        try:
            self.process.start()
        except OSError:
            self.process = None
            self._cleanup()

    def stop(self) -> None:
        if self.process is not None:
            self.process.terminate()
            self.process.close()
            self.process = None
        self._queue.clear()
        self.busy = False
        self._cleanup()

    def _cleanup(self) -> None:
        directory, self._directory = self._directory, None
        if directory is not None:
            shutil.rmtree(directory, ignore_errors=True)

    def set_size(self, columns: int, lines: int) -> None:
        if self.process is not None:
            self.process.set_size(columns, lines)

    def write(self, data: bytes) -> None:
        """Type *data* at whatever is running -- a key while a command runs."""
        if self.process is not None:
            self.process.write(data)

    def paste(self, text: str) -> None:
        """Paste *text* at whatever is running, bracketed if it asked for that."""
        data = text.encode()
        if self._paste:
            data = b"\x1b[200~" + data + b"\x1b[201~"
        self.write(data)

    # -- commands --------------------------------------------------------------

    def run(self, command: str, cwd: Path | None = None) -> None:
        """Run *command* in *cwd*, starting the shell if it has to be.

        Sent at once if the shell is at its prompt, and queued until it is
        otherwise -- which is every time on the first command, while the rc
        files are still loading.
        """
        if not self.is_running:
            # Started where the command is to run, so no cd is needed first.
            self.start(cwd, self.screen.columns, self.screen.lines)
            if not self.is_running:
                if self.on_finished is not None:
                    self.on_finished(127, self.cwd)
                return
        elif cwd is not None and cwd != self.cwd:
            self._queue.append((f" cd -- {shlex.quote(str(cwd))}", True))
        self._queue.append((command, False))
        self.busy = True
        self._send_next()

    def _send_next(self) -> None:
        if not self._ready or not self._queue or self.process is None:
            return
        text, silent = self._queue.pop(0)
        self._ready = False
        self._silent = silent
        if not silent:
            # The prompt the shell printed and we kept back, so the command
            # it is about to echo lands after it, as it would have typed.
            self._feed(self._prompt)
        data = text.encode()
        if self._paste and not silent:
            # A tab is a completion request and a newline an Enter to a line
            # editor; pasted, the line is taken as written.
            data = b"\x1b[200~" + data + b"\x1b[201~"
        self.process.write(data + b"\r")

    # -- output ----------------------------------------------------------------

    def _on_output(self, data: bytes) -> None:
        if _PASTE_ON in data or _PASTE_OFF in data:
            self._paste = data.rfind(_PASTE_ON) > data.rfind(_PASTE_OFF)
        data = self._tail + data
        self._tail = b""
        # A mark cut off by the end of the read is kept for the next one.
        cut = data.rfind(b"\x1b]")
        if cut != -1 and self._marks is not None:
            rest = data[cut:]
            if b"\x07" not in rest and b"\x1b\\" not in rest and len(rest) < 4096:
                data, self._tail = data[:cut], rest
        position = 0
        if self._marks is not None:
            for match in self._marks.finditer(data):
                self._text(data[position : match.start()])
                position = match.end()
                self._mark(match.group(1), match.group(2))
        self._text(data[position:])

    def _text(self, data: bytes) -> None:
        if not data:
            return
        if self._in_prompt:
            self._prompt += data
        elif not self._silent:
            self._feed(data)

    def _feed(self, data: bytes) -> None:
        if data:
            self.screen.feed(data)
            if self.on_output is not None:
                self.on_output()

    def _mark(self, kind: bytes, data: bytes | None) -> None:
        if kind == b"D":
            status, _, cwd = (data or b"").partition(b";")
            try:
                self.status = int(status)
            except ValueError:
                self.status = 0
            path = Path(os.fsdecode(cwd)) if cwd else None
            if path is not None and path.is_absolute():
                self.cwd = path
            if self._silent:
                self._silent = False
            elif self.busy and not self._queue:
                self.busy = False
                if self.on_finished is not None:
                    self.on_finished(self.status, self.cwd)
        elif kind == b"A":
            self._in_prompt = True
            self._prompt = b""
        elif kind == b"B":
            self._in_prompt = False
            self._ready = True
            self._send_next()

    def _on_exit(self, status: int) -> None:
        self.process = None
        self._ready = False
        self._queue.clear()
        self._cleanup()
        was_busy, self.busy = self.busy, False
        if self.on_exit is not None:
            self.on_exit(status)
        if was_busy and self.on_finished is not None:
            self.on_finished(status, self.cwd)
