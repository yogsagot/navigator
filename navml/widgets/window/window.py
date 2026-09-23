"""The chrome and the dragging behind ``window.nml``.

Four things are worth reading this file for.

**The first click on a background window is not swallowed.**  A press on a
window that is not the active one brings it forward and restores its focus,
and is *then* delivered as though it had been active all along -- Turbo
Vision's rule, and the one that lets a click on a file in the other window
both select that window and move the cursor to the file.  The one exception
is the chrome: an icon on a window that was not active a moment ago is not
there to be clicked, because an inactive window does not paint it.

**Chrome is tested before the children, not after.**  A frameless window --
the file manager, whose panels' frames *are* its frame -- has children on
row 0, and they would otherwise claim every press on its title.  So
:meth:`dispatch_mouse` asks :meth:`chrome_hit` first, and painting and
hit-testing read one column table, so the two cannot drift apart.

**A drag holds the mouse.**  Routing is by position and the pointer outruns
the window routinely, so a move or a resize calls
:meth:`~navkit.application.Application.capture_mouse` and every action until
the release arrives here, in this window's coordinates, whatever is under the
pointer.

**The rectangle is state.**  Nothing binds ``x``, ``y``, ``width`` or
``height``, because everything here assigns them.  :meth:`layout` is
consequently not the cascade :class:`~navkit.widget.Widget` runs: a window
keeps its own size, and the desktop's size only clamps it -- or, zoomed,
becomes it.
"""

from __future__ import annotations

from typing import Any

from navkit.events import DoubleClickEvent, KeyEvent, MouseClickEvent
from navkit.glyphs import BOX_CHARSETS
from navkit.reactive import computed
from navkit.screen import Surface
from navkit.stylesheet import StyleProperty
from navkit.widget import Widget

#: The chrome, Turbo Vision's layout: close on the left, zoom on the right, one
#: cell of content between brackets so it survives an ASCII terminal.
CLOSE_ICON, ASCII_CLOSE_ICON = "[■]", "[x]"
ZOOM_ICON, ASCII_ZOOM_ICON = "[↑]", "[^]"
UNZOOM_ICON, ASCII_UNZOOM_ICON = "[↕]", "[v]"
GRIP, ASCII_GRIP = "─┘", "-+"

#: Where the close icon starts, counted from the left edge.
CLOSE_X = 2

#: How much of a window a drag must leave on the desktop, so that there is
#: always a title to take hold of again.
KEEP_VISIBLE = 8

#: The keyboard move/size mode, one cell per press.
_MOVES = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}


class Window(Widget):
    """A detached window on a desktop."""

    #: Single when inactive; ``Window:active { border: double }`` in a sheet is
    #: what makes the one with the keyboard stand out, as in the original.
    border = StyleProperty("single", values=tuple(BOX_CHARSETS))

    #: The title across the top edge, and the icons beside it.
    parts = ("title", "icon")

    #: Whether this window draws its own frame.  A class-level fact about what
    #: the window *is* rather than a look, so it is not a sheet property: the
    #: file manager is frameless because its panels already are the frame, and
    #: a sheet cannot change that.  A frameless window paints its icons in
    #: :meth:`render_after`, on top of whatever its children drew on row 0.
    framed: bool = True

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: The rectangle a zoom set aside, to come back to.
        self._restore: tuple[int, int, int, int] | None = None
        #: ``("move" | "resize", dx, dy)`` while the mouse is dragging.
        self._drag: tuple[str, int, int] | None = None
        #: What had the keyboard, and the rectangle, when keyboard move/size
        #: mode began -- the first to give back, the second for Escape.
        self._key_move: tuple[Widget | None, tuple[int, int, int, int]] | None = None
        #: What had the keyboard when this window last stopped being active.
        #: Kept and restored by the desktop.
        self._saved_focus: Widget | None = None

    # -- where it lives ------------------------------------------------------

    @property
    def desktop(self) -> Any:
        """The desktop this window is on, or None.  Anything with ``activate``."""
        parent = self.parent
        return parent if hasattr(parent, "active_window") else None

    @computed
    def active(self) -> bool:
        """Whether this is the desktop's top window.  The ``:active`` state."""
        return getattr(self.parent, "active_window", None) is self

    def _bounds(self) -> tuple[int, int]:
        parent = self.parent
        if parent is None:
            return self.width, self.height
        return parent.width, parent.height

    # -- geometry ------------------------------------------------------------

    def layout(self, width: int, height: int) -> None:
        """Fit into a desktop of *width* x *height* -- by clamping, not filling.

        Zoomed, the desktop's size *is* this window's.  Otherwise the window
        keeps its own rectangle and is only pulled back far enough to leave a
        title to take hold of, and shrunk if the desktop got smaller than it.
        A window nobody has sized yet opens at three quarters of the desktop,
        centred.  The children are not cascaded into: a component's children
        are placed by its markup, and a hand-written window places its own.
        """
        if self.zoomed:
            self.x, self.y, self.width, self.height = 0, 0, width, height
            return
        if self.width <= 0 or self.height <= 0:
            w = min(width, max(self.min_width, width * 3 // 4))
            h = min(height, max(self.min_height, height * 3 // 4))
            self.x, self.y = (width - w) // 2, (height - h) // 2
            self.width, self.height = w, h
        self._clamp(width, height)

    def _clamp(self, width: int, height: int) -> None:
        w = max(min(self.min_width, width), min(self.width, width))
        h = max(min(self.min_height, height), min(self.height, height))
        x = max(min(self.x, max(0, width - KEEP_VISIBLE)), min(0, KEEP_VISIBLE - w))
        y = max(0, min(self.y, max(0, height - 1)))
        self.x, self.y, self.width, self.height = x, y, w, h

    def move_to(self, x: int, y: int) -> None:
        """Put the top-left corner at *x*, *y* of the desktop, within reason."""
        self.x, self.y = x, y
        self._clamp(*self._bounds())

    def resize_to(self, width: int, height: int) -> None:
        """Take *width* x *height*, no smaller than the minimum and no larger
        than what is left of the desktop to the right of and below it."""
        dw, dh = self._bounds()
        self.width = max(min(self.min_width, dw), min(width, dw - max(0, self.x)))
        self.height = max(min(self.min_height, dh), min(height, dh - self.y))

    def toggle_zoom(self) -> None:
        """Fill the desktop, or go back to the rectangle that filling it replaced."""
        width, height = self._bounds()
        if self.zoomed:
            self.zoomed = False
            if self._restore is not None:
                self.x, self.y, self.width, self.height = self._restore
            else:
                # Opened zoomed, so there is nothing to go back to: take the
                # size a fresh window would.
                self.width = self.height = 0
            self.layout(width, height)
        else:
            self._restore = (self.x, self.y, self.width, self.height)
            self.zoomed = True
            self.layout(width, height)

    # -- the chrome ----------------------------------------------------------

    def _icons(self) -> dict[str, int]:
        """Which icons are showing, and the column each one starts at.

        The one table both :meth:`render` and :meth:`chrome_hit` read.  Only
        the active window has them, as in Turbo Vision: a background window's
        frame is plain, and clicking where an icon would be only brings the
        window forward.
        """
        if not self.active:
            return {}
        icons: dict[str, int] = {}
        if self.closable and self.width >= CLOSE_X + 6:
            icons["close"] = CLOSE_X
        if self.zoomable and self.width >= (CLOSE_X + 9 if self.closable else 8):
            icons["zoom"] = self.width - 5
        return icons

    def _has_grip(self) -> bool:
        return (
            self.active and self.resizable and not self.zoomed
            and self.width >= 4 and self.height >= 2
        )

    def chrome_hit(self, x: int, y: int) -> str | None:
        """What the chrome at *x*, *y* does: close, zoom, move, resize or nothing."""
        if y == 0:
            for name, start in self._icons().items():
                if start <= x < start + 3:
                    return name
            return "move"
        if y == self.height - 1 and x >= self.width - 2 and self._has_grip():
            return "resize"
        return None

    def render(self, surface: Surface) -> None:
        if not self.framed or self.width < 2 or self.height < 2:
            return
        surface.draw_box(
            0, 0, self.width, self.height, self.style,
            charset=self.box_charset(), fill=" ",
        )
        if self.title:
            label = f" {self.title} "[: max(0, self.width - 2)]
            surface.draw_text(
                max(1, (self.width - len(label)) // 2), 0, label,
                self.part_style("title"),
            )
        self._paint_chrome(surface)

    def render_after(self, surface: Surface) -> None:
        if not self.framed:
            self._paint_chrome(surface)

    def _paint_chrome(self, surface: Surface) -> None:
        unicode = self.glyphs > 1
        style = self.part_style("icon")
        for name, start in self._icons().items():
            if name == "close":
                icon = CLOSE_ICON if unicode else ASCII_CLOSE_ICON
            elif self.zoomed:
                icon = UNZOOM_ICON if unicode else ASCII_UNZOOM_ICON
            else:
                icon = ZOOM_ICON if unicode else ASCII_ZOOM_ICON
            surface.draw_text(start, 0, icon, style)
        if self._has_grip():
            surface.draw_text(
                self.width - 2, self.height - 1, GRIP if unicode else ASCII_GRIP, style
            )

    def close(self) -> None:
        """Take this window off its desktop, which activates the next one."""
        desktop = self.desktop
        if desktop is not None:
            desktop.close_window(self)
        elif self.parent is not None:
            self.parent.remove(self)

    # -- the mouse -----------------------------------------------------------

    async def dispatch_mouse(self, event: MouseClickEvent) -> bool:
        """Bring the window forward, then try the chrome, then the children.

        *event* is in the desktop's coordinates, as for any widget.
        """
        local = event.translated(-self.x, -self.y)
        if isinstance(event, DoubleClickEvent):
            if event.button == "left" and await self.on_double_click(local):
                return True
            return await super().dispatch_mouse(event)
        if event.action == "press" and not event.is_wheel:
            was_active = self.active
            desktop = self.desktop
            if desktop is not None and not was_active:
                desktop.activate(self)
            if was_active and event.button == "left" and self._press_chrome(local):
                return True
            if not was_active and event.button == "left" and local.y == 0 and (
                self.chrome_hit(local.x, local.y) == "move"
            ):
                # Taking hold of a background window's title moves it, as
                # well as raising it -- but its icons were not showing.
                self._start_drag("move", local)
                return True
        return await super().dispatch_mouse(event)

    def _press_chrome(self, local: MouseClickEvent) -> bool:
        hit = self.chrome_hit(local.x, local.y)
        if hit == "close":
            self.close()
        elif hit == "zoom":
            self.toggle_zoom()
        elif hit in ("move", "resize"):
            self._start_drag(hit, local)
        else:
            return False
        return True

    def _start_drag(self, kind: str, local: MouseClickEvent) -> None:
        if kind == "move" and self.zoomed:
            # Dragging a zoomed window takes it back to its own size first,
            # under the pointer rather than wherever it used to be.
            pointer_x, pointer_y = self.x + local.x, self.y + local.y
            self.toggle_zoom()
            grab = min(local.x, max(0, self.width - 1))
            self.move_to(pointer_x - grab, pointer_y)
            local = local.translated(grab - local.x, 0)
        if kind == "move":
            self._drag = ("move", local.x, local.y)
        else:
            self._drag = ("resize", self.width - local.x, self.height - local.y)
        app = self.application
        if app is not None:
            app.capture_mouse(self)

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        """A drag in progress -- delivered here by the capture, not by position."""
        if self._drag is None:
            return False
        kind, dx, dy = self._drag
        if event.action == "release":
            self._drag = None
        elif event.action == "move":
            if kind == "move":
                self.move_to(self.x + event.x - dx, self.y + event.y - dy)
            else:
                self.resize_to(event.x + dx, event.y + dy)
        return True

    async def on_double_click(self, event: DoubleClickEvent) -> bool:
        """A double click on the title zooms, as in Turbo Vision."""
        if not self.zoomable or event.y != 0 or self.chrome_hit(event.x, 0) != "move":
            return False
        self._drag = None
        app = self.application
        if app is not None and app.mouse_capture is self:
            app.release_mouse()
        self.toggle_zoom()
        return True

    # -- the keyboard move/size mode -----------------------------------------

    @property
    def moving(self) -> bool:
        """Whether the keyboard is moving or sizing this window."""
        return self._key_move is not None

    def begin_move(self) -> None:
        """Take the keyboard: arrows move, Shift+arrows resize, Enter keeps it,
        Escape puts it back.  Turbo Vision's ``dmDragMove``, off Ctrl+F5."""
        app = self.application
        if app is None or self._key_move is not None:
            return
        if self.zoomed:
            self.toggle_zoom()
        self._key_move = (app.focused, (self.x, self.y, self.width, self.height))
        self.can_focus = True
        self.focus()

    def end_move(self, keep: bool = True) -> None:
        """Leave keyboard move/size mode, giving the keyboard back."""
        if self._key_move is None:
            return
        previous, rect = self._key_move
        self._key_move = None
        if not keep:
            self.x, self.y, self.width, self.height = rect
        if previous is not None and previous.is_mounted and self._holds(previous):
            previous.focus()
        else:
            order = self.focusable()
            others = [widget for widget in order if widget is not self]
            if others:
                others[0].focus()
        self.can_focus = False
        app = self.application
        if app is not None and app.focused is self:
            app.focused = None

    async def on_key(self, event: KeyEvent) -> bool:
        if self._key_move is None:
            return False
        if event.matches("enter"):
            self.end_move(keep=True)
        elif event.matches("escape"):
            self.end_move(keep=False)
        else:
            for name, (dx, dy) in _MOVES.items():
                if event.matches(name):
                    self.move_to(self.x + dx, self.y + dy)
                    break
                if event.matches(f"shift+{name}"):
                    self.resize_to(self.width + dx, self.height + dy)
                    break
        # Everything else is swallowed: a key that reached a panel in the
        # middle of a move would be a surprise, and Escape is the way out.
        return True
