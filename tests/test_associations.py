"""``extensions.ini``, ``viewers.ini``, ``editors.ini`` and ``quickrun.ini``:
DOS Navigator's ``DN.EXT``, ``DN.VWR``, ``DN.EDT`` and ``DN.XRN``."""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator import associations
from navigator.__main__ import Navigator
from navigator.associations import EDITORS, EXTENSIONS, QUICK_RUN, TEMPLATES, VIEWERS, for_file, for_key, parse
from navigator.settings import SETTINGS
from navigator.widgets.shell.commands import ExtFileEdit
from navml.widgets.dialog.control.control import parse_shortcut
from navml.widgets.menu.popup_menu import PopupMenu

SAMPLE = """\
# a comment
[*.TXT;*.md]
Show = cat !.!; echo done  # the shell's, not a comment
; another comment
Count words = <Which
   <=-w
   wc %3 !.!

[*.txt]
Never = this one: the section above takes .txt first

[F2]
Only = make
"""


def test_sections_are_masks_and_captions_keep_their_case_and_the_shells_characters():
    groups = parse(SAMPLE)
    show, count = for_file(groups, "notes.txt").actions
    assert show.caption == "Show" and show.commands.lines == ["cat !.!; echo done  # the shell's, not a comment"]
    assert count.caption == "Count words" and count.commands.lines == ["wc %3 !.!"]
    assert count.commands.asks and count.commands.title == "Which" and count.commands.default == "-w"
    assert for_file(groups, "README.MD").name == "*.TXT;*.md"
    assert for_file(groups, "a.py") is None
    assert for_key(groups, "f2").actions[0].commands.lines == ["make"] and for_key(groups, "F3") is None


def test_a_file_that_is_not_an_ini_is_a_value_error_and_a_missing_one_is_empty():
    with pytest.raises(ValueError):
        parse("no section here = x\n")
    assert associations.read(EXTENSIONS) == []


def test_every_template_reads_as_what_it_says():
    assert for_file(parse(TEMPLATES[EXTENSIONS]), "x.tgz").actions[1].caption == "Extract here"
    assert for_file(parse(TEMPLATES[VIEWERS]), "a.PDF") is not None
    assert for_file(parse(TEMPLATES[EDITORS]), "a.docx") is not None
    assert for_key(parse(TEMPLATES[QUICK_RUN]), "F1") is not None


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    SETTINGS.system.temp_dir = str(tmp_path / "tmp")
    (tmp_path / "tmp").mkdir()
    work = tmp_path / "work"
    work.mkdir()
    for name in ("a.txt", "b.pdf", "c.odt"):
        (work / name).write_text(name)
    run = work / "run.sh"
    run.write_text("true\n")
    run.chmod(0o755)
    return work


def write(file_name: str, text: str) -> None:
    path = associations.path_of(file_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def navigator(path: Path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


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


def popup(app) -> PopupMenu | None:
    return next((child for child in app.root.children if isinstance(child, PopupMenu)), None)


def test_enter_on_a_file_runs_its_one_entry_and_a_program_is_still_run_itself(place):
    write(EXTENSIONS, "[*.txt]\nOpen = less !\\!.!\n[*.sh]\nNot this = x\n")
    app = navigator(place)
    ran: list[str] = []
    run_app(app, [lambda a: capture(a, ran), to("a.txt"), KeyEvent("enter"), Until(lambda a: ran)])
    assert script_of(ran) == f"less {place}/a.txt\n"

    ran.clear()
    app = navigator(place)
    run_app(app, [lambda a: capture(a, ran), to("run.sh"), KeyEvent("enter"), Until(lambda a: ran)])
    assert ran == ["./run.sh"]


def test_several_entries_are_offered_in_a_menu_with_their_macros_in(place):
    write(EXTENSIONS, "[*.txt]\nShow !.! = cat !.!\nCount = wc !.!\n")
    app = navigator(place)
    ran: list[str] = []
    seen = {}

    def look(a):
        seen["captions"] = [parse_shortcut(entry.text)[0] for entry in popup(a).box.entries()]

    run_app(app, [lambda a: capture(a, ran), to("a.txt"), KeyEvent("enter"), Until(lambda a: popup(a) is not None),
                  look, KeyEvent("down"), KeyEvent("enter"), Until(lambda a: ran)])
    assert seen["captions"] == ["Show a.txt", "Count"]
    assert script_of(ran) == "wc a.txt\n"


def test_a_file_with_no_entry_is_left_alone(place):
    write(EXTENSIONS, "[*.py]\nRun = python3 !.!\n")
    app = navigator(place)
    ran: list[str] = []
    run_app(app, [lambda a: capture(a, ran), to("a.txt"), KeyEvent("enter"), lambda a: None, lambda a: None])
    assert ran == [] and app.modal is None


def test_f3_and_f4_use_the_ini_only_where_the_internal_one_is_not_chosen(place, monkeypatch):
    write(VIEWERS, "[*.pdf]\nPDF = zathura !.!\n")
    write(EDITORS, "[*.odt]\nWriter = lowriter !.!\n")
    ran: list[str] = []
    seen = {}

    # Internal on: F3 opens the window; Alt+F3 runs viewers.ini's entry.
    app = navigator(place)
    run_app(app, [lambda a: capture(a, ran), to("b.pdf"), KeyEvent("f3"), lambda a: None,
                  lambda a: seen.update(windows=len(a.shell.desktop.windows())), KeyEvent("escape"), lambda a: None,
                  KeyEvent("f3", alt=True), Until(lambda a: ran)])
    assert seen["windows"] == 2 and script_of(ran) == "zathura b.pdf\n"

    # Internal off: F4 runs editors.ini's entry, and $EDITOR without one.
    SETTINGS.system.internal_editor = False
    monkeypatch.setenv("EDITOR", "ed")
    ran.clear()
    app = navigator(place)
    run_app(app, [lambda a: capture(a, ran), to("c.odt"), KeyEvent("f4"), Until(lambda a: ran)])
    assert script_of(ran) == "lowriter c.odt\n"
    ran.clear()
    app = navigator(place)
    run_app(app, [lambda a: capture(a, ran), to("a.txt"), KeyEvent("f4"), Until(lambda a: ran)])
    assert ran == [f"ed {place}/a.txt"]


def test_quick_run_runs_its_keys_section(place):
    write(QUICK_RUN, "[F3]\nBuild = make -C !/\n")
    app = navigator(place)
    ran: list[str] = []
    run_app(app, [lambda a: capture(a, ran), KeyEvent("f2", ctrl=True, shift=True), lambda a: None,
                  KeyEvent("f3", ctrl=True, shift=True), Until(lambda a: ran)])
    assert script_of(ran) == f"make -C {place}\n"


def test_a_broken_file_is_said_so(place):
    write(EXTENSIONS, "not an ini\n")
    app = navigator(place)
    seen = {}
    run_app(app, [to("a.txt"), KeyEvent("enter"),
                  Until(lambda a: getattr(a.modal, "title", None) == "Error"),
                  lambda a: seen.update(prompt=a.modal.prompt), KeyEvent("enter")])
    assert seen["prompt"].startswith("Cannot read extensions.ini")


def test_options_opens_the_file_written_from_its_template_first(place):
    app = navigator(place)
    seen = {}
    run_app(app, [lambda a: a.spawn(a.run_command(ExtFileEdit)),
                  Until(lambda a: len(a.shell.desktop.windows()) == 2, timeout=5),
                  lambda a: seen.update(title=a.shell.desktop.windows()[-1].title)])
    assert associations.path_of(EXTENSIONS).read_text() == TEMPLATES[EXTENSIONS]
    assert EXTENSIONS in str(seen["title"])
