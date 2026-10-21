"""Panel > Panelize command (Alt+Y): a command's output as a panel's listing."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.config.usermenu import commands_of
from navigator.lib.file_ops.filefind import list_from_lines
from navigator.lib.file_ops.panelize import PanelizeJob, capture, lines_of
from navigator.lib.system.job import Stopped
from navigator.widgets.manager.commands import Panelize, Rescan
from navigator.widgets.manager.panel.panel import entry_at


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setenv("SHELL", "/bin/sh")
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "one.txt").write_text("1")
    (tmp_path / "a" / "two.txt").write_text("2")
    (tmp_path / "top.txt").write_text("top")
    return tmp_path


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def keys(panel) -> list[str]:
    return [e.key for e in panel.items]


def listed(app) -> bool:
    return app.manager.left.found is not None and app.modal is None


# -- the model ---------------------------------------------------------------------------


def test_lines_and_nul_separated_output():
    assert lines_of("a\nb\n") == ["a", "b"]
    assert lines_of("a b\0c\0") == ["a b", "c", ""]


def test_list_from_lines_reads_names_as_a_list_file_does(place):
    entries = list_from_lines(["a/one.txt", "  top.txt ", "missing", "a/*.txt", ".."], place,
                              lambda p: entry_at(p, p.parent))
    assert [str(e.path_in(place).relative_to(place)) for e in entries] == ["a/one.txt", "top.txt", "a/two.txt"]


def test_capture_runs_in_the_directory_and_keeps_what_went_wrong(place):
    job = PanelizeJob()
    capture("ls a; echo oops >&2; exit 3", place, job)
    assert job.output.split() == ["one.txt", "two.txt"]
    assert job.errors.strip() == "oops" and job.status == 3


def test_stop_ends_a_long_command(place):
    job = PanelizeJob()
    threading.Timer(0.2, job.stop).start()
    began = time.monotonic()
    with pytest.raises(Stopped):
        capture("sleep 30", place, job)
    assert time.monotonic() - began < 5


def test_a_pipe_line_in_a_menu_item_panelizes_it():
    assert commands_of(["<|", "git ls-files"]).panelize
    assert commands_of(["<|", "<Title", "grep -l %3 ."]).title == "Title"
    assert not commands_of(["ls"]).panelize


# -- the command -------------------------------------------------------------------------


def test_alt_y_asks_and_lists_what_the_command_printed(place):
    app = navigator(place)
    seen = {}

    def type_command(a):
        seen["box"] = a.modal.title
        a.modal.line.value = "find a -name '*.txt' | sort"

    run_app(app, [KeyEvent("y", alt=True), Until(lambda a: a.modal is not None), type_command, KeyEvent("enter"),
                  Until(listed), lambda a: None,
                  lambda a: seen.update(items=keys(a.manager.left), title=a.manager.left.found.title,
                                        command=a.manager.left.found.command)])
    assert seen["box"] == "Panelize command"
    assert seen["items"] == ["..", str(place / "a" / "one.txt"), str(place / "a" / "two.txt")]
    assert seen["title"] == "Panel: find a -name '*.txt' | sort" and seen["command"] == "find a -name '*.txt' | sort"


def test_nothing_printed_says_so_with_the_error(place):
    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: a.spawn(a.manager.panelize(a.manager.left, "echo broken >&2; false")),
                  Until(lambda a: a.modal is not None and a.modal.title == "Error"),
                  lambda a: seen.update(prompt=a.modal.prompt, found=a.manager.left.found), KeyEvent("enter")])
    assert seen == {"prompt": "No files found\nbroken", "found": None}


def test_ctrl_r_runs_the_command_again(place):
    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: a.spawn(a.manager.panelize(a.manager.left, "ls a/*.txt")), Until(listed),
                  lambda a: (place / "a" / "three.txt").write_text("3"),
                  lambda a: a.spawn(a.run_command(Rescan)),
                  Until(lambda a: len(a.manager.left.items) == 4), lambda a: None,
                  lambda a: seen.update(items=keys(a.manager.left))])
    assert seen["items"] == ["..", *(str(place / "a" / n) for n in ("one.txt", "three.txt", "two.txt"))]


def test_a_pipe_on_the_command_line_panelizes_instead_of_running(place):
    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: a.shell.run_command("| echo top.txt"), Until(listed), lambda a: None,
                  lambda a: seen.update(items=keys(a.manager.left), console=a.shell.console_visible)])
    assert seen == {"items": ["..", str(place / "top.txt")], "console": False}


def test_a_menu_item_with_a_pipe_line_panelizes(place):
    app = navigator(place)
    seen = {}
    item = commands_of(["<|", "printf 'a/two.txt\\n'"])
    run_app(app, [lambda a: a.spawn(a.shell.run_commands(item)), Until(listed), lambda a: None,
                  lambda a: seen.update(items=keys(a.manager.left))])
    assert seen["items"] == ["..", str(place / "a" / "two.txt")]


def test_panelize_is_off_away_from_the_disk(place):
    from navigator.lib.drives import mount, unmount
    from navigator.lib.drives.memory import MemoryDrive

    drive = mount(MemoryDrive("panelize"))
    drive.make("/work/a.txt", "alpha")
    app = navigator(place)
    seen = {}
    try:
        run_app(app, [lambda a: seen.update(disk=a.command_enabled(Panelize())),
                      lambda a: setattr(a.manager.left, "location", drive.location("/work")),
                      Until(lambda a: "a.txt" in [e.name for e in a.manager.left.items]),
                      lambda a: seen.update(memory=a.command_enabled(Panelize()))])
    finally:
        unmount(drive.site)
    assert seen == {"disk": True, "memory": False}
