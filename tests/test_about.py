"""≡ > About: what it says, where that comes from, and that it opens."""

from __future__ import annotations

import tomllib
from email.message import Message

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent
from navigator import __version__, about
from navigator.__main__ import Navigator
from navigator.about import ProjectInfo, about_text, project_info
from navigator.widgets.about_dialog import AboutDialog


@pytest.fixture(autouse=True)
def fresh_info():
    project_info.cache_clear()
    yield
    project_info.cache_clear()


def test_a_checkout_reads_pyproject_toml():
    project = tomllib.loads(about.PYPROJECT.read_text(encoding="utf-8"))["project"]
    info = project_info()
    assert info.version == __version__
    assert info.summary == project["description"]
    assert info.license == project["license"]
    assert (info.author, info.email) == (project["authors"][0]["name"], project["authors"][0]["email"])
    assert info.homepage == project["urls"]["Homepage"]


def test_an_installed_copy_reads_the_metadata(monkeypatch, tmp_path):
    """No pyproject.toml beside the package: the same table, compiled into METADATA."""
    meta = Message()
    meta["Version"] = "9.9.9"
    meta["Summary"] = "A summary"
    meta["License-Expression"] = "MIT"
    meta["Author-email"] = '"Ada Lovelace" <ada@example.org>'
    meta["Project-URL"] = "Repository, https://example.org/repo"
    meta["Project-URL"] = "Homepage, https://example.org"
    monkeypatch.setattr(about, "PYPROJECT", tmp_path / "pyproject.toml")
    monkeypatch.setattr(about.metadata, "metadata", lambda name: meta)
    assert project_info() == ProjectInfo(
        version="9.9.9",
        summary="A summary",
        license="MIT",
        author="Ada Lovelace",
        email="ada@example.org",
        homepage="https://example.org",
    )


def test_somebody_elses_pyproject_is_not_ours(monkeypatch, tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "other"\ndescription = "no"\n')
    monkeypatch.setattr(about, "PYPROJECT", tmp_path / "pyproject.toml")

    def missing(name):
        raise about.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(about.metadata, "metadata", missing)
    assert project_info() == ProjectInfo(version=__version__)


def test_the_text_leaves_out_what_is_missing():
    assert about_text(ProjectInfo(version="1.0")) == "Navigator\nVersion 1.0"
    assert about_text(ProjectInfo(version="1.0", license="MIT", homepage="https://x")) == (
        "Navigator\nVersion 1.0\n\nLicense: MIT\n\nhttps://x"
    )


def test_the_about_entry_opens_the_dialog_and_enter_closes_it(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.widgets.console.Console.start", lambda self, argv=None: None)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []
    run_app(app, [
        KeyEvent("f10"),
        KeyEvent("enter"),   # the ≡ menu
        KeyEvent("a", "a"),  # ~A~bout...
        lambda a: None,
        lambda a: seen.append(a.modal),
        KeyEvent("enter"),
        lambda a: None,
        lambda a: seen.append(a.modal),
    ])
    dialog, after = seen
    assert isinstance(dialog, AboutDialog)
    assert f"Version {project_info().version}" in dialog.message.text
    assert dialog.message.align == "center"
    assert after is None


def test_the_home_page_is_a_link(tmp_path, monkeypatch):
    from navkit.screen import ScreenBuffer

    monkeypatch.setattr("navigator.widgets.console.Console.start", lambda self, argv=None: None)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    homepage = project_info().homepage
    links = []

    def look(a):
        buffer = ScreenBuffer(80, 24)
        a.shell.render_tree(buffer)
        links.extend(
            {buffer.get(x, y)[1].link for x in range(80)} - {None} for y in range(24)
        )

    run_app(app, [KeyEvent("f10"), KeyEvent("enter"), KeyEvent("a", "a"),
                  lambda a: None, look])
    assert [row for row in links if row] == [{homepage}]
