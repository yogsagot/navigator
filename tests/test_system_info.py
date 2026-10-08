"""Utilities > System Information: DN's ``SystemInfo``, read for Linux."""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app

from navigator.__main__ import Navigator
from navigator.sysinfo import SystemFacts, gather, lines, size_text


@pytest.fixture
def root(tmp_path) -> Path:
    def put(path: str, text: str) -> None:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)

    put("sys/class/dmi/id/sys_vendor", "ACME\n")
    put("sys/class/dmi/id/product_name", "Box 9000\n")
    put("proc/cpuinfo", "processor : 0\nmodel name : Fast CPU\nprocessor : 1\nmodel name : Fast CPU\n")
    put("sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq", "3600000\n")
    put("sys/block/sda/size", str(2 * 1024 * 1024 * 1024 // 512 * 100) + "\n")  # 200G
    put("sys/block/sda/device/model", "DISK ONE  \n")
    put("sys/block/sdb/size", str(16 * 1024 * 1024 // 512 * 1024) + "\n")  # 16G
    put("sys/block/sdb/removable", "1\n")
    put("sys/block/loop0/size", "100\n")
    put("sys/block/sr0/size", "0\n")
    put("proc/meminfo", "MemTotal: 16777216 kB\nMemAvailable: 8388608 kB\nSwapTotal: 0 kB\n")
    put("etc/os-release", 'NAME="Test"\nPRETTY_NAME="Test OS 1.0"\n')
    put("proc/sys/kernel/osrelease", "6.1.0-test\n")
    put("proc/sys/kernel/hostname", "box\n")
    put("proc/uptime", "90061.5 0\n")
    return tmp_path


def test_the_four_boxes_from_proc_and_sys(root):
    facts = gather(root)
    assert facts.board[:2] == [("Machine type", "ACME Box 9000"), ("CPU", "Fast CPU 3600 MHz")]
    assert facts.board[2] == ("CPUs", "2")
    assert facts.disks == [("sda", "200G, DISK ONE"), ("sdb", "16G, removable")]
    assert facts.memory == [("Total", "16G"), ("Available", "8,192M"), ("Swap", "0K")]
    assert facts.other[0] == ("OS", "Test OS 1.0") and facts.other[1][1].startswith("6.1.0-test")
    assert ("Host", "box") in facts.other and ("Up", "1d 1:01") in facts.other


def test_the_boxes_text_and_sizes():
    assert lines([("Total", "16G"), ("Available", "8G")], 40) == "    Total : 16G\nAvailable : 8G"
    assert lines([], 40) == " None"
    assert lines([("OS", "x" * 50)], 20).endswith("...")
    cut = lines([("OS", "x" * 50)], 20, "\u2026")
    assert len(cut) == 20 and cut.endswith("x\u2026")
    assert size_text(512 * 1024) == "512K" and size_text(20 << 20) == "20M" and size_text(12 << 30) == "12G"


def test_a_missing_root_reads_as_little_as_there_is(tmp_path):
    facts = gather(tmp_path)
    assert facts.disks == [] and facts.memory == []
    assert facts.board[0][0] == "Machine type"


def test_the_menu_opens_the_dialog_on_what_was_read(tmp_path, monkeypatch, root):
    from navigator.widgets.shell.commands import SystemInfo

    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setattr("navigator.sysinfo.gather", lambda: gather(root))
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 25))
    seen = {}
    run_app(app, [lambda a: a.spawn(a.run_command(SystemInfo)), Until(lambda a: a.modal is not None),
                  lambda a: seen.update(title=a.modal.title, memory=a.modal.memory.text)])
    assert seen["title"] == "System Information"
    assert seen["memory"].splitlines()[0] == "    Total : 16G"


@pytest.mark.parametrize("ascii", [False, True])
def test_a_value_too_long_for_its_box_ends_in_the_tiers_ellipsis(ascii):
    from dataclasses import replace

    from conftest import FULL
    from navkit.application import Application
    from navkit.glyphs import GLYPHS_ASCII, GLYPHS_UNICODE
    from navkit.widget import Widget
    from navigator.widgets.shell.system_info_dialog import SystemInfoDialog

    info = replace(FULL, glyphs=GLYPHS_ASCII if ascii else GLYPHS_UNICODE)
    app = Application(Widget(), terminal=FakeTerminal(80, 25, info=info))
    dialog = SystemInfoDialog(SystemFacts(other=[("OS", "x" * 200)]))
    seen = {}
    run_app(app, [lambda a: a.spawn(dialog.execute(a)), Until(lambda a: a.modal is dialog),
                  lambda a: seen.update(text=dialog.other.text), lambda a: dialog.close()])
    assert seen["text"].endswith("x..." if ascii else "x\u2026")
