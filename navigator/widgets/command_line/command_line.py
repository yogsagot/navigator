"""DOS Navigator's command line: a prompt, and a line that runs on Enter.

``TCommandLine`` (``CMDLINE.PAS``), one row directly above the key bar.  It is
an :class:`~navml.widgets.dialog.input_line.InputLine` in everything but three
respects, each of which is the original's:

* **It never holds the keyboard.**  DOS Navigator's line was ``ofPostProcess``
  and not selectable: it got the keys the focused panel left alone, which is
  every printable character and the editing keys a list has no use for.
  Here that is ``Shell.on_key``, which is where a key the panel declined walks
  up to -- so the caret is drawn here by ``Shell.cursor_position`` rather than
  by focus, and the line is never in anybody's tab order.
* **It paints its prompt**, ``<directory>>``, before the text, and scrolls the
  text in the room that is left.  No ``◄``/``►`` margins: the original scrolled
  silently.
* **Esc clears it and Ctrl+E / Ctrl+X walk the command history**, the keys
  ``CMDLINE.PAS`` answers to while the panel eats Up and Down.

Enter is not here.  It runs the line only while there is something on it and
belongs to the panel otherwise, which is a question about the line asked by a
key table -- ``ExecuteCommandLine`` in ``navigator/commands.py``.
"""

from __future__ import annotations

from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import reactive
from navkit.screen import Surface
from navml.history import HISTORY
from navml.widgets.dialog.input_line import InputLine

#: The history list the command line keeps, in :data:`~navml.history.HISTORY`.
HISTORY_ID = "command"


class CommandLine(InputLine):
    """A prompt and one line of input, above the key bar."""

    #: Not a dialog control: keys reach it without the focus.
    accepts_focus = False

    #: What is painted before the text -- the active panel's directory and
    #: ``>``.  Bound by ``Shell``.
    prompt: str = reactive("")

    #: ``::prompt`` beside the input line's own parts.
    parts = ("prompt",)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #: Where Ctrl+E / Ctrl+X have got to in the history, or -1 for the
        #: line the user is typing.
        self._recalled = -1

    @property
    def shown_prompt(self) -> str:
        """The prompt, cut from the left so a third of the row stays for text."""
        prompt = self.prompt
        keep = max(0, self.width - max(1, self.width // 3))
        if len(prompt) > keep:
            prompt = prompt[len(prompt) - keep :]
        return prompt

    @property
    def room(self) -> int:
        """The row, less the prompt and the column the caret sits in at the end."""
        return max(0, self.width - len(self.shown_prompt) - 1)

    def clear(self) -> None:
        self.value = ""
        self.cursor = self.first = 0
        self.anchor = None
        self._recalled = -1

    def set_text(self, text: str) -> None:
        self.value = text
        self.anchor = None
        self.cursor = len(text)

    def home(self) -> None:
        self._move(0, False)

    def end(self) -> None:
        self._move(len(self.value), False)

    def insert(self, text: str) -> None:
        """Type *text* at the caret, as though it had been typed."""
        self._replace_selection(text)

    # -- input ---------------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if event.matches("escape"):
            if not self.value:
                return False
            self.clear()
            return True
        if event.matches("ctrl+e"):
            return self._recall(+1)
        if event.matches("ctrl+x"):
            return self._recall(-1)
        if event.key in ("up", "down", "enter", "tab"):
            return False
        taken = await super().on_key(event)
        if taken:
            self._recalled = -1
        return taken

    def _recall(self, step: int) -> bool:
        """Ctrl+E goes back a command, Ctrl+X forward, and past the newest clears."""
        entries = HISTORY.entries(HISTORY_ID)
        index = self._recalled + step
        if index < -1 or index >= len(entries):
            return True
        self._recalled = index
        self.set_text(entries[index] if index >= 0 else "")
        return True

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.action != "press" or event.button != "left":
            return False
        start = len(self.shown_prompt)
        if event.x >= start:
            self._move(self.first + event.x - start, event.shift)
        return True

    # -- painting ------------------------------------------------------------

    def cursor_position(self) -> tuple[int, int] | None:
        return len(self.shown_prompt) + self.cursor - self.first, 0

    def render(self, surface: Surface) -> None:
        if self.width < 1 or self.height < 1:
            return
        style = self.style
        surface.fill(0, 0, self.width, self.height, " ", style)
        prompt = self.shown_prompt
        surface.draw_text(0, 0, prompt, self.part_style("prompt"))
        start, room = len(prompt), self.room
        if room < 1:
            return
        surface.draw_text(start, 0, self.value[self.first : self.first + room], style, room)
        low, high = self.selection
        if low != high:
            run = self.value[max(low, self.first) : min(high, self.first + room)]
            if run:
                surface.draw_text(
                    start + max(0, low - self.first), 0, run,
                    self.part_style("selection"), room,
                )
