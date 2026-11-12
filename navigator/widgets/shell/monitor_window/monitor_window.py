"""The handlers behind ``monitor_window.nml``.

The processors, the memory and the sensors are read on a thread (:class:`navigator.lib.system.monitor.Monitor`,
through ``Background``) when the window opens, on Ctrl+R, and every ``[monitor] refresh`` seconds. A tick is skipped
while a read is still under way, or while a box is up over the desktop. Only the newest read is shown.

**The window is as big as what it shows.** :meth:`MonitorWindow.natural_size` adds up three things:
- the processors' columns (:func:`~navigator.widgets.shell.monitor_meters.cpu_layout`, chosen from the width alone);
- the memory's three lines;
- each sensor chip's lines.

The window opens at that size, centred, within the desktop. A read whose
:meth:`~navigator.lib.system.monitor.Snapshot.shape` differs from the last (a processor taken offline, a USB disk's
sensor plugged in) fits it again. That happens only while it still has the rectangle it last gave itself. Once the
user has moved, resized, zoomed or tiled it, the rectangle is theirs, and a refit would undo it. Within whatever size
it has, :attr:`MonitorWindow.heights` shares the rows out: the memory box first, then the processors, then the sensors.
A box too short for its lines scrolls.
"""

from __future__ import annotations

from typing import Any

from navkit.reactive import computed
from navml.background import Background, Outcome
from navml.widgets.window import Window

from navigator.lib.system import monitor
from navigator.lib.system.processes import processors
from navigator.widgets.shell.monitor_meters import cpu_layout, memory_width, sensor_rows
from navigator.widgets.shell.monitor_meters.monitor_meters import cpu_width, sensors_width

#: Where the window reads.
_READER = Background("nav-monitor", workers=1)

#: The memory box: its three lines and its frame.
MEMORY_HEIGHT = 5
#: The cells a line loses to the window's frame, the box's frame, their margins and the scroll bar.
MARGIN = 8


def _refresh() -> float:
    """``[monitor] refresh``: seconds between reads, 0 for none."""
    from navigator.settings import SETTINGS

    try:
        return max(0.0, float(SETTINGS.monitor.refresh))
    except (AttributeError, TypeError, ValueError):
        return 1.0


class MonitorWindow(Window):
    """The processors, the memory and the sensors in a window of their own."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._monitor = monitor.Monitor()
        self._shape: Any = None
        #: The rectangle the window last gave itself; another one is the user's.
        self._fitted: tuple[int, int, int, int] | None = None
        self._reads = 0
        self._reading = False
        self._ticker: Any = None

    def mounted(self) -> None:
        super().mounted()
        # A first guess, before anything is read: every processor with a
        # clock, no sensors.  The first read fits it to what there is.
        self.cpu.cpus = tuple(monitor.Cpu(number, 0.0, 0.0) for number in range(processors()))
        self.fit()
        # Not from ``__init__``: until the window is on the desktop it has no
        # application, and ``Background`` would read on the loop instead.
        self.reload()
        app = self.application
        seconds = _refresh()
        if app is not None and seconds > 0:
            self._ticker = app.call_every(seconds, self._tick)

    def unmounting(self) -> None:
        if self._ticker is not None:
            self._ticker.cancel()
            self._ticker = None
        super().unmounting()

    # -- the size ---------------------------------------------------------------------

    def natural_size(self, width: int, height: int) -> tuple[int, int]:
        """The size that shows everything, within a desktop of *width* x *height*."""
        cpus = self.cpu.cpus
        clocks = any(cpu.mhz is not None for cpu in cpus)
        rows = sensor_rows(self.sensors.chips)
        content = max(cpu_width(len(cpus), clocks, max(0, width - MARGIN)), memory_width(), sensors_width(rows))
        w = max(min(self.min_width, width), min(width, content + MARGIN))
        cpu_rows = cpu_layout(len(cpus), clocks, max(0, w - MARGIN))[1] + 1
        h = 2 + cpu_rows + 2 + MEMORY_HEIGHT + (len(rows) + 2 if rows else 0)
        return w, max(min(self.min_height, height), min(height, h))

    def fit(self) -> None:
        """Take the natural size, centred -- unless the user has made the rectangle theirs."""
        desktop = self.parent
        if desktop is None or self.zoomed:
            return
        if self._fitted is not None and self._fitted != (self.x, self.y, self.width, self.height):
            return
        w, h = self.natural_size(desktop.width, desktop.height)
        self.x, self.y = max(0, (desktop.width - w) // 2), max(0, (desktop.height - h) // 2)
        self.width, self.height = w, h
        self._fitted = (self.x, self.y, w, h)

    @computed
    def heights(self) -> tuple[int, int, int]:
        """The *CPU*, *Memory* and *Sensors* boxes' heights in the window's height.

        The memory first, then the processors what they need -- but no less than half of what is left when the
        sensors want more than there is -- and the sensors the rest. A window taller than it needs gives the
        sensors the room, or the processors when there are none.
        """
        rest = max(0, self.height - 2 - MEMORY_HEIGHT)
        cpu_need = self.cpu.wanted + 2
        sensor_lines = len(self.sensors.items)
        if not sensor_lines:
            return rest, MEMORY_HEIGHT, 0
        cpu = min(cpu_need, max(rest - (sensor_lines + 2), rest // 2, min(cpu_need, 4)))
        return cpu, MEMORY_HEIGHT, max(0, rest - cpu)

    # -- reading ----------------------------------------------------------------------

    def reload(self) -> None:
        """Read again, on a thread; only the newest read is shown."""
        self._reads += 1
        self._reading = True
        _READER.run(self, self._monitor, done=lambda outcome, n=self._reads: self._read(n, outcome))

    async def _tick(self) -> None:
        """The clock's read -- skipped while one is under way or a box is up."""
        app = self.application
        if self._reading or app is None or app.modal is not None:
            return
        self.reload()

    def _read(self, read: int, outcome: Outcome) -> None:
        if read != self._reads:
            return
        self._reading = False
        try:
            snapshot = outcome.result()
        except OSError:
            return
        self.show(snapshot)

    def show(self, snapshot: monitor.Snapshot) -> None:
        """Put *snapshot* in the meters, and fit the window again if its shape changed."""
        self.cpu.total = snapshot.total
        self.cpu.cpus = snapshot.cpus
        self.memory.memory = snapshot.memory
        self.sensors.chips = snapshot.chips
        shape = snapshot.shape()
        if shape != self._shape:
            self._shape = shape
            self.fit()

    # -- the right-click menu: ``ContextMenuHost``'s hooks, written out, as
    # ``ProcessWindow``'s are.

    def prepare_context(self, x: int, y: int) -> None:
        """Nothing to point at: the menu is the same anywhere."""

    def context_point(self) -> tuple[int, int]:
        return 3, 2

    # -- Tab ----------------------------------------------------------------------------

    def _step(self, by: int) -> None:
        """From one list to the other, wrapping."""
        order = [widget for widget in self.focusable() if widget is not self]
        if not order:
            return
        app = self.application
        focused = app.focused if app is not None else None
        index = order.index(focused) if focused in order else (-1 if by > 0 else 0)
        order[(index + by) % len(order)].focus()
