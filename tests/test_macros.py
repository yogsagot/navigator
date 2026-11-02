"""Macros: DOS Navigator's key macros (Ctrl+J R N records, Ctrl+J N plays,
anywhere) and its editor macros (``macros.ini``, Ctrl+J 0 in the editor) --
``navigator/lib/config/macros.py``."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, IDLE, Until, run_app
from navkit.events import KeyEvent, PasteEvent

from navigator.__main__ import Navigator
from navigator.lib.config import macros
from navigator.lib.config.macros import decode, encode, keys_of, parse, resolve, tokens


def ctrl(key: str) -> KeyEvent:
    return KeyEvent(key, ctrl=True)


def typed(text: str) -> list[KeyEvent]:
    return keys_of(text)


def record(slot: int) -> list[KeyEvent]:
    return [ctrl("j"), KeyEvent("r", "r"), KeyEvent(str(slot), str(slot))]


def play(slot: int) -> list[KeyEvent]:
    return [ctrl("j"), KeyEvent(str(slot), str(slot))]


# -- the model ---------------------------------------------------------------------


def test_keys_and_pastes_round_trip():
    events = [KeyEvent("a", "a"), KeyEvent("f7"), KeyEvent("x", ctrl=True, alt=True), PasteEvent("two\nlines")]
    assert decode(encode(events)) == events
    assert decode("not json") == [] and decode('[{"nothing": 1}, 3]') == []


def test_a_slot_is_kept_in_the_database():
    macros.store(3, [KeyEvent("a", "a")])
    macros.store(3, [KeyEvent("b", "b")])
    assert macros.load(3) == [KeyEvent("b", "b")]
    assert macros.load(4) == []


def test_text_is_typed_as_keys():
    assert [k.name for k in keys_of("aB\r\t")] == ["a", "shift+b", "enter", "tab"]


def test_dns_tokens():
    assert tokens("'it''s', 3") == ["it's", "3"]
    assert tokens("'a'^M'b'#65") == ["a\rbA"]
    assert tokens("WordLeft,2") == ["WordLeft", "2"]


MACROS = """\
; a comment
[*]
MACRO everywhere
  PRINT 'x'
ENDMACRO

[*.txt]
MACRO 1
  PRINT 'ab', 2
  GOTOXY 3, 0
  GOTOX 1
  GOTOY 2
  MARK 4
  GOTO 4
  WordLeft, 2
  word_right
  NoSuchThing
  PRINT
ENDMACRO
stray line
"""


def test_the_file_reads_as_dns_hgl_did():
    sections, problems = parse(MACROS)
    assert [s.masks for s in sections] == [["*"], ["*.txt"]]
    steps = sections[1].macros[0].steps
    assert [(s.kind, s.text, s.count, s.x, s.y) for s in steps] == [
        ("print", "ab", 2, None, None), ("goto", "", 1, 3, 0), ("goto", "", 1, 1, None),
        ("goto", "", 1, None, 2), ("mark", "", 4, None, None), ("jump", "", 4, None, None),
        ("command", "WordLeft", 2, None, None), ("command", "word_right", 1, None, None),
        ("command", "NoSuchThing", 1, None, None),
    ]
    assert len(problems) == 2 and "PRINT" in problems[0] and "stray line" in problems[1]
    found = macros.macros_for(sections, "notes.TXT")
    assert [m.name for m in found] == ["everywhere", "1"]
    assert [m.name for m in macros.macros_for(sections, "a.py")] == ["everywhere"]


def test_the_template_reads_without_a_problem():
    from navigator.lib.config import associations

    sections, problems = parse(associations.TEMPLATES[associations.MACROS])
    assert sections and not problems


def test_command_names_dns_and_navigators():
    from navigator.widgets.editor.commands import SwitchIndent

    entries = {"word_left": "WL", "page_up": "PU", "new_line": "NL", "text_start": "TS"}
    assert resolve("WordLeft", entries) == "WL"
    assert resolve("word_left", entries) == "WL"
    assert resolve("PgUp", entries) == "PU" and resolve("Enter", entries) == "NL"
    assert resolve("CtrlHome", entries) == "TS"
    assert resolve("SwitchIndent", entries) == SwitchIndent()
    assert resolve("NoSuchThing", entries) is None


# -- the recorder -------------------------------------------------------------------


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.lib.system.subshell.Subshell.start", lambda self, *a, **k: None)
    (tmp_path / "zz.txt").write_text("one two three\nfour\nfive\n")
    return tmp_path


def navigator(path) -> Navigator:
    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def test_keys_recorded_into_a_slot_play_again(files):
    app = navigator(files)
    seen = {}
    run_app(app, [
        *record(2),
        lambda a: seen.update(mark=a.shell.macro_mark.slot),
        *typed("echo hi"),
        *record(7),  # any slot stops it
        lambda a: seen.update(after=a.shell.macro_mark.slot, line=a.shell.command_line.value),
        lambda a: setattr(a.shell.command_line, "value", ""),
        *play(2), Until(lambda a: not a.macros.playing and a.shell.command_line.value == "echo hi"),
        lambda a: seen.update(played=a.shell.command_line.value),
    ])
    assert seen == {"mark": 2, "after": 0, "line": "echo hi", "played": "echo hi"}
    assert [k.char for k in macros.load(2)] == list("echo hi")
    assert macros.load(7) == []


def test_a_slot_survives_a_new_navigator(files):
    macros.store(1, keys_of("ls"))
    app = navigator(files)
    seen = {}
    run_app(app, [*play(1), Until(lambda a: not a.macros.playing and a.shell.command_line.value == "ls"),
                  lambda a: seen.update(line=a.shell.command_line.value)])
    assert seen["line"] == "ls"


def test_a_played_key_that_opens_a_dialog_has_it_take_the_next(files):
    from navml.widgets.dialog.dialog import Dialog

    macros.store(1, [KeyEvent("f7"), *keys_of("newdir")])
    app = navigator(files)
    seen = {}
    run_app(app, [*play(1), Until(lambda a: not a.macros.playing),
                  lambda a: seen.update(modal=isinstance(a.modal, Dialog),
                                        text=getattr(getattr(a.modal, "entry", None), "value", None)),
                  KeyEvent("escape"), IDLE])
    assert seen["modal"] and seen["text"] == "newdir"


def test_playing_while_recording_records_what_is_played(files):
    macros.store(1, keys_of("ab"))
    app = navigator(files)
    run_app(app, [*record(2), *play(1), Until(lambda a: not a.macros.playing), *typed("c"), *record(2)])
    assert [k.char for k in macros.load(2)] == ["a", "b", "c"]


# -- the editor ------------------------------------------------------------------------


def editor_window(app):
    from navigator.widgets.editor.edit_window import EditWindow

    window = app.shell.desktop.active_window
    return window if isinstance(window, EditWindow) else None


def test_ctrl_j_0_offers_the_files_macros_and_plays_one(files):
    from navigator.lib.config import associations

    path = associations.path_of(associations.MACROS)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("""\
[*.txt]
MACRO stamp
  PRINT '>>'
  MARK 1
  CtrlEnd
  PRINT 'end'^M
  GOTO 1
  WordRight, 2
  PRINT '!'
ENDMACRO
""")
    app = navigator(files)
    seen = {}
    run_app(app, [
        KeyEvent("end"), KeyEvent("f4"), Until(lambda a: editor_window(a) is not None),
        ctrl("j"), KeyEvent("0", "0"), Until(lambda a: a.modal is not None),
        KeyEvent("enter"), Until(lambda a: a.modal is None and "!" in editor_window(a).editor.document.encode().decode()),
        lambda a: seen.update(text=editor_window(a).editor.document.encode().decode()),
    ], timeout=10)
    assert seen["text"] == ">>one two !three\nfour\nfive\nend\n"
