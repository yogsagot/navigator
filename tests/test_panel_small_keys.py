"""The smaller panel keys, as DN's ``TFilePanel`` had them."""

from __future__ import annotations

import zipfile

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    here = tmp_path / "here"
    here.mkdir()
    with zipfile.ZipFile(here / "pack.zip", "w") as zipped:
        zipped.writestr("inside.txt", "x")
    for n in range(100):
        (here / f"f{n:03}.txt").write_text("x")
    (here / ("long" * 30 + ".txt")).write_text("x")
    return tmp_path


def app_in(place, **kw):
    return Navigator(place / "here", place / "here", terminal=FakeTerminal(100, 30), **kw)


# a -- Shift+Backspace under *BS upper dir*

@pytest.mark.parametrize("bs_on, goes_up", [(True, True), (False, False)])
def test_shift_backspace_follows_bs_upper_dir(place, monkeypatch, bs_on, goes_up):
    monkeypatch.setattr(SETTINGS.file_manager, "bs_upper_dir", bs_on)
    app = app_in(place)
    run_app(app, [KeyEvent("backspace", shift=True), lambda a: None, lambda a: None])
    assert (app.manager.left.path == place) is goes_up


def test_ctrl_pageup_goes_up_whatever_bs_upper_dir_says(place, monkeypatch):
    monkeypatch.setattr(SETTINGS.file_manager, "bs_upper_dir", False)
    app = app_in(place)
    run_app(app, [KeyEvent("pageup", ctrl=True), lambda a: None, lambda a: None])
    assert app.manager.left.path == place


# b -- Home scrolls the names back

def test_home_resets_the_name_scroll(place):
    app = app_in(place)
    seen = {}

    def scrolled(a):
        a.manager.left.name_scroll = 3

    run_app(app, [KeyEvent("end"), scrolled, KeyEvent("home"), lambda a: None,
                  lambda a: seen.update(scroll=a.manager.left.name_scroll, cursor=a.manager.left.cursor)])
    assert seen == {"scroll": 0, "cursor": 0}


# c -- a page is the whole view

@pytest.mark.parametrize("mode", ["detailed", "list"])
def test_page_down_steps_the_whole_view(place, mode):
    app = app_in(place)
    seen = {}

    def go(a):
        a.manager.left.view_mode = mode

    run_app(app, [go, lambda a: None, KeyEvent("home"), KeyEvent("pagedown"), lambda a: None,
                  lambda a: seen.update(cursor=a.manager.left.cursor, page=a.manager.left.capacity)])
    assert seen["cursor"] == seen["page"]


# d -- Shift+Enter on a file: no archive test

def test_shift_enter_on_an_archive_runs_it_as_a_file_and_enter_enters_it(place, monkeypatch):
    from navigator.widgets.manager.panel.panel import Panel

    monkeypatch.setattr(SETTINGS.file_manager, "enter_opens_archive", True)
    ran = []

    async def run_file(self, entry):
        ran.append(entry.name)

    monkeypatch.setattr(Panel, "_run_file", run_file)
    app = app_in(place)

    def on_zip(a):
        panel = a.manager.left
        panel.cursor = [e.name for e in panel.items].index("pack.zip")

    seen = {}
    run_app(app, [on_zip, KeyEvent("enter", shift=True), lambda a: None,
                  lambda a: seen.update(after_shift=a.manager.left.location.outer),
                  KeyEvent("enter"), Until(lambda a: a.manager.left.location.outer is not None)])
    assert ran == ["pack.zip"] and seen["after_shift"] is None


def test_shift_enter_with_text_on_the_line_still_runs_the_line_in_a_window(place):
    from navigator.widgets.manager.commands import EnterWithoutArchive

    app = app_in(place)
    seen = {}
    run_app(app, [*[KeyEvent(c, c) for c in "ls"],
                  lambda a: seen.update(why=a.manager.refusal(EnterWithoutArchive()))])
    assert seen["why"] == "The command line holds text: the key edits it"
