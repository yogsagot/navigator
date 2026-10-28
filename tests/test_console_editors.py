"""Alt+F4's console editors (navigator/lib/editor/console_editors.py), and the box Alt+F4 offers them in."""

from __future__ import annotations

import shlex
from pathlib import Path

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.lib.config import associations
from navigator.lib.config.associations import EDITORS
from navigator.lib.editor import console_editors
from navigator.lib.editor.console_editors import actions, installed
from navml.widgets.dialog.control.control import parse_shortcut
from navml.widgets.menu.popup_menu import PopupMenu


def programs(tmp_path: Path, *names: str) -> dict[str, str]:
    """A ``bin`` of empty programs called *names*; a ``name=target`` one is a link."""
    found = {}
    for name in names:
        name, _, target = name.partition("=")
        path = tmp_path / name
        if target:
            path.symlink_to(tmp_path / target)
        else:
            path.write_text("")
        found[name] = str(path)
    return found


def test_the_environments_editors_come_first_then_the_known_ones_installed(tmp_path):
    found = programs(tmp_path, "nano", "mcedit", "vim", "emacs")
    which = found.get
    assert installed(which, {"EDITOR": "vim -u NONE"}) == [
        ("vim -u NONE", "vim -u NONE"), ("N~a~no", "nano"), ("~M~cedit", "mcedit"), ("~E~macs", "emacs -nw"),
    ]
    assert installed(which, {"VISUAL": "nano", "EDITOR": "~/bin/ed"}) == [
        ("nano", "nano"), ("~V~im", "vim"), ("~M~cedit", "mcedit"), ("~E~macs", "emacs -nw"),
    ]


def test_an_editor_that_is_another_ones_link_is_offered_once(tmp_path):
    found = programs(tmp_path, "vim", "vi=vim", "nano")
    assert installed(found.get, {"EDITOR": "vi"}) == [("vi", "vi"), ("N~a~no", "nano")]
    assert installed(found.get, {}) == [("~V~im", "vim"), ("N~a~no", "nano")]


def test_nothing_installed_is_nothing_offered():
    assert installed(lambda name: None, {"EDITOR": "vim"}) == []


def test_each_runs_on_the_file_in_a_window_that_closes_and_the_shells_characters_are_kept():
    nano, odd = actions([("N~a~no", "nano"), ("$E", "ed -p '!$%'")])
    assert nano.commands.window.closes and nano.commands.lines == ["nano !.!"]
    assert odd.commands.lines == ["ed -p '!!$$%%' !.!"]


def test_the_known_editors_hotkeys_are_distinct_and_leave_the_internal_editors_alone():
    letters = [parse_shortcut(caption)[2] for caption, _ in console_editors.KNOWN]
    assert len(set(letters)) == len(letters) and "i" not in letters and "" not in letters


# -- Alt+F4 ------------------------------------------------------------------------


def navigator(place: Path) -> Navigator:
    path = associations.path_of(EDITORS)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("[*.odt]\nWriter = lowriter !.!\n")
    return Navigator(place, place, terminal=FakeTerminal(80, 24))


def to(name):
    def action(app):
        panel = app.manager.left
        panel.cursor = [e.name for e in panel.items].index(name)
    return action


def popup(app) -> PopupMenu | None:
    return next((child for child in app.root.children if isinstance(child, PopupMenu)), None)


def capture(app, ran: list[tuple[str, dict]]):
    app.shell.run_in_window = lambda command, **options: ran.append((command, options))


def editor_windows(app) -> int:
    from navigator.widgets.editor.edit_window import EditWindow

    return sum(isinstance(window, EditWindow) for window in app.shell.desktop.windows())


def test_alt_f4_offers_the_console_editors_and_runs_the_one_chosen_in_a_window(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("a")
    monkeypatch.setattr(console_editors, "installed", lambda: [("N~a~no", "nano")])
    app = navigator(tmp_path)
    ran: list[tuple[str, dict]] = []
    seen = {}

    def look(a):
        seen["captions"] = [parse_shortcut(entry.text)[0] for entry in popup(a).box.entries()]
        seen["title"] = popup(a).box.title

    run_app(app, [lambda a: capture(a, ran), to("a.txt"), KeyEvent("f4", alt=True),
                  Until(lambda a: popup(a) is not None), look, KeyEvent("enter"), Until(lambda a: ran)])
    assert seen == {"captions": ["Nano", "Internal editor"], "title": "Choose editor"}
    command, options = ran[0]
    assert command.startswith(". ")
    assert Path(shlex.split(command[2:])[0]).read_text() == "nano a.txt\n"
    assert options["zoomed"] is None and options["modal"] is None and options["closes"]


def test_alt_f4_s_internal_editor_and_no_console_editor_open_the_editor_window(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("a")
    monkeypatch.setattr(console_editors, "installed", lambda: [("N~a~no", "nano")])
    app = navigator(tmp_path)
    seen = {}
    run_app(app, [to("a.txt"), KeyEvent("f4", alt=True), Until(lambda a: popup(a) is not None),
                  KeyEvent("down"), KeyEvent("enter"), Until(lambda a: editor_windows(a) == 1),
                  lambda a: seen.update(windows=editor_windows(a))])
    assert seen["windows"] == 1

    monkeypatch.setattr(console_editors, "installed", lambda: [])
    app = navigator(tmp_path)
    seen.clear()
    run_app(app, [to("a.txt"), KeyEvent("f4", alt=True), Until(lambda a: editor_windows(a) == 1),
                  lambda a: seen.update(popup=popup(a))])
    assert seen["popup"] is None


def test_editors_ini_still_wins_over_the_console_editors(tmp_path, monkeypatch):
    (tmp_path / "c.odt").write_text("c")
    monkeypatch.setattr(console_editors, "installed", lambda: [("N~a~no", "nano")])
    app = navigator(tmp_path)
    ran: list[str] = []
    app.shell.run_command = lambda command, typed=True: ran.append(command)
    run_app(app, [to("c.odt"), KeyEvent("f4", alt=True), Until(lambda a: ran)])
    assert Path(shlex.split(ran[0][2:])[0]).read_text() == "lowriter c.odt\n"


def test_ctrl_k_is_alternate_edit_too_as_alt_f4_may_close_the_terminal(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("a")
    monkeypatch.setattr(console_editors, "installed", lambda: [("N~a~no", "nano")])
    app = navigator(tmp_path)
    seen = {}
    run_app(app, [to("a.txt"), KeyEvent("k", ctrl=True), Until(lambda a: popup(a) is not None),
                  lambda a: seen.update(title=popup(a).box.title), KeyEvent("escape")])
    assert seen["title"] == "Choose editor"
