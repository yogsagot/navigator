"""The pages of F1 Help, painted: DOS Navigator's ``THelpViewer`` (``HELPFILE.PAS``).

A page is Markdown under ``docs/`` (``navigator/lib/help/pages.py``), laid
out by the viewer's Markdown reading (``navigator/lib/viewer/markdown.py``)
with the three things the layout has for Help: heading anchors, links, and
pictures.  Both the read and the layout are on a thread; until a page lands
the last one stays painted.

What is DN's: Tab and Shift+Tab select the next and previous link, round the
ends; Enter follows the selected one; a stack of where one came from, 200
deep (``MaxUndo``), each with its place.  Departures, both asked for:

- **No text cursor.**  ``THelpViewer`` was a ``TScroller`` with a cursor the
  arrows moved, and a reference was selected while the cursor stood on it.
  Here the arrows, PgUp/PgDn and Home/End scroll: the rows are reflowed
  Markdown laid out for Hebrew and Arabic, and the mouse does the pointing.
- **A single click follows a link**; DN's placed the cursor, and a double
  click followed.

A link out of Help -- another site -- is not followed (an in-app opener was
declined): it is an OSC 8 link for the terminal, and Tab passes over it.
Kept left to right on a mirrored screen, as the viewer is: its rows are laid
out already, and a picture must not be turned round.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import GLYPHS_UNICODE
from navkit.i18n import LOCALE, tr
from navkit.reactive import reactive
from navkit.screen import Surface
from navkit.widget import Widget
from navml.background import Background, Outcome

from navigator.lib.help import pages
from navigator.lib.viewer import markdown
from navigator.widgets.viewer.file_viewer.helpers import _laid_row

#: ``MaxUndo``: how many places Alt+F1 goes back through.
HISTORY_LIMIT = 200
#: Rows a notch of the wheel scrolls, as the viewer's.
WHEEL_ROWS = 3

_READER = Background("nav-help", workers=1)


@dataclass(frozen=True, slots=True)
class Place:
    """Where one was: DN's ``THelpParameters``.  *src* is the source offset
    of the row on top, not a row number, so it is the same place at any width."""

    page: str
    src: int = 0
    selected: int = -1


def _load(name: str, data: bytes | None, width: int, unicode: bool, language: str) -> tuple[bytes, Any]:
    """On the thread: *name* read (unless *data* is it already) and laid out."""
    if data is None:
        data = pages.read(name, language).data
    layout = markdown.render(
        data, width, unicode=unicode, pictures=lambda source: pages.shot(name, source, language))
    return data, layout


class HelpViewer(Widget):
    """One help page, its links, and the way back."""

    parts = ("md", "selected")
    mirrors = False

    #: The page shown, by name (``clipboard.md``); "" before the first lands.
    page: str = reactive("")
    #: Its layout, replaced whole when a page or a width lands.
    layout: Any = reactive(None)
    #: The row on top.
    top: int = reactive(0)
    #: How many rows the page has, for the scroll bar.
    total: int = reactive(0)
    #: Which of ``links`` Enter follows, -1 for none.
    selected: int = reactive(-1)
    #: What to say in the page's place: a page that is not there.
    problem: str = reactive("")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.can_focus = True
        #: The places Alt+F1 goes back to, oldest first.
        self.history: list[Place] = []
        #: The links of ``layout`` that lead to a page of Help.
        self.links: list[Any] = []
        #: The page asked for and not landed yet: its name, the anchor to
        #: open at, and the place to restore instead (going back).
        self._wanted: tuple[str, str, Place | None] | None = None
        #: The Markdown of ``page``, kept for laying out again at a new width.
        self._data: bytes | None = None
        #: What the thread was last asked for; an answer to anything else is dropped.
        self._asked: tuple[Any, ...] | None = None

    # -- going places ----------------------------------------------------------

    def show(self, topic: str) -> None:
        """Go to *topic* (``page.md#anchor``), remembering where this was."""
        name, anchor = pages.split(topic)
        if self.page or self._wanted is not None:
            if name == self._name() and self.layout is not None and self._wanted is None:
                if not anchor:
                    return
                if anchor in self.layout.anchors:
                    # On this page already: no read, only the place.
                    self._remember()
                    self._arrive(anchor, None)
                    return
            self._remember()
        self._open(name, anchor, None)

    def back(self) -> bool:
        """Alt+F1: the place before this one.  False with none."""
        if not self.history:
            return False
        place = self.history.pop()
        if place.page == self.page and self.layout is not None and self._wanted is None:
            self._arrive("", place)
        else:
            self._open(place.page, "", place)
        return True

    def follow(self) -> bool:
        """Enter: the selected link's page.  False with none selected."""
        if not 0 <= self.selected < len(self.links):
            return False
        topic = pages.follow(self.page, self.links[self.selected].href)
        if topic is None:
            return False
        self.show(topic)
        return True

    def step(self, by: int) -> None:
        """Tab / Shift+Tab: the next or previous link, round the ends, shown."""
        if not self.links:
            return
        if self.selected < 0:
            self.selected = 0 if by > 0 else len(self.links) - 1
        else:
            self.selected = (self.selected + by) % len(self.links)
        row = self.links[self.selected].row
        if row < self.top:
            self.scroll_to(row)
        elif row >= self.top + self.height:
            self.scroll_to(row - self.height + 1)

    def scroll_to(self, row: int) -> None:
        self.top = max(0, min(row, self.total - max(1, self.height)))

    def _name(self) -> str:
        return self._wanted[0] if self._wanted is not None else self.page

    def _place(self) -> Place:
        layout = self.layout
        src = layout.rows[self.top].src if layout is not None and self.top < len(layout.rows) else 0
        return Place(self.page, src, self.selected)

    def _remember(self) -> None:
        if not self.page:
            return
        self.history.append(self._place())
        del self.history[:-HISTORY_LIMIT]

    def _open(self, name: str, anchor: str, place: Place | None) -> None:
        self._wanted = (name, anchor, place)
        self._asked = None
        self._request()

    # -- reading and laying out -------------------------------------------------

    def _request(self) -> None:
        """Ask the thread for the page wanted (or the one shown) at the width
        and glyphs in force, unless that is what was asked last.  Called from
        ``render`` too, which is how a new width is noticed."""
        name = self._name()
        if not name or self.width <= 0:
            return
        unicode = self.glyphs >= GLYPHS_UNICODE
        language = LOCALE.code
        key = (name, self.width, unicode, language)
        if key == self._asked:
            return
        self._asked = key
        data = self._data if self._wanted is None else None
        held = self._place() if self._wanted is None else None

        def landed(outcome: Outcome) -> None:
            if key != self._asked:
                return  # another page or width was asked for meanwhile
            self._landed(name, outcome, held)

        _READER.run(self, _load, name, data, self.width, unicode, language, done=landed)

    def _landed(self, name: str, outcome: Outcome, held: Place | None) -> None:
        wanted, self._wanted = self._wanted, None
        if isinstance(outcome.error, pages.PageNotFound):
            self.page, self._data, self.layout, self.links = name, None, None, []
            self.total, self.top, self.selected = 0, 0, -1
            self.problem = tr("There is no help page {name}").format(name=name)
            return
        self._data, layout = outcome.result()
        self.problem = ""
        self.page = name
        self.layout = layout
        self.total = len(layout.rows)
        self.links = [
            link for link in layout.links()
            if not link.image and pages.follow(name, link.href) is not None
        ]
        if wanted is not None:
            self._arrive(wanted[1], wanted[2])
        else:
            self._arrive("", held)

    def _arrive(self, anchor: str, place: Place | None) -> None:
        """The place on the page in hand: *place*'s (a way back, or the same
        page at a new width), else *anchor*'s heading, else the top."""
        layout = self.layout
        if place is not None:
            self.scroll_to(layout.row_for(place.src))
            self.selected = place.selected if place.selected < len(self.links) else -1
            return
        self.scroll_to(layout.anchors.get(anchor, 0))
        # DN's ``Selected := 1``: the first link, here the first from the top row on.
        self.selected = next(
            (index for index, link in enumerate(self.links) if link.row >= self.top),
            0 if self.links else -1,
        )

    # -- keys and the mouse ------------------------------------------------------

    async def on_key(self, event: KeyEvent) -> bool:
        if event.ctrl or event.alt or event.shift:
            return False
        page = max(1, self.height - 1)
        moves = {"up": -1, "down": 1, "pageup": -page, "pagedown": page}
        if event.key in moves:
            self.scroll_to(self.top + moves[event.key])
        elif event.key == "home":
            self.scroll_to(0)
        elif event.key == "end":
            self.scroll_to(self.total)
        else:
            return False
        return True

    def link_at(self, x: int, y: int) -> int:
        """Which of ``links`` is painted at *x*, *y*, or -1."""
        layout = self.layout
        index = self.top + y
        if layout is None or not 0 <= index < len(layout.rows) or x < 0:
            return -1
        _, columns = _laid_row(layout.rows[index], self.width)
        if x >= len(columns) or columns[x] is None:
            return -1
        column = columns[x]
        for number, link in enumerate(self.links):
            if any(row == index and start <= column < end for row, start, end in link.spans):
                return number
        return -1

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        await super().on_mouse_click(event)
        if event.is_wheel:
            if event.button in ("wheel_up", "wheel_down"):
                self.scroll_to(self.top + (-WHEEL_ROWS if event.button == "wheel_up" else WHEEL_ROWS))
                return True
            return False
        if event.action != "press" or event.button != "left":
            return False
        self.focus()
        found = self.link_at(event.x, event.y)
        if found >= 0:
            self.selected = found
            self.follow()
        return True

    # -- painting ----------------------------------------------------------------

    def render(self, surface: Surface) -> None:
        self._request()
        base = self.style
        surface.fill(0, 0, self.width, self.height, " ", base)
        layout = self.layout
        if layout is None:
            if self.problem:
                surface.draw_text(0, 0, self.problem, base, self.width)
            return
        chosen: set[tuple[int, int]] = set()
        if 0 <= self.selected < len(self.links):
            for row, start, end in self.links[self.selected].spans:
                chosen.update((row, column) for column in range(start, end))
        selected = self.part_style("selected")
        looks: dict[Any, Any] = {}
        width = self.width
        for y in range(self.height):
            index = self.top + y
            if index >= len(layout.rows):
                break
            row = layout.rows[index]
            cells, columns = _laid_row(row, width)
            if row.picture is not None:
                # The gutter or bullet before it as ever, then the picture's
                # own cells, their colours and all.
                cells, extra = cells[: row.lead], row.picture
            else:
                extra = ()
            for x, (char, classes, link) in enumerate(cells[:width]):
                if (index, columns[x]) in chosen:
                    look = selected
                else:
                    look = looks.get((classes, link))
                    if look is None:
                        look = looks[classes, link] = self._look(classes, link)
                if char == "":
                    if x == 0:
                        surface.set_cell(x, y, " ", look)
                    continue
                if x == width - 1 and x + 1 < len(cells) and cells[x + 1][0] == "":
                    surface.set_cell(x, y, " ", look)
                    continue
                surface.set_cell(x, y, char, look)
            for offset, (char, style) in enumerate(extra):
                x = row.lead + offset
                if x < width and char != "":
                    surface.set_cell(x, y, char, style)

    def _look(self, classes: tuple[str, ...], link: str | None) -> Any:
        """A cell's look: its classes' under ``HelpViewer::md``.  A code
        block is one colour -- the syntax colours were not chosen for Help's
        ground -- so a token's classes are left out."""
        if "token" in classes:
            classes = classes[: classes.index("token")]
        look = self.part_style("md", classes=classes) if classes else self.style
        if link and pages.follow(self.page, link) is None and not link.startswith("/"):
            # Out of Help: the terminal's to open (OSC 8).
            return look.derive(link=link)
        return look
