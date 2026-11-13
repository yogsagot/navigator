"""Show modes, sorting, the column titles and their tooltips, hidden files, and the settings
remembered per directory.

A mixin of :class:`Panel` (``navkit.widget.Mixin``): methods only; its state,
keys and the listing are in ``panel.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from navkit.commands import key_for, key_label
from navkit.i18n import tr, tr_n
from navkit.reactive import untracked
from navkit.tooltip import lines as tooltip_lines, with_keys

from navigator.lib.appearance import filetypes
from navigator.lib.config import directory_settings
from navigator.lib.drives import Location
from navigator.settings import SETTINGS
from navigator.widgets.manager.commands import AdvancedFilter
from navigator.widgets.manager.panel.helpers import SORT_MODES, direction_arrow, text_width

if TYPE_CHECKING:
    from navigator.widgets.manager.panel.panel import Panel as _Base
else:
    from navkit.widget import Mixin as _Base


class Modes(_Base):
    """Show modes, sorting, the column titles and their tooltips, hidden files, and the settings"""

    # -- show modes ----------------------------------------------------------

    def cycle_view_mode(self) -> None:
        """Ctrl+Y: the next of :data:`VIEW_MODES`, the last wrapping to the first.

        The heading row comes and goes with it: the simple mode is the panel
        as it always was, and the other two title their columns.
        """
        modes = self.VIEW_MODES
        mode = modes[(modes.index(self.view_mode) + 1) % len(modes)]
        self.view_mode = mode
        self._follow_column_titles()
        self.name_scroll = 0

    def _follow_column_titles(self) -> None:
        """The heading row: the detailed and list modes', under File Manager
        Setup's *Column titles*; also an effect, so unticking it takes the
        row away at once.  The dividers stay either way."""
        titled = self.view_mode != "simple" and SETTINGS.file_manager.column_titles
        self.header = 1 if titled else 0

    def shows(self, option: str) -> bool:
        """Whether *Display* box *option* is on for this panel: its own, once
        Alt+S has set them, else the *New Manager defaults*' -- read live, a
        departure: DN copied the defaults into each manager it made, and only
        *Panel Options* changed one."""
        display = self.display
        if display is None:
            return bool(getattr(SETTINGS.panel_defaults, option))
        return option in display

    def set_options(self, sort: str, display: frozenset[str], mask: str, reverse: bool = False) -> None:
        """Alt+S's answer (DN's ``Setup``): this panel's order and its
        direction, *Display* boxes and file mask, and one re-read keeping the
        cursor on its entry."""
        if sort not in SORT_MODES:
            raise ValueError(f"unknown sort mode {sort!r}")
        entry = self.selected
        if entry is not None:
            self._keep = (self.location, entry.key, self.cursor, self.scroll)
        self.sort_reverse = reverse and sort != "unsorted"
        self.sort_mode = sort
        self.display = frozenset(display)
        self.file_mask = mask.strip() or filetypes.ALL_FILES

    def set_file_mask(self, mask: str) -> None:
        """A new file mask, and one re-read keeping the cursor on its entry."""
        mask = mask.strip() or filetypes.ALL_FILES
        if mask == self.file_mask:
            return
        entry = self.selected
        if entry is not None:
            self._keep = (self.location, entry.key, self.cursor, self.scroll)
        self.file_mask = mask

    def sort_by(self, mode: str, reverse: bool = False) -> None:
        """Order the listing by *mode*: what Alt+B's choice does (``CM_SortBy``),
        *reverse* turning it round (a column title's second click).

        A re-read, as DN's ``RereadDir`` was, keeping the cursor on its entry;
        the order it already has changes nothing.
        """
        if mode not in SORT_MODES:
            raise ValueError(f"unknown sort mode {mode!r}")
        if mode == "unsorted":
            reverse = False
        if (mode, reverse) == (self.sort_mode, self.sort_reverse):
            return
        entry = self.selected
        if entry is not None:
            self._keep = (self.location, entry.key, self.cursor, self.scroll)
        self.sort_mode = mode
        self.sort_reverse = reverse

    #: The sort modes a click on a column's title steps through, each up and
    #: then reversed; the other columns sort nothing.  The name's title takes
    #: the extension too, there being no column of its own for it.
    COLUMN_SORTS = {"name": ("name", "extension"), "size": ("size",), "attributes": ("attributes",), "owner": ("owner",), "date": ("time",)}

    def heading_at(self, x: int, y: int) -> str | None:
        """The key of the column whose title is at *x*, *y*, or None."""
        if not self.header or self.view_mode == "simple" or self.error is not None or y != self.inset:
            return None
        if self.view_mode == "list":
            return "name" if self.inset <= x < self.inset + self.inner_width else None
        for key, left, width in self.detail_columns:
            if left <= x < left + width:
                return key
        return None

    def sort_by_column(self, key: str) -> bool:
        """A click on column *key*'s title: the next of its orders -- each of
        :data:`COLUMN_SORTS`' modes, then that reversed, wrapping -- or its
        first when sorted by another column.  False for a column that sorts
        nothing.  Name's: name, name reversed, extension, extension reversed."""
        step = self.next_column_sort(key)
        if step is None:
            return False
        mode, reverse = step
        self.sort_by(mode, reverse=reverse)
        return True

    def next_column_sort(self, key: str) -> tuple[str, bool] | None:
        """``(mode, reverse)`` a click on column *key*'s title sorts by next,
        or None for a column that sorts nothing."""
        modes = self.COLUMN_SORTS.get(key)
        if modes is None:
            return None
        steps = [(mode, reverse) for mode in modes for reverse in (False, True)]
        here = (self.sort_mode, self.sort_reverse)
        return steps[(steps.index(here) + 1) % len(steps)] if here in steps else steps[0]

    def tooltip_at(self, x: int, y: int) -> str:
        """Over a column's title: what the column shows, and the order a click
        sorts by -- the titles are short (``Attr``, ``%``), and a click on one
        does something the title does not say.  A departure: DN's titles had
        no tooltip, and sorted nothing when clicked."""
        if self.framed and y == 0:
            text = self.title_text()
            start = self.label_x(text)
            if self.error is None and start <= x < start + len(text):
                return self._title_tooltip()
            return super().tooltip_at(x, y)
        info = self.info_line_at(x, y)
        if info is not None:
            return self._info_tooltip(info)
        index = self.index_at(x, y) if self.inset <= x < self.inset + self.inner_width else None
        if index is not None and self.heading_at(x, y) is None:
            return self._row_tooltip_at(index, x)
        key = self.heading_at(x, y)
        if key is None:
            return super().tooltip_at(x, y)
        text = self.column_description(key)
        step = self.next_column_sort(key)
        if step is None:
            return text
        from navigator.widgets.manager.manager.helpers import sort_captions

        mode, reverse = step
        caption = dict(zip(SORT_MODES, sort_captions()))[mode].replace("~", "")
        order = f"{caption} {self.direction_arrow(mode, reverse)}".rstrip()
        return f"{text}\n{tr('A click sorts by {order}').format(order=order)}"

    def title_part_at(self, x: int, y: int) -> str | None:
        """What a press at *x*, *y* on the title means (``TTopView.HandleEvent``):
        ``"drive"`` on its drive part, ``"directory"`` on the rest, None off it.

        DN's drive part was ``C:``, up to the first colon.  A POSIX path has
        none: the drive part is the path up to its first ``/`` -- a local
        path's root, ``~/``, or a drive's ``ZIP:a.zip:/`` as ``get_dir`` writes
        it, as DN's ``C:\\`` was; a title cut in its middle keeps it
        (:meth:`_cut_title`).  One too narrow for that, cut at its start, or a
        *Find:* listing's, has only its first cell, as DN's ``I := 0`` left it."""
        if not self.framed or y != 0 or self.error is not None or self.quick_search is not None:
            return None
        text = self.title_text()
        start = self.label_x(text)
        if not start <= x < start + len(text):
            return None
        mark = self.remembered_mark()
        first = start + 1 + (len(mark) + 1 if mark else 0)
        if x < first:
            return "directory"
        whole = self.found.title if self.found is not None else self.title_location
        shown = text[first - start:]
        cut = not whole or not shown.startswith(whole[:1]) or shown.startswith(("…", "..."))
        slash = whole.find("/")
        end = first if self.found is not None or cut or slash < 0 else first + slash
        return "drive" if x <= end else "directory"

    def _title_tooltip(self) -> str:
        """What the title leaves out: the whole path where its start was cut,
        the file mask in words, and the git branch with its counts spelled
        out -- even where a narrow title dropped it.  Nothing for a title
        that says it all.  A departure: DN's title had no tooltip."""
        lines = []
        whole = self.found.title if self.found is not None else self.title_location
        if whole not in self.title_text():
            lines.append(whole)
        if self.read_only and self.found is None:
            lines.append(tr("A read-only file system: nothing here can be changed"))
        if self.remembered and self.found is None:
            if self.remembers_here:
                lines.append(tr("This directory keeps its own sort order, view and file mask"))
            else:
                lines.append(tr("Shown with the settings remembered for {path} and below").format(
                    path=self.remembered))
        mask = self.file_mask.strip()
        if mask not in ("", filetypes.ALL_FILES):
            shown = tr("Only files matching {mask} are shown").format(mask=mask)
            app = self.application
            key = key_for(app, AdvancedFilter, self) if app is not None else None
            lines.append(with_keys(shown, key_label(key) if key else ""))
        git = self.git
        if git is not None and git.branch:
            if git.detached:
                lines.append(tr("Git work tree, HEAD detached at {commit}").format(commit=git.branch))
            else:
                lines.append(tr("Git work tree, on {branch}").format(branch=git.branch))
            if git.ahead:
                lines.append(tr_n("{n} commit ahead of its upstream", "{n} commits ahead of its upstream", git.ahead))
            if git.behind:
                lines.append(tr_n("{n} commit behind its upstream", "{n} commits behind its upstream", git.behind))
        return tooltip_lines(*lines)

    def _row_tooltip_at(self, index: int, x: int) -> str:
        """Row *index* at column *x*: what the row left out there.

        Over the name, the whole name while it is cut or scrolled (Left and
        Right), and a link's target, which only the info line's second line
        shows otherwise.  Over the detailed mode's owner and path, their
        whole text while cut.  Elsewhere nothing: a size, a date or the
        attributes are never cut.  A departure: DN's rows had no tooltip.
        """
        item = self.items[index]
        if item.name == "..":
            return ""
        if self.view_mode == "detailed":
            for key, left, width in self.detail_columns:
                if not left <= x < left + width or key == "name":
                    continue
                if key == "owner":
                    whole = getattr(item, self.DETAIL_COLUMNS[key][2])
                    return whole if text_width(whole) > width else ""
                return ""
        lines = []
        if self.name_offset or text_width(self.shown_name(item)) > self._name_room(index):
            lines.append(self.shown_name(item))
        if item.link_target is not None:
            lines.append(f"-> {item.link_target}")
        return "\n".join(lines)

    def _name_room(self, index: int) -> int:
        """The cells row *index*'s name is drawn in: :meth:`_draw_name`'s
        *width* for its mode, less the gutter and the git letter."""
        if self.view_mode == "detailed":
            width = next((w for key, _x, w in self.detail_columns if key == "name"), 0)
        elif self.view_mode == "list":
            right = self.inset + self.inner_width
            width = next((min(w, right - left) for first, left, w in self.list_columns
                          if first <= index < first + self.rows), 0)
        else:
            width = max(1, self.name_width)
        gutter = min(self.gutter, width)
        git = self.git_cells if width > gutter + self.git_cells else 0
        return max(0, width - gutter - git)

    @staticmethod
    def column_description(key: str) -> str:
        """What column *key* shows, in a sentence: its title's longer self."""
        return {
            "name": tr("The file's name"),
            "size": tr("The file's size"),
            "packed": tr("The size packed in the archive"),
            "ratio": tr("The packed size as a percentage of the original"),
            "attributes": tr("Permissions: the owner's, the group's and others'"),
            "links": tr("How many names the file has: its hard links"),
            "owner": tr("The owner and group"),
            "date": tr("When the file was last modified"),
        }[key]

    def sort_arrow(self, key: str) -> str:
        """What follows column *key*'s title: ``↑`` sorted by it ascending,
        ``↓`` descending (``^``/``v`` in ASCII), else nothing; ``.`` before
        the arrow on the name's when it is the extension that sorts."""
        mode = self.sort_mode
        if mode not in self.COLUMN_SORTS.get(key, ()):
            return ""
        return ("." if mode == "extension" else "") + self.direction_arrow(mode, self.sort_reverse)

    def direction_arrow(self, mode: str, reverse: bool) -> str:
        """:func:`direction_arrow` at this panel's glyph tier."""
        return direction_arrow(mode, reverse, self.glyphs)

    def toggle_hidden(self) -> None:
        """Ctrl+H: hide the dot-files, or show them again.

        A re-read like :meth:`reload`'s, so the cursor stays on its entry, or
        where it was if that entry is the one just hidden.  A tag on a name
        that goes is dropped with it, so nothing unseen stays selected.
        """
        entry = self.selected
        if entry is not None:
            self._keep = (self.location, entry.key, self.cursor, self.scroll)
        self.show_hidden = not self.show_hidden

    # -- settings remembered per directory ------------------------------------
    #
    # A departure: DN's sort, mask and display went wherever the panel went
    # (navigator.lib.config.directory_settings has the rules).

    def _arriving(self, location: Location) -> None:
        """:attr:`location` is about to be *location*: the cursor left on in
        the directory going is kept, the one left on in *location* is where
        the read will put it (unless the move says where already), and its
        record's settings -- or the panel's own -- are what it is read with."""
        with untracked():
            old = self.location
            if location == old:
                return
            remembered = bool(self.remembered)
            restore = SETTINGS.file_manager.restore_cursor
            entry = self.selected
            if ((restore or remembered) and entry is not None and self.found is None
                    and self._listed == old and not self.scanning):
                directory_settings.keep_cursor(old, entry.name)
            if remembered and self.found is None:
                # What it was left showing is its record's, a change made in
                # the same batch as the move included -- which the effect
                # keeping them sees only as the move.
                shown = directory_settings.values(self)
                if self._kept_dir is None or self._kept_dir[2] != shown:
                    directory_settings.remember(self.remembered, shown)
            self.settle_directory(location)
            if self._return_to is None and (restore or self.remembered):
                self._return_to = directory_settings.cursor_of(location)

    def settle_directory(self, location: Location | None = None) -> None:
        """The settings *location* (else the place shown) is to be shown
        with: its record's, the panel's own put aside first; or, with none,
        the panel's own back."""
        with untracked():
            where = self.location if location is None else location
            found = directory_settings.find(where)
            if found is None:
                self.drop_directory_settings()
                self._arrival = directory_settings.values(self)
                return
            key, kept = found
            if self._base is None:
                self._base = directory_settings.values(self)
            directory_settings.assign(self, kept)
            self.remembered = key

    def drop_directory_settings(self) -> None:
        """The panel's own settings back, a record's no longer shown."""
        with untracked():
            if self._base is not None:
                base, self._base = self._base, None
                directory_settings.assign(self, base)
            self.remembered = ""

    def own_settings(self) -> dict[str, Any]:
        """The panel's own settings (``directory_settings.KEPT``): those held
        aside while a remembered directory's are shown, else those shown --
        what the side and a saved desktop keep.  Tracked, so an effect asking
        follows both what is shown and the record coming and going."""
        shown = directory_settings.values(self)
        _ = self.remembered
        return dict(self._base) if self._base is not None else shown

    @property
    def remembers_here(self) -> bool:
        """Whether the directory shown has a record of its own (Panel >
        *Remember for this directory* is ticked) -- not one above's."""
        return bool(self.remembered) and self.remembered == directory_settings.key_of(self.location)

    def remember_here(self, subdirs: bool) -> None:
        """Panel > *Remember for this directory*: what the panel shows kept
        as the directory's own record, *subdirs* saying whether the
        directories below take it too.  The panel's own become what it came
        to the directory with: a sort changed here and then remembered is
        this directory's, and does not follow the panel out of it."""
        with untracked():
            key = directory_settings.key_of(self.location)
            shown = directory_settings.values(self)
            if self._base is None:
                self._base = dict(self._arrival) if self._arrival is not None else shown
            directory_settings.remember(key, shown, subdirs)
            self.remembered = key
            # What a change after this one is told from, made in the same
            # batch or not.
            self._kept_dir = (self.location, key, shown)

    def forget_here(self) -> None:
        """The directory's own record forgotten: it is shown with the one
        above it marked for those below, or else the panel's own."""
        with untracked():
            directory_settings.forget(directory_settings.key_of(self.location))
            entry = self.selected
            if entry is not None:
                self._keep = (self.location, entry.key, self.cursor, self.scroll)
            self.settle_directory()

    def _keep_directory_settings(self) -> None:
        """A setting changed in a remembered directory -- by any key, menu,
        dialog or column title -- is written to its record; under *Every
        directory*, one changed anywhere makes the directory a record.  A
        change of place or of record only notes what is shown."""
        kept = directory_settings.values(self)
        where = self.location
        key = self.remembered
        found = self.found
        last, self._kept_dir = self._kept_dir, (where, key, kept)
        if last is None or last[0] != where or last[1] != key or kept == last[2] or found is not None:
            return
        with untracked():
            if key:
                directory_settings.remember(key, kept)
            elif directory_settings.mode() == "all" and directory_settings.rememberable(where):
                # What was shown until now was the panel's own.
                self._base = last[2]
                key = directory_settings.key_of(where)
                directory_settings.remember(key, kept, subdirs=False)
                self.remembered = key

    def toggle_info(self) -> None:
        """Alt+I: hide the footer under the listing, or show it again; the
        listing takes the rows it gives up."""
        self.show_info = not self.show_info
