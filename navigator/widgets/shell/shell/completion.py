"""Tab completion on the command line, and the list it offers.

A mixin of :class:`Shell` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``shell.py``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from navkit.events import KeyEvent

from navigator.lib.system.subshell import CompletionsReady, shell_word
from navigator.widgets.shell.shell.helpers import MAX_COMPLETIONS, _escape

if TYPE_CHECKING:
    from navigator.widgets.shell.shell import Shell as _Base
else:
    from navkit.widget import Mixin as _Base


class Completion(_Base):
    """Tab completion on the command line, and the list it offers."""

    # -- completion ------------------------------------------------------------

    def _ask_completions(self) -> None:
        """Ask the shell about the word at the caret; the answer is posted back."""
        line = self.command_line
        value, point = line.value, line.cursor
        app = self.application

        def answered(start: int, candidates: list[str]) -> None:
            ready = CompletionsReady(value, point, start, tuple(candidates))
            if app is not None and app.is_running:
                app.post_event(ready)
            else:
                self.completions_ready(ready)

        self.console.subshell.complete(value, point, self._command_directory(), answered)

    @property
    def completion_list(self) -> Any:
        """The completions drop-down, while it is open."""
        window = self._completion_list
        return window if window is not None and window.parent is not None else None

    def completions_ready(self, event: CompletionsReady) -> None:
        """Apply the shell's answer as readline would: complete, extend, or list.

        One candidate replaces the word and ends it -- with ``/`` for a
        directory and a space for anything else.  Several that agree on more
        than the word already says extend it that far.  Otherwise the choice
        is the user's, in a drop-down over the line.

        **While that drop-down is open the answer only refills it**: it is an
        answer to typing, and completing or extending the word under the
        user's fingers would fight them.  An empty one closes it.
        """
        line = self.command_line
        if line.value != event.line or line.cursor != event.point:
            return
        # The word as the shell reads it -- escapes and quotes off -- which is
        # what the candidates are spelled like.
        word = shell_word(event.line, event.point)[1]
        candidates = list(dict.fromkeys(event.candidates))[:MAX_COMPLETIONS]
        if self.completion_list is not None:
            if candidates:
                self._completing, self._candidates = event, candidates
                self._show_completions(event.start, candidates)
            else:
                self._close_completions()
            return
        if not candidates:
            return
        if len(candidates) == 1:
            self._complete_word(event, candidates[0], final=True)
            return
        prefix = os.path.commonprefix(candidates)
        if len(prefix) > len(word):
            self._complete_word(event, prefix, final=False)
            return
        self._open_completions(event, candidates)

    def _complete_word(self, event: CompletionsReady, text: str, *, final: bool) -> None:
        line = self.command_line
        suffix = ""
        if final and not text.endswith(("/", " ", "=")):
            suffix = "/" if self._is_directory(text) else " "
        if not text.endswith(" "):
            text = _escape(text)
        value = event.line[: event.start] + text + suffix + event.line[event.point :]
        line.value = value
        line.anchor = None
        line.cursor = event.start + len(text) + len(suffix)

    def _is_directory(self, text: str) -> bool:
        path = Path(os.path.expanduser(text))
        if not path.is_absolute():
            base = self._command_directory()
            if base is None:
                return False
            path = base / path
        try:
            return path.is_dir()
        except OSError:
            return False

    def _open_completions(self, event: CompletionsReady, candidates: list[str]) -> None:
        """The list over the command line, its left edge under the word."""
        from navigator.widgets.shell.completion_list import CompletionList

        app = self.application
        if app is None:
            return
        self._completing, self._candidates = event, candidates
        window = CompletionList(
            lambda text: self._complete_word(self._completing, text, final=True),
            self._type_in_completions,
        )
        self._completion_list = window
        self._show_completions(event.start, candidates)
        app.overlay(window)

    def _show_completions(self, start: int, candidates: list[str]) -> None:
        """Fill the list with *candidates* and fit it to them, above the line."""
        window, line = self._completion_list, self.command_line
        shown = candidates or [""]
        width = min(self.width, max(len(c) for c in shown) + 4)
        height = min(len(shown) + 2, max(3, line.y - 1))
        column = line.x + line.text_origin + start - line.first - 1
        x = max(0, min(column, self.width - width))
        y = max(0, line.y - height)
        window.items = candidates
        window.cursor = 0
        window.pin_rect(x, y, width, height)

    def _close_completions(self) -> None:
        window = self.completion_list
        if window is not None:
            window.close()

    async def _type_in_completions(self, event: KeyEvent) -> None:
        """A key typed with the list open: onto the line, and the list follows.

        Narrowed at once to what still starts with the word, so the list
        keeps up with the keyboard, and then refilled by the shell's own
        answer -- which is what makes a ``/`` descend into the directory.  A
        blank ends the word and Backspace past its start leaves it; either
        closes the list.
        """
        line, state = self.command_line, self._completing
        await line.on_key(event)
        if state is None or line.cursor < state.start or (event.char or "x").isspace():
            self._close_completions()
            return
        word = shell_word(line.value, line.cursor)[1]
        narrowed = [c for c in self._candidates if c.startswith(word)]
        self._completing = CompletionsReady(line.value, line.cursor, state.start, tuple(narrowed))
        self._show_completions(state.start, narrowed)
        self._ask_completions()
