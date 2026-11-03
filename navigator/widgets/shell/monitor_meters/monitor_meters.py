"""The meters inside Utilities > System monitor, painted as Disk > Volumes' list is.

Not DOS Navigator's: the whole window is a departure (:mod:`navigator.lib.system.monitor`).

- **:class:`CpuMeters`** is the processors. The top line is every processor together. Under it each processor has a
  cell (``12 ███▒▒▒▒ 41% 3.4G``), flowed down and then across into as many columns as :func:`cpu_layout` chooses. The
  bars are DN's gauge characters (``█▒``, ``#.`` on an ASCII terminal), and a processor at 90% or more is drawn in the
  ``.busy`` class.
- **:class:`MemoryMeters`** is three lines: *Memory*, *Virtual* (the commit charge) and *Swap*. Each has a bar, its
  share, and how much of how much.
- **:class:`SensorList`** is each chip's heading, then its temperatures and fans, one per line. A temperature at its
  chip's high limit is ``.warm``, and at its critical limit ``.hot``.

The two lists scroll when the window is too short for them, by the arrows, PgUp/PgDn, Home/End, the wheel or the
bar. **Their cursor is never drawn**: a reading is there to be seen, not chosen. Each movement scrolls straight away,
instead of walking an unseen cursor to the edge first.

Every line is painted in one ``draw_runs`` call, so a mirrored screen keeps it in order (``navkit-bidi``).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any

from navkit.bidi import display_width, pad_cells
from navkit.glyphs import DEFAULT_GAUGE, gauge
from navkit.i18n import tr
from navkit.reactive import computed, effect, reactive
from navkit.screen import Surface
from navkit.style import Style
from navkit.widget import Widget
from navml.widgets.dialog.list_viewer import ListViewer

from navigator.lib.system.monitor import Chip, Cpu, Fan, Memory, Temperature, short_size

#: The fewest cells a bar is drawn in, and what a window opened at its natural size gives one.
BAR_MIN = 8
BAR_NATURAL = 12
#: Blank cells between two columns of processors.
GAP = 3
#: The rows a column of processors is filled to before another column is started, when the width allows.
COLUMN_ROWS = 8
#: A processor at or past this share is ``.busy``.
BUSY = 90.0
#: ``100%``: the share's cells.
PERCENT_WIDTH = 4
#: `` 4.3G``: a clock's cells, the blank before it counted.
CLOCK_WIDTH = 6


def _label_width(count: int) -> int:
    """The cells before a bar: the widest processor number, or *All* over them if it is wider, so that every bar,
    the line for all of them included, starts in one column."""
    return max(len(str(max(0, count - 1))), display_width(tr("All")))


def _cell_tail(clocks: bool) -> int:
    """A processor's cells after its bar: a blank, the share, and the clock."""
    return 1 + PERCENT_WIDTH + (CLOCK_WIDTH if clocks else 0)


def _cell_fixed(count: int, clocks: bool) -> int:
    """A processor's cell without its bar: its label, a blank, then the tail."""
    return _label_width(count) + 1 + _cell_tail(clocks)


def cpu_layout(count: int, clocks: bool, width: int) -> tuple[int, int, int]:
    """``(columns, rows, bar)`` for *count* processors in *width* cells.

    The fewest columns that keep a column at :data:`COLUMN_ROWS` rows or fewer, and never more than fit at
    :data:`BAR_MIN` cells a bar; the bars then take the width there is. It depends on the width alone, so the box's
    height can follow it without going round in a circle.
    """
    if count <= 0:
        return 0, 0, BAR_MIN
    fixed = _cell_fixed(count, clocks)
    fit = max(1, (width + GAP) // (fixed + BAR_MIN + GAP))
    columns = max(1, min(count, fit, ceil(count / COLUMN_ROWS)))
    rows = ceil(count / columns)
    bar = max(BAR_MIN, (width - (columns - 1) * GAP) // columns - fixed)
    return columns, rows, bar


def cpu_width(count: int, clocks: bool, room: int) -> int:
    """How wide the processors are at their natural size, in no more than *room* cells."""
    columns, _, _ = cpu_layout(count, clocks, room)
    if not columns:
        return 0
    return min(room, columns * (_cell_fixed(count, clocks) + BAR_NATURAL) + (columns - 1) * GAP)


def _memory_labels() -> tuple[str, str, str]:
    return tr("Memory"), tr("Virtual"), tr("Swap")


def memory_width() -> int:
    """How wide the memory lines are at their natural size: a label, a bar, the share, and ``26.0G of 23.2G``."""
    label = max(display_width(text) for text in _memory_labels())
    sizes = display_width(tr("{used} of {total}").format(used="99.9G", total="99.9G"))
    return label + 1 + BAR_NATURAL + 1 + PERCENT_WIDTH + 2 + sizes


def _bar_runs(chars: str, share: float, width: int, done: Style, rest: Style) -> list[tuple[str, Style]]:
    filled = min(width, max(0, round(width * min(100.0, max(0.0, share)) / 100)))
    return [(chars[0] * filled, done), (chars[1] * (width - filled), rest)]


def _percent(share: float) -> str:
    return pad_cells(f"{share:.0f}%", PERCENT_WIDTH, "right")


class _Meters(ListViewer):
    """A list whose cursor is never drawn: every movement scrolls instead."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("framed", False)
        super().__init__(**kwargs)

    def row_selected(self, index: int) -> bool:
        return False

    def move_cursor(self, delta: int) -> None:
        """Scroll by *delta*, and put the cursor on the edge it scrolled towards, so the scroll follows it at once."""
        count = len(self.items)
        if not count:
            return
        rows = max(1, self.rows)
        top = min(max(0, self.scroll + delta), max(0, count - rows))
        self.cursor = top if delta < 0 else min(count - 1, top + rows - 1)

    async def choose(self) -> bool:
        return False


class CpuMeters(_Meters):
    """Every processor together, then each one, in columns."""

    #: Every processor together, and each one, from the last read.
    total: Cpu = reactive(Cpu(-1, 0.0))
    cpus: tuple[Cpu, ...] = reactive(())

    parts = ListViewer.parts + ("done",)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.header = 1

    def mounted(self) -> None:
        super().mounted()
        effect(self, CpuMeters._lay_out)

    @computed
    def clocks(self) -> bool:
        """Whether any processor's clock is known: its column is left out otherwise."""
        return any(cpu.mhz is not None for cpu in self.cpus)

    @computed
    def layout(self) -> tuple[int, int, int]:
        """``(columns, rows, bar)`` in the width the list has."""
        return cpu_layout(len(self.cpus), self.clocks, self.inner_width)

    @computed
    def wanted(self) -> int:
        """Lines it would take to show it all: every processor's, and the one over them."""
        return self.layout[1] + self.header

    def _lay_out(self) -> None:
        """A row's items are the processors across it: the first column top to bottom, then the next."""
        columns, rows, _ = self.layout
        cpus = self.cpus
        self.items = [tuple(cpus[column * rows + row] for column in range(columns) if column * rows + row < len(cpus))
                      for row in range(rows)]

    def row_text(self, index: int, item: Any) -> str:
        return "  ".join(f"{cpu.number} {cpu.percent:.0f}%" for cpu in item)

    def row_tooltip(self, index: int, item: Any) -> str:
        return ""

    def _gauge(self) -> str:
        return gauge(DEFAULT_GAUGE, self.glyphs)

    def _bar_style(self, share: float) -> Style:
        return self.part_style("done", classes=("busy",) if share >= BUSY else ())

    def _cells_width(self) -> int:
        """The processors' cells side by side, the gaps between them counted."""
        columns, _, bar = self.layout
        return min(self.inner_width, columns * (_cell_fixed(len(self.cpus), self.clocks) + bar) + (columns - 1) * GAP)

    def render_header(self, surface: Surface) -> None:
        """Every processor together, as wide as the cells under it: its bar starts where theirs do, and ends where
        the last column's does, with its share under that column's shares."""
        count = len(self.cpus)
        label = _label_width(count)
        width = self._cells_width() if count else self.inner_width
        tail = _cell_tail(self.clocks)
        bar = max(1, width - label - 1 - tail)
        share = self.total.percent
        runs = [(pad_cells(tr("All"), label) + " ", self.style),
                *_bar_runs(self._gauge(), share, bar, self._bar_style(share), self.style),
                (" " + _percent(share), self.style)]
        surface.draw_runs(self.inset, self.inset, runs, self.inner_width)

    def render_row(self, surface: Surface, y: int, index: int, item: Any) -> None:
        _, _, bar = self.layout
        label = _label_width(len(self.cpus))
        chars = self._gauge()
        runs: list[tuple[str, Style]] = []
        for column, cpu in enumerate(item):
            if column:
                runs.append((" " * GAP, self.style))
            runs.append((pad_cells(str(cpu.number), label, "right") + " ", self.style))
            runs.extend(_bar_runs(chars, cpu.percent, bar, self._bar_style(cpu.percent), self.style))
            text = " " + _percent(cpu.percent)
            if self.clocks:
                clock = "" if cpu.mhz is None else f"{cpu.mhz / 1000:.1f}G"
                text += " " + pad_cells(clock, CLOCK_WIDTH - 1, "right")
            runs.append((text, self.style))
        surface.draw_runs(self.inset, y, runs, self._cells_width())


class MemoryMeters(Widget):
    """*Memory*, *Virtual* (the commit charge) and *Swap*, a line each."""

    memory: Memory = reactive(Memory())

    parts = ("done",)

    def lines(self) -> list[tuple[str, float, str]]:
        """Each line's label, share and ``used of total`` -- the share None-like (-1) for no swap at all."""
        memory = self.memory
        of = tr("{used} of {total}")
        found = []
        for label, used, total in zip(_memory_labels(), (memory.used, memory.committed, memory.swap_used),
                                      (memory.total, memory.commit_limit, memory.swap_total)):
            if total <= 0:
                found.append((label, -1.0, tr("none")))
            else:
                found.append((label, used * 100.0 / total,
                              of.format(used=short_size(used), total=short_size(total))))
        return found

    def tooltip_at(self, x: int, y: int) -> str:
        own = super().tooltip_at(x, y)
        if own:
            return own
        return {
            0: tr("In use: all of it less what can still be had without swapping"),
            1: tr("Promised to the programs (Committed_AS) of what the kernel allows (CommitLimit); "
                  "it can pass 100% when memory is overcommitted"),
            2: tr("Swap in use"),
        }.get(y, "")

    def render(self, surface: Surface) -> None:
        if self.width < 1:
            return
        lines = self.lines()
        label_width = max(display_width(label) for label, _, _ in lines)
        sizes_width = max(display_width(sizes) for _, _, sizes in lines)
        bar = max(1, self.width - label_width - 1 - 1 - PERCENT_WIDTH - 2 - sizes_width)
        chars = gauge(DEFAULT_GAUGE, self.glyphs)
        surface.fill(0, 0, self.width, self.height, " ", self.style)
        for y, (label, share, sizes) in enumerate(lines[: self.height]):
            runs = [(pad_cells(label, label_width) + " ", self.style)]
            if share < 0:
                runs.append((sizes, self.style))
            else:
                done = self.part_style("done", classes=("busy",) if share >= BUSY else ())
                runs.extend(_bar_runs(chars, share, bar, done, self.style))
                runs.append((" " + _percent(share) + "  " + pad_cells(sizes, sizes_width, "right"), self.style))
            surface.draw_runs(0, y, runs, self.width)


@dataclass(frozen=True, slots=True)
class SensorRow:
    """A line of the sensor list: a chip's heading, or one of its readings."""

    chip: Chip
    reading: Temperature | Fan | None = None


def _chip_title(chip: Chip) -> str:
    return f"{chip.name} ({chip.device})" if chip.device else chip.name


def _degrees(value: float) -> str:
    return f"{value:.0f}°C"


def sensor_rows(chips: tuple[Chip, ...] | list[Chip]) -> list[SensorRow]:
    """Each chip's heading, then its temperatures, then its fans."""
    rows: list[SensorRow] = []
    for chip in chips:
        rows.append(SensorRow(chip))
        rows.extend(SensorRow(chip, reading) for reading in (*chip.temperatures, *chip.fans))
    return rows


def _reading_cells(reading: Temperature | Fan) -> tuple[str, str, str]:
    """A reading's label, its value, and its limits (``""`` for none)."""
    if isinstance(reading, Fan):
        return reading.label, tr("{rpm} RPM").format(rpm=reading.rpm), ""
    limits = []
    if reading.high is not None and reading.high > 0:
        limits.append(tr("high {degrees}").format(degrees=_degrees(reading.high)))
    if reading.critical is not None and reading.critical > 0:
        limits.append(tr("critical {degrees}").format(degrees=_degrees(reading.critical)))
    return reading.label, _degrees(reading.celsius), "(" + ", ".join(limits) + ")" if limits else ""


def _columns(rows: list[SensorRow]) -> tuple[int, int]:
    """The label column's width and the value column's, over every reading."""
    cells = [_reading_cells(row.reading) for row in rows if row.reading is not None]
    if not cells:
        return 0, 0
    return max(display_width(label) for label, _, _ in cells), max(display_width(value) for _, value, _ in cells)


def sensor_text(row: SensorRow, label_width: int, value_width: int) -> str:
    """A line of the list as it is painted."""
    if row.reading is None:
        return _chip_title(row.chip)
    label, value, limits = _reading_cells(row.reading)
    text = "  " + pad_cells(label, label_width) + "  " + pad_cells(value, value_width, "right")
    return text + ("  " + limits if limits else "")


def sensors_width(rows: list[SensorRow]) -> int:
    """The longest line of the list."""
    label_width, value_width = _columns(rows)
    return max((display_width(sensor_text(row, label_width, value_width)) for row in rows), default=0)


class SensorList(_Meters):
    """Each chip's heading, then its temperatures and fans."""

    #: The chips from the last read.
    chips: tuple[Chip, ...] = reactive(())

    parts = ListViewer.parts + ("heading",)

    def mounted(self) -> None:
        super().mounted()
        effect(self, SensorList._list)

    def _list(self) -> None:
        self.items = sensor_rows(self.chips)

    @computed
    def widths(self) -> tuple[int, int]:
        return _columns(self.items)

    def row_text(self, index: int, item: Any) -> str:
        return sensor_text(item, *self.widths)

    def row_tooltip(self, index: int, item: Any) -> str:
        reading = item.reading
        if reading is None:
            return ""
        if isinstance(reading, Temperature) and reading.level == "hot":
            return tr("At or past its critical temperature")
        if isinstance(reading, Temperature) and reading.level == "warm":
            return tr("At or past its high temperature")
        return ""

    def row_style(self, index: int, item: Any) -> Style:
        if item.reading is None:
            return self.part_style("heading")
        level = item.reading.level if isinstance(item.reading, Temperature) else ""
        return self.part_style("row", classes=(level,) if level else ())
