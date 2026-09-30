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
* **It paints its prompt** before the text, and scrolls the text in the room
  that is left.  No ``◄``/``►`` margins: the original scrolled silently.  The
  prompt is the shell's own, colours and all (``prompt_cells``), and DOS
  Navigator's ``<directory>>`` (``prompt``) only until the shell has printed
  one for the directory in front -- the one place this line is not the
  original's, whose ``SetDirShape`` ignored ``PROMPT``.
* **Esc clears it and Ctrl+E / Ctrl+X walk the command history**, the keys
  ``CMDLINE.PAS`` answers to while the panel eats Up and Down.

Enter is not here.  It runs the line only while there is something on it and
belongs to the panel otherwise, which is a question about the line asked by a
key table -- ``ExecuteCommandLine`` in ``navigator/commands.py``.
"""

from __future__ import annotations

from navkit.events import KeyEvent, MouseClickEvent
from navkit.reactive import reactive
from navkit.screen import Cell, Surface
from navkit.style import Style
from navml.history import HISTORY
from navml.widgets.dialog.input_line import InputLine

#: The history list the command line keeps, in :data:`~navml.history.HISTORY`.
HISTORY_ID = "command"

#: What ends a word for ``cmInsertName``: ``CMDLINE.PAS``'s ``Separators``.
_SEPARATORS = set(":.,/\\[]+><|; ")


class CommandLine(InputLine):
    """A prompt and one line of input, above the key bar."""

    #: Not a dialog control: keys reach it without the focus.
    accepts_focus = False

    #: What is painted before the text -- the active panel's directory and
    #: ``>``.  Bound by ``Shell``.
    prompt: str = reactive("")

    #: The shell's prompt as cells, each in the style the shell asked for.
    #: Painted instead of ``prompt`` whenever it holds any.  Bound by ``Shell``.
    prompt_cells: tuple = reactive(())

    #: ``::prompt`` beside the input line's own parts.
    parts = ("prompt",)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        #: Where Ctrl+E / Ctrl+X have got to in the history, or -1 for the
        #: line the user is typing.
        self._recalled = -1

    @property
    def _keep(self) -> int:
        """The most a prompt may take: a third of the row stays for text."""
        return max(0, self.width - max(1, self.width // 3))

    @property
    def shown_prompt(self) -> str:
        """The prompt, cut from the left so a third of the row stays for text."""
        prompt, keep = self.prompt, self._keep
        if len(prompt) > keep:
            prompt = prompt[len(prompt) - keep :]
        return prompt

    @property
    def shown_cells(self) -> tuple[Cell, ...]:
        """The shell's prompt, cut from the left the same way."""
        cells, keep = self.prompt_cells, self._keep
        if len(cells) > keep:
            cells = cells[len(cells) - keep :]
            if cells and cells[0][0] == "":
                # The cut took the left half of a wide character.
                cells = ((" ", cells[0][1]),) + cells[1:]
        return cells

    @property
    def prompt_width(self) -> int:
        """How many columns the prompt takes, whichever of the two is painted."""
        if self.prompt_cells:
            return len(self.shown_cells)
        return len(self.shown_prompt)

    @property
    def room(self) -> int:
        """The row, less the prompt and the column the caret sits in at the end."""
        return max(0, self.width - self.prompt_width - 1)

    def clear(self) -> None:
        self.value = ""
        self.cursor = self.first = 0
        self.anchor = None
        self._recalled = -1

    def set_text(self, text: str) -> None:
        self.value = text
        self.anchor = None
        self.cursor = len(text)

    def insert_name(self, name: str) -> None:
        """Type *name* at the caret as ``cmInsertName`` did (``CMDLINE.PAS``).

        A space goes after it, so the next name or argument can follow -- but
        not after a directory ending in ``/``, which the next name continues.
        And a space goes before it if the caret sits right after a word, so a
        name is never glued onto one.
        """
        text = name if name.endswith("/") else name + " "
        before = self.value[: self.cursor]
        if before and before[-1] not in _SEPARATORS:
            text = " " + text
        self.anchor = None
        self._replace_selection(text)
        self._recalled = -1

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

    @property
    def text_origin(self) -> int:
        return self.prompt_width

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """The input line's caret and selection, without its taking the focus."""
        return self.pointer(event)

    # -- painting ------------------------------------------------------------

    def cursor_position(self) -> tuple[int, int] | None:
        return self.prompt_width + self.cursor - self.first, 0

    def render(self, surface: Surface) -> None:
        if self.width < 1 or self.height < 1:
            return
        style = self.style
        surface.fill(0, 0, self.width, self.height, " ", style)
        if self.prompt_cells:
            for x, (char, cell) in enumerate(self.shown_cells):
                if char:
                    surface.set_cell(x, 0, char, _over(cell, style))
        else:
            surface.draw_text(0, 0, self.shown_prompt, self.part_style("prompt"))
        start, room = self.prompt_width, self.room
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


def _over(cell: Style, line: Style) -> Style:
    """A prompt cell's style, with what the shell left unsaid taken from the line.

    A cell the shell gave no colour is the terminal's default in a plain
    terminal, and the line's own colour is this one's default -- so it takes
    that whole, pinned palette included, keeping only the shell's attributes.
    A cell with a colour of its own keeps it and fills in the other half.
    """
    if cell.fg is None and cell.bg is None:
        return line.derive(
            bold=line.bold or cell.bold,
            italic=line.italic or cell.italic,
            underline=line.underline or cell.underline,
            reverse=line.reverse or cell.reverse,
        )
    return cell.derive(
        fg=line.fg if cell.fg is None else cell.fg,
        bg=line.bg if cell.bg is None else cell.bg,
    )
