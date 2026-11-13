"""Keys and commands -- the key tables, chords, running a command -- and the terminal's input:
reading it, the escape timeout, asking which pictures it draws, signals.

A mixin of :class:`~navkit.application.Application` (:class:`navkit.widget.Mixin`):
methods only; its state, keys and ``checks`` are in ``navkit/application.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import contextlib
import dataclasses
import signal

from navkit.events import Event, KeyEvent, MouseClickEvent, PasteEvent, ResizeEvent, TerminalReplyEvent
from navkit.terminal import GRAPHICS_QUERY_ID as _GRAPHICS_QUERY_ID
from navkit import commands
from navkit.widget import Widget
from navkit.application import ESCAPE_TIMEOUT, GRAPHICS_ANSWER_TIMEOUT

if TYPE_CHECKING:
    from navkit.application import Application as _Base
else:
    from navkit.widget import Mixin as _Base


class Input(_Base):
    """Keys and commands -- the key tables, chords, running a command -- and the terminal's input:"""

    # -- commands ------------------------------------------------------------

    def _key_tables(self) -> list[dict[str, commands.Binding]]:
        """The tables a key is looked up in, in the order it is: the
        application's (not past a modal), then the focus path's, nearest first."""
        scope = self.modal or self._root
        tables = [] if self.modal is not None else [commands.key_table(type(self))]
        if scope is not None:
            path = scope._focus_path() or [scope]
            tables += [commands.key_table(type(widget)) for widget in path]
        return tables

    async def _deliver_key(self, event: KeyEvent) -> bool:
        """A key through the chord, the application's table, its own
        ``on_key`` and the focus path; whether anything took it."""
        if await self._chord_key(event):
            return True
        # Dispatching on the modal rather than the root is the whole of
        # keyboard exclusivity: the walk runs from the focused widget up to
        # whatever it was called on, so it neither starts outside the modal
        # nor bubbles past it.
        target = self.modal or self._root
        if await self._run_key(event):
            return True
        if await self.on_key(event):
            return True
        return target is not None and await target.dispatch_key(event)

    async def _chord_key(self, event: KeyEvent) -> bool:
        """A key that begins, continues or ends a chord; False for any other.

        A key completing a chord runs the first binding of it found where a
        key is looked up.  One that neither completes nor continues the chord
        held is swallowed with it -- it was typed as the chord's second key,
        not as text.  Only the tables on the current path count, so Ctrl+K
        is held for an editor's chords and still reaches a program in the
        console.
        """
        if event.name in ("", None):
            return False
        if not self.chord and self._raw_keys():
            # A program on a pty is typed at: Ctrl+J is its, not a chord's.
            return False
        sequence = f"{self.chord} {event.name}" if self.chord else event.name
        tables = self._key_tables()
        if self.chord:
            self.chord = ""
            for table in tables:
                binding = table.get(sequence)
                if binding is not None:
                    await commands.run(self, binding)
                    return True
        if any(sequence in commands.chord_prefixes(table) for table in tables):
            self.chord = sequence
            return True
        return bool(sequence != event.name)

    def _raw_keys(self) -> bool:
        """Whether a widget on the focus path takes keys raw just now
        (:meth:`Widget.takes_raw_keys`), so no chord may begin."""
        if self.modal is not None:
            return False
        scope = self._root
        path = scope._focus_path() if scope is not None else []
        return any(widget.takes_raw_keys() for widget in path)

    async def _run_key(self, event: KeyEvent) -> bool:
        """The application's own key table, before the tree and never past a
        modal."""
        if self.modal is not None:
            return False
        binding = commands.key_table(type(self)).get(event.name)
        return binding is not None and await commands.run(self, binding)

    async def run_command(
        self, binding: commands.Binding, start: Widget | None = None
    ) -> bool:
        """Ask for a command as if its key had been pressed.

        What a key bar button and a menu item call.  False if the command is
        disabled or nobody claimed it.  *start* asks from a widget other than
        the focus -- a context menu runs its choice from the widget it was
        opened over -- see :func:`navkit.commands.origin`.
        """
        return await commands.run(self, binding, start)

    def command_enabled(
        self, binding: commands.Binding, start: Widget | None = None
    ) -> bool:
        """Whether asking for *binding*'s command now would run it.

        *start* asks from a widget other than the focus -- see
        :func:`navkit.commands.origin`.
        """
        return commands.enabled(self, binding, start)

    def command_checked(
        self, binding: commands.Binding, start: Widget | None = None
    ) -> bool | None:
        """Whether *binding*'s command is a toggle that is on now -- see
        :func:`navkit.commands.checked`."""
        return commands.checked(self, binding, start)

    def bindings(self, start: Widget | None = None) -> dict[str, commands.Command]:
        """Every key that asks for a command right now -- what a key bar shows."""
        return commands.bindings(self, start)

    # Hooks -- an application subclass sees every event before the widgets do.

    async def on_event(self, event: Event) -> bool:
        """Handle any event.  Return True to stop it reaching the widgets."""
        return False

    async def on_key(self, event: KeyEvent) -> bool:
        return False

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        return False

    async def on_resize(self, event: ResizeEvent) -> None:
        pass

    async def on_paste(self, event: PasteEvent) -> bool:
        """A paste, before the focused widget is offered it; True keeps it."""
        return False

    # -- input plumbing -----------------------------------------------------

    def _attach_input(self) -> None:
        assert self._loop is not None
        if self.terminal.is_tty:
            self._reader_fd = self.terminal.input_fd
            self._loop.add_reader(self._reader_fd, self._on_readable)
        for signum in (signal.SIGWINCH, signal.SIGTERM, signal.SIGHUP):
            with contextlib.suppress(NotImplementedError, ValueError, AttributeError):
                self._loop.add_signal_handler(signum, self._on_signal, signum)
                self._signals.append(signum)

    def _detach_input(self) -> None:
        if self._loop is None:
            return
        if self._escape_timer is not None:
            self._escape_timer.cancel()
            self._escape_timer = None
        if self._graphics_timer is not None:
            self._graphics_timer.cancel()
            self._graphics_timer = None
        if self._reader_fd is not None:
            with contextlib.suppress(Exception):
                self._loop.remove_reader(self._reader_fd)
            self._reader_fd = None
        for signum in self._signals:
            with contextlib.suppress(Exception):
                self._loop.remove_signal_handler(signum)
        self._signals.clear()

    def _on_readable(self) -> None:
        data = self.terminal.read()
        if not data:
            # End of input: the tty went away, so there is nothing left to do.
            self.exit()
            return
        if self._released is not None:
            # Raw, to whoever the terminal was released to; what it hands
            # back -- whatever followed the key that reclaimed it -- is ours.
            data = self._released(data)
            if not data:
                return
        for event in self._parser.feed(data):
            if isinstance(event, TerminalReplyEvent):
                self._terminal_replied(event)
            else:
                self.post_event(event)
        self._schedule_escape_flush()

    def _schedule_escape_flush(self) -> None:
        """Arm the timer that turns an ambiguous ``ESC`` into an escape key."""
        if self._escape_timer is not None:
            self._escape_timer.cancel()
            self._escape_timer = None
        if self._parser.pending_escape and self._loop is not None:
            self._escape_timer = self._loop.call_later(
                ESCAPE_TIMEOUT, self._flush_escape
            )

    def _flush_escape(self) -> None:
        self._escape_timer = None
        for event in self._parser.flush():
            self.post_event(event)

    # -- which pictures the terminal draws ------------------------------------

    def _ask_graphics(self) -> None:
        """Ask the terminal how it draws pictures, if anything wants to know.

        It is asked when :attr:`TerminalInfo.probe_graphics` says to, and
        also when ``NAVKIT_GRAPHICS`` named a protocol but the tty does not
        know its cell size in pixels, which ``CSI 16 t`` may still say.  The
        answers come in as input (:meth:`_terminal_replied`); the terminal's
        info is updated once the last has, or after
        :data:`GRAPHICS_ANSWER_TIMEOUT`.
        """
        info = self.terminal.info
        cell_px = getattr(self.terminal, "cell_px", None)
        if cell_px is not None and cell_px != info.cell_px:
            info = dataclasses.replace(info, cell_px=cell_px)
            self.terminal.info = info
        if not self.terminal.is_tty or self._loop is None:
            return
        if not (info.probe_graphics or (info.graphics and info.cell_px is None)):
            return
        self._graphics_answers = {}
        self._parser.answers_graphics = True
        self.terminal.query_graphics()
        self._graphics_timer = self._loop.call_later(GRAPHICS_ANSWER_TIMEOUT, self._graphics_answered)

    def _terminal_replied(self, event: TerminalReplyEvent) -> None:
        answers = self._graphics_answers
        if answers is None:
            return  # a reply nobody waits for any more
        if event.kind == "graphics":
            keys, _, message = event.text.partition(";")
            if f"i={_GRAPHICS_QUERY_ID}" in keys.split(","):
                answers["kitty"] = message.startswith("OK")
        elif event.kind == "cell" and len(event.params) == 2 and all(event.params):
            height, width = event.params
            answers["cell"] = (width, height)
        elif event.kind == "da1":
            answers["sixel"] = 4 in event.params
            self._graphics_answered()

    def _graphics_answered(self) -> None:
        """The terminal has said all it will: draw pictures its way."""
        answers, self._graphics_answers = self._graphics_answers, None
        if answers is None:
            return
        if self._graphics_timer is not None:
            self._graphics_timer.cancel()
            self._graphics_timer = None
        self._parser.answers_graphics = False
        info = self.terminal.info
        graphics = info.graphics
        if info.probe_graphics:
            graphics = "kitty" if answers.get("kitty") else "sixel" if answers.get("sixel") else ""
        updated = dataclasses.replace(
            info, graphics=graphics, probe_graphics=False, cell_px=info.cell_px or answers.get("cell")
        )
        # Not use_terminal_info(): its whole-screen repaint, a second or so
        # after the first frame, is what starting up looked like.  No cell
        # on the screen depends on the answer -- no picture is shown yet --
        # so what follows the info re-renders through the usual diff.
        if updated.graphics != info.graphics:
            self.terminal.write(self._graphics.release(info.graphics))
        self.terminal.info = updated
        if (updated.graphics, updated.cell_px) != (info.graphics, info.cell_px):
            self.info_revision += 1
            self.invalidate()

    def _on_signal(self, signum: int) -> None:
        if signum == signal.SIGWINCH:
            cell_px = getattr(self.terminal, "cell_px", None)
            font_changed = cell_px is not None and cell_px != self.terminal.info.cell_px
            if font_changed:
                # A font size changed with the window: pictures are scaled by it.
                self.terminal.info = dataclasses.replace(self.terminal.info, cell_px=cell_px)
                self.info_revision += 1
            size = self.terminal.size
            if size == self._asked_size and not font_changed:
                # Some terminals signal once more just after the start with
                # the size they already had; a resize clears the screen and
                # sends every cell again, which a slow terminal shows as a
                # second, flashing first frame.  Nothing moved, so nothing to do.
                return
            self._asked_size = size
            self.post_event(ResizeEvent(*size))
        else:
            self.exit()
