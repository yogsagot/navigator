"""Utilities > System monitor: reading ``/proc`` and ``/sys``, the meters' layout, and the window that sizes itself."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

from conftest import Until, run_app

from navigator.lib.system import monitor
from navigator.lib.system.monitor import Chip, Cpu, CpuSampler, Fan, Memory, Snapshot, Temperature, cpu_times
from navigator.widgets.shell.monitor_meters import cpu_layout, sensor_rows

# -- the model ------------------------------------------------------------------------


def write(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def stat(*lines: tuple[int, int, int, int, int]) -> str:
    """A ``/proc/stat`` from ``(user, nice, system, idle, iowait)`` per line, the first the sum."""
    names = ["cpu "] + [f"cpu{n}" for n in range(len(lines) - 1)]
    body = "\n".join(f"{name} " + " ".join(str(v) for v in values) + " 0 0 0 0 0"
                     for name, values in zip(names, lines))
    return body + "\nintr 1 2 3\nctxt 99\n"


def test_cpu_times_count_idle_and_iowait_as_idle_and_leave_guest_time_out():
    found = cpu_times("cpu  10 0 5 80 5 0 0 0 7 7\ncpu0 10 0 5 80 5 0 0 0 7 7\ncpufreq x\nintr 1\n")
    assert found == {-1: monitor.Ticks(15, 100), 0: monitor.Ticks(15, 100)}


def test_the_sampler_gives_each_processor_its_share_since_the_read_before():
    sampler = CpuSampler()
    first = sampler.sample(cpu_times(stat((0, 0, 0, 100, 0), (0, 0, 0, 50, 0), (0, 0, 0, 50, 0))))
    assert first == {-1: 0.0, 0: 0.0, 1: 0.0}
    second = sampler.sample(cpu_times(stat((50, 0, 0, 150, 0), (50, 0, 0, 50, 0), (0, 0, 0, 100, 0))))
    assert second == {-1: 50.0, 0: 100.0, 1: 0.0}


def test_a_processor_that_comes_online_or_whose_ticks_went_back_starts_at_zero():
    sampler = CpuSampler()
    sampler.sample(cpu_times(stat((0, 0, 0, 100, 0), (0, 0, 0, 100, 0))))
    found = sampler.sample(cpu_times(stat((10, 0, 0, 100, 0), (5, 0, 0, 5, 0), (10, 0, 0, 10, 0))))
    assert found[0] == 0.0  # went backwards: brought online again
    assert found[1] == 0.0  # new
    assert found[-1] == 100.0


def test_memory_reads_the_commit_charge_and_no_swap(tmp_path):
    write(tmp_path, "proc/meminfo", "MemTotal: 1000 kB\nMemFree: 100 kB\nMemAvailable: 400 kB\nBuffers: 10 kB\n"
                                    "Cached: 90 kB\nSwapTotal: 0 kB\nSwapFree: 0 kB\nCommitLimit: 500 kB\n"
                                    "Committed_AS: 750 kB\nHugePages_Total: 0\n")
    found = monitor.memory(tmp_path)
    assert found == Memory(1000 * 1024, 400 * 1024, 100 * 1024, 0, 0, 750 * 1024, 500 * 1024)
    assert found.used == 600 * 1024
    assert found.swap_used == 0


def hwmon(root: Path, number: int, name: str, device: str = "", **files: str) -> Path:
    base = root / "sys/class/hwmon" / f"hwmon{number}"
    write(base.parent, f"hwmon{number}/name", name + "\n")
    if device:
        target = root / "sys/devices" / device
        target.mkdir(parents=True, exist_ok=True)
        os.symlink(target, base / "device")
    for file, text in files.items():
        write(base, file, text + "\n")
    return base


def test_sensors_read_each_chip_and_tell_two_of_one_name_apart(tmp_path):
    hwmon(tmp_path, 0, "nvme", "nvme0", temp1_input="30850", temp1_label="Composite", temp1_max="74850",
          temp1_crit="79850")
    hwmon(tmp_path, 1, "nvme", "nvme1", temp1_input="85000", temp1_label="Composite", temp1_max="82850",
          temp1_crit="84850")
    hwmon(tmp_path, 2, "k10temp", "0000:00:18.3", temp1_input="48250", temp1_label="Tctl",
          temp3_input="38625", temp3_label="Tccd1")
    hwmon(tmp_path, 10, "it8686", fan1_input="1200", fan2_input="900", fan2_label="Rear",
          temp1_input="51000")
    chips = monitor.sensors(tmp_path)
    assert [(chip.name, chip.device) for chip in chips] == [
        ("nvme", "nvme0"), ("nvme", "nvme1"), ("k10temp", ""), ("it8686", "")]
    assert chips[0].temperatures == (Temperature("Composite", 30.85, 74.85, 79.85),)
    assert chips[1].temperatures[0].level == "hot"
    assert [t.label for t in chips[2].temperatures] == ["Tctl", "Tccd1"]
    assert chips[3].fans == (Fan("fan1", 1200), Fan("Rear", 900))
    assert chips[3].temperatures == (Temperature("temp1", 51.0),)


def test_a_reading_that_cannot_be_read_is_left_out_and_its_chip_stays(tmp_path):
    hwmon(tmp_path, 0, "iwlwifi_1", temp1_input="")
    hwmon(tmp_path, 1, "amdgpu", temp1_input="57000", temp1_label="edge", temp2_input="oops", fan1_input="0")
    chips = monitor.sensors(tmp_path)
    assert [chip.name for chip in chips] == ["amdgpu"]
    assert chips[0].temperatures == (Temperature("edge", 57.0),)
    assert chips[0].fans == (Fan("fan1", 0),)


def test_without_hwmon_temperatures_the_thermal_zones_stand_in(tmp_path):
    write(tmp_path, "sys/class/thermal/thermal_zone0/type", "x86_pkg_temp\n")
    write(tmp_path, "sys/class/thermal/thermal_zone0/temp", "42000\n")
    write(tmp_path, "sys/class/thermal/cooling_device0/type", "Processor\n")
    assert monitor.sensors(tmp_path) == [Chip("thermal", "", (Temperature("x86_pkg_temp", 42.0),))]


def test_the_temperature_levels():
    assert Temperature("t", 69.0, 70.0, 90.0).level == ""
    assert Temperature("t", 70.0, 70.0, 90.0).level == "warm"
    assert Temperature("t", 95.0, 70.0, 90.0).level == "hot"
    assert Temperature("t", 95.0, None, 0.0).level == ""


def test_clocks_come_from_cpufreq_else_cpuinfo(tmp_path):
    write(tmp_path, "proc/cpuinfo", "processor\t: 0\ncpu MHz\t\t: 3400.125\n\nprocessor\t: 1\ncpu MHz\t\t: 2000\n")
    assert monitor.frequencies(tmp_path) == {0: 3400.125, 1: 2000.0}
    write(tmp_path, "sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq", "4259005\n")
    write(tmp_path, "sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq", "1\n")
    assert monitor.frequencies(tmp_path) == {0: 4259.005}


def test_a_monitor_reads_a_snapshot_whose_shape_is_what_the_window_size_follows(tmp_path):
    write(tmp_path, "proc/stat", stat((0, 0, 0, 100, 0), (0, 0, 0, 50, 0), (0, 0, 0, 50, 0)))
    write(tmp_path, "proc/meminfo", "MemTotal: 1000 kB\nMemAvailable: 500 kB\n")
    hwmon(tmp_path, 0, "k10temp", temp1_input="48250", temp1_label="Tctl")
    reader = monitor.Monitor(tmp_path)
    reader()
    write(tmp_path, "proc/stat", stat((100, 0, 0, 200, 0), (50, 0, 0, 100, 0), (50, 0, 0, 100, 0)))
    found = reader()
    assert found.total == Cpu(-1, 50.0)
    assert found.cpus == (Cpu(0, 50.0), Cpu(1, 50.0))
    assert found.memory.used == 500 * 1024
    assert found.shape() == (2, False, (("k10temp", 1),))
    assert monitor.available(tmp_path)
    assert not monitor.available(tmp_path / "nowhere")


def test_short_sizes():
    assert monitor.short_size(512 * 1024) == "512K"
    assert monitor.short_size(900 << 20) == "900M"
    assert monitor.short_size(int(12.5 * (1 << 30))) == "12.5G"
    assert monitor.short_size(3 << 40) == "3.0T"


# -- the layout -------------------------------------------------------------------------


@pytest.mark.parametrize(("count", "width", "expected"), [
    (2, 72, (1, 2)),
    (16, 72, (2, 8)),
    (16, 200, (2, 8)),
    (64, 200, (7, 10)),
    (128, 72, (2, 64)),
    (128, 200, (7, 19)),
])
def test_cpu_columns_keep_eight_rows_where_the_width_allows(count, width, expected):
    columns, rows, bar = cpu_layout(count, True, width)
    assert (columns, rows) == expected
    assert bar >= 8


def test_sensor_rows_put_each_chip_over_its_readings():
    chip = Chip("k10temp", "", (Temperature("Tctl", 50.0),), (Fan("fan1", 900),))
    rows = sensor_rows([chip])
    assert [row.reading for row in rows] == [None, chip.temperatures[0], chip.fans[0]]


# -- the window ------------------------------------------------------------------------------


def snapshot(cores: int = 4, chips: tuple[Chip, ...] = ()) -> Snapshot:
    return Snapshot(Cpu(-1, 25.0), tuple(Cpu(n, n * 10.0 % 100, 3000.0) for n in range(cores)),
                    Memory(32 << 30, 20 << 30, 0, 8 << 30, 8 << 30, 24 << 30, 30 << 30), chips)


CHIP = Chip("k10temp", "", (Temperature("Tctl", 48.0), Temperature("Tccd1", 95.0, 70.0, 90.0)))
NVME = Chip("nvme", "", (Temperature("Composite", 31.0, 75.0, 80.0),))


def monitor_run(where, monkeypatch, snapshots, *actions, size=(100, 40)):
    from test_nav import navigator

    from navigator.settings import SETTINGS
    from navigator.widgets.shell.monitor_window import monitor_window

    queue = list(snapshots)
    monkeypatch.setattr(monitor.Monitor, "__call__", lambda self: queue.pop(0) if len(queue) > 1 else queue[0])
    monkeypatch.setattr(monitor_window, "processors", lambda: 4)
    monkeypatch.setattr(SETTINGS.monitor, "refresh", 0)
    app = navigator(where, size=size)

    def open_it(a):
        from navigator.widgets.shell.commands import OpenMonitorWindow

        a.spawn(a.run_command(OpenMonitorWindow))

    def read(a):
        # ``_shape`` is set in the read's callback, which posts the wake-up that
        # runs the effects filling the meters (the sensors' rows among them):
        # not busy is once that batch is handled and painted.
        window = a.shell.desktop.active_window
        return getattr(window, "cpu", None) is not None and window._shape is not None and not a.busy

    run_app(app, [open_it, Until(read), *actions, lambda a: None])
    return app


def window_of(a):
    return a.shell.desktop.active_window


def screen(a, width=100, height=40) -> list[str]:
    buffer = ScreenBuffer(width, height)
    a.root.render_tree(buffer)
    return ["".join(buffer.get(x, y)[0] or " " for x in range(width)) for y in range(height)]


def test_the_window_opens_at_the_size_its_content_needs(tmp_path, monkeypatch):
    seen = []

    def look(a):
        window = window_of(a)
        seen.append(((window.x, window.y, window.width, window.height), window.heights, screen(a),
                     a.shell.desktop.height))

    monitor_run(tmp_path, monkeypatch, [snapshot(4, (CHIP,))], look)
    (x, y, width, height), heights, lines, desktop_height = seen[0]
    # Four processors in one column under the line for all of them; three memory lines; a chip and its two.
    assert heights == (4 + 1 + 2, 5, 3 + 2)
    assert height == 2 + sum(heights)
    assert (x, y) == ((100 - width) // 2, (desktop_height - height) // 2)
    text = "\n".join(lines)
    for words in ("System monitor", "CPU", "Memory", "Virtual", "Swap", "Sensors", "k10temp", "Tctl", "48°C",
                  "(high 70°C, critical 90°C)", "3.0G", "12.0G of 32.0G"):
        assert words in text, text


def test_more_processors_take_columns_and_a_new_sensor_grows_the_window(tmp_path, monkeypatch):
    seen = []
    look = lambda a: seen.append((window_of(a).width, window_of(a).height, window_of(a).cpu.layout[:2]))  # noqa: E731
    monitor_run(tmp_path, monkeypatch, [snapshot(16, (CHIP,)), snapshot(16, (CHIP, NVME))], look,
                KeyEvent("r", ctrl=True), look)
    (w1, h1, layout), (w2, h2, _) = seen
    assert layout == (2, 8)
    assert w2 >= w1
    assert h2 == h1 + 2


def test_once_the_user_has_resized_the_window_it_is_no_longer_refitted(tmp_path, monkeypatch):
    seen = []

    look = lambda a: seen.append((window_of(a).width, window_of(a).height))  # noqa: E731
    monitor_run(tmp_path, monkeypatch, [snapshot(4, (CHIP,)), snapshot(4, (CHIP, NVME))],
                lambda a: window_of(a).resize_to(70, 18), look, KeyEvent("r", ctrl=True), look)
    assert seen == [(70, 18), (70, 18)]


def test_a_short_screen_scrolls_the_processors_and_esc_closes_the_window(tmp_path, monkeypatch):
    seen = []

    def look(a):
        window = window_of(a)
        seen.append((window.height - a.shell.desktop.height, len(window.cpu.items), window.cpu.rows,
                     window.cpu.scroll, type(window).__name__))

    monitor_run(tmp_path, monkeypatch, [snapshot(128, (CHIP,))], look, KeyEvent("pagedown"), look,
                KeyEvent("escape"), lambda a: seen.append(type(window_of(a)).__name__), size=(80, 25))
    (short, items, rows, scroll, name), (_, _, _, scrolled, _), closed = seen
    assert short == 0
    assert items == 64 and rows < items and scroll == 0
    assert scrolled == rows - 1
    assert name == "MonitorWindow" and closed != "MonitorWindow"


def test_a_hot_sensor_a_warm_one_and_a_busy_bar_are_coloured_apart(tmp_path, monkeypatch):
    seen = []

    def look(a):
        window = window_of(a)
        rows = window.sensors.items
        styles = [window.sensors.row_style(index, row) for index, row in enumerate(rows)]
        seen.append((styles, window.cpu.part_style("done"), window.cpu.part_style("done", classes=("busy",)),
                     window.cpu.style))

    hot = Chip("k10temp", "", (Temperature("a", 40.0, 70.0, 90.0), Temperature("b", 75.0, 70.0, 90.0),
                               Temperature("c", 95.0, 70.0, 90.0)))
    # The rows are filled by an effect the read's wake-up runs, which can come
    # a batch after ``monitor_run``'s wait on a slow machine: wait for them.
    monitor_run(tmp_path, monkeypatch, [snapshot(4, (hot,))],
                Until(lambda a: len(window_of(a).sensors.items) >= 4), look)
    (heading, normal, warm, hot_style), done, busy, base = seen[0]
    assert len({heading, normal, warm, hot_style}) == 4
    assert done != busy
    assert base.bg == normal.bg
