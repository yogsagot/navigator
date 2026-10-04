"""Ctrl+F9 in the file manager: DN's ``CM_Print`` -> ``PrintFiles`` (FLTOOLS.PAS, GAUGES.PAS)."""

from __future__ import annotations

import subprocess

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent

from navigator import printing
from navigator.__main__ import Navigator


@pytest.fixture
def tree(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    return tmp_path


@pytest.fixture
def spooler(monkeypatch):
    jobs = []
    answer = {"code": 0, "stderr": b""}

    def run(argv, input=None, **kwargs):
        jobs.append(argv)
        return subprocess.CompletedProcess(argv, answer["code"], b"", answer["stderr"])

    monkeypatch.setattr(printing.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(printing.subprocess, "run", run)
    return jobs, answer


def on(app, name):
    panel = app.manager.left
    panel.cursor = next(i for i, e in enumerate(panel.items) if e.name == name)


def press_ctrl_f9(tree, *before, answer="y"):
    """Ctrl+F9 after *before*; what was asked, and the panel's tags after."""
    app = Navigator(tree, tree, terminal=FakeTerminal(80, 24))
    asked = []
    run_app(app, [*before, KeyEvent("f9", ctrl=True), lambda a: None,
                  lambda a: asked.append(a.modal.prompt if a.modal else None),
                  KeyEvent(answer, alt=True), lambda a: None, lambda a: None])
    return app, asked


def test_ctrl_f9_prints_the_file_under_the_cursor(tree, spooler):
    jobs, _ = spooler
    _, asked = press_ctrl_f9(tree, lambda a: on(a, "a.txt"))
    assert asked == ["Print file a.txt?"]
    assert jobs == [["lp", str(tree / "a.txt")]]


def test_ctrl_f9_prints_the_tagged_files_skipping_directories_and_untags_them(tree, spooler):
    jobs, _ = spooler

    def tag(a):
        a.manager.left.marked = frozenset({"a.txt", "b.txt", "sub"})

    app, asked = press_ctrl_f9(tree, tag)
    assert asked == ["Print 3 files?"]  # DN counted the directory too
    assert jobs == [["lp", str(tree / "a.txt")], ["lp", str(tree / "b.txt")]]
    assert app.manager.left.marked == {"sub"}


def test_no_prints_nothing(tree, spooler):
    jobs, _ = spooler
    press_ctrl_f9(tree, lambda a: on(a, "a.txt"), answer="n")
    assert jobs == []


def test_a_directory_alone_prints_nothing_and_asks_nothing(tree, spooler):
    jobs, _ = spooler
    _, asked = press_ctrl_f9(tree, lambda a: on(a, "sub"))
    assert asked == [None] and jobs == []


def test_a_refusing_spooler_stops_and_keeps_the_rest_tagged(tree, spooler):
    jobs, answer = spooler
    answer.update(code=1, stderr=b"lp: Error - No default destination.")
    said = []

    def tag(a):
        a.manager.left.marked = frozenset({"a.txt", "b.txt"})

    app = Navigator(tree, tree, terminal=FakeTerminal(80, 24))
    run_app(app, [tag, KeyEvent("f9", ctrl=True), lambda a: None, KeyEvent("y", alt=True),
                  lambda a: None, lambda a: None,
                  lambda a: said.append(a.modal.prompt if a.modal else None)])
    assert said == ["Cannot print a.txt: lp: Error - No default destination."]
    assert len(jobs) == 1 and app.manager.left.marked == {"a.txt", "b.txt"}
