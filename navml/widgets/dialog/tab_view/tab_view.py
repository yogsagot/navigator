"""Pages behind a row of tabs, one page shown at a time.

Turbo Vision had no tab control, and DOS Navigator gave every group of
settings a dialog of its own; this is the library's for a dialog that holds
several of them.  **Every child is a page**, and the caption on its tab is the
page's ``title``.

**The tabs are drawn as tabs**: each a box open at the bottom, its caption
between two bars, standing side by side on a baseline that runs the whole
width.  The current tab is drawn double and its foot is left open, so it
reads as raised and joined to the page under it; every other tab is single
and closed off by the baseline.

**One row, scrolled.**  Tabs that do not all fit get a ◄ at the left edge and
a ► at the right, each there only while there is a tab out of sight that way;
a click on one moves the row a tab along, and on top so does a notch of the
wheel anywhere over the tabs.  Down the left a notch of the wheel is the tab
above or below instead.  Selecting a tab out of sight (by
key) brings it into view, which an effect does, so the view follows however
the tab came to be current -- the scrolling is the view's, not the model's.

**A page's first row is the baseline**, as a dialog's first row is its frame:
a page lays its controls out from ``y: 1`` exactly as the dialog it might once
have been did, and the row that would have been the frame's is not lost.

**A page that is not current is hidden**, which is the whole of keeping it
out of the way: a hidden widget is already out of the paint, the tab order
(:meth:`~navkit.widget.Widget.focusable`) and the Alt+letter walk
(:meth:`~navml.widgets.dialog.modal.Modal.controls`).  It is set in
:meth:`select` itself rather than by an effect, so the focus can move onto the
new page in the same call.

**The strip takes the keyboard, last.**  In a dialog's tab order it comes
after the dialog's own buttons (``focus_last``), so Tab past Cancel reaches
it, Left/Right or Up/Down (Home, End) change the tab while it keeps the
keyboard, and the next Tab goes on into the page chosen.

**A page remembers where the keyboard was on it.**  Coming back to a page by
Ctrl+PgDn, Ctrl+PgUp or a click, or by Tab from the strip, puts the keyboard
back on the control that last had it there, as long as it can still take it;
a page not yet visited starts at its first control.
From anywhere on a page Ctrl+PgDn and Ctrl+PgUp (or Ctrl+Tab and
Ctrl+Shift+Tab, where a terminal sends them) change it as well, and so do
PgDn and PgUp unless the control with the keyboard takes them (a list pages,
a number steps); a click on a tab selects it.
"""

from __future__ import annotations

from navkit.events import KeyEvent, MouseClickEvent
from navkit.glyphs import BOX_CHARSETS, GLYPHS_UNICODE, charset, ellipsis, joins, scrollbar
from navkit.reactive import effect, peek, reactive
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget

from navml.widgets.dialog.commands import NextTab, PreviousTab, SelectNext
from navml.widgets.layout.layout import Layout
from navml.widgets.layout.layout.layout import Rect


#: Where the tabs go: in a row along the top, or a column down the left.
SIDES = ("top", "left")

#: The widest the left column of tabs grows; a longer caption is cut.
MAX_COLUMN = 20


class TabView(Layout):
    """A strip of tabs over the one page it has chosen."""

    #: The index of the page shown.  Assign it through :meth:`select`, which
    #: also hides the others and moves the focus.
    current: int = reactive(0)

    #: The first tab in view while they do not all fit.  The arrows move it;
    #: :meth:`_reveal` moves it to bring the current tab into view.
    first: int = reactive(0)

    #: ``top``: a row of tabs over the page, scrolled sideways.  ``left``: a
    #: column of them beside it, a tab a row, scrolled up and down.
    side: str = reactive("top")

    #: The strip's two ends lie on the parent's frame: on top the first and
    #: last columns, down the left the first and last rows.  The baseline or
    #: the rule meets the frame there in its tees (``╟``/``╢`` and ``╤``/``╧``
    #: on a double one), and the tabs, the arrows and the pages keep to what
    #: is between.
    joins_frame: bool = reactive(False)

    #: The tabs' boxes and the baseline.
    border = StyleProperty("single", values=tuple(BOX_CHARSETS))

    #: A tab's caption, the current one's, and the scrolling arrows.
    parts = ("tab", "selected", "arrow")

    #: The rows above the baseline on top: the tabs' tops and their captions.
    strip_rows = 2

    #: After the dialog's own buttons in its tab order, as
    #: :meth:`~navml.widgets.dialog.dialog.Dialog.focusable` reads it.
    focus_last = True

    #: PgDn and PgUp too, where the control with the keyboard does not take
    #: them for itself -- a list pages, a number steps -- as Ctrl+ always do.
    keys = {
        "ctrl+pagedown": NextTab,
        "ctrl+pageup": PreviousTab,
        "pagedown": NextTab,
        "pageup": PreviousTab,
        "ctrl+tab": NextTab,
        "ctrl+shift+tab": PreviousTab,
    }

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.can_focus = True
        #: Each page's control that last had the keyboard.  Plain, not
        #: reactive: nothing is drawn from it.
        self._last_focus: dict[Widget, Widget] = {}

    def mounted(self) -> None:
        super().mounted()
        effect(self, TabView._reveal)
        effect(self, TabView._remember)

    # -- the pages -----------------------------------------------------------

    def remove(self, child: Widget) -> None:
        self._last_focus.pop(child, None)
        super().remove(child)

    def page_of(self, widget: Widget | None) -> Widget | None:
        """The page *widget* is on, or None if it is on none of them."""
        while widget is not None and widget.parent is not self:
            widget = widget.parent
        return widget

    def _remember(self) -> None:
        """Note the control on a page that has the keyboard: an effect on the
        application's focus, which only ever records."""
        app = self.application
        focused = app.focused if app is not None else None
        page = self.page_of(focused)
        if page is not None:
            self._last_focus[page] = focused

    def add(self, child: Widget) -> Widget:
        child.visible = len(self.children) == peek(self, TabView.current)
        return super().add(child)

    @property
    def pages(self) -> list[Widget]:
        return list(self.children)

    def index_of(self, page: Widget) -> int:
        return self.children.index(page)

    def select(self, index: int) -> None:
        """Show page *index* alone, and give the keyboard to the page (see
        :meth:`enter_page`) -- unless the strip has it, which keeps it: the
        next Tab goes on into the page."""
        pages = self.children
        if not pages:
            return
        index %= len(pages)
        self.current = index
        for number, page in enumerate(pages):
            page.visible = number == index
        if not self.focused:
            self.enter_page()

    def enter_page(self) -> bool:
        """Give the keyboard to the current page: to the control that last
        had it there if it still can take it, else to its first.  False if
        the page has nothing to take it."""
        if not self.children:
            return False
        page = self.children[self.current]
        order = page.focusable()
        if not order:
            return False
        last = self._last_focus.get(page)
        return (last if last in order else order[0]).focus()

    async def on_select_next(self, event: SelectNext) -> bool:
        """Tab from the strip goes into the page, where the keyboard last was
        on it.  Anywhere else -- or with nothing on the page to take it --
        Tab is the dialog's, and it passes on out."""
        if not self.focused:
            return False
        return self.enter_page()

    async def on_key(self, event: KeyEvent) -> bool:
        """With the keyboard on the strip: the arrows step through the tabs,
        stopping at the ends, and Home and End go to them."""
        if not self.focused or not self.children:
            return False
        last = len(self.children) - 1
        if event.matches("left") or event.matches("up"):
            index = max(0, self.current - 1)
        elif event.matches("right") or event.matches("down"):
            index = min(last, self.current + 1)
        elif event.matches("home"):
            index = 0
        elif event.matches("end"):
            index = last
        else:
            return False
        self.select(index)
        return True

    async def on_next_tab(self, event: NextTab) -> bool:
        self.select(self.current + 1)
        return True

    async def on_previous_tab(self, event: PreviousTab) -> bool:
        self.select(self.current - 1)
        return True

    # -- the strip -----------------------------------------------------------

    def captions(self) -> list[str]:
        return [str(getattr(page, "title", "") or index + 1) for index, page in enumerate(self.children)]

    @staticmethod
    def _width(caption: str) -> int:
        """A tab's cells on top: its caption, a blank either side, two bars."""
        return len(caption) + 4

    def _sizes(self) -> list[int]:
        """Each tab's cells along the strip: its width on top, a row down the left."""
        if self.side == "left":
            return [1] * len(self.children)
        return [self._width(caption) for caption in self.captions()]

    def _framed(self) -> bool:
        """Whether this strip's ends lie on its parent's frame."""
        return self.joins_frame

    def _offset(self) -> int:
        """Where the strip's run begins: past the frame's column or row if
        its ends lie on one."""
        return 1 if self._framed() else 0

    def _length(self) -> int:
        """The strip's cells along its run: the width on top, the height down
        the left -- less the frame's two columns or rows if it runs over them."""
        run = self.height if self.side == "left" else self.width
        return max(0, run - 2 * self._offset())

    @property
    def column(self) -> int:
        """The left strip's width: a mark, a blank, the longest caption and a
        blank, but never more than :data:`MAX_COLUMN` -- a page needs the rest."""
        longest = max((len(caption) for caption in self.captions()), default=0)
        return min(MAX_COLUMN, longest + 3)

    @property
    def scrolls(self) -> bool:
        """Whether the tabs are more than the strip holds."""
        return sum(self._sizes()) > self._length()

    def _start(self) -> int:
        """The first tab in view: :attr:`first`, but never so far on that the
        strip would end short with tabs before it hidden."""
        if not self.scrolls:
            return 0
        sizes = self._sizes()
        room, start = self._length() - 2, len(sizes)
        while start > 0 and sum(sizes[start - 1:]) <= room:
            start -= 1
        return max(0, min(self.first, start))

    def tabs(self) -> list[tuple[int, int, str]]:
        """``(at, index, caption)`` for every tab in view, in order; *at* is
        its column on top, its row down the left.

        Only whole tabs are shown, past the first arrow while the strip
        scrolls; one tab bigger than all the room there is is shown cut
        rather than not at all.
        """
        scrolls = self.scrolls
        offset = self._offset()
        lead = offset + (1 if scrolls else 0)
        end = offset + (self._length() - 1 if scrolls else self._length())
        placed, at = [], lead
        sizes, captions = self._sizes(), self.captions()
        for index in range(self._start(), len(captions)):
            if placed and at + sizes[index] > end:
                break
            placed.append((at, index, captions[index]))
            at += sizes[index]
        return placed

    def can_scroll(self) -> tuple[bool, bool]:
        """Whether there are tabs out of sight before, and after."""
        placed = self.tabs()
        if not placed or not self.scrolls:
            return False, False
        return placed[0][1] > 0, placed[-1][1] < len(self.children) - 1

    def scroll(self, delta: int) -> None:
        """Move the strip *delta* tabs along, as a click on an arrow does."""
        self.first = max(0, self._start() + delta)

    def _reveal(self) -> None:
        """Bring the current tab into view: an effect on the size, the side,
        the captions and :attr:`current`, which writes :attr:`first`."""
        current = self.current
        if self._length() <= 0 or not self.scrolls:
            return
        first = min(peek(self, TabView.first), current)
        sizes = self._sizes()
        while first < current and sum(sizes[first:current + 1]) > self._length() - 2:
            first += 1
        if first != peek(self, TabView.first):
            self.first = first

    def plan(self, children: list[Widget]) -> dict[Widget, Rect]:
        if self.side not in SIDES:
            raise ValueError(f"side is {self.side!r}; it takes {', '.join(SIDES)}")
        if self.side == "left":
            left, top = self.column + 1, self._offset()
            height = max(0, self.height - 2 * top)
            return {child: (left, top, max(0, self.width - left), height) for child in children}
        left, top = self._offset(), self.strip_rows
        width = max(0, self.width - 2 * left)
        return {child: (left, top, width, max(0, self.height - top)) for child in children}

    def in_strip(self, x: int, y: int) -> bool:
        """Whether *x*, *y* is the strip's.  On top that is a tab's top, its
        caption, or its foot on the baseline, which is a page's first row as
        well; a page leaves that row empty, so a click there falls out to
        here.  Down the left it is the column of tabs and the rule beside it,
        but not the frame's rows: a click there is the frame's, to drag by."""
        offset = self._offset()
        if self.side == "left":
            return 0 <= x <= self.column and offset <= y < offset + self._length()
        return 0 <= y <= self.strip_rows and offset <= x < offset + self._length()

    def tab_at(self, x: int, y: int) -> int | None:
        if not self.in_strip(x, y):
            return None
        for at, index, caption in self.tabs():
            if self.side == "left":
                if y == at:
                    return index
            elif at <= x < at + self._width(caption):
                return index
        return None

    def _on_arrow(self, x: int, y: int) -> int:
        """-1 over the arrow back, 1 over the one on, 0 elsewhere -- and over
        an arrow only while it is there."""
        earlier, later = self.can_scroll()
        if not self.in_strip(x, y):
            return 0
        at = (y if self.side == "left" else x) - self._offset()
        if at == 0 and earlier:
            return -1
        if at == self._length() - 1 and later:
            return 1
        return 0

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.is_wheel:
            if not self.in_strip(event.x, event.y):
                return False
            step = -1 if event.button in ("wheel_up", "wheel_left") else 1
            if self.side == "left":
                # Down the left a notch is the tab above or below, as a list's
                # cursor moves; it stops at the ends.
                index = max(0, min(len(self.children) - 1, self.current + step))
                if index != self.current:
                    self.select(index)
            elif self.scrolls:
                # On top the row moves a tab a notch, as the arrows move it;
                # which tab is current does not change.
                self.scroll(step)
            return True
        if event.action != "press" or event.button != "left":
            return False
        arrow = self._on_arrow(event.x, event.y)
        if arrow:
            self.scroll(arrow)
            return True
        index = self.tab_at(event.x, event.y)
        if index is None:
            return False
        self.select(index)
        return True

    def render(self, surface: Surface) -> None:
        if self.width <= 0 or self.height <= 0:
            return
        if self.side == "left":
            self._render_left(surface)
        else:
            self._render_top(surface)

    def _render_top(self, surface: Surface) -> None:
        top_left, top_right, _, _, line, bar = self.box_charset()
        foot = self.box_joins()[3]
        # The current tab's double box, and where its double sides come down
        # onto the single baseline -- a meeting no join table holds.
        raised = charset("double", self.glyphs)
        if self.glyphs >= GLYPHS_UNICODE:
            raised_feet = ("╜", "╙")
        else:
            raised_feet = (raised[3], raised[2])
        base, offset, length = self.strip_rows, self._offset(), self._length()
        surface.fill(offset, 0, length, base, " ", self.style)
        baseline = [line] * self.width
        if self._framed() and self.width >= 2:
            tees = joins(getattr(self.parent, "border", "double"), self.glyphs)
            baseline[0], baseline[-1] = tees[0], tees[1]
        surface.draw_text(0, base, "".join(baseline), self.style)
        for x, index, caption in self.tabs():
            inner = self._width(caption) - 2
            chosen = index == self.current
            if chosen:
                left, right, side, edge = raised[0], raised[1], raised[5], raised[4]
            else:
                left, right, side, edge = top_left, top_right, bar, line
            surface.draw_text(x, 0, left + edge * inner + right, self.style)
            surface.draw_text(x, 1, side, self.style)
            surface.draw_text(x + 1, 1, f" {caption} ", self.part_style("selected" if chosen else "tab"))
            surface.draw_text(x + 1 + inner, 1, side, self.style)
            if chosen:
                surface.draw_text(x, base, raised_feet[0] + " " * inner + raised_feet[1], self.style)
            else:
                surface.draw_text(x, base, foot + line * inner + foot, self.style)
        earlier, later = self.can_scroll()
        arrows = scrollbar("dos", self.glyphs)
        if earlier:
            surface.draw_text(offset, 1, arrows[2], self.part_style("arrow"))
        if later:
            surface.draw_text(offset + length - 1, 1, arrows[3], self.part_style("arrow"))

    def _render_left(self, surface: Surface) -> None:
        """A tab a row, a mark before the current one, and the rule beside
        them the whole height -- into the frame's tees if it lies on one."""
        column = self.column
        bar = self.box_charset()[5]
        arrows = scrollbar("dos", self.glyphs)
        offset = self._offset()
        rows = {at: (index, caption) for at, index, caption in self.tabs()}
        surface.fill(0, offset, column, self._length(), " ", self.style)
        for y in range(offset, offset + self._length()):
            if y not in rows:
                continue
            index, caption = rows[y]
            chosen = index == self.current
            if len(caption) > column - 3:
                cut = ellipsis(self.glyphs)
                caption = caption[: max(0, column - 3 - len(cut))] + cut
            if chosen:
                surface.draw_text(0, y, arrows[3], self.part_style("arrow"))
            text = f" {caption}".ljust(column - 1)
            surface.draw_text(1, y, text, self.part_style("selected" if chosen else "tab"))
        rule = [bar] * self.height
        if self._framed() and self.height >= 2:
            tees = joins(getattr(self.parent, "border", "double"), self.glyphs)
            rule[0], rule[-1] = tees[2], tees[3]
        for y, char in enumerate(rule):
            surface.draw_text(column, y, char, self.style)
        earlier, later = self.can_scroll()
        if earlier:
            surface.draw_text(column // 2, offset, arrows[0], self.part_style("arrow"))
        if later:
            surface.draw_text(column // 2, offset + self._length() - 1, arrows[1], self.part_style("arrow"))
