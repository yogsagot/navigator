"""The completions for the word at the command line's caret, to choose from.

Not DOS Navigator's: its command line completed nothing.  The drop-down it
did have is Turbo Vision's history list, so this is one -- the same framed,
modal list, the same colours (a ``HistoryList`` rule matches a subclass), the
same keys: Enter or a double click takes the entry, Esc leaves the line alone.
Typing goes on into the line, and the list follows it.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from navkit.events import KeyEvent

from navml.widgets.dialog.history.history import HistoryList


class CompletionList(HistoryList):
    """A history list whose entry goes wherever *on_choose* puts it.

    **Typing goes past it.**  A printable key or Backspace is handed to
    *on_type*, which edits the command line underneath and narrows the list,
    so the word can be finished by hand as well as chosen.  The line it
    edits stays at full strength: this modal dims nothing behind it.
    """

    dims_behind = False

    def __init__(
        self,
        on_choose: Callable[[str], None],
        on_type: Callable[[KeyEvent], Awaitable[None]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(None, **kwargs)
        self._on_choose = on_choose
        self._on_type = on_type

    async def on_key(self, event: KeyEvent) -> bool:
        typed = (event.is_printable and event.char) or event.matches("backspace")
        if typed and self._on_type is not None:
            await self._on_type(event)
            return True
        return await super().on_key(event)

    async def choose(self) -> bool:
        text = self.selected
        self.close()
        if text is not None:
            self._on_choose(text)
        return True
