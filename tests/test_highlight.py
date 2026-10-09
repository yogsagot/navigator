"""Syntax highlighting: ``highlight.ini``, the Pygments lexing, and the editor and viewer painting tokens."""

from __future__ import annotations

import threading

import pytest

from conftest import FakeTerminal, Until, run_app, settle
from navkit.events import KeyEvent
from navkit.screen import ScreenBuffer

from navigator import associations, highlight
from navigator.__main__ import Navigator
from navigator.editor.document import Pos
from navigator.settings import SETTINGS


# -- highlight.ini ---------------------------------------------------------------------


RULES = highlight.parse_rules("""\
[*.py]
lexer = python

[*.inc;*.TXT]
lexer = none

[*.weird]
lexer = no-such-lexer

[#!]
python = python
sh;bash = bash

[*]
lexer = auto
""")


def name_of(lexer) -> str | None:
    return None if lexer is None else type(lexer).__name__


def test_the_first_mask_that_takes_the_name_decides_case_aside():
    assert name_of(highlight.lexer_for("dir/a.py", "", RULES)) == "PythonLexer"
    assert name_of(highlight.lexer_for("NOTES.txt", "", RULES)) is None
    assert name_of(highlight.lexer_for("a.inc", "#!/bin/sh", RULES)) is None   # `none' beats the #! line


def test_a_shebang_names_the_lexer_through_env_and_a_version():
    assert highlight.shebang_interpreter("#!/usr/bin/env -S PYTHONPATH=. python3.12 -u") == "python3.12"
    assert name_of(highlight.lexer_for("script", "#!/usr/bin/env -S python3.12 -u", RULES)) == "PythonLexer"
    assert name_of(highlight.lexer_for("run", "#!/bin/bash -e", RULES)) == "BashLexer"
    assert highlight.shebang_interpreter("no shebang") is None


def test_an_unknown_lexer_falls_through_to_pygments_own_guess():
    assert name_of(highlight.lexer_for("a.weird", "", RULES)) is None
    assert name_of(highlight.lexer_for("main.c", "", RULES)) == "CLexer"


def test_star_none_leaves_unnamed_files_plain():
    rules = highlight.parse_rules("[*.py]\nlexer = python\n[*]\nlexer = none\n")
    assert name_of(highlight.lexer_for("main.c", "", rules)) is None
    assert name_of(highlight.lexer_for("a.py", "", rules)) == "PythonLexer"


def test_the_template_lexes_every_pattern_as_pygments_would():
    """Each file name a Pygments lexer claims, in each of the template's sections,
    comes out with the lexer Pygments' own guess gives it."""
    import fnmatch
    import sys
    from pathlib import Path

    from pygments.lexers import find_lexer_class_for_filename

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    from highlight_ini import lexers, sample

    rules = highlight.default_rules()
    assert len(rules.masks) > 400
    for _, _, patterns in lexers():
        for pattern in patterns:
            name = sample(pattern)
            if rules.by_mask(name) == highlight.NONE:
                continue
            ours = highlight.lexer_for(name, "", rules)
            theirs = find_lexer_class_for_filename(name, "")
            assert type(ours) is theirs, f"{name}: {type(ours).__name__} where Pygments says {theirs.__name__}"
    assert all(fnmatch.fnmatchcase("x.nml", mask) for mask in rules.masks[0][0])


def test_the_template_is_what_the_tool_writes():
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    done = subprocess.run([sys.executable, "tools/highlight_ini.py", "--check"], cwd=root,
                          capture_output=True, text=True)
    assert done.returncode == 0, done.stdout + done.stderr


def test_a_missing_file_means_the_template_and_seeding_writes_it_once():
    assert highlight.read_rules() == highlight.default_rules()
    assert associations.seed(associations.HIGHLIGHT)
    assert not associations.seed(associations.HIGHLIGHT)
    assert highlight.read_rules() == highlight.default_rules()


def test_a_changed_file_is_read_again():
    path = associations.path_of(associations.HIGHLIGHT)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("[*.py]\nlexer = none\n")
    assert highlight.lexer_for("a.py", "") is None
    path.write_text("[*.py]\nlexer = python\n\n")
    assert name_of(highlight.lexer_for("a.py", "")) == "PythonLexer"


def test_a_broken_file_means_the_template():
    path = associations.path_of(associations.HIGHLIGHT)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not an ini at all\n")
    assert highlight.read_rules() == highlight.default_rules()


# -- tokens ------------------------------------------------------------------------------


def test_a_tokens_classes_are_its_types_pieces():
    from pygments.token import Comment, Name, String, Text, Whitespace

    assert highlight.classes_of(String.Double) == ("literal", "string", "double")
    assert highlight.classes_of(Name.Builtin.Pseudo) == ("name", "builtin", "pseudo")
    assert highlight.classes_of(Comment) == ("comment",)
    assert highlight.classes_of(Text) == highlight.classes_of(Whitespace) == ()


def python():
    return highlight.lexer_for("a.py", "", highlight.default_rules())


def test_lines_keep_exact_indices_across_a_string_running_over_breaks():
    lines = ['x = """abc', 'def""" # c', "y = 1"]
    spans = highlight.lex_lines(python(), lines, 99)
    strings = [(line, first, last) for line, row in enumerate(spans)
               for first, last, classes in row if "string" in classes]
    assert (0, 4, 7) in strings and (1, 0, 3) in strings
    assert (1, 7, 10, ("comment", "single")) in [(1, *span) for span in spans[1]]
    assert any(classes[:2] == ("literal", "number") and (first, last) == (4, 5) for first, last, classes in spans[2])


def test_a_c_comment_over_two_lines_is_cut_at_the_break():
    lexer = highlight.lexer_for("a.c", "", highlight.default_rules())
    spans = highlight.lex_lines(lexer, ["int a; /* one", "two */ b"], 9)
    assert (7, 13, ("comment", "multiline")) in spans[0]
    assert (0, 6, ("comment", "multiline")) in spans[1]


def test_lexing_stops_past_the_line_asked_for_and_when_told():
    lines = [f"x{n} = {n}" for n in range(1000)]
    assert len(highlight.lex_lines(python(), lines, 9)) == 10
    stop = threading.Event()
    stop.set()
    assert highlight.lex_lines(python(), lines, 999, stop) is None


def test_byte_spans_count_utf8_bytes_and_one_byte_code_pages():
    text = 's = "é" # ü'
    spans = highlight.lex_bytes(python(), text.encode(), 100)
    comment = next(span for span in spans if span[2][0] == "comment")
    assert comment == (100 + len('s = "é" '.encode()), 100 + len(text.encode()), ("comment", "single"))
    spans = highlight.lex_bytes(python(), 's = "ж" # ю'.encode("cp1251"), 0, "cp1251")
    assert next(span for span in spans if span[2][0] == "comment")[:2] == (8, 11)


def test_spans_follow_an_edit():
    spans = [[(0, 3, ("a",)), (5, 9, ("b",))], [(0, 2, ("c",))]]
    highlight.shift_spans(spans, "insert", Pos(0, 6), Pos(0, 8))      # typed inside b: it widens
    assert spans[0] == [(0, 3, ("a",)), (5, 11, ("b",))]
    highlight.shift_spans(spans, "insert", Pos(0, 4), Pos(1, 1))      # a break and a character
    assert spans[0] == [(0, 3, ("a",))] and spans[1] == [(2, 8, ("b",))] and spans[2] == [(0, 2, ("c",))]
    highlight.shift_spans(spans, "delete", Pos(0, 4), Pos(1, 1))      # and back
    assert spans == [[(0, 3, ("a",)), (5, 11, ("b",))], [(0, 2, ("c",))]]
    highlight.shift_spans(spans, "delete", Pos(0, 2), Pos(0, 6))
    assert spans[0] == [(0, 2, ("a",)), (2, 7, ("b",))]


# -- the editor ---------------------------------------------------------------------------


@pytest.fixture
def quiet_console(monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)


@pytest.fixture
def files(tmp_path, quiet_console):
    (tmp_path / "dir").mkdir()
    return tmp_path


CODE = b'x = "s"  # note\ny = 42 + 1\n'


def window(app):
    return app.shell.desktop.active_window


def lexed(app) -> bool:
    """Whether the active window's text shows every token it is going to."""
    editor, viewer = getattr(window(app), "editor", None), getattr(window(app), "viewer", None)
    child = editor or viewer
    if child is None or not child.syntax_highlight:
        return child is not None
    if child._lex_stop is not None:
        return False
    if editor is not None:
        return editor._plain or editor._lexed >= min(editor.line_count, editor.top + editor.height)
    return viewer._plain or bool(viewer._spans) or viewer.mode != "text"


def painted(files, name, data, key, *actions):
    """*data* as *name*, opened with *key* (F4 or F3), then *actions*: the
    window's text widget and a reader of its cell at (row, column)."""
    (files / name).write_bytes(data)
    SETTINGS.interface.store_editor_position = False
    app = Navigator(files, files, terminal=FakeTerminal(80, 24))
    seen = {}

    def look(a):
        buffer = ScreenBuffer(80, 24)
        a.shell.layout(80, 24)
        settle()
        a.shell.render_tree(buffer)
        child = getattr(window(a), "editor", None) or window(a).viewer
        ox, oy = child.offset()
        seen["child"] = child
        seen["cell"] = lambda row, col: buffer.get(ox + child.x + col, oy + child.y + row)

    run_app(app, [KeyEvent("end"), KeyEvent(key), Until(lexed), *actions, Until(lexed), look])
    return seen["child"], seen["cell"]


def token(widget, *classes, **states):
    return widget.part_style("token", classes=classes, **states)


def test_the_editor_paints_comments_strings_numbers_and_symbols(files):
    editor, cell = painted(files, "code.py", CODE, "f4")
    assert cell(0, 0) == ("x", editor.style)                         # a name stays plain
    assert cell(0, 2) == ("=", token(editor, "operator"))
    assert cell(0, 4) == ('"', token(editor, "literal", "string", "double"))
    assert cell(0, 9) == ("#", token(editor, "comment", "single"))
    assert cell(1, 4) == ("4", token(editor, "literal", "number", "integer"))
    assert len({cell(0, 2)[1], cell(0, 4)[1], cell(0, 9)[1], cell(1, 4)[1], editor.style}) == 5


def test_keywords_are_yellow_in_the_default_theme_and_plain_in_another(files):
    from navigator.scheme import load_scheme

    editor, cell = painted(files, "code.py", b"if x and None:\n    pass\n", "f4")
    yellow = token(editor, "keyword")
    assert cell(0, 0) == ("i", yellow) and yellow.fg != editor.style.fg
    assert cell(0, 5) == ("a", token(editor, "operator", "word")) and cell(0, 5)[1].fg == yellow.fg
    assert cell(0, 9)[1].fg == yellow.fg                              # Keyword.Constant
    norton = load_scheme("norton").variables                          # not given a colour: normal text
    assert norton["keyword-fg"] == norton["editor-normal-text-fg"]


def test_a_comment_on_the_current_line_takes_its_own_colour(files):
    SETTINGS.editor.highlight_line = True
    editor, cell = painted(files, "code.py", CODE + b"# two\n", "f4")
    assert cell(0, 9)[1] == token(editor, "comment", "single", current_line=True)
    assert cell(2, 0)[1] == token(editor, "comment", "single")
    assert cell(0, 9)[1] != cell(2, 0)[1]


def test_a_block_is_painted_over_the_tokens(files):
    editor, cell = painted(files, "code.py", CODE, "f4", *[KeyEvent("right", shift=True)] * 5)
    assert cell(0, 4)[1] == editor.part_style("selected")


def test_an_opened_string_colours_the_lines_below_once_lexed_again(files):
    editor, cell = painted(files, "code.py", b"a = 1\nb = 2\n", "f4", *[KeyEvent(c, c) for c in '"""'])
    assert cell(1, 4) == ("2", token(editor, "literal", "string", "doc"))


def test_syntax_highlight_switches_off_and_is_ticked(files):
    from navigator.widgets.editor.commands import SwitchHighLight

    seen = []
    editor, cell = painted(files, "code.py", CODE, "f4",
                           lambda a: seen.append(window(a).editor.checks(SwitchHighLight())),
                           lambda a: a.spawn(window(a).editor.on_switch_high_light(SwitchHighLight())),
                           lambda a: None,
                           lambda a: seen.append(window(a).editor.checks(SwitchHighLight())))
    assert seen == [True, False]
    assert cell(0, 9) == ("#", editor.style)


def test_a_file_with_no_lexer_stays_plain(files):
    editor, cell = painted(files, "notes.txt", b'x = "s"  # note\n', "f4")
    assert editor._plain and cell(0, 9) == ("#", editor.style)


def test_the_setting_off_leaves_a_new_editor_plain(files):
    SETTINGS.editor.syntax_highlight = False
    editor, cell = painted(files, "code.py", CODE, "f4")
    assert cell(0, 9) == ("#", editor.style)


# -- the viewer ---------------------------------------------------------------------------


C_CODE = b'int main(void) { /* hi */\n  return "s"[0] + 42;\n}\n'


def test_the_viewer_paints_tokens_in_text_mode(files):
    viewer, cell = painted(files, "main.c", C_CODE, "f3")
    assert cell(0, 17) == ("/", token(viewer, "comment", "multiline"))
    assert cell(1, 9) == ('"', token(viewer, "literal", "string"))
    assert cell(0, 0) == ("i", token(viewer, "keyword", "type"))
    assert cell(0, 4)[1] == viewer.style                               # a name: normal text


def test_the_viewer_paints_both_halves_of_a_wrapped_string(files):
    data = b'x = "' + b"a" * 100 + b'"\n'
    viewer, cell = painted(files, "long.py", data, "f3", KeyEvent("f2"))
    assert viewer.wrap
    string = token(viewer, "literal", "string", "double")
    assert cell(0, 10)[1] == string and cell(1, 10)[1] == string


def test_hex_mode_is_not_highlighted(files):
    viewer, cell = painted(files, "main.c", C_CODE, "f3", KeyEvent("f4"))
    assert viewer.mode == "hex"
    assert all(cell(0, x)[1] == viewer.style for x in range(60))


def test_a_new_encoding_lexes_again(files):
    viewer, _ = painted(files, "main.c", C_CODE, "f3", lambda a: window(a).viewer.set_encoding("cp1251"))
    assert viewer._lexed_for[1] == "cp1251" and viewer._spans


def test_highlight_file_edit_opens_highlight_ini(files):
    from navigator.widgets.shell.commands import EditHGL

    app = Navigator(files, files, terminal=FakeTerminal(80, 24))
    run_app(app, [lambda a: a.spawn(a.shell.on_edit_hgl(EditHGL())),
                  Until(lambda a: getattr(window(a), "editor", None) is not None)])
    path = associations.path_of(associations.HIGHLIGHT)
    assert path.read_text() == associations.TEMPLATES[associations.HIGHLIGHT]


# -- Navigator's own lexers ------------------------------------------------------------------


def tokens_of(lexer, text):
    """*text*'s tokens, checked to cover it whole and in order."""
    found, at = [], 0
    for index, token, value in lexer.get_tokens_unprocessed(text):
        assert index == at
        at += len(value)
        found.append((token, value))
    assert at == len(text)
    return found


@pytest.mark.parametrize("pattern", ["navigator/**/*.nss", "navigator/**/*.nml", "navml/**/*.nml"])
def test_every_document_in_the_tree_lexes_whole_and_without_an_error(pattern):
    from pathlib import Path

    from pygments.token import Error

    from navigator.lexers import NmlLexer, NssLexer

    root = Path(__file__).resolve().parent.parent
    paths = sorted(root.glob(pattern))
    assert paths
    for path in paths:
        lexer = NssLexer() if path.suffix == ".nss" else NmlLexer()
        tokens = tokens_of(lexer, path.read_text(encoding="utf-8"))
        assert not [value for token, value in tokens if token in Error], path


def test_the_template_gives_nml_and_nss_their_own_lexers():
    rules = highlight.default_rules()
    assert name_of(highlight.lexer_for("a.nml", "", rules)) == "NmlLexer"
    assert name_of(highlight.lexer_for("navigator.nss", "", rules)) == "NssLexer"


def test_a_stylesheet_reads_variables_selectors_and_literals():
    from pygments.token import Comment, Keyword, Name, Number

    from navigator.lexers import NssLexer

    tokens = [pair for pair in tokens_of(NssLexer(), (
        "$panel-fg: #d8d8d8; /* c */\n"
        "Panel:active::row, *:not(.root) { fg: $panel-fg; bg: light_cyan; bold: true; caret: block }\n"
    )) if pair[1].strip()]
    assert tokens[:3] == [(Name.Variable, "$panel-fg"), (tokens[1][0], ":"), (Number.Hex, "#d8d8d8")]
    assert (Comment.Multiline, "/*") in tokens
    assert (Name.Tag, "Panel") in tokens and (Name.Decorator, "::row") in tokens
    assert (Keyword, "not") in tokens and (Name.Class, ".root") in tokens
    assert (Name.Property, "fg") in tokens and (Name.Variable, "$panel-fg") in tokens[4:]
    assert (Name.Builtin, "light_cyan") in tokens and (Keyword.Constant, "true") in tokens
    assert (Name.Attribute, "caret") in tokens and (Name.Constant, "block") in tokens


def test_markup_reads_heads_directives_blocks_and_python():
    from pygments.token import Comment, Keyword, Name, Number, String

    from navigator.lexers import NmlLexer

    tokens = [pair for pair in tokens_of(NmlLexer(), (
        "from navml.widgets.dialog.label import Label\n"
        "\n"
        "#: A doc comment.\n"
        "Dialog(Window):\n"
        "    property text: \"x\"  # trailing\n"
        "    style_property border: single | double\n"
        "    event ClickEvent\n"
        "    keys:\n"
        "        ctrl+f2: SaveAll\n"
        "    style:\n"
        "        bg: #1e1e2e\n"
        "    Label:\n"
        "        id: entry\n"
        "        text: root.title if (\n"
        "            root.wide) else \"\"\n"
        "        on_click: self.close()\n"
    )) if pair[1].strip()]
    assert (Keyword.Namespace, "from") in tokens
    assert (Comment.Special, "#: A doc comment.") in tokens
    assert (Name.Class, "Dialog") in tokens and (Name.Class, "Window") in tokens
    assert (Keyword.Declaration, "property") in tokens and (Name.Variable, "text") in tokens
    assert (Comment.Single, "# trailing") in tokens
    assert (Name.Constant, "single") in tokens and (Name.Class, "ClickEvent") in tokens
    assert (String.Symbol, "ctrl+f2") in tokens and (Number.Hex, "#1e1e2e") in tokens   # a colour, not a comment
    assert (Keyword, "id") in tokens and (Name.Variable, "entry") in tokens
    assert (Keyword, "else") in tokens                                 # the bracket carried the line on
    assert (Name.Function, "on_click") in tokens and (Name.Builtin.Pseudo, "self") in tokens
