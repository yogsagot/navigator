"""The command palette (Alt+Shift+P): every command that applies, found by a few letters, and run."""

from __future__ import annotations

import pytest

from conftest import IDLE, FakeTerminal, run_app
from navkit.events import KeyEvent
from navml import fuzzy

from navigator.widgets.shell.command_palette.command_palette import Entry, gather, narrow

PALETTE = KeyEvent("p", alt=True, shift=True)


def typed(text):
    return [KeyEvent(c, c) for c in text]


# -- the matcher ---------------------------------------------------------------------


def test_letters_in_order_match_and_out_of_order_do_not():
    assert fuzzy.score("mkd", "Make directory") is not None
    assert fuzzy.score("dkm", "Make directory") is None
    assert fuzzy.score("MAKE", "make directory") is not None
    assert fuzzy.score("", "anything") == 0
    assert fuzzy.score("longer than it", "short") is None


def test_word_starts_rank_above_letters_inside_words():
    assert fuzzy.score("md", "Make directory") > fuzzy.score("md", "Compare directories")
    assert fuzzy.score("ff", "Find file") > fuzzy.score("ff", "Diff files")


def test_a_prefix_ranks_above_the_same_letters_later():
    assert fuzzy.score("dir", "Directory sizes") > fuzzy.score("dir", "Change directory")


def test_spans_are_the_best_placement_not_the_first():
    assert fuzzy.spans("md", "Make directory") == [0, 5]
    assert fuzzy.spans("dir", "Directory sizes") == [0, 1, 2]
    assert fuzzy.spans("xyz", "Make") == []


def test_narrow_keeps_the_given_order_between_equals_and_drops_misses():
    entries = [Entry(command=None, title=title, path="", key="", enabled=True, reason="")
               for title in ("Copy", "Copy", "Move")]
    found = narrow(entries, "copy")
    assert [f.entry for f in found] == entries[:2]
    assert found[0].places == (0, 1, 2, 3)
    assert len(narrow(entries, "  ")) == 3


def test_a_match_in_the_menu_path_counts_but_less_than_in_the_title():
    in_title = Entry(command=None, title="Symlink", path="File", key="", enabled=True, reason="")
    in_path = Entry(command=None, title="Edit link target", path="File > Symlinks", key="", enabled=True, reason="")
    found = narrow([in_path, in_title], "symlink")
    assert [f.entry for f in found] == [in_title, in_path]
    assert found[1].places == ()


# -- the box -------------------------------------------------------------------------


@pytest.fixture
def nav(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / "a.txt").write_text("hello\n")
    return tmp_path


def navigator(path):
    from navigator.__main__ import Navigator

    return Navigator(path, path, terminal=FakeTerminal(80, 24))


def rows(app):
    return [(f.entry.title, f.entry.key, f.entry.enabled) for f in app.modal.results.items]


def test_alt_shift_p_opens_it_and_typing_finds_make_directory_with_its_key(nav):
    app = navigator(nav)
    seen = []
    run_app(app, [PALETTE, lambda a: None, lambda a: seen.append(type(a.modal).__name__),
                  *typed("mkd"), lambda a: seen.append(rows(a)[0]),
                  lambda a: seen.append(a.modal.hint.text),
                  KeyEvent("enter"), lambda a: None, lambda a: seen.append(type(a.modal).__name__)])
    assert seen == ["CommandPalette", ("Make directory", "F7", True), "File", "MkdirDialog"]


def test_the_palette_offers_no_row_for_itself(nav):
    app = navigator(nav)
    titles = []
    run_app(app, [lambda a: titles.extend(e.title for e in gather(a, a.focused))])
    assert titles and "Command palette..." not in titles
    assert "About..." in titles


def test_the_active_windows_own_menus_are_listed_only_while_it_shows(nav):
    app = navigator(nav)
    paths = {}
    def collect(name):
        return lambda a: paths.__setitem__(name, {e.path.split(" > ")[0] for e in gather(a, a.focused)})
    run_app(app, [collect("panel"), KeyEvent("o", ctrl=True), lambda a: None, collect("console")])
    assert "Panel" in paths["panel"]
    assert "Panel" not in paths["console"]


def test_keys_bound_where_the_keyboard_is_that_no_menu_holds_are_listed(nav):
    from navigator.settings import SETTINGS

    SETTINGS.interface.store_editor_position = False
    app = navigator(nav)
    found = {}
    run_app(app, [KeyEvent("end"), KeyEvent("f4"), IDLE,
                  lambda a: found.update({e.title: e for e in gather(a, a.focused)})])
    assert found["Select all"].key == "Ctrl-A"
    assert found["Select all"].path == ""


def test_a_greyed_command_says_why_and_enter_on_it_keeps_the_box(nav):
    app = navigator(nav)
    seen = []
    # The cursor on "..": nothing to copy.
    run_app(app, [KeyEvent("home"), PALETTE, lambda a: None, *typed("copy"),
                  lambda a: seen.append(rows(a)[0]), lambda a: seen.append(a.modal.hint.text),
                  KeyEvent("enter"), lambda a: None, lambda a: seen.append(type(a.modal).__name__)])
    title, key, enabled = seen[0]
    assert (title, key, enabled) == ("Copy...", "F5", False)
    assert seen[1]
    assert seen[2] == "CommandPalette"


def test_esc_empties_the_line_first_then_closes_and_nothing_runs(nav):
    app = navigator(nav)
    seen = []
    run_app(app, [PALETTE, lambda a: None, *typed("mkd"), KeyEvent("escape"), lambda a: None,
                  lambda a: seen.append((type(a.modal).__name__, a.modal.filter.value, len(rows(a)) > 50)),
                  KeyEvent("escape"), lambda a: None, lambda a: seen.append(a.modal)])
    assert seen == [("CommandPalette", "", True), None]


def test_down_moves_the_list_while_the_line_keeps_the_keyboard(nav):
    app = navigator(nav)
    seen = []
    run_app(app, [PALETTE, lambda a: None, KeyEvent("down"), KeyEvent("down"),
                  lambda a: seen.append((a.modal.results.cursor, a.modal.filter.focused))])
    assert seen == [(2, True)]


def test_nothing_matching_says_so(nav):
    app = navigator(nav)
    seen = []
    run_app(app, [PALETTE, lambda a: None, *typed("qqqzzz"),
                  lambda a: seen.append((rows(a), a.modal.results.error)),
                  KeyEvent("enter"), lambda a: None, lambda a: seen.append(type(a.modal).__name__)])
    assert seen == [([], "No command matches"), "CommandPalette"]


def test_the_menu_item_opens_it(nav):
    from navigator.widgets.shell.commands import OpenCommandPalette

    app = navigator(nav)
    seen = []

    async def ask(a):
        await a.run_command(OpenCommandPalette)

    run_app(app, [lambda a: a.spawn(ask(a)), lambda a: None, lambda a: seen.append(type(a.modal).__name__)])
    assert seen == ["CommandPalette"]
    assert app.shell.menu.item_for(OpenCommandPalette) is not None
