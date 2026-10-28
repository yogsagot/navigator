"""Running a child program on a pty this application owns.

The counterpart to :mod:`navkit.console`: that module turns a program's
output into cells, this one is where the output comes from.  Owning the pty
is the whole trick.  A program started the ordinary way writes to the real
terminal and the bytes are gone; started here it writes to a pty whose other
end we hold, so its output can be kept, painted behind the panels, and
scrolled back through.

There is a cost, and it is worth stating plainly: a program only ever talks
to what :mod:`navkit.console` can emulate.  That is the line-oriented output
a file manager runs -- listings, compilers, version control -- and, with the
console's own alternate screen, query answers, cursor-key modes and mouse
reports, the full-screen programs too.  What it cannot show (an image drawn
with a graphics protocol) needs the real terminal, which is the
application's to lend (``Application.release_terminal``), not this module's.
"""

from __future__ import annotations

import fcntl
import os
import pty
import signal
import struct
import termios
from asyncio import AbstractEventLoop, get_running_loop
from typing import Callable, Mapping, Sequence

#: How often a hung-up child is looked for, and how long it has to go before
#: it is killed.
_REAP_EVERY = 0.05
HANG_UP_GRACE = 2.0

#: What a child is told it is talking to.  ``pyte`` implements the xterm
#: sequences a program is likely to reach for; claiming anything richer would
#: invite escapes the console would drop on the floor.
DEFAULT_TERM = "xterm-256color"

#: Set in every child's environment, the way DOS Navigator set its own marker,
#: so a shell profile can tell it is running inside the file manager.
MARKER = "NAVIGATOR"


def set_winsize(fd: int, columns: int, lines: int) -> None:
    """Tell the pty at *fd* how big it is.

    Setting it on the master is enough: the kernel carries the size to the
    slave and raises ``SIGWINCH`` on the foreground process group itself, so
    nothing here has to signal the child by hand.
    """
    packed = struct.pack("HHHH", max(1, lines), max(1, columns), 0, 0)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, packed)


class PtyProcess:
    """A child program on a pty, read through the asyncio loop.

    *on_output* is handed each chunk the child writes -- normally
    :meth:`~navkit.console.ConsoleScreen.feed` -- and *on_exit* is called once
    with the exit status when it finishes.
    """

    def __init__(
        self,
        argv: Sequence[str],
        *,
        cwd: str | os.PathLike[str] | None = None,
        env: Mapping[str, str] | None = None,
        columns: int = 80,
        lines: int = 24,
        term: str = DEFAULT_TERM,
        on_output: Callable[[bytes], None] | None = None,
        on_exit: Callable[[int], None] | None = None,
    ):
        self.argv = list(argv)
        self.cwd = cwd
        self.term = term
        self._env = dict(env if env is not None else os.environ)
        self.columns = max(1, columns)
        self.lines = max(1, lines)
        self.on_output = on_output
        self.on_exit = on_exit
        self.pid: int | None = None
        self.status: int | None = None
        self._fd: int | None = None
        self._loop: AbstractEventLoop | None = None

    @property
    def is_running(self) -> bool:
        return self.pid is not None and self.status is None

    def environment(self) -> dict[str, str]:
        """The environment the child is started in."""
        env = dict(self._env)
        env["TERM"] = self.term
        # No ``LINES``/``COLUMNS``, not even ones Navigator was started with:
        # ncurses lets them override the pty's size for good, so after a
        # ``SIGWINCH`` ``htop`` went on drawing for the size it started at.
        # The size is the pty's (``TIOCSWINSZ``), which follows the widget.
        env.pop("COLUMNS", None)
        env.pop("LINES", None)
        env[MARKER] = "1"
        return env

    def start(self) -> None:
        """Fork the child and start reading from it."""
        if self.pid is not None:
            raise RuntimeError("process already started")
        # pty.fork does the part that is easy to get wrong: a new session, the
        # slave as the controlling terminal, and the three standard streams
        # pointed at it.
        pid, fd = pty.fork()
        if pid == 0:  # the child; never returns
            try:
                if self.cwd is not None:
                    os.chdir(self.cwd)
                os.execvpe(self.argv[0], self.argv, self.environment())
            except BaseException:
                os._exit(127)
        self.pid = pid
        self._fd = fd
        os.set_blocking(fd, False)
        self.set_size(self.columns, self.lines)
        self._loop = get_running_loop()
        self._loop.add_reader(fd, self._on_readable)

    def set_size(self, columns: int, lines: int) -> None:
        self.columns, self.lines = max(1, columns), max(1, lines)
        if self._fd is not None:
            try:
                set_winsize(self._fd, self.columns, self.lines)
            except OSError:
                pass

    def write(self, data: bytes) -> None:
        """Send *data* to the child as though it had been typed."""
        if self._fd is None or not data:
            return
        try:
            os.write(self._fd, data)
        except (OSError, BlockingIOError):
            pass

    def signal(self, signum: int = signal.SIGTERM) -> None:
        """Signal the child's whole process group."""
        if not self.is_running or self.pid is None:
            return
        try:
            os.killpg(os.getpgid(self.pid), signum)
        except OSError:
            pass

    terminate = signal

    def kill(self) -> None:
        self.signal(signal.SIGKILL)

    def close(self) -> None:
        """Stop reading and let go of the pty, without waiting for the child."""
        self._detach()

    def hang_up(self, grace: float | None = None) -> None:
        """End the child the way closing its terminal would, without waiting.

        ``SIGHUP`` to its process group and the pty let go; one that is still
        there after *grace* seconds (:data:`HANG_UP_GRACE`) -- it ignored the signal -- gets
        ``SIGKILL``.  It is reaped from the loop with ``WNOHANG``, never by a
        blocking ``waitpid``, and *on_exit* is not called: whoever hangs up
        has stopped listening.
        """
        if not self.is_running:
            self._detach()
            return
        self.on_exit = None
        self.signal(signal.SIGHUP)
        self._detach()
        loop = self._loop or get_running_loop()
        deadline = loop.time() + (HANG_UP_GRACE if grace is None else grace)

        def look() -> None:
            if self.reap():
                return
            if loop.time() >= deadline:
                self.kill()
            loop.call_later(_REAP_EVERY, look)

        loop.call_later(0, look)

    def reap(self) -> bool:
        """Collect the child's status if it has exited; True once it is gone."""
        if self.pid is None or self.status is not None:
            return True
        try:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
        except (ChildProcessError, OSError):
            pid, status = self.pid, 0
        if pid == 0:
            return False
        self.status = status
        return True

    # -- internals -----------------------------------------------------------

    def _on_readable(self) -> None:
        fd = self._fd
        if fd is None:
            return
        try:
            data = os.read(fd, 65536)
        except BlockingIOError:
            return
        except OSError:
            # A pty master reports EIO rather than end of input once the last
            # process holding the slave has gone.  That is this loop's exit.
            data = b""
        if not data:
            self._finish()
            return
        if self.on_output is not None:
            self.on_output(data)

    def _detach(self) -> None:
        fd, self._fd = self._fd, None
        if fd is None:
            return
        if self._loop is not None:
            try:
                self._loop.remove_reader(fd)
            except (OSError, ValueError, RuntimeError):
                pass
        try:
            os.close(fd)
        except OSError:
            pass

    def _finish(self) -> None:
        self._detach()
        if self.pid is not None and self.status is None:
            try:
                _, status = os.waitpid(self.pid, 0)
            except (ChildProcessError, OSError):
                status = 0
            self.status = status
        if self.on_exit is not None:
            self.on_exit(self.status or 0)
