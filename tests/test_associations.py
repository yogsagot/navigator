"""``extensions.ini``, ``viewers.ini``, ``editors.ini`` and ``quickrun.ini``:
DOS Navigator's ``DN.EXT``, ``DN.VWR``, ``DN.EDT`` and ``DN.XRN``."""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest

from conftest import IDLE, FakeTerminal, Until, run_app
from navkit.events import KeyEvent

from navigator.lib.config import associations
from navigator.__main__ import Navigator
from navigator.lib.config.associations import EDITORS, EXTENSIONS, QUICK_RUN, TEMPLATES, VIEWERS, for_file, for_key, parse
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


def test_seed_all_writes_the_missing_files_and_leaves_the_users_alone():
    mine = associations.path_of(VIEWERS)
    mine.parent.mkdir(parents=True, exist_ok=True)
    mine.write_text("[*.png]\nMine = feh !.!\n", encoding="utf-8")
    assert associations.seed_all() == []
    assert mine.read_text(encoding="utf-8") == "[*.png]\nMine = feh !.!\n"
    for file_name in (EXTENSIONS, EDITORS, QUICK_RUN, associations.MENU):
        assert associations.path_of(file_name).read_text(encoding="utf-8") == TEMPLATES[file_name]
    assert associations.seed(EXTENSIONS) is False


def test_every_template_reads_as_what_it_says():
    assert for_file(parse(TEMPLATES[EXTENSIONS]), "x.tgz").actions[1].caption == "Extract here"
    # Navigator reads a PDF's text itself: the example is a comment.
    assert for_file(parse(TEMPLATES[VIEWERS]), "a.PDF") is None
    assert for_file(parse(TEMPLATES[EDITORS]), "a.docx") is not None
    assert for_key(parse(TEMPLATES[QUICK_RUN]), "F1") is not None


@pytest.fixture
def place(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
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
    app.shell.run_command = lambda command, typed=True, **kw: ran.append(command)


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
        seen["title"] = popup(a).box.title

    run_app(app, [lambda a: capture(a, ran), to("a.txt"), KeyEvent("enter"), Until(lambda a: popup(a) is not None),
                  look, KeyEvent("down"), KeyEvent("enter"), Until(lambda a: ran)])
    assert seen["captions"] == ["Show a.txt", "Count"] and seen["title"] == "Choose action"
    assert script_of(ran) == "wc a.txt\n"


def test_a_file_with_no_entry_is_left_alone(place):
    write(EXTENSIONS, "[*.py]\nRun = python3 !.!\n")
    app = navigator(place)
    ran: list[str] = []
    run_app(app, [lambda a: capture(a, ran), to("a.txt"), KeyEvent("enter"), lambda a: None, lambda a: None])
    assert ran == [] and app.modal is None


def test_f3_runs_viewers_ini_before_the_viewer_and_alt_f3_never_does(place, monkeypatch):
    write(VIEWERS, "[*.pdf]\nPDF = zathura !.!\n")
    write(EDITORS, "[*.odt]\nWriter = lowriter !.!\n")
    ran: list[str] = []
    seen = {}

    # DN's ``ViewFile``: F3 runs ``DN.VWR``'s entry; Alt+F3 is ``InternalView``.
    app = navigator(place)
    run_app(app, [lambda a: capture(a, ran), to("b.pdf"), KeyEvent("f3"), Until(lambda a: ran),
                  lambda a: seen.update(script=script_of(ran)), lambda a: ran.clear(),
                  KeyEvent("f3", alt=True), IDLE,
                  lambda a: seen.update(windows=len(a.shell.desktop.windows()), after=list(ran))])
    assert seen["script"] == "zathura b.pdf\n"
    assert seen["windows"] == 2 and seen["after"] == []

    # A file no section takes: F3 opens the viewer.
    ran.clear()
    app = navigator(place)
    run_app(app, [lambda a: capture(a, ran), to("a.txt"), KeyEvent("f3"), IDLE,
                  lambda a: seen.update(windows=len(a.shell.desktop.windows()))])
    assert seen["windows"] == 2 and ran == []

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


def test_options_file_edits_follow_internal_editor_and_editors_ini(place, tmp_path, monkeypatch):
    """DN's ``EditFile(True, ...)`` for the Options edits: editors.ini's entry for the
    file named, its macros naming that file and not the panel's, else ``$EDITOR``."""
    conf = tmp_path / "conf"
    conf.mkdir()
    target = conf / "menu.ini"
    SETTINGS.system.internal_editor = False
    monkeypatch.setenv("EDITOR", "ed")
    ran: list[str] = []
    app = navigator(place)
    run_app(app, [lambda a: capture(a, ran), to("a.txt"),
                  lambda a: a.spawn(a.shell.edit_menu_file(target)), Until(lambda a: ran)])
    assert ran == [f"ed {target}"]

    write(EDITORS, "[*.ini]\nEdit = myed !\\!.!\n")
    ran.clear()
    app = navigator(place)
    run_app(app, [lambda a: capture(a, ran), to("a.txt"),
                  lambda a: a.spawn(a.shell.edit_menu_file(target)), Until(lambda a: ran)])
    assert script_of(ran) == f"myed {target}\n"


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


def test_f3_opens_a_database_or_sheet_before_viewers_ini_and_alt_f3_shows_its_text(place):
    from navigator.widgets.viewer.db_window import DBWindow
    from navigator.widgets.viewer.file_window import FileWindow

    write(VIEWERS, "[*.csv]\nSheet = gnumeric !.!\n")
    (place / "t.csv").write_text("a,b\n1,2\n")
    ran: list[str] = []
    seen = {}

    def kinds(a):
        return [type(w).__name__ for w in a.shell.desktop.windows()]

    app = navigator(place)
    run_app(app, [lambda a: capture(a, ran), KeyEvent("r", ctrl=True), IDLE, to("t.csv"), KeyEvent("f3"),
                  Until(lambda a: len(a.shell.desktop.windows()) == 2), lambda a: seen.update(f3=kinds(a)),
                  KeyEvent("escape"), IDLE, KeyEvent("f3", alt=True),
                  Until(lambda a: len(a.shell.desktop.windows()) == 2), lambda a: seen.update(alt=kinds(a))])
    assert DBWindow.__name__ in seen["f3"] and ran == []
    assert FileWindow.__name__ in seen["alt"]


@pytest.mark.parametrize("enter_opens", [True, False])
def test_f3_opens_an_archive_in_the_panel_whatever_enter_does(place, monkeypatch, enter_opens):
    import zipfile

    monkeypatch.setattr(SETTINGS.file_manager, "enter_opens_archive", enter_opens)
    with zipfile.ZipFile(place / "z.zip", "w") as zipped:
        zipped.writestr("inner.txt", "inside")
    seen = {}
    app = navigator(place)
    run_app(app, [KeyEvent("r", ctrl=True), IDLE, to("z.zip"), KeyEvent("f3"),
                  Until(lambda a: a.manager.left.location.outer is not None),
                  lambda a: seen.update(names=[e.name for e in a.manager.left.items],
                                        windows=len(a.shell.desktop.windows()))])
    assert "inner.txt" in seen["names"] and seen["windows"] == 1


def test_f3_on_a_zip_that_is_not_one_views_it_and_one_inside_an_archive_is_not_entered(place):
    import io
    import zipfile

    from navigator.widgets.viewer.file_window import FileWindow

    (place / "fake.zip").write_text("not a zip at all\n")
    nested = io.BytesIO()
    with zipfile.ZipFile(nested, "w") as zipped:
        zipped.writestr("deep.txt", "deep")
    with zipfile.ZipFile(place / "outer.zip", "w") as zipped:
        zipped.writestr("nested.zip", nested.getvalue())
    seen = {}

    def kinds(a):
        return [type(w).__name__ for w in a.shell.desktop.windows()]

    app = navigator(place)
    run_app(app, [KeyEvent("r", ctrl=True), IDLE, to("fake.zip"), KeyEvent("f3"),
                  Until(lambda a: len(a.shell.desktop.windows()) == 2),
                  lambda a: seen.update(fake=kinds(a), outer=a.manager.left.location.outer),
                  KeyEvent("escape"), IDLE, to("outer.zip"), KeyEvent("enter"),
                  Until(lambda a: a.manager.left.location.outer is not None
                        and "nested.zip" in [e.name for e in a.manager.left.items]),
                  to("nested.zip"), KeyEvent("f3"),
                  Until(lambda a: len(a.shell.desktop.windows()) == 2),
                  lambda a: seen.update(nested=kinds(a), names=[e.name for e in a.manager.left.items])])
    assert FileWindow.__name__ in seen["fake"] and seen["outer"] is None
    assert FileWindow.__name__ in seen["nested"] and "nested.zip" in seen["names"]


def test_f3_on_a_directory_in_an_archive_does_nothing(place):
    import zipfile

    with zipfile.ZipFile(place / "d.zip", "w") as zipped:
        zipped.writestr("sub/x.txt", "x")
    seen = {}
    app = navigator(place)
    run_app(app, [KeyEvent("r", ctrl=True), IDLE, to("d.zip"), KeyEvent("enter"),
                  Until(lambda a: "sub" in [e.name for e in a.manager.left.items]),
                  to("sub"), KeyEvent("f3"), IDLE, IDLE,
                  lambda a: seen.update(sub=next(e for e in a.manager.left.items if e.name == "sub").counted,
                                        modal=a.modal, windows=len(a.shell.desktop.windows()))])
    assert not seen["sub"] and seen["modal"] is None and seen["windows"] == 1


def _changed_then_f4_outside(place, monkeypatch, answer, name="a.txt"):
    """a.txt in an editor window with a character typed, then F4 with *Internal
    editor* off: ``Valid(cmQuit)``'s question, answered by the steps *answer*
    makes of the list the commands run land in."""
    from navigator.widgets.editor.edit_window import EditWindow

    monkeypatch.setenv("EDITOR", "ed")
    SETTINGS.system.internal_editor = True  # F4 opens the window first
    app = navigator(place)
    ran: list[str] = []
    seen = {}

    def outside(a):
        SETTINGS.system.internal_editor = False
        a.manager.spawn(a.manager.edit_file(True))

    def look(a):
        seen["modal"] = getattr(a.modal, "prompt", None)

    run_app(app, [lambda a: capture(a, ran), to("a.txt"), KeyEvent("f4"),
                  Until(lambda a: any(isinstance(w, EditWindow) for w in a.shell.desktop.windows())),
                  KeyEvent("x", char="x"), lambda a: a.manager.focus(), to(name), outside,
                  Until(lambda a: a.modal is not None or ran), look, *answer(ran), lambda a: None])
    return ran, seen


def test_an_external_editor_asks_to_save_a_changed_window_on_its_file_first(place, monkeypatch):
    ran, seen = _changed_then_f4_outside(place, monkeypatch, lambda ran: [KeyEvent("y", alt=True), Until(lambda a: ran)])
    from navigator.widgets.editor.edit_window.edit_window import cut_path

    assert seen["modal"] == f"File {cut_path(str(place / 'a.txt'))} was modified. Save?"
    assert (place / "a.txt").read_text().startswith("x")
    assert ran == [f"ed {place}/a.txt"]


def test_cancel_runs_nothing_and_no_runs_it_unsaved(place, monkeypatch):
    ran, _ = _changed_then_f4_outside(place, monkeypatch, lambda ran: [KeyEvent("escape")])
    assert ran == [] and (place / "a.txt").read_text() == "a.txt"
    ran, _ = _changed_then_f4_outside(place, monkeypatch, lambda ran: [KeyEvent("n", alt=True), Until(lambda a: ran)])
    assert ran == [f"ed {place}/a.txt"] and (place / "a.txt").read_text() == "a.txt"


def test_a_changed_window_on_another_file_is_not_asked_about(place, monkeypatch):
    ran, seen = _changed_then_f4_outside(place, monkeypatch, lambda ran: [], name="b.pdf")
    assert seen["modal"] is None and ran == [f"ed {place}/b.pdf"]


def test_an_options_edit_outside_asks_about_a_changed_window_on_that_file(place, tmp_path, monkeypatch):
    from navigator.lib.config.file_history import open_editor

    target = tmp_path / "menu.ini"
    target.write_text("[x]\n")
    monkeypatch.setenv("EDITOR", "ed")
    app = navigator(place)
    ran: list[str] = []
    seen = {}

    def outside(a):
        SETTINGS.system.internal_editor = False
        a.spawn(a.shell.edit_menu_file(target))

    run_app(app, [lambda a: capture(a, ran), lambda a: a.spawn(open_editor(a.shell.desktop, target)),
                  Until(lambda a: len(a.shell.desktop.windows()) == 2), KeyEvent("x", char="x"), outside,
                  Until(lambda a: a.modal is not None), lambda a: seen.update(prompt=a.modal.prompt),
                  KeyEvent("escape"), lambda a: None])
    from navigator.widgets.editor.edit_window.edit_window import cut_path

    assert seen["prompt"] == f"File {cut_path(str(target))} was modified. Save?" and ran == []
