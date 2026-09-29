"""The shell behind the command line: one, long-lived, and its prompt held back.

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
  what the command line shows, and it is painted into the console only when
  a command is sent, immediately before the shell echoes it, so the console
  log reads ``user@host:~$ ls`` -- the shape of DOS Navigator's
  ``DosWrite(ActiveDir + '>' + S)``, with the user's own prompt in it.

**The prompt is the user's**, bracketed rather than replaced: the hook keeps
whatever ``PS1`` the rc files or a prompt command set, and puts the two marks
around it, so the shell does every expansion -- ``\\w``, colours, a git
segment -- exactly as it would in a plain terminal.  DOS Navigator ignored
``PROMPT`` and drew ``<dir>>``; that is the one departure, taken on purpose,
and it survives as the fallback for a shell with no prompt of its own and for
``sh``, which has no hook to bracket one with.

Each mark is ``ESC ] 6973 ; <nonce> ; <kind> [; <data>] BEL``.  The nonce is
random per shell, so a program that happens to print something mark-shaped --
a nested shell with the same rc, a ``cat`` of this file -- cannot forge a
finished command.  A mark with a foreign nonce is not a mark and goes to the
screen, where the emulator drops an OSC it does not know.

**The directory flows both ways.**  The shell tells Navigator where it is after
every command; Navigator tells the shell where the active panel is before one,
with a *silent* ``cd``: a leading space keeps it out of the history, and
everything the shell prints until its next prompt is swallowed.  Only when the
two differ, so an ordinary command costs no extra round trip.  The same ``cd``
is sent whenever the active panel moves while the shell is idle
(:meth:`Subshell.sync`), which is what keeps the prompt on the command line
naming the panel's directory.
"""

from __future__ import annotations

import base64
import binascii
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


@dataclass(frozen=True, slots=True)
class HistoryReady(Event):
    """The shell's history, newest first, for Up on the idle console."""

    entries: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HistoryChosen(Event):
    """What atuin's search handed back: empty if it was cancelled."""

    text: str


@dataclass(frozen=True, slots=True)
class CompletionsReady(Event):
    """The shell answered Tab: *candidates* for ``line[start:point]``.

    Posted, like :class:`CommandFinished`, so it is applied in a batch.  It
    carries the line and caret it was asked about, and is dropped if the
    command line has moved on since.
    """

    line: str
    point: int
    start: int
    candidates: tuple[str, ...]


#: Tab on the command line, answered by bash: the candidates for the word at the
#: caret, as readline would find them.  ``$1`` is the line in base64 and ``$2``
#: the caret; the answer is a ``C`` mark carrying where the word starts and the
#: candidates, NUL-separated and in base64, so nothing in them can end the mark.
#: Words are split on blanks, which is readline's split for everything but
#: quoted text.  The first word is a command -- ``compgen -c`` knows aliases,
#: functions and builtins as well as ``PATH`` -- and every later one goes to the
#: command's own completion: the ``complete`` spec, loaded on demand when
#: bash-completion is installed, and a ``-F`` function called the way readline
#: calls it.  Files are the fallback, as they are for readline.
_BASH_COMPLETE = r"""
__nav_complete() {
    local line point left cur cmd spec func
    line=$(printf '%s' "$1" | base64 -d 2>/dev/null) point=$2
    left=${line:0:point}
    local -a words reply=()
    read -ra words <<< "$left"
    [[ -z $left || $left =~ [[:space:]]$ ]] && words+=("")
    local cword=$(( ${#words[@]} - 1 ))
    cur=${words[cword]}
    if (( cword == 0 )) && [[ $cur != */* ]]; then
        mapfile -t reply < <(compgen -c -- "$cur" 2>/dev/null | sort -u)
    else
        cmd=${words[0]}
        spec=$(complete -p -- "$cmd" 2>/dev/null)
        if [[ -z $spec ]]; then
            if declare -F _comp_load >/dev/null; then
                _comp_load -- "$cmd" >/dev/null 2>&1
            elif declare -F _completion_loader >/dev/null; then
                _completion_loader "$cmd" >/dev/null 2>&1
            fi
            spec=$(complete -p -- "$cmd" 2>/dev/null)
        fi
        if [[ $spec =~ \ -F\ ([^ ]+) ]]; then
            func=${BASH_REMATCH[1]}
            local COMP_LINE=$left COMP_POINT=${#left} COMP_CWORD=$cword
            local COMP_KEY=9 COMP_TYPE=9
            local -a COMP_WORDS=("${words[@]}") COMPREPLY=()
            "$func" "$cmd" "$cur" "${words[cword-1]}" >/dev/null 2>&1
            reply=("${COMPREPLY[@]}")
        elif [[ -n $spec ]]; then
            spec=${spec#complete }
            spec=${spec% *}
            mapfile -t reply < <(eval "compgen $spec -- \"\$cur\"" 2>/dev/null)
        fi
        if (( ${#reply[@]} == 0 )) && [[ -z $spec || $spec == *default* ]]; then
            mapfile -t reply < <(compgen -f -- "$cur" 2>/dev/null)
        fi
    fi
    printf '@MARK@;C;%s;%s\007' "$(( ${#left} - ${#cur} ))" \
        "$( (( ${#reply[@]} )) && printf '%s\0' "${reply[@]}" | base64 -w0)"
}
"""

#: The same for zsh, which cannot be asked what its own completion system
#: would offer -- compsys runs only inside the line editor, on a line it is
#: editing -- so this is the two things the shell *can* be asked: which
#: commands it knows, and which files a word names.
_ZSH_COMPLETE = r"""
__nav_complete() {
    local line=$(print -rn -- $1 | base64 -d 2>/dev/null) point=$2
    local left=${line[1,point]}
    local -a words reply
    words=(${=left})
    [[ -z $left || $left == *[[:space:]] ]] && words+=('')
    local cur=${words[-1]}
    local pat=${(b)cur}
    if (( ${#words} == 1 )) && [[ $cur != */* ]]; then
        reply=(${(M)${(k)aliases}:#${~pat}*} ${(M)${(k)functions}:#${~pat}*}
               ${(M)${(k)builtins}:#${~pat}*} ${(M)${(k)commands}:#${~pat}*})
        reply=(${(u)reply})
    else
        [[ $cur == '~'* ]] && pat="~${(b)cur[2,-1]}"
        reply=(${~pat}*(N))
    fi
    printf '@MARK@;C;%s;%s\a' "$(( ${#left} - ${#cur} ))" \
        "$( (( ${#reply} )) && print -rn -- ${(pj:\0:)reply} | base64 -w0)"
}
"""

#: Up on the idle console, answered by bash.  ``__nav_history`` is the shell's
#: own history, newest first, as an ``H`` mark -- what readline's Up walks.
#: ``__nav_atuin`` is what atuin's Up and Ctrl+R bindings run, run the same
#: way: its interface on the terminal, the chosen command on the swapped
#: descriptor, handed back as an ``R`` mark.  The ``O`` mark before it is where
#: the console starts showing, so the line that ran it is never seen.
#: ``__nav_keys`` says, once, which of the two the user's Up and Ctrl+R are.
_BASH_HISTORY = r"""
__nav_history() {
    local -a entries
    mapfile -t entries < <(HISTTIMEFORMAT= fc -lnr -1000 2>/dev/null | sed 's/^[[:space:]]*//')
    printf '@MARK@;H;%s\007' \
        "$( (( ${#entries[@]} )) && printf '%s\0' "${entries[@]}" | base64 -w0)"
}
__nav_atuin() {
    local line out
    line=$(printf '%s' "$1" | base64 -d 2>/dev/null)
    shift
    printf '@MARK@;O\007'
    out=$(ATUIN_SHELL_BASH=t ATUIN_LOG=error ATUIN_QUERY="$line" atuin search "$@" -i 3>&1 1>&2 2>&3)
    printf '@MARK@;R;%s\007' "$(printf '%s' "$out" | base64 -w0)"
}
__nav_keys() {
    local keys up= search=
    keys=$(bind -X 2>/dev/null)
    [[ $keys == *'"\e[A": "__atuin_history'* ]] && up=atuin
    [[ $keys == *'"\C-r": "__atuin_history'* ]] && search=atuin
    printf '@MARK@;U;%s;%s\007' "$up" "$search"
}
__nav_keys
"""

#: The same three for zsh, whose history is ``fc`` too and whose atuin
#: bindings are ZLE widgets -- so they are recognised by name and atuin is run
#: directly, the way its own widget runs it.
_ZSH_HISTORY = r"""
__nav_history() {
    local -a entries
    entries=("${(@f)$(fc -lnr -1000 2>/dev/null)}")
    printf '@MARK@;H;%s\a' \
        "$( (( ${#entries} )) && print -rn -- ${(pj:\0:)entries} | base64 -w0)"
}
__nav_atuin() {
    local line=$(print -rn -- $1 | base64 -d 2>/dev/null) out
    shift
    printf '@MARK@;O\a'
    out=$(ATUIN_SHELL_ZSH=t ATUIN_LOG=error ATUIN_QUERY=$line atuin search "$@" -i 3>&1 1>&2 2>&3)
    printf '@MARK@;R;%s\a' "$(print -rn -- $out | base64 -w0)"
}
__nav_keys() {
    local up= search=
    [[ $(bindkey '^[[A') == *atuin* || $(bindkey '^[OA') == *atuin* ]] && up=atuin
    [[ $(bindkey '^R') == *atuin* ]] && search=atuin
    printf '@MARK@;U;%s;%s\a' "$up" "$search"
}
__nav_keys
"""


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
    # The user's own prompt, bracketed rather than replaced: whatever set it
    # -- the rc, or a prompt command that rebuilds it every time -- left
    # something other than what we set last, and that is the one to keep.
    [[ $PS1 != "$__nav_wrapped" ]] && __nav_ps1=$PS1
    local own=${{__nav_ps1:-$p>}}
    __nav_wrapped="\\[{mark};A\\007\\]$own\\[{mark};B\\007\\]"
    PS1=$__nav_wrapped
    PS2=''
}}
if [[ "$(declare -p PROMPT_COMMAND 2>/dev/null)" == "declare -a"* ]]; then
    PROMPT_COMMAND=('__nav_status=$?' "${{PROMPT_COMMAND[@]}}" __nav_prompt)
else
    PROMPT_COMMAND="__nav_status=\\$?;${{PROMPT_COMMAND:+$PROMPT_COMMAND;}}__nav_prompt"
fi
HISTCONTROL="ignorespace${{HISTCONTROL:+:$HISTCONTROL}}"
""" + (_BASH_COMPLETE + _BASH_HISTORY).replace("@MARK@", mark)


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
    [[ $PS1 != "$__nav_wrapped" ]] && __nav_ps1=$PS1
    __nav_wrapped=$'%{{{mark};A\\a%}}'"${{__nav_ps1:-%/>}}"$'%{{{mark};B\\a%}}'
    PS1=$__nav_wrapped
    PS2='' RPS1='' RPROMPT=''
}}
precmd_functions=(__nav_status $precmd_functions __nav_prompt)
setopt HIST_IGNORE_SPACE
""" + (_ZSH_COMPLETE + _ZSH_HISTORY).replace("@MARK@", mark)


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
    which the next command starts another.  *on_prompt* is called with every
    prompt the shell prints, held back as it is, and the directory it was
    printed in.
    """

    def __init__(
        self,
        screen: ConsoleScreen,
        *,
        shell: str | None = None,
        on_output: Callable[[], None] | None = None,
        on_finished: Callable[[int, Path | None], None] | None = None,
        on_exit: Callable[[int], None] | None = None,
        on_prompt: Callable[[bytes, Path | None], None] | None = None,
    ):
        self.screen = screen
        self.shell = shell or os.environ.get("SHELL") or "/bin/sh"
        self.on_output = on_output
        self.on_finished = on_finished
        self.on_exit = on_exit
        self.on_prompt = on_prompt
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
        #: Where :meth:`sync` last asked the shell to be, until it is sent.
        self._wanted: Path | None = None
        #: Where the silent ``cd`` :meth:`sync` sent is taking the shell,
        #: until the prompt it prints; and whether that ``cd`` is the line
        #: the shell is running now.
        self._following: Path | None = None
        self._following_sent = False
        #: What to send once the shell is ready: ``(text, mode)``, the mode one
        #: of ``"command"`` (echoed after the held-back prompt, as typed),
        #: ``"silent"`` (nothing shown until the prompt), ``"follow"`` (a
        #: silent ``cd`` from :meth:`sync`) and ``"reveal"``
        #: (nothing shown until the ``O`` mark -- the line that ran it stays
        #: hidden, what it draws does not).
        self._queue: list[tuple[str, str]] = []
        #: A ``"reveal"`` line is running: hidden until the O mark, and its
        #: end is no command finishing.
        self._revealing = False
        #: Whoever waits for the shell's history, oldest first, and for what
        #: atuin chose.
        self._histories: list[Callable[[list[str]], None]] = []
        self._chosen: Callable[[str], None] | None = None
        #: What the user's Up and Ctrl+R run in their own terminal: ``"atuin"``,
        #: or None for readline's history walk and reverse search.
        self.up_binding: str | None = None
        self.search_binding: str | None = None
        self._paste = False
        #: The line editor is zsh's, which reads a bracketed paste whenever.
        self._zle = False
        #: Whether the running shell can answer :meth:`complete`.
        self.can_complete = False
        #: Who is waiting for an answer to :meth:`complete`, oldest first: the
        #: shell answers queries in the order they were sent, and typing can
        #: send the next before the last is answered.
        self._completions: list[Callable[[int, list[str]], None]] = []
        # What the program asks the terminal -- where the cursor is, what the
        # terminal is -- is answered by the screen, back down the pty.
        screen.respond = self.write

    @property
    def is_running(self) -> bool:
        return self.process is not None and self.process.is_running

    @property
    def catching_up(self) -> bool:
        """A :meth:`sync` is on its way: the next prompt is printed where it asked."""
        return self.is_running and (self._wanted is not None or self._following is not None)

    # -- the process ---------------------------------------------------------

    def start(self, cwd: Path | None = None, columns: int = 80, lines: int = 24) -> None:
        """Start the shell if it is not running already."""
        if self.is_running:
            return
        self._cleanup()
        self._nonce = secrets.token_hex(8)
        self._marks = re.compile(
            rb"\x1b\]%d;%s;([ABCDHORU])(?:;([^\x07\x1b]*))?(?:\x07|\x1b\\)"
            % (MARK, self._nonce.encode())
        )
        self._directory = tempfile.mkdtemp(prefix="navigator-shell-")
        argv, extra = shell_argv(self.shell, Path(self._directory), self._nonce)
        self._zle = Path(argv[0]).name == "zsh"
        #: Whether the hook defines ``__nav_complete``: bash's and zsh's do.
        self.can_complete = Path(argv[0]).name in ("bash", "zsh")
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
        self._completions.clear()
        self._histories.clear()
        self._chosen = None
        self._revealing = False
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
            self._queue.append((f" cd -- {shlex.quote(str(cwd))}", "silent"))
        self._queue.append((command, "command"))
        self.busy = True
        self._send_next()

    def complete(
        self,
        line: str,
        point: int,
        cwd: Path | None,
        callback: Callable[[int, list[str]], None],
    ) -> bool:
        """Ask the shell what the word at *point* in *line* could become.

        Asked silently, like the ``cd``: the query never reaches the history
        or the screen.  *callback* is called with where the word starts and
        the candidates, once, when the shell answers -- in *cwd*, where the
        command would run.  False, and no callback, if the shell cannot be
        asked: not running, running a command, or a shell with no hook.
        """
        if not self.is_running or self.busy or not self.can_complete:
            return False
        if cwd is not None and cwd != self.cwd:
            self._queue.append((f" cd -- {shlex.quote(str(cwd))}", "silent"))
        encoded = base64.b64encode(line.encode()).decode("ascii")
        self._queue.append((f" __nav_complete {encoded} {point}", "silent"))
        self._completions.append(callback)
        self._send_next()
        return True

    def history(self, callback: Callable[[list[str]], None]) -> bool:
        """Ask for the shell's history, newest first -- what readline's Up walks.

        Silent, like :meth:`complete`.  False if the shell cannot be asked.
        """
        if not self.is_running or self.busy or not self.can_complete:
            return False
        self._queue.append((" __nav_history", "silent"))
        self._histories.append(callback)
        self._send_next()
        return True

    def search_history(self, line: str, args: list[str], callback: Callable[[str], None]) -> bool:
        """Run atuin's search on the console, as the user's Up or Ctrl+R would.

        Its interface is drawn on the console and gets every key while it runs
        -- :attr:`busy` is set, as for a command -- but the line that started
        it is never shown and its end finishes no command.  *callback* gets
        what was chosen: empty if the search was cancelled, and prefixed
        ``__atuin_accept__:`` if the user asked for it to run at once.
        """
        if not self.is_running or self.busy or not self.can_complete:
            return False
        encoded = base64.b64encode(line.encode()).decode("ascii")
        words = " ".join(shlex.quote(arg) for arg in args)
        self._queue.append((f" __nav_atuin {encoded} {words}", "reveal"))
        self._chosen = callback
        self.busy = True
        self._send_next()
        return True

    def sync(self, cwd: Path) -> None:
        """Send the shell to *cwd* silently, so its next prompt is printed there.

        At once if it is idle, and otherwise at its next prompt: a running
        command owns the shell, and one that has not started yet has no
        prompt to print.  The prompt that follows is what reaches
        *on_prompt*.
        """
        self._wanted = cwd
        self._follow()

    def _follow(self) -> None:
        wanted = self._wanted
        if wanted is None or not self.is_running or self.busy or self._queue:
            return
        # Asked for once: a directory the cd cannot reach would otherwise be
        # asked for again at every prompt the failed cd prints.
        self._wanted = None
        if wanted != self.cwd:
            self._following = wanted
            self._queue.append((f" cd -- {shlex.quote(str(wanted))}", "follow"))
            self._send_next()

    def _send_next(self) -> None:
        if not self._ready or not self._queue or self.process is None:
            return
        text, mode = self._queue.pop(0)
        self._ready = False
        silent = mode != "command"
        self._silent = silent
        self._revealing = mode == "reveal"
        self._following_sent = mode == "follow"
        if not silent:
            # The prompt the shell printed and we kept back, so the command
            # it is about to echo lands after it, as it would have typed.
            self._feed(self._prompt)
        data = text.encode()
        # zsh turns bracketed paste on in a write of its own *after* the
        # prompt, so at the B mark it has usually not been seen yet -- and a
        # command sent unbracketed then has its tabs taken for completion.
        # ZLE binds the paste sequence whether or not it has announced it, so
        # a line for zsh is always bracketed.  bash announces it before the
        # prompt, and is taken at its word.
        if (self._paste or self._zle) and not silent:
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
        if kind == b"U":
            up, _, search = (data or b"").partition(b";")
            self.up_binding = up.decode() or None
            self.search_binding = search.decode() or None
            return
        if kind == b"H":
            entries = _decode_list(data)
            if self._histories and entries is not None:
                self._histories.pop(0)(entries)
            return
        if kind == b"O":
            # What the revealed line draws from here on is the console's.
            self._silent = False
            return
        if kind == b"R":
            chosen, self._chosen = self._chosen, None
            try:
                text = base64.b64decode(data or b"").decode("utf-8", "replace")
            except (ValueError, binascii.Error):
                text = ""
            if chosen is not None:
                chosen(text)
            return
        if kind == b"C":
            start, _, encoded = (data or b"").partition(b";")
            try:
                candidates = base64.b64decode(encoded).decode("utf-8", "replace")
                where = int(start)
            except (ValueError, binascii.Error):
                return
            if self._completions:
                self._completions.pop(0)(where, [c for c in candidates.split("\0") if c])
            return
        if kind == b"D":
            status, _, cwd = (data or b"").partition(b";")
            try:
                self.status = int(status)
            except ValueError:
                self.status = 0
            path = Path(os.fsdecode(cwd)) if cwd else None
            if path is not None and path.is_absolute():
                self.cwd = path
            if self._revealing:
                # The history search is over, and it was no command: the
                # keys go back, and nothing is re-read.
                self._revealing = self._silent = False
                self.busy = False
            elif self._silent:
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
            if self._following_sent:
                self._following, self._following_sent = None, False
            if self.on_prompt is not None:
                self.on_prompt(self._prompt, self.cwd)
            self._send_next()
            self._follow()

    def _on_exit(self, status: int) -> None:
        self.process = None
        self._completions.clear()
        self._histories.clear()
        self._chosen = None
        self._revealing = False
        self._ready = False
        self._following, self._following_sent = None, False
        self._queue.clear()
        self._cleanup()
        was_busy, self.busy = self.busy, False
        if self.on_exit is not None:
            self.on_exit(status)
        if was_busy and self.on_finished is not None:
            self.on_finished(status, self.cwd)


def _decode_list(data: bytes | None) -> list[str] | None:
    """A mark's base64 of NUL-separated strings, or None if it is not one."""
    try:
        text = base64.b64decode(data or b"").decode("utf-8", "replace")
    except (ValueError, binascii.Error):
        return None
    return [entry for entry in text.split("\0") if entry]
