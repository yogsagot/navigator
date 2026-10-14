"""What the error box answers: ``"continue"``, or ``"quit"`` (None for Esc)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit.events import Event
from navkit.i18n import tr
from navkit.reactive import effect
from navml.widgets.dialog.dialog import Dialog

from navigator.lib.highlight import Span, lex_text
from navigator.lib.system.errorlog import format_error

#: Pygments' Python traceback lexer: the header, each frame's file, line and
#: function, the source lines as Python, and the exception.
TRACEBACK_LEXER = "pytb"


def fold(line: str, width: int, indent: int) -> list[tuple[int, int]]:
    """Where *line* breaks to fit *width*: each row's ``(start, end)`` in it.

    At the last space that fits, else mid-word (a path has none), the spaces
    at a break dropped; every row after the first loses *indent* columns to
    the indent it is drawn with.  Offsets rather than strings, so the line's
    highlight spans can be cut the same way.
    """
    rows: list[tuple[int, int]] = []
    start, budget = 0, width
    while len(line) - start > budget:
        cut = line.rfind(" ", start + 1, start + budget + 1)
        if cut <= start:
            cut = start + budget
        rows.append((start, cut))
        start = cut
        while start < len(line) and line[start] == " ":
            start += 1
        budget = max(1, width - indent)
    rows.append((start, len(line)))
    return rows


class ErrorDialog(Dialog):
    """*error*, its traceback, and where it was logged (*log*, or None)."""

    def __init__(self, error: BaseException | None = None, log: Path | None = None,
                 **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.row.visible = False
        self.message.visible = False
        error = error if error is not None else RuntimeError()
        #: Everything *Copy* puts on the clipboard: the whole traceback.
        self.text = format_error(error)
        self.summary.text = f"{type(error).__name__}: {error}"
        self._lines = [line.expandtabs(4) for line in self.text.splitlines()]
        #: Each line's highlight, lexed once; :meth:`_wrap` cuts it with the line.
        self._spans = lex_text(TRACEBACK_LEXER, self._lines)
        self.trace.spans = self._spans
        self.trace.items = list(self._lines)
        # The innermost frame and the error itself are what is read first.
        self.trace.cursor = max(0, len(self.trace.items) - 1)
        self.logged.text = (
            tr("Also written to {path}").format(path=log) if log is not None
            else tr("Not logged to a file this session")
        )

    def mounted(self) -> None:
        super().mounted()
        effect(self, ErrorDialog._wrap)
        self.resume.focus()

    def _wrap(self) -> None:
        """The traceback folded to the list's width, again whenever it changes.

        A continuation is indented four past its line's own indent -- deeper
        than the source line Python prints under a ``File`` line -- so a long
        path still reads as part of the ``File ...`` line it came from.  Each
        row takes its piece of the line's highlight.  The cursor stays on the
        last row if it was there.
        """
        width = self.trace.inner_width
        if width < 8:
            return
        rows: list[str] = []
        spans: list[list[Span]] = []
        for line, line_spans in zip(self._lines, self._spans):
            indent = min(len(line) - len(line.lstrip()) + 4, width // 2)
            for number, (start, end) in enumerate(fold(line, width, indent)):
                pad = indent if number else 0
                rows.append(" " * pad + line[start:end])
                spans.append([(max(s, start) - start + pad, min(e, end) - start + pad, classes)
                              for s, e, classes in line_spans if s < end and e > start])
        at_end = self.trace.cursor >= len(self.trace.items) - 1
        self.trace.spans = spans
        self.trace.items = rows
        if at_end:
            self.trace.cursor = max(0, len(rows) - 1)

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return (self.resume, self.copy, self.quit)

    async def on_resume_click(self, event: Event) -> bool:
        self.close("continue")
        return True

    async def on_copy_click(self, event: Event) -> bool:
        app = self.application
        if app is not None:
            app.copy_to_clipboard(self.text)
            self.copy.text = tr("Copied")
        return True

    async def on_quit_click(self, event: Event) -> bool:
        self.close("quit")
        return True
