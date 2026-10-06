"""F2's user menu: ``dn.mnu`` (USERMENU.PAS), its macros, and running an item."""

from __future__ import annotations

import os
import shlex
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.__main__ import Navigator
from navigator.settings import SETTINGS
from navigator.usermenu import Side, caption, expand, find_menu, parse, script_text
from navml.widgets.dialog.control.control import parse_shortcut
from navml.widgets.menu.popup_menu import PopupMenu

SAMPLE = """\
; DN's example, and then some
>1 ~W~indows
    win
>1
>1 ~F~ormat
  >2 1.4~4~ Mb
    format a: /f:1440
  >2 ~D~efine...
    <Format what
    <=format a:
    %3 %4
>>1 F5 ~E~dit !.!
    ; open it
    vi !\\!.!

    cp %1 $\\ %%3 $$HOME
"""


def test_items_nest_by_level_and_a_bare_level_is_a_line():
    menu = parse(SAMPLE)
    top = menu.items
    assert [e.caption for e in top] == ["~W~indows", "", "~F~ormat", "F5 ~E~dit !.!"]
    assert top[1].is_line and not top[0].is_line
    assert [e.caption for e in top[2].children] == ["1.4~4~ Mb", "~D~efine..."]
    assert top[3].fkey == "f5" and top[0].fkey is None
    assert parse(">x nothing\n>0 nor this\n>2 deep\n").items[0].caption == "deep"


def test_an_items_lines_run_to_the_next_item_and_say_whether_to_ask():
    menu = parse(SAMPLE)
    windows, _, fmt, edit = menu.items
    assert menu.commands(windows).lines == ["win"] and not menu.commands(windows).asks
    assert menu.commands(fmt).lines == []
    define = menu.commands(fmt.children[1])
    assert define.asks and define.title == "Format what" and define.default == "format a:"
    assert define.lines == ["%3 %4"]
    # Comments and blank lines go; %%3 is a literal, not a parameter.
    assert menu.commands(edit).lines == ["vi !\\!.!", "cp %1 $\\ %%3 $$HOME"]
    assert not menu.commands(edit).asks
    assert parse(">1 x\n  echo %3\n").commands(parse(">1 x\n  echo %3\n").items[0]).asks


ACTIVE = Side.of(Path("/home/me/my dir"), "read me.txt", "/tmp/a.lst")
PASSIVE = Side.of(Path("/"), "archive.tar.gz", "-")


def test_the_macros_are_dns_and_quoted_only_where_a_name_needs_it():
    assert expand("!.!", ACTIVE, PASSIVE) == "'read me'.txt"
    assert expand("!\\!.!", ACTIVE, PASSIVE) == "'/home/me/my dir/''read me'.txt"
    assert expand("!/", ACTIVE, PASSIVE) == "'/home/me/my dir'"
    assert expand("[!:]", ACTIVE, PASSIVE) == "[]"
    assert expand("$ .$ $\\ $/", ACTIVE, PASSIVE) == "archive.tar .gz / /"
    assert expand("$$HOME !! %%", ACTIVE, PASSIVE) == "$HOME ! %"
    assert expand("%0 %1 %2 %3 %4 %5", ACTIVE, PASSIVE, script="/s.sh", params="a b") == \
        "/s.sh /tmp/a.lst - a b "
    assert caption(parse(">1 Edit !.! in $/").items[0], ACTIVE, PASSIVE) == "Edit read me.txt in /"


def test_what_a_macro_puts_in_is_never_read_as_another():
    side = Side.of(Path("/x"), "100%1!.txt")
    assert expand("!.!", side, PASSIVE, quote=False) == "100%1!.txt"


def test_a_dot_file_has_no_extension_and_the_script_is_every_line_expanded():
    assert Side.of(Path("/"), ".bashrc").name == ".bashrc"
    menu = parse(SAMPLE)
    text = script_text(menu.commands(menu.items[3]), ACTIVE, PASSIVE, "/s.sh")
    assert text == "vi '/home/me/my dir/''read me'.txt\ncp /tmp/a.lst / %3 $HOME\n"


def test_the_local_menu_is_the_nearest_above_else_the_global_one(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    deep = tmp_path / "a" / "b"
    deep.mkdir(parents=True)
    assert find_menu(deep) is None
    (tmp_path / "config" / "navigator").mkdir(parents=True)
    (tmp_path / "config" / "navigator" / "dn.mnu").write_text(">1 g\n")
    assert find_menu(deep) == (tmp_path / "config" / "navigator" / "dn.mnu", True)
    (tmp_path / "a" / "dn.mnu").write_text(">1 l\n")
    assert find_menu(deep) == (tmp_path / "a" / "dn.mnu", False)
    assert find_menu(deep, want_global=True)[1] is True


def test_the_private_directory_is_this_users_alone(tmp_path):
    from navigator.tempdir import private_dir

    SETTINGS.system.temp_dir = str(tmp_path)
    made = private_dir()
    assert made.parent == tmp_path and made.stat().st_mode & 0o777 == 0o700
    made.chmod(0o777)
    with pytest.raises(OSError):
        private_dir()


# -- in the file manager ---------------------------------------------------------------


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    (tmp_path / "config" / "navigator").mkdir(parents=True)
    SETTINGS.system.temp_dir = str(tmp_path / "tmp")
    (tmp_path / "tmp").mkdir()
    work = tmp_path / "work"
    work.mkdir()
    for name in ("a.txt", "b.txt"):
        (work / name).write_text(name)
    (work / "dn.mnu").write_text(SAMPLE + ">1 ~L~ist\n    cat %1\n")
    return work


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def popup(app) -> PopupMenu | None:
    return next((child for child in app.root.children if isinstance(child, PopupMenu)), None)


def captions(box) -> list[str]:
    return [parse_shortcut(entry.text)[0] if hasattr(entry, "text") else "-" for entry in box.entries()]


def capture(app, ran: list[str]):
    app.shell.run_command = lambda command, typed=True: ran.append(command)


def to(name):
    def action(app):
        panel = app.manager.left
        panel.cursor = [e.name for e in panel.items].index(name)
    return action


def script_of(ran: list[str]) -> str:
    assert len(ran) == 1 and ran[0].startswith(". ")
    return Path(shlex.split(ran[0][2:])[0]).read_text()


def test_f2_shows_the_local_menu_centred_and_enter_runs_the_item(place):
    app = navigator(place)
    ran: list[str] = []
    seen = {}

    def look(a):
        box = popup(a)
        width, height = PopupMenu.measure(box.menu, a, a.shell)
        seen.update(captions=captions(box.box), at=box.at,
                    centre=((a.root.width - width) // 2, (a.root.height - height) // 2))

    run_app(app, [lambda a: capture(a, ran), to("a.txt"), KeyEvent("f2"),
                  Until(lambda a: popup(a) is not None), look,
                  KeyEvent("end"), KeyEvent("up"), KeyEvent("enter"),
                  Until(lambda a: ran)])
    assert seen["captions"] == ["Windows", "-", "Format", "F5 Edit a.txt", "List"]
    assert seen["at"] == seen["centre"]
    assert script_of(ran) == f"vi {place}/a.txt\ncp {place.parent}/tmp/navigator-{os.getuid()}/active.lst " \
                             f"{place}/ %3 $HOME\n"


def test_percent_1_lists_the_tagged_names(place):
    app = navigator(place)
    ran: list[str] = []

    def tag(a):
        a.manager.left.marked = frozenset({"a.txt", "b.txt"})

    run_app(app, [lambda a: capture(a, ran), tag, KeyEvent("f2"), Until(lambda a: popup(a) is not None),
                  KeyEvent("l", "l"), Until(lambda a: ran)])
    listed = Path(shlex.split(script_of(ran).split()[1])[0])
    assert listed.read_text().splitlines() == ["a.txt", "b.txt"]


def test_a_submenu_opens_beside_and_its_item_asks_for_parameters(place):
    app = navigator(place)
    ran: list[str] = []
    seen = {}
    run_app(app, [lambda a: capture(a, ran), KeyEvent("f2"), Until(lambda a: popup(a) is not None),
                  KeyEvent("f", "f"), lambda a: None,
                  lambda a: seen.update(boxes=len(popup(a).boxes), inner=captions(popup(a).boxes[-1])),
                  KeyEvent("d", "d"), Until(lambda a: a.modal is not None and a.modal.title == "Menu Parameters"),
                  lambda a: seen.update(caption=a.modal.caption, value=a.modal.entry.value),
                  KeyEvent("end"), *[KeyEvent(c, c) for c in " /q"], KeyEvent("enter"),
                  Until(lambda a: ran)])
    assert seen["boxes"] == 2 and seen["inner"] == ["1.44 Mb", "Define..."]
    assert seen["caption"] == "Format what" and seen["value"] == "format a:"
    assert script_of(ran) == "format a:\n"  # %3 %4: the first two words typed


def test_a_captions_f_key_chooses_its_item(place):
    app = navigator(place)
    ran: list[str] = []
    run_app(app, [lambda a: capture(a, ran), to("b.txt"), KeyEvent("f2"),
                  Until(lambda a: popup(a) is not None), KeyEvent("f5"), Until(lambda a: ran)])
    assert script_of(ran).startswith(f"vi {place}/b.txt\n")


def test_f2_in_the_box_changes_to_the_global_menu_and_f4_edits_it(place):
    from navigator.widgets.editor.edit_window import EditWindow

    global_menu = place.parent / "config" / "navigator" / "dn.mnu"
    global_menu.write_text(">1 ~G~lobal thing\n    true\n")
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f2"), Until(lambda a: popup(a) is not None), KeyEvent("f2"),
                  Until(lambda a: popup(a) is not None and captions(popup(a).box) == ["Global thing"]),
                  KeyEvent("f4"),
                  Until(lambda a: isinstance(a.shell.desktop.active_window, EditWindow)),
                  lambda a: seen.update(path=a.shell.desktop.active_window.editor.path)])
    assert seen["path"] == global_menu


def test_no_menu_anywhere_says_so(place):
    (place / "dn.mnu").unlink()
    app = navigator(place)
    seen = {}
    run_app(app, [KeyEvent("f2"), Until(lambda a: a.modal is not None),
                  lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("enter")])
    assert seen["prompt"] == "File dn.mnu not found"


def test_escape_runs_nothing(place):
    app = navigator(place)
    ran: list[str] = []
    run_app(app, [lambda a: capture(a, ran), KeyEvent("f2"), Until(lambda a: popup(a) is not None),
                  KeyEvent("escape"), lambda a: None])
    assert ran == []
