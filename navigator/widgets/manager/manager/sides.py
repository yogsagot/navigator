"""The two sides: Miller columns, switching, hiding and swapping a side, and the divider
between them with its mouse handling.

A mixin of :class:`Manager` (``navkit.widget.Mixin``): methods only; its state,
keys and ``checks`` are in ``manager.py``.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any

from navkit.commands import key_for, key_label
from navkit.events import DoubleClickEvent, MouseClickEvent
from navkit.i18n import tr
from navkit.reactive import untracked

from navigator.widgets.manager.commands import MoveSeparator
from navigator.commands import ToggleConsole
from navigator.lib.drives import Location
from navigator.lib.cut import cut_path
from navigator.settings import SETTINGS
from navigator.widgets.manager.manager.helpers import _SINGLE_VERTICAL, _hint

if TYPE_CHECKING:
    from navigator.widgets.manager.manager import Manager as _Base
else:
    from navkit.widget import Mixin as _Base


class Sides(_Base):
    """The two sides: Miller columns, switching, hiding and swapping a side, and the divider"""

    def _remember_panel(self) -> None:
        if self.right.focused:
            self._last_panel = self.right
        elif self.left.focused:
            self._last_panel = self.left

    def toggle_miller(self, location: Location | None = None, cursor: str | None = None) -> None:
        """Alt+F12: Miller columns in the two panels' place, or the panels back.

        The columns open on the active panel's directory, the cursor on its
        entry (or on *location* and *cursor*, for a restored desktop); a side
        hidden or stood in for is shown first.  Back, the side that was active
        goes to the directory browsed, the cursor on its entry, and the other
        is as it was left.
        """
        if self.miller_mode:
            self._leave_miller()
            return
        panel = self.active_panel
        if location is None:
            if panel.found is not None:
                return
            entry = panel.selected
            location = panel.location
            cursor = entry.name if entry is not None and entry.name != ".." else None
        if self.hidden_side is not None:
            self.show_side(self.hidden_side)
        if self.replacement is not None:
            self.switch_view(self.replacement)
        self._miller_side = "right" if panel is self.right else "left"
        self.left.visible = self.right.visible = False
        self.miller.visible = True
        self.miller.open_at(location, cursor, like=panel)
        self.panels.invalidate()

    def _leave_miller(self) -> None:
        current = self.miller.current
        location, entry = current.location, current.selected
        side = self.right if self._miller_side == "right" else self.left
        self.left.visible = self.right.visible = True
        side.focus()
        self.miller.close()
        self.miller.visible = False
        name = entry.name if entry is not None else None
        if side.location != location or side.found is not None:
            side.leave_found()
            side._return_to = name
            side.location = location
        elif name is not None:
            side.reload(key=name)
        self.panels.invalidate()

    def list_name(self) -> str:
        """What the window list shows for this window: DN's ``cmGetName``
        (DBLWND.PAS:670-671), answered by the double window itself --
        ``File Manager``, the left panel's directory and the right's, each
        ``Cut`` to 20, whichever has the keyboard or a view stands in."""
        left, right = (cut_path(str(panel.location), 20) for panel in (self.left, self.right))
        return tr("File Manager {left},{right}").format(left=left, right=right)

    def short_name(self) -> str:
        """The window strip's chip: the last part of the active panel's
        directory.  A window in the background has lost the keyboard, so
        which panel was active is read off what it will get back, not off
        the focus."""
        app = self.application
        saved = self._saved_focus
        panel = self.active_panel
        if (
            self.replaced is None
            and not (app is not None and self._holds(app.focused))
            and saved in (self.left, self.right)
        ):
            panel = saved
        name = str(panel.location)
        return PurePosixPath(name).name or name

    def switch_panel(self) -> None:
        """Move the keyboard to the other panel, or between panel and tree."""
        replacement = self.replacement
        if replacement is not None:
            if replacement.focus_within:
                self.active_panel.focus()
            else:
                self._focus_replacement()
            return
        self.passive_panel.focus()

    # -- hiding a side ---------------------------------------------------------

    def side_view(self, side: str) -> Any:
        """What stands on *side*: its panel, or the tree or quick view in its place.

        DOS Navigator's ``LeftView``/``RightView``.
        """
        panel = self.left if side == "left" else self.right
        return self.replacement if self.replaced is panel else panel

    async def toggle_side(self, side: str) -> None:
        """Ctrl+F1 / Ctrl+F2: ``cmHideLeft`` / ``cmHideRight``.

        A hidden side is shown again.  Hiding the one side still showing would
        leave nothing, so it shows the console instead, as DN's
        ``cmShowOutput`` did -- and the same key from there brings this side
        back alone (``Shell.on_hide_left``).
        """
        if self.hidden_side == side:
            self.show_side(side)
        elif self.hidden_side is not None:
            await self.emit(ToggleConsole())
        else:
            self.hide_side(side)

    def toggle_inactive_side(self) -> None:
        """Ctrl+P: ``cmSwitchOther``, the side without the keyboard hidden or shown.

        ``if LSelected then SwitchRight else SwitchLeft``: with one side
        hidden, the one showing is the selected one, so this shows the other.
        Unlike Ctrl+F1/Ctrl+F2 it never falls back to the console.
        """
        if self.side_view("right").focus_within:
            selected = "right"
        elif self.side_view("left").focus_within:
            selected = "left"
        else:
            selected = "left" if self.active_panel is self.left else "right"
        other = "right" if selected == "left" else "left"
        if self.hidden_side == other:
            self.show_side(other)
        elif self.hidden_side is None:
            self.hide_side(other)

    def swap_panels(self) -> None:
        """Ctrl+U: ``cmSwapPanels``, the two sides change places.

        Each panel goes over whole -- directory, cursor, tags, view mode,
        order -- and so does a tree or quick view standing in for one, beside
        the panel it stands in for.  The keyboard stays with the panel it was
        with, now on the other side, as DN's ``LeftView`` and ``RightView``
        changed places and the selected view stayed selected.  ``left`` and
        ``right`` are names for the sides, so they change places too.

        **A side hidden stays hidden, the visible panel going across.**  DN's
        ``HandleEvent`` read ``LVisible``/``RVisible`` once, at its top: the
        ``cmHideRight``/``cmHideLeft`` before the swap showed the hidden side,
        and the one after it, chosen by those first flags, found both showing
        and so hid the other side.  With the right side hidden, the left panel
        ends on the right, the window shrunk to it, and the left side hidden;
        Ctrl+U again puts everything back.
        """
        hidden = self.hidden_side
        if hidden is not None:
            self.show_side(hidden)
        left, right = self.left, self.right
        row = self.panels.children
        i, j = row.index(left), row.index(right)
        row[i], row[j] = right, left
        replacement = self.replacement
        if replacement is not None:
            row.remove(replacement)
            row.insert(row.index(self.replaced), replacement)
        left.on_execute_file, right.on_execute_file = right.on_execute_file, left.on_execute_file
        self.left, self.right = right, left
        # The row's order changed in place, which its layout does not
        # follow: placed again here, in this batch.  The divider stays
        # where it was, so the hint moves to the side now first.
        self.place_divider()
        self.panels.arrange()
        self.panels.invalidate()
        if hidden is not None:
            # DN's trailing ``cmHideLeft`` after a right side hidden, and
            # ``cmHideRight`` after a left: the side the other panel is now on.
            self.hide_side("left" if hidden == "right" else "right")

    # -- the divider -------------------------------------------------------
    #
    # DOS Navigator's ``TSeparator``: the two columns where the sides meet, the
    # left side's right frame edge and the right side's left one, dragged with
    # the mouse or moved a column by Alt+Left/Alt+Right.

    def _sides(self) -> list[Any]:
        """The views the row is showing, left to right."""
        return [child for child in self.panels.children if child.visible]

    def place_divider(self) -> None:
        """Give the row's first side the width :attr:`split` asks for.

        The run's effect, reading the split, the row's width and which views
        are showing, so a side hidden, shown or stood in for re-places it.  The
        width is the first side's ``basis`` with ``grow: 0``, and every other
        view says nothing; with one side showing, or no split, none says
        anything and the row shares itself out as it always did.
        """
        sides = self._sides()
        width = self.panels.width
        first = None
        if len(sides) == 2 and self.split is not None:
            first = self._clamp_divider(round(width * self.split), width)
        with untracked():
            for child in self.panels.children:
                if first is not None and child is sides[0]:
                    _hint(child, first, 0)
                else:
                    _hint(child, 0, 1)

    def _clamp_divider(self, column: int, width: int) -> int:
        return max(self.MIN_SIDE, min(column, width - self.MIN_SIDE))

    def move_divider_to(self, column: int) -> None:
        """The divider where the right side starts at *column* of the row."""
        width = self.panels.width
        if width < 2 * self.MIN_SIDE or len(self._sides()) != 2:
            return
        self.split = self._clamp_divider(column, width) / width

    def divider_hit(self, x: int, y: int) -> bool:
        """Whether *x*, *y* -- in the window's coordinates -- takes hold of the divider.

        The right side's left frame column always does.  The left side's
        right one does where its scroll bar is not, which is what a press
        there means otherwise.
        """
        sides = self._sides()
        if len(sides) != 2 or not 0 <= y < self.panels.height:
            return False
        first, second = sides
        if x == second.x:
            return True
        if x != second.x - 1:
            return False
        bar = getattr(first, "bar", None)
        return bar is None or not bar.visible or not bar.y <= y - first.y < bar.y + bar.height

    def tooltip_at(self, x: int, y: int) -> str:
        """Over the divider, how to move it -- a mouse affordance nothing else
        announces, its keys and the double click that evens it out; read off
        :meth:`divider_hit`, so it shows exactly where a press takes hold.  A
        departure: DN's ``TSeparator`` had no tooltip."""
        if not self.divider_hit(x, y):
            return super().tooltip_at(x, y)
        lines = [tr("Drag to resize the panels")]
        app = self.application
        if app is not None:
            keys = [key_for(app, MoveSeparator(step), self) for step in (-1, 1)]
            if all(keys):
                lines[0] += f" ({', '.join(key_label(key) for key in keys)})"
        lines.append(tr("Double-click to split them evenly"))
        return "\n".join(lines)

    async def dispatch_mouse(self, event: MouseClickEvent) -> bool:
        """The divider before anything else.

        Tried ahead of the window's chrome and the panels, as ``Window`` tries
        its chrome ahead of the children: a panel takes a press anywhere in its
        rectangle, its frame included.
        """
        local = event.translated(-self.x, -self.y)
        if (
            event.action == "press" and event.button == "left"
            and not isinstance(event, DoubleClickEvent)
            and self.divider_hit(local.x, local.y)
        ):
            desktop = self.desktop
            if desktop is not None and not self.active:
                desktop.activate(self)
            self._divider = local.x - self._sides()[1].x
            app = self.application
            if app is not None:
                app.capture_mouse(self)
            # Drawn single while it is held (``render_after``).
            self.invalidate()
            return True
        return await super().dispatch_mouse(event)

    def chrome_hit(self, x: int, y: int) -> str | None:
        """The window's chrome -- but not a panel's title on the top row:
        a press there is the panel's (``TTopView``: *Change drive* or
        *Change directory*), and the rest of the row still moves the window."""
        hit = super().chrome_hit(x, y)
        if hit == "move" and y == 0:
            for side in self._sides():
                part = getattr(side, "title_part_at", None)
                if part is not None and part(x - side.x - self.panels.x, y - side.y - self.panels.y) is not None:
                    return None
        return hit

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """A divider drag in progress, else the window's own."""
        if self._divider is None:
            return await super().on_mouse_click(event)
        if event.action == "release":
            self._divider = None
            self.invalidate()
        elif event.action == "move":
            self.move_divider_to(event.x - self._divider)
        return True

    async def on_double_click(self, event: DoubleClickEvent) -> bool:
        """A double click on the divider puts it back in the middle.

        Not DN's, which had no way back but dragging.  The second press has
        already taken hold of the divider (:meth:`dispatch_mouse`), so the
        capture brings the double click here; it lets go, and the even split
        returns.
        """
        if self._divider is None:
            return await super().on_double_click(event)
        self._divider = None
        app = self.application
        if app is not None and app.mouse_capture is self:
            app.release_mouse()
        self.split = None
        self.invalidate()
        return True

    def render_after(self, surface: Any) -> None:
        """While the divider is held, its two columns drawn with single lines.

        ``TSeparator.Draw``: the active window's ``║``/``╗``/``╝`` became
        ``│``/``┐``/``┘`` under ``sfDragging``.  The sides have painted their
        frames by now, so each double-line character on the two columns is
        swapped for its single one, which keeps a junction where a side's
        divider row meets its frame and leaves a scroll bar alone.
        """
        if self._divider is not None:
            sides = self._sides()
            if len(sides) == 2:
                for column in (sides[1].x - 1, sides[1].x):
                    for row in range(self.panels.height):
                        char, style = surface.get(column, row)
                        single = _SINGLE_VERTICAL.get(char)
                        if single is not None:
                            surface.set_cell(column, row, single, style)
        super().render_after(surface)

    def show_only(self, side: str) -> None:
        """*side* showing and the other hidden: DN's ``cmPostHideLeft``/``Right``.
        Nothing in Miller columns, which have no sides."""
        if self.miller_mode:
            return
        other = "right" if side == "left" else "left"
        if self.hidden_side == side:
            self.show_side(side)
        if self.hidden_side is None:
            self.hide_side(other)

    def apply_left_panel(self) -> None:
        """*New Manager defaults*' *Left panel in a new Manager*, once the
        window is open: ``TDoubleWindow.Init`` sent ``cmDiskInfo``,
        ``cmDirTree`` or ``cmHideLeft`` with the right panel selected, so the
        information panel or the tree stood in the left one's place, or the
        left side was hidden.  *Files* leaves both panels."""
        choice = SETTINGS.panel_defaults.left_panel
        if choice == "files":
            return
        self.right.focus()
        if choice == "info":
            self.switch_view(self.info)
        elif choice == "tree":
            self.switch_view(self.tree)
        elif choice == "absent":
            self.hide_side("left")

    def hide_side(self, side: str) -> None:
        """Hide *side*, and shrink the window to what is left: ``SwitchLeft``.

        **The window shrinks; the other side does not stretch.**  The window
        takes the rectangle the other side had, so the console shows through
        where the hidden side stood, as DN's user screen did.  The other side
        takes the keyboard if the hidden one had it.
        """
        other = "right" if side == "left" else "left"
        hidden, kept = self.side_view(side), self.side_view(other)
        self._collapse = {
            "before": (self.x, self.y, self.width, self.height),
            "zoomed": self.zoomed,
            "hidden_width": hidden.width,
            "kept_width": kept.width,
        }
        if hidden.focus_within:
            if kept is self.replacement:
                self._focus_replacement()
            else:
                kept.focus()
        x, width = self.x + kept.x, kept.width
        self.zoomed = False
        self.x, self.width = x, width
        hidden.visible = False
        self.hidden_side = side
        self._collapse["after"] = (self.x, self.y, self.width, self.height)
        self.panels.invalidate()

    def show_side(self, side: str) -> None:
        """Show the hidden *side* again, and grow the window back to hold it.

        Untouched since it was hidden, the window gets back exactly the
        rectangle it had, zoomed if it was.  Moved or resized in between, it
        grows by the share the hidden side had, as DN's ``SwitchRight`` grew
        by ``OldX``/``OldW``, and is clamped to the desktop.
        """
        if self.hidden_side != side:
            return
        # Alt+Z's zoom over the hide, undone first: the window is then as the
        # hide left it, and gets back exactly what it had.
        self._unzoom_view()
        state = self._collapse or {}
        self.side_view(side).visible = True
        self.hidden_side = None
        self._collapse = None
        rect = (self.x, self.y, self.width, self.height)
        if state and rect == state["after"]:
            if state["zoomed"]:
                self.zoomed = True
                self.layout(*self._bounds())
            else:
                self.x, self.y, self.width, self.height = state["before"]
                self._clamp(*self._bounds())
        else:
            kept = state.get("kept_width") or 1
            grow = self.width * state.get("hidden_width", self.width) // kept
            width, _ = self._bounds()
            if side == "left":
                # The right edge stays where it is; the left one stops at
                # the desktop's.
                right = self.x + self.width
                self.x = max(0, self.x - grow)
                self.width = right - self.x
            else:
                self.width = min(self.width + grow, max(self.width, width - self.x))
            self._clamp(*self._bounds())
        self.panels.invalidate()
