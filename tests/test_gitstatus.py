"""Git status in the panels: a letter per entry, the branch in the title
(navigator.lib.system.gitstatus, Panel.git)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.screen import ScreenBuffer

from navigator.__main__ import Navigator
from navigator.lib.system import gitstatus
from navigator.lib.system.gitstatus import GitState
from navigator.settings import SETTINGS

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="needs git")


@pytest.fixture(autouse=True)
def _plain_git(monkeypatch, tmp_path):
    """No user's configuration, and an author for the commits."""
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for who in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{who}_NAME", "Test")
        monkeypatch.setenv(f"GIT_{who}_EMAIL", "test@example.com")


def git(where: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(where), *args], check=True,
                          capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path) -> Path:
    """A repository on ``main`` with one commit: ``kept``, ``changed``,
    ``gone``, ``old``, ``src/deep/inner.c`` and a ``.gitignore``."""
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    for name in ("kept", "changed", "gone", "old"):
        (root / name).write_text(f"{name}\n")
    (root / "src" / "deep").mkdir(parents=True)
    (root / "src" / "deep" / "inner.c").write_text("int x;\n")
    (root / ".gitignore").write_text("*.log\nbuild/\n")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "one")
    return root


def test_outside_a_work_tree_there_is_nothing(tmp_path):
    assert gitstatus.read(tmp_path) is None


def test_inside_the_git_directory_there_is_nothing(repo):
    assert gitstatus.read(repo / ".git") is None


def test_a_clean_tree_names_its_branch_and_marks_nothing(repo):
    state = gitstatus.read(repo)
    assert state == GitState("main", False, 0, 0, (repo / ".git").resolve(), {})


def test_each_kind_of_change_has_its_letter(repo):
    (repo / "changed").write_text("more\n")
    (repo / "gone").unlink()
    git(repo, "mv", "old", "new")
    (repo / "added").write_text("a\n")
    git(repo, "add", "added")
    (repo / "loose").write_text("?\n")
    (repo / "noise.log").write_text("!\n")
    (repo / "build").mkdir()
    (repo / "build" / "out.o").write_text("!\n")
    marks = gitstatus.read(repo).marks
    assert marks == {"changed": "M", "gone": "D", "new": "R", "added": "A",
                     "loose": "?", "noise.log": "!", "build": "!"}


def test_a_directory_takes_the_strongest_letter_beneath_it(repo):
    (repo / "src" / "deep" / "inner.c").write_text("int y;\n")
    (repo / "src" / "fresh.c").write_text("new\n")
    (repo / "src" / "trace.log").write_text("ignored, says nothing of src\n")
    assert gitstatus.read(repo).marks == {"src": "M"}


def test_a_subdirectory_is_read_by_its_own_names(repo):
    (repo / "src" / "deep" / "inner.c").write_text("int y;\n")
    (repo / "changed").write_text("not in src\n")
    assert gitstatus.read(repo / "src").marks == {"deep": "M"}
    assert gitstatus.read(repo / "src" / "deep").marks == {"inner.c": "M"}


def test_odd_names_survive(repo):
    (repo / "two words").write_text("x\n")
    (repo / "line\nbreak").write_text("x\n")
    marks = gitstatus.read(repo).marks
    assert marks["two words"] == "?" and marks["line\nbreak"] == "?"


def test_a_conflict_is_u(repo):
    git(repo, "checkout", "-q", "-b", "other")
    (repo / "changed").write_text("theirs\n")
    git(repo, "commit", "-q", "-am", "theirs")
    git(repo, "checkout", "-q", "main")
    (repo / "changed").write_text("ours\n")
    git(repo, "commit", "-q", "-am", "ours")
    subprocess.run(["git", "-C", str(repo), "merge", "-q", "other"], capture_output=True)
    assert gitstatus.read(repo).marks["changed"] == "U"


def test_a_detached_head_is_named_by_its_commit(repo):
    head = git(repo, "rev-parse", "HEAD").strip()
    git(repo, "checkout", "-q", "--detach")
    state = gitstatus.read(repo)
    assert state.detached and state.branch == head[:7]


def test_ahead_and_behind_its_upstream(repo, tmp_path):
    clone = tmp_path / "clone"
    git(tmp_path, "clone", "-q", str(repo), str(clone))
    (repo / "kept").write_text("upstream moved\n")
    git(repo, "commit", "-q", "-am", "up")
    git(clone, "fetch", "-q")
    (clone / "changed").write_text("mine\n")
    git(clone, "commit", "-q", "-am", "mine")
    (clone / "gone").write_text("mine too\n")
    git(clone, "commit", "-q", "-am", "mine too")
    state = gitstatus.read(clone)
    assert (state.branch, state.ahead, state.behind) == ("main", 2, 1)


# -- the panel ---------------------------------------------------------------


@pytest.fixture
def no_shell(monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)


def row_of(panel, name: str) -> str:
    buffer = ScreenBuffer(panel.width, panel.height)
    panel.render(buffer)
    index = [entry.name for entry in panel.items].index(name)
    y = panel.inset + panel.header + index - panel.scroll
    return "".join(buffer.get(x, y)[0] or " " for x in range(panel.width))


def test_the_panel_marks_its_rows_and_names_the_branch(repo, tmp_path, no_shell):
    (repo / "changed").write_text("more\n")
    clone = tmp_path / "clone"
    git(tmp_path, "clone", "-q", str(repo), str(clone))
    (clone / "changed").write_text("ahead\n")
    git(clone, "commit", "-q", "-am", "ahead")
    (clone / "kept").write_text("edited\n")
    seen = {}

    def look(app):
        panel = app.manager.left
        seen["kept"] = row_of(panel, "kept")
        seen["changed"] = row_of(panel, "changed")
        seen["title"] = panel.title_text()

    app = Navigator(clone, tmp_path, terminal=FakeTerminal(100, 30))
    run_app(app, [Until(lambda a: a.manager.left.git is not None), look])
    # The cursor bar is on ``..``; ``kept`` is painted with its letter at the
    # end of the name's cells, a blank after it, ``changed`` (committed,
    # clean) with none.
    name_end = 1 + app.manager.left.name_width - 2
    assert seen["kept"][name_end] == "M"
    assert seen["changed"][name_end] == " "
    assert "main ↑1" in seen["title"]


def test_with_git_status_off_there_is_neither(repo, tmp_path, no_shell):
    SETTINGS.file_manager.git_status = False
    (repo / "kept").write_text("edited\n")
    seen = {}

    def look(app):
        seen["git"] = app.manager.left.git
        seen["title"] = app.manager.left.title_text()

    run_app(Navigator(repo, tmp_path, terminal=FakeTerminal(100, 30)), [look])
    assert seen["git"] is None and "main" not in seen["title"]


def test_a_change_in_the_git_directory_alone_reads_again(repo, tmp_path, no_shell):
    # ``git add`` writes the index and nothing in the directory shown: only
    # the watch on ``.git`` hears it.
    (repo / "fresh").write_text("new\n")

    def stage(app):
        git(repo, "add", "fresh")

    def mark(app):
        git_state = app.manager.left.git
        return git_state.marks.get("fresh") if git_state is not None else None

    run_app(Navigator(repo, tmp_path, terminal=FakeTerminal(100, 30)), [
        Until(lambda a: mark(a) == "?"),
        stage,
        Until(lambda a: mark(a) == "A", timeout=3.0),
    ])
