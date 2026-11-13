"""The info lines under the list: DN's TInfoView.

A mixin of :class:`Panel` (``navkit.widget.Mixin``): methods only; its state,
keys and the listing are in ``panel.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from navkit.bidi import fit_cells
from navkit import glyphs as glyphs_module
from navkit.i18n import tr, tr_n
from navkit.screen import Surface

from navigator.lib.config import country
from navigator.lib.drives.listing import DirEntry
from navigator.settings import SETTINGS
from navigator.widgets.manager.panel.helpers import fit_text, text_width

if TYPE_CHECKING:
    from navigator.widgets.manager.panel.panel import Panel as _Base
else:
    from navkit.widget import Mixin as _Base


class InfoLines(_Base):
    """The info lines under the list: DN's TInfoView."""

    # -- the info lines: TInfoView ------------------------------------------------

    #: The parts drawn as they are, from the left: a name may hold a ``~``.
    PLAIN_INFO = frozenset({"current-file"})
    #: The parts drawn from the left, ``~`` around what is bright; the rest are centred.
    LEFT_INFO = frozenset({"packed"})

    @property
    def info_lines(self) -> tuple[tuple[str, str], ...]:
        """The lines under the listing, ``(text, part)``, ``~`` around what is
        bright: :attr:`_info_lines` with *Current file* laid out as it is
        read, since the rows' gutter it follows is not reactive
        (:attr:`Widget.glyphs`)."""
        return tuple(
            (self._current_file_text(self.selected) if text is None else text, part)
            for text, part in self._info_lines
        )

    def _selection_text(self, marked: list[DirEntry]) -> str:
        """*Selected files*: DN's ``dlBytesIn`` and ``dlSelectedFiles``, or
        its ``No files selected``.  Only the two numbers are bright, as DN's
        ``'~'+bytes+' ~bytes in ~'+N+'~ selected files'`` had them.  In an
        archive the packed bytes follow in brackets where they differ, those
        a member does not say left out."""
        if not marked:
            return tr("No files selected")
        size = sum(item.size for item in marked)
        packed = sum(item.packed for item in marked if item.packed is not None)
        if self.in_archive and packed != size:
            # DN's ``SelectedLen <> PackedLen``: ``1,234(567) bytes in 2``.
            total = tr_n("~{n:,}({packed:,})~ byte", "~{n:,}({packed:,})~ bytes", size, packed=packed)
        else:
            total = tr_n("~{n:,}~ byte", "~{n:,}~ bytes", size)
        return tr_n("{total} in ~{n}~ selected file", "{total} in ~{n}~ selected files", len(marked), total=total)

    def _current_file_text(self, entry: DirEntry | None) -> str:
        """*Current file*: the entry laid out as a detailed row is, in the
        simple and list modes -- :attr:`detail_columns`' columns at their
        places, a blank where each divider stands.  The detailed mode's rows
        show those already, so there it is the whole name
        (:meth:`_full_name_text`).

        DN's ``GetDown`` was name, size, date and time whatever the columns;
        following *Columns Setup* is Navigator's.  The size has every digit,
        right-aligned on the column's edge, and where that is wider than the
        column it takes the cells before it from the name.  The name starts
        where the rows' names do, the gutter left blank.
        """
        if entry is None:
            return ""
        if self.view_mode == "detailed":
            return self._full_name_text(entry)
        inset = self.inset
        pieces = []
        name_x = name_width = 0
        for key, x, width in self.detail_columns:
            x -= inset
            if key == "name":
                # Under the rows' names, past the gutter their marks take.
                gutter = min(self.gutter, max(0, width - 1))
                name_x, name_width = x + gutter, width - gutter
                continue
            if key == "size":
                text = entry.info_size
                if text_width(text) > width:
                    start = max(name_x + 2, x + width - text_width(text))
                    name_width = min(name_width, start - name_x - 1)
                    width = x + width - start
                    x = start
                text = fit_text(text, width, self.ellipsis)
                text = " " * (width - text_width(text)) + text
            else:
                text = fit_text(getattr(entry, self.DETAIL_COLUMNS[key][2]), width, self.ellipsis)
                if key == "links":
                    text = text.rjust(width)
            pieces.append((x, text))
        line = fit_text(self.shown_name(entry), max(1, name_width), self.ellipsis)
        line = " " * name_x + line
        for x, text in pieces:
            line += " " * max(0, x - text_width(line)) + text
        return line

    def _full_name_text(self, entry: DirEntry) -> str:
        """*Current file* in the detailed mode: the name whole, which the rows
        above already give the columns of (Navigator's).  It starts under the
        rows' names, past the gutter, and takes the panel's whole width --
        the gutter's cells too -- where it is longer than that leaves."""
        name = self.shown_name(entry)
        width = self.inner_width
        name_x = next((x - self.inset for key, x, _ in self.detail_columns if key == "name"), 0)
        start = max(0, name_x + min(self.gutter, max(0, width - 1)))
        if text_width(name) > width - start:
            start = 0
        return " " * start + fit_text(name, max(1, width - start), self.ellipsis)

    @property
    def in_archive(self) -> bool:
        """Listing an archive's members, not a *Find:* listing of them."""
        return self.location.outer is not None and self.found is None

    def _packed_line(self, entry: DirEntry | None) -> str:
        """The line under *Current file* in an archive, DN's ``dtArc`` one:
        ``~Packed:~ 1,234     ~Ratio:~ 56%``, the labels bright and from the
        left (FLPANEL.PAS:845-852).  Blank on a directory, ``..`` or a member
        that does not say, and kept, so the panel does not change height."""
        if entry is None or entry.is_dir or entry.packed is None:
            return ""
        packed = f"{entry.packed:,}".ljust(13)
        return tr("~Packed:~ {packed} ~Ratio:~ {ratio}").format(packed=packed, ratio=entry.display_ratio.strip())

    def _second_line(self, entry: DirEntry | None) -> str | None:
        """The line under *Current file*, or None where the listing needs
        none: the directory of a *Find:* listing's file (the whole width, where
        a column never had room for it), ``-> target`` for a symlink, blank for
        anything else while the line is kept."""
        if self.found is not None:
            if entry is None:
                return ""
            where = str(entry.directory) if entry.directory is not None else str(self.location)
            return self._cut_start(where, self.inner_width)
        if self._listing_facts.any_trashed:
            # The Trash (not DN's): where the entry came from, and when.
            if entry is None or entry.trashed is None:
                return ""
            origin, deleted = entry.trashed
            if deleted is None:
                template = tr("From {path}")
            else:
                template = tr("From {path}, deleted {when}").replace("{when}", country.stamp(deleted))
            # The path gives up its start, as a *Find:* listing's does; the date stays.
            room = self.inner_width - text_width(template.replace("{path}", ""))
            text = template.replace("{path}", self._cut_start(origin or tr("an unknown place"), max(1, room)))
            return fit_text(text, self.inner_width, self.ellipsis)
        if not SETTINGS.file_manager.link_line or not self._listing_facts.any_link:
            return None
        if entry is None or entry.link_target is None:
            return ""
        return fit_text(f"-> {entry.link_target}", self.inner_width, self.ellipsis)

    def info_line_at(self, x: int, y: int) -> int | None:
        """The index in :attr:`info_lines` of the line at *x*, *y*, or None --
        the divider above them is none of theirs."""
        height = self.info_height
        if not height or not self.inset <= x < self.inset + self.inner_width:
            return None
        first = self.height - self.inset - height + (1 if SETTINGS.file_manager.info_divider else 0)
        index = y - first
        return index if 0 <= index < len(self._info_lines) else None

    def _info_tooltip(self, index: int) -> str:
        """Info line *index* whole, where the line had to leave something out.

        *Current file*: the name, every byte, the date and a link's target,
        which its columns cut to their widths.  The line under it: the whole
        directory, origin or target, whose start it cut.  *Free space*: the
        bytes, which it rounds as ``df -h`` does.  Any other: its text, while
        it is wider than the panel.  A departure: DN's ``TInfoView`` had no
        tooltip.
        """
        lines = self._info_lines
        text, part = lines[index]
        entry = self.selected
        if part == "current-file":
            if text is None:
                return self._entry_details(entry)
            return self._second_whole(entry)
        if part == "free-space" and self.free_space:
            free, mount = self.free_space
            whole = tr_n("~{n:,}~ free byte on ~{mount}", "~{n:,}~ free bytes on ~{mount}", free, mount=mount)
            return whole.replace("~", "")
        plain = text.replace("~", "")
        return plain if text_width(plain) > self.inner_width else ""

    def _entry_details(self, entry: DirEntry | None) -> str:
        """*entry*'s name, size in bytes, date and link target, a line each."""
        if entry is None:
            return ""
        details = [self.shown_name(entry)]
        if not entry.is_dir or entry.counted:
            details.append(tr_n("{n:,} byte", "{n:,} bytes", entry.size))
        if entry.name != "..":
            details.append(entry.display_date)
        if entry.link_target is not None:
            details.append(f"-> {entry.link_target}")
        return "\n".join(details)

    def _second_whole(self, entry: DirEntry | None) -> str:
        """What :meth:`_second_line` says for *entry*, uncut."""
        if entry is None:
            return ""
        if self.found is not None:
            return str(entry.directory) if entry.directory is not None else str(self.location)
        if entry.trashed is not None:
            origin, deleted = entry.trashed
            where = origin or tr("an unknown place")
            if deleted is None:
                return tr("From {path}").replace("{path}", where)
            return tr("From {path}, deleted {when}").replace("{when}", country.stamp(deleted)).replace("{path}", where)
        if entry.link_target is not None:
            return f"-> {entry.link_target}"
        return ""

    def render_info(self, surface: Surface) -> None:
        """The divider and the info lines, centred, between the listing and the frame."""
        height = self.info_height
        if not height:
            return
        left, width = self.inset, self.inner_width
        y = self.height - self.inset - height
        if SETTINGS.file_manager.info_divider:
            # DN's ``─``, ``┴`` where a column divider comes down onto it.
            single = glyphs_module.charset("single", self.glyphs)[4]
            tee = glyphs_module.joins("single", self.glyphs)[3]
            divider = self.part_style("divider")
            surface.draw_text(left, y, single * width, divider, width)
            if self.view_mode != "simple":
                spans = self._column_spans()
                for index, (_, x, span) in enumerate(spans[:-1]):
                    if x + span < left + width:
                        surface.draw_text(x + span, y, tee, divider, 1)
            if self.framed:
                # Joined to the frame at both ends, ``├``/``┤`` (``╟``/``╢``
                # on a double one), in the frame's colour.
                vertical = self.box_charset()[5]
                left_tee, right_tee = self.box_joins()[:2]
                for edge, tee in ((left - 1, left_tee), (left + width, right_tee)):
                    char, style = surface.get(edge, y)
                    if char == vertical:
                        surface.set_cell(edge, y, tee, style)
            y += 1
        for text, part in self.info_lines:
            surface.fill(left, y, width, 1, " ", self.part_style(part))
            if part in self.PLAIN_INFO:
                surface.draw_text(left, y, text, self.part_style(part), width)
                y += 1
                continue
            plain = text.replace("~", "")
            x = left if part in self.LEFT_INFO else left + max(0, (width - text_width(plain)) // 2)
            bright = False
            for piece in text.split("~"):
                room = left + width - x
                if piece and room > 0:
                    style = self.part_style(f"{part}-numbers" if bright else part)
                    piece = fit_cells(piece, room)
                    surface.draw_text(x, y, piece, style, room)
                    x += text_width(piece)
                bright = not bright
            y += 1
