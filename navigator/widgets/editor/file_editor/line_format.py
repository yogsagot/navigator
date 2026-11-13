"""Line endings and encoding (a departure, asked for: ``format_menu``).

A mixin of :class:`FileEditor` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``file_editor.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio

from navkit.i18n import tr

from navigator.widgets.editor.commands import ReopenWithEncoding, SaveWithEncoding, SetLineEnding
from navigator.lib.editor import encodings
from navigator.lib.editor.buffer import State
from navigator.lib.editor.document import NEWLINES, Pos

if TYPE_CHECKING:
    from navigator.widgets.editor.file_editor.file_editor import FileEditor as _Base
else:
    from navkit.widget import Mixin as _Base


class LineFormat(_Base):
    """Line endings and encoding (a departure, asked for: ``format_menu``)."""

    # -- line endings and encoding (a departure, asked for: ``format_menu``) -----

    async def on_set_line_ending(self, event: SetLineEnding) -> bool:
        """Every line's ending made the one asked for, and new lines' too:
        one undo step, nothing done when the text has it already."""
        newline = NEWLINES[event.ending]
        document = self.document
        # Chosen by hand: the text's own endings say it now, over a mask's.
        self.forced_ending = ""
        if document.newline == newline and set(document.counts) <= {newline}:
            return True
        endings = [newline if ending else "" for ending in document.endings]
        self._edit_here()
        self.buffer.swap(State(list(document.lines), endings, newline, document.encoding),
                         (self.line, self.col))
        self.revision += 1
        return True

    async def on_reopen_with_encoding(self, event: ReopenWithEncoding) -> bool:
        self.spawn(self.reopen_with_encoding(event.encoding))
        return True

    async def on_save_with_encoding(self, event: SaveWithEncoding) -> bool:
        self.spawn(self.save_with_encoding(event.encoding))
        return True

    async def reopen_with_encoding(self, encoding: str) -> bool:
        """The text's bytes read again as *encoding*, on a thread: the file is
        not touched, so a changed text keeps its changes, and an unchanged one
        stays unchanged.  One undo step.  False, and said, when the bytes are
        not *encoding* or the text cannot be written in its own."""
        document = self.document
        if document.encoding == encoding:
            return True
        old = document.encoding
        try:
            new = await asyncio.to_thread(document.reinterpreted, encoding)
        except UnicodeEncodeError:
            await self._say_format(tr("The text has characters {encoding} cannot write, so it has no "
                                      "bytes to read again.").format(encoding=encodings.label(old)))
            return False
        except UnicodeDecodeError:
            await self._say_format(tr("The text does not read as {encoding}.").format(
                encoding=encodings.label(encoding)))
            return False
        if self.document is not document:
            return False  # another file opened meanwhile
        was_modified = self.buffer.modified
        # The text's decoding, so every view of it takes it (Window > *New view*).
        self._edit_here()
        self.buffer.swap(State(new.lines, new.endings, new.newline, encoding), (self.line, self.col))
        if not was_modified:
            self.buffer.mark_saved()
        self.revision += 1
        return True

    async def save_with_encoding(self, encoding: str) -> bool:
        """The text to be written in *encoding* from the next save on; one
        undo step.  Refused, and said, when a character of it cannot be."""
        document = self.document
        if document.encoding == encoding:
            return True
        where = await asyncio.to_thread(encodings.first_unencodable, list(document.lines), encoding)
        if self.document is not document:
            return False
        if where is not None:
            line, index = where
            text = document.lines[line]
            char = text[index] if index < len(text) else "?"
            await self._say_format(tr("{char} (U+{code:04X}) on line {line} cannot be written in {encoding}").format(
                char=char, code=ord(char), line=line + 1, encoding=encodings.label(encoding)))
            self._go(Pos(line, index))
            return False
        self.buffer.swap(State(list(document.lines), list(document.endings), document.newline, encoding),
                         (self.line, self.col))
        self.revision += 1
        return True

    async def _say_format(self, message: str) -> None:
        from navml.widgets.dialog.dialog import Dialog

        app = self.application
        if app is not None:
            await Dialog(title=tr("Encoding"), prompt=message, buttons="ok").execute(app)

    def next_line_ending(self) -> str:
        """What a left click on the line-ending marker makes the text: the
        next of LF, CRLF and CR after the one it has -- or, with more than
        one, the one most of its lines have (``Document.newline``)."""
        order = ("lf", "crlf", "cr")
        current = self.document.line_ending
        if current == "Mixed":
            return next(key for key, newline in NEWLINES.items() if newline == self.document.newline)
        return order[(order.index(current.lower()) + 1) % len(order)]

    def ending_indicator(self) -> tuple[int, int]:
        """Where the line ending stands in :attr:`format_text`, end exclusive."""
        _ = self.format_text
        return self._ending_at

    def encoding_indicator(self) -> tuple[int, int]:
        """Where the encoding stands in :attr:`format_text`, end exclusive."""
        _ = self.format_text
        return self._encoding_at
