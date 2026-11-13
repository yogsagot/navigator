"""Painting: the columns, scrolling the names, the gutter and its marks, the title and footer,
the rows and the header.

A mixin of :class:`Panel` (``navkit.widget.Mixin``): methods only; its state,
keys and the listing are in ``panel.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from navkit.bidi import REVEALED, display_width, reveal, reveal_runs
from navkit import glyphs as glyphs_module
from navkit.glyphs import GLYPHS_NERD
from navkit.i18n import tr
from navkit.reactive import peek
from navkit.screen import Surface
from navkit.style import Style

from navml.widgets.dialog.list_viewer import ListViewer

from navigator.lib.appearance import filetypes
from navigator.lib.appearance import icons as icon_glyphs
from navigator.lib.config.bookmarks import bookmarked_paths
from navigator.lib.drives import DriveGone, drive_of
from navigator.lib.file_ops.clip import CLIP
from navigator.lib.drives.listing import DirEntry
from navigator.lib.system import gitstatus
from navigator.settings import SETTINGS
from navigator.widgets.manager.panel.helpers import fit_text, text_width, window_text

if TYPE_CHECKING:
    from navigator.widgets.manager.panel.panel import Panel as _Base
else:
    from navkit.widget import Mixin as _Base


class Painting(_Base):
    """Painting: the columns, scrolling the names, the gutter and its marks, the title and footer,"""

    #: The detailed mode's columns after the name: heading, width, and the
    #: ``DirEntry`` property that fills it.  Dropped in :data:`DROP_ORDER`
    #: when the name would get too narrow.  A width of ``None`` is measured
    #: off the listing (:meth:`_owner_width`), or off *Country support*'s
    #: format for the date (``country.stamp_width``).
    DETAIL_COLUMNS = {
        # 8 cells, K/M/G/T: a departure from DN's 11 (``DirEntry.display_size``).
        "size": ("Size", 8, "display_size"),
        "packed": ("Packed", 8, "display_packed"),
        "ratio": ("%", 4, "display_ratio"),
        "attributes": ("Attr", 9, "display_attributes"),
        "links": ("Links", 5, "display_links"),
        "owner": ("Owner", None, "display_owner"),
        "date": ("Date", None, "display_date"),
    }
    DETAIL_ORDER = ("size", "packed", "ratio", "attributes", "links", "owner", "date")
    DROP_ORDER = ("links", "owner", "attributes", "ratio", "packed", "date")
    #: The columns only an archive's entries fill.
    ARCHIVE_ONLY = frozenset(("packed", "ratio"))
    #: The widest the owner column grows; a longer ``user:group`` ends in
    #: ``...``.
    MAX_OWNER_WIDTH = 17
    #: The narrowest the detailed mode lets the name column get before it
    #: gives up a column to widen it.
    MIN_NAME_WIDTH = 12

    def _owner_width(self) -> int:
        """The owner column's width: its longest ``user:group``, never
        narrower than its heading nor wider than :data:`MAX_OWNER_WIDTH`."""
        longest = max((text_width(item.display_owner) for item in self.items), default=0)
        return max(len(self.heading("owner")), min(longest, self.MAX_OWNER_WIDTH))

    def _follow_cursor(self) -> None:
        """In the list mode, scroll a whole column at a time.

        ``scroll`` stays a multiple of ``rows``, so a column's contents -- and
        so its width -- do not change as the cursor moves through it.
        """
        if self.view_mode != "list":
            super()._follow_cursor()
            return
        rows = self.rows
        if not rows:
            return
        cursor = self.cursor
        scroll = peek(self, ListViewer.scroll)
        scroll -= scroll % rows
        if cursor < scroll:
            scroll = cursor - cursor % rows
        # Advance a column at a time until the cursor's is shown whole.  The
        # columns depend on the scroll, so each step lays them out again.
        while True:
            self.scroll = scroll
            columns = self.list_columns
            right = self.inset + self.inner_width
            if not columns or any(
                first <= cursor < first + rows and x + width <= right
                for first, x, width in columns
            ) or (columns and columns[0][0] <= cursor < columns[0][0] + rows):
                break
            scroll += rows

    def page(self) -> int:
        """PgUp/PgDn: the whole view, every row of every column -- DN's scroll
        bar page (``Size.Y * (Size.X+1) div LineLength``), where navml's list
        keeps a row back.  Every mode, not the list mode alone."""
        return max(1, self.capacity)

    def tooltip_anchor(self) -> tuple[int, int]:
        """The cursor's name: in the list mode, in the column it is in."""
        if self.view_mode != "list" or self.cursor_position() is not None:
            return super().tooltip_anchor()
        for first, left, _width in self.list_columns:
            if first <= self.cursor < first + self.rows:
                return left + 1, self.inset + self.header + self.cursor - first
        return super().tooltip_anchor()

    def index_at(self, x: int, y: int) -> int | None:
        if self.view_mode != "list":
            return super().index_at(x, y)
        row = y - self.inset - self.header
        if not 0 <= row < self.rows:
            return None
        for first, left, width in self.list_columns:
            if left <= x < left + width:
                index = first + row
                return index if index < len(self.items) else None
        return None

    def can_scroll_names(self, step: int) -> bool:
        offset = self.name_offset
        return offset > 0 if step < 0 else offset < self.max_name_scroll

    def scroll_names(self, step: int) -> None:
        """Left and Right in the simple and detailed modes: every name a cell along."""
        self.name_scroll = max(0, min(self.name_offset + step, self.max_name_scroll))

    async def on_hbar_scroll(self, event: Any) -> bool:
        """The bottom bar was worked (a departure, as the editor's): the names
        scrolled to its value."""
        self.name_scroll = max(0, min(event.value, self.max_name_scroll))
        return True

    # -- painting ------------------------------------------------------------

    @property
    def show_icons(self) -> bool:
        """Whether to reserve the icon gutter.

        Both halves have to agree, the way a terminal's mouse support and the
        caller's wish for it do: the sheet says whether icons are wanted and
        the terminal says whether its font could draw one.
        """
        return self.icons != "none" and self.glyphs >= GLYPHS_NERD

    @property
    def gutter(self) -> int:
        """Columns held back at the left of a row, for the icon or the type mark.

        Two with an icon, not one.  A Nerd Font *Mono* build patches its icons
        to a single cell but the plain build does not, and the difference is
        invisible until a name starts one column late on somebody else's
        terminal.  Without one it is a single cell holding
        :attr:`DirEntry.type_mark` -- and always kept, because a tagged
        entry's :attr:`tag_char` is drawn there too.
        """
        return 2 if self.show_icons else 1

    #: The cells a git letter takes at the end of a name: a blank, it, and a
    #: blank keeping it off the column divider.
    GIT_CELLS = 3

    @property
    def git_cells(self) -> int:
        """:data:`GIT_CELLS` while the directory shown is in a work tree, else none."""
        return self.GIT_CELLS if self.git is not None else 0

    def git_mark(self, item: DirEntry) -> str:
        """*item*'s letter (:mod:`navigator.lib.system.gitstatus`), or a blank."""
        git = self.git
        if git is None or item.name == ".." or item.directory is not None:
            return " "
        return git.marks.get(item.name, " ")

    def read_only_mark(self) -> str:
        """What the title says a read-only file system with: a lock at the
        Nerd tier, else ``[R/O]``.  Not DN's, whose DOS drives were written
        or failed with a box; a disk image is read-only before anything is
        tried, and the title says it before the refusal does."""
        if self.glyphs >= GLYPHS_NERD:
            return icon_glyphs.READ_ONLY
        return f"[{tr('R/O')}]"

    def remembered_mark(self) -> str:
        """What the title starts with in a remembered directory: ``◆`` for
        its own record, ``◇`` for one above's (``*`` and ``+`` in ASCII, a
        pin and a bookmark at the Nerd tier); ``""`` elsewhere.  Without it
        a sort or a mask coming back with a directory would look like a
        fault."""
        if not self.remembered or self.found is not None:
            return ""
        own = self.remembers_here
        if self.glyphs >= GLYPHS_NERD:
            return icon_glyphs.REMEMBERED if own else icon_glyphs.REMEMBERED_ABOVE
        if self.glyphs <= glyphs_module.GLYPHS_ASCII:
            return "*" if own else "+"
        return "\u25c6" if own else "\u25c7"

    def git_text(self) -> str:
        """The branch for the title, with how far it is ahead of and behind
        its upstream (``master ↑2↓1``), or ``""`` outside a work tree."""
        git = self.git
        if git is None or not git.branch:
            return ""
        up, down = ("^", "v") if self.glyphs <= glyphs_module.GLYPHS_ASCII else ("\u2191", "\u2193")
        counts = (f"{up}{git.ahead}" if git.ahead else "") + (f"{down}{git.behind}" if git.behind else "")
        return f"{git.branch} {counts}" if counts else git.branch

    @property
    def title_location(self) -> str:
        """What the title names the directory by: its path on the disk, and
        elsewhere what the drive calls it (``GetDir``)."""
        location = self.location
        if location.is_local:
            return str(location.path)
        try:
            return drive_of(location).get_dir(location)
        except DriveGone:
            return str(location)

    def title_text(self) -> str:
        """The path across the top frame, clipped to fit -- or, for a *Find:*
        listing, what it was found by (DN's drive name, ``Find: *.c``).

        **A file mask other than ``*`` follows in brackets**, ``/src [*.c;*.h]``
        -- Alt+Del's *Filter* or Alt+S's *File mask*.  Not DN's: its panel said
        nothing of a mask, and a panel that hides files without saying so
        reads as a directory that lacks them.  The path gives way first; the
        mask is cut only when the bracket alone would not fit.

        **On a file system mounted read-only, a mark goes before it**
        (:meth:`read_only_mark`), ``/media/me/UBUNTU [R/O]``: a disk image
        Enter mounted is never written, and the title says so first.

        **In a remembered directory a mark goes first**
        (:meth:`remembered_mark`), ``◆ /src``, not DN's either.

        **In a git work tree the branch follows** (:meth:`git_text`), also
        not DN's: it is dropped before the path would be cut under
        :data:`MIN_NAME_WIDTH` cells to keep it.
        """
        title = self.found.title if self.found is not None else self.title_location
        mask = self.file_mask.strip()
        suffix = f" [{mask}]" if mask not in ("", filetypes.ALL_FILES) else ""
        if self.read_only and self.found is None:
            suffix = f" {self.read_only_mark()}{suffix}"
        room = max(4, self.width - 4 - 2 * self.title_margin)
        if suffix and len(suffix) > room - 4:
            suffix = suffix[: max(0, room - 8)] + "...]" if room > 12 else ""
        # The branch goes before the mask does, once the path would be cut
        # under a dozen cells to keep it.
        branch = self.git_text()
        if branch:
            branch = f"  {branch}"
            if room - len(suffix) - len(branch) < min(len(title), self.MIN_NAME_WIDTH):
                branch = ""
        mark = self.remembered_mark()
        prefix = f"{mark} " if mark else ""
        space = room - len(suffix) - len(branch) - len(prefix)
        title = self._cut_start(title, space) if self.found is not None else self._cut_title(title, space)
        return f" {prefix}{title}{suffix}{branch} "

    def footer_text(self) -> str:
        """What a search has typed, while it is searching; else nothing --
        the current file and the selection are info lines, as DN's were."""
        if self.quick_search is not None:
            return f"{self.search_label}{self.quick_search} "
        return ""

    def key_hints(self) -> list[tuple[str, str]]:
        """While searching, Ctrl+S again finds the next -- for the key bar."""
        return [("Ctrl+S", tr("Next"))] if self.quick_search else []

    def type_classes(self, item: DirEntry) -> tuple[str, ...]:
        """*item*'s file-type classes on ``Panel::row``: ``.directory`` and its
        category.  *Files highlight* off, none -- directories as plain as
        files, as DN's ``HLC[1..8] := C1`` made ``ttDirectory`` too."""
        if not self.shows("files_highlight"):
            return ()
        classes = ("directory",) if item.is_dir else ()
        category = filetypes.category_of(item.name, item.is_dir, item.type_mark)
        return classes + (category,) if category else classes

    def row_style(self, index: int, item: DirEntry) -> Style:
        classes = self.type_classes(item)
        if self.is_marked(item):
            classes += ("marked",)
        if CLIP and CLIP.holds(self.entry_location(item)):
            # Waiting for Ctrl+V: ``Panel::row.clip-cut`` / ``.clip-copy``.
            classes += ("clip-cut" if CLIP.move else "clip-copy",)
        classes += self.row_classes(index, item)
        return self.part_style("row", classes=classes, selected=self.row_selected(index))

    def row_classes(self, index: int, item: DirEntry) -> tuple[str, ...]:
        """More classes for row *index*'s ``Panel::row``: none here; a Miller
        column marks the entry its next column shows (``.trail``)."""
        return ()

    @property
    def divider_glyph(self) -> str:
        """``│`` between columns -- always single, whatever the frame, as DN's were."""
        return glyphs_module.charset("single", self.glyphs)[5]

    #: What stands in the gutter of a tagged entry where File Manager Setup's
    #: *Tag sign* is empty: DN's default ``FMSetup.TagChar``, CP437's
    #: ``$FB``.  A plain ``+`` where the terminal draws ASCII only and the
    #: sign is not ASCII.
    TAG_CHAR = "√"
    TAG_CHAR_ASCII = "+"

    @property
    def tag_char(self) -> str:
        """The tag sign, or ``""`` with *Tag character* off: the colour alone."""
        setup = SETTINGS.file_manager
        if not setup.tag_character:
            return ""
        sign = setup.tag_sign[:1] or self.TAG_CHAR
        if self.glyphs <= glyphs_module.GLYPHS_ASCII and not sign.isascii():
            return self.TAG_CHAR_ASCII
        return sign

    #: The type mark of a bookmarked directory, in place of ``/``: CP437's
    #: ``$04``, a character DN could have drawn.  The ASCII tier keeps ``/``.
    BOOKMARK_MARK = "♦"

    #: What stands in the gutter of an entry Ctrl+C or Ctrl+X has clipped, a
    #: tag's sign winning over it: ``(copy, cut)`` per glyph tier.
    CLIP_MARKS = {
        glyphs_module.GLYPHS_ASCII: ("c", "x"),
        glyphs_module.GLYPHS_UNICODE: ("❐", "✂"),
        glyphs_module.GLYPHS_NERD: ("\U000f018f", "\U000f0190"),  # md-content_copy, md-content_cut
    }

    def clip_mark(self, move: bool) -> str:
        return self.CLIP_MARKS.get(self.glyphs, self.CLIP_MARKS[glyphs_module.GLYPHS_UNICODE])[move]

    def is_bookmarked(self, item: DirEntry) -> bool:
        """Whether *item* is a directory on the Alt+F1/Alt+F2 list."""
        if not item.is_dir or item.name == "..":
            return False
        return str(self.entry_location(item)) in bookmarked_paths()

    @property
    def ellipsis(self) -> str:
        """What marks a name or path cut short: ``…``, or ``...`` in ASCII."""
        return glyphs_module.ellipsis(self.glyphs)

    def shown_name(self, item: DirEntry) -> str:
        """*item*'s name as the panel shows it: a direction override, an
        isolate or a control in it as a visible ``⁇`` (``?`` in ASCII) that
        reorders nothing, so ``photo`` + U+202E + ``gpj.exe`` cannot pass for
        a picture.  A departure: DOS names had no such characters."""
        return reveal(item.name, glyphs_module.hidden_mark(self.glyphs))

    def _cut_title(self, text: str, room: int) -> str:
        """The title's path in *room* characters, cut in its middle: the drive
        part kept, then the ellipsis, then as much of the end as fits.

        DN's ``TTopView.Draw`` wrote ``C:\\...\\tail``, deleting after the
        first colon and the character beyond it.  The drive part here is the
        path up to its first ``/`` (:meth:`title_part_at`'s): a local path's
        root, or a drive's ``ZIP:a.zip:/``.  Where even that would not fit,
        the start is cut as :meth:`_cut_start` cuts it."""
        if len(text) <= room:
            return text
        slash = text.find("/")
        marker = self.ellipsis
        head = text[:slash + 1] if slash >= 0 else ""
        tail = room - len(head) - len(marker)
        if not head or tail < 1:
            return self._cut_start(text, room)
        return head + marker + text[-tail:]

    def _cut_start(self, text: str, room: int) -> str:
        """*text* in *room* characters, its start cut and marked if it must be."""
        if len(text) <= room:
            return text
        marker = self.ellipsis
        if room > len(marker):
            return marker + text[-(room - len(marker)):]
        return text[-room:] if room > 0 else ""

    def _draw_name(self, surface: Surface, x: int, y: int, width: int,
                   item: DirEntry, style: Style, offset: int = 0, selected: bool = False) -> None:
        """The tag, the icon or the type mark, the name, and in a work tree
        its git letter, in *width* cells.

        A tag takes the gutter over whichever of the other two it would hold:
        the colour says *tagged* too, but not on a monochrome terminal.  The
        letter stands a cell before the end, in its own colour (``Panel::git``) except
        under the cursor bar, whose colours keep it readable.
        """
        gutter = min(self.gutter, width)
        if gutter:
            sign = style
            if self.is_marked(item) and self.tag_char:
                mark = self.tag_char
                # The sign in the type's colour over the row's, as DN's
                # ``CC and $0F`` was -- unless that would hide it.
                fg = self.part_style("row", classes=self.type_classes(item)).fg
                if fg != style.bg:
                    sign = style.derive(fg=fg)
            elif CLIP and CLIP.holds(self.entry_location(item)):
                mark = self.clip_mark(CLIP.move)
            elif self.show_icons:
                mark = icon_glyphs.icon_for(item.name, item.is_dir, item.type_mark,
                                            self.is_bookmarked(item))
            elif self.glyphs > glyphs_module.GLYPHS_ASCII and self.is_bookmarked(item):
                mark = self.BOOKMARK_MARK
            else:
                mark = item.type_mark
            surface.draw_text(x, y, mark, sign, gutter)
        git = self.git_cells if width > gutter + self.git_cells else 0
        if git:
            mark = self.git_mark(item)
            letter = style if selected or mark == " " else self.part_style(
                "git", classes=(gitstatus.CLASSES.get(mark, "modified"),))
            surface.draw_text(x + width - 2, y, mark, letter, 1)
        if width > gutter + git:
            room = width - gutter - git
            name = window_text(reveal(item.name, REVEALED), offset, room, self.ellipsis)
            # The mark reversed out of the row, whatever the theme: a warning
            # needs no colour of its own to be seen, monochrome included.
            mark = glyphs_module.hidden_mark(self.glyphs)
            runs = reveal_runs(name, style, mark, style.derive(reverse=not style.reverse))
            surface.draw_runs(x + gutter, y, runs, room)

    def render_row(self, surface: Surface, y: int, index: int, item: DirEntry) -> None:
        style = self.row_style(index, item)
        if self.view_mode == "detailed":
            selected = self.row_selected(index)
            for key, x, width in self.detail_columns:
                if key == "name":
                    self._draw_name(surface, x, y, width, item, style, self.name_offset, selected)
                    continue
                if selected:
                    # The cursor bar covers the dividers; draw them back in it.
                    surface.draw_text(x - 1, y, self.divider_glyph, style, 1)
                text = getattr(item, self.DETAIL_COLUMNS[key][2])
                if key == "links":
                    text = text.rjust(width)  # a count, right-aligned as ``ls -l`` has it
                surface.draw_text(x, y, fit_text(text, width, self.ellipsis), style, width)
            return
        # Still an explicit limit: the name stops where the size column
        # begins, which is nearer than the edge the surface would clip at.
        self._draw_name(surface, 1, y, max(1, self.name_width), item, style, self.name_offset,
                        self.row_selected(index))
        surface.draw_text(self.width - 9, y, item.display_size, style, 8)

    def render(self, surface: Surface) -> None:
        super().render(surface)
        self.render_info(surface)

    def render_items(self, surface: Surface) -> None:
        if self.scanning:
            surface.draw_text(self.inset + 1, self.inset + self.header, tr("Reading directory..."),
                              self.style, max(0, self.width - 4))
            return
        if self.view_mode != "list":
            super().render_items(surface)
            return
        top = self.inset + self.header
        right = self.inset + self.inner_width
        items = self.items
        for first, x, width in self.list_columns:
            # The last column may run past the edge: end its names at the edge,
            # so the marker is shown rather than clipped.
            width = min(width, right - x)
            for row in range(self.rows):
                index = first + row
                if index >= len(items):
                    break
                item = items[index]
                style = self.row_style(index, item)
                selected = self.row_selected(index)
                if selected:
                    surface.fill(x, top + row, width, 1, " ", style)
                self._draw_name(surface, x, top + row, width, item, style, selected=selected)

    @staticmethod
    def heading(key: str) -> str:
        """The column *key*'s heading in the current language: ``name`` or
        one of :data:`DETAIL_COLUMNS`, whose headings are these in English."""
        return {
            "name": tr("Name"),
            "size": tr("Size"),
            "packed": tr("Packed"),
            "ratio": tr("%"),
            "attributes": tr("Attr"),
            "links": tr("Links"),
            "owner": tr("Owner"),
            "date": tr("Date"),
        }[key]

    def _column_spans(self) -> list[tuple[str, int, int]]:
        """``(heading, x, width)`` for the columns of the current mode."""
        if self.view_mode == "detailed":
            return [(self.heading(key) + self.sort_arrow(key), x, width) for key, x, width in self.detail_columns]
        if self.view_mode == "list":
            columns = self.list_columns
            name = self.heading("name") + self.sort_arrow("name")
            if not columns:
                return [(name, self.inset, self.inner_width)]
            return [(name, x, width) for _, x, width in columns]
        return []

    def render_header(self, surface: Surface) -> None:
        """The column titles, and the dividers from them down to the last row.

        Drawn before the rows, so the cursor bar covers a divider it crosses
        -- DN's did.  Nothing in the simple mode, and nothing over an error;
        the dividers alone with *Column titles* off.
        A divider meets the frame in a tee at each end, ``┬``/``┴`` or
        ``╤``/``╧`` as the frame is single or double, except where the title
        or the footer already stands on that cell.
        """
        if self.view_mode == "simple" or self.error is not None:
            return
        top = self.inset
        bottom = top + self.header + self.rows
        right = self.inset + self.inner_width
        glyph = self.divider_glyph
        heading = self.part_style("heading")
        divider = self.part_style("divider")
        horizontal = self.box_charset()[4]
        top_tee, bottom_tee = self.box_joins()[2:4]
        spans = self._column_spans()
        for index, (text, x, width) in enumerate(spans):
            shown = min(width, right - x)
            if shown <= 0:
                break
            if self.header:
                text = text[:shown]
                surface.draw_text(x + (shown - display_width(text)) // 2, top, text, heading, shown)
            # Dividers go between columns: none after the last one.
            edge = x + width
            if index < len(spans) - 1 and edge < right:
                for y in range(top, bottom):
                    surface.draw_text(edge, y, glyph, divider, 1)
                if self.framed:
                    # The info lines stand between the column and the bottom
                    # frame: the divider over them takes the tee, if any.
                    ends = ((0, top_tee),) if self.info_height else ((0, top_tee), (self.height - 1, bottom_tee))
                    for y, tee in ends:
                        char, style = surface.get(edge, y)
                        if char == horizontal:
                            surface.set_cell(edge, y, tee, style)
