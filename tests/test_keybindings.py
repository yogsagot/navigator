"""keybindings.ini and Options > Configuration > Key bindings."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, Until, run_app
from navkit.commands import command_of, key_table
from navkit.events import KeyEvent
from navigator import keybindings
from navigator.__main__ import Navigator
from navigator.widgets.manager.commands import Copy, MakeDirectory
from navigator.widgets.manager.manager import Manager
from navigator.widgets.shell.commands import KeyBindingsSetup


def section(name: str) -> keybindings.Section:
    return next(s for s in keybindings.sections(Navigator) if s.name == name)


# -- the sections and their names ----------------------------------------------------


def test_every_section_names_each_command_once():
    for found in keybindings.sections(Navigator):
        names = [entry.name for entry in found.entries]
        assert names, found.name
        assert len(names) == len(set(names)), found.name
        assert all(name == name.lower() and " " not in name for name in names)


def test_variants_are_told_apart_and_keys_gathered():
    manager = section("manager")
    assert manager.entry("copy").defaults == ("f5",)
    assert manager.entry("store_quick_dir_1").defaults == ("alt+shift+1", "alt+!")
    assert manager.entry("select_group_invert").defaults == ("shift+kp_plus",)
    assert manager.entry("scroll_names_minus_1").defaults == ("left",)
    editor = section("editor")
    assert editor.entry("move_left_extend").defaults == ("shift+left",)
    assert editor.entry("block_start").defaults == ("ctrl+k b", "ctrl+k ctrl+b")
    assert section("global").entry("quick_run_10").defaults == ("ctrl+shift+f10",)


def test_a_section_is_both_halves_of_its_component():
    manager = section("manager")
    assert manager.cls is Manager and manager.base.__name__ == "Window"
    assert set(manager.table(manager.defaults())) == set(key_table(Manager)) - set(
        key_table(manager.base)
    )


# -- the file --------------------------------------------------------------------------


def test_seed_writes_every_default_once(tmp_path):
    file = tmp_path / "keybindings.ini"
    assert keybindings.seed(Navigator, file)
    assert not keybindings.seed(Navigator, file)
    text = file.read_text()
    assert "[manager]\n# File panels\n" in text
    assert "\ncopy = f5\n" in text
    assert "\nblock_start = ctrl+k b, ctrl+k ctrl+b\n" in text
    assert keybindings.load(Navigator, file) == []
    assert not keybindings.sections(Navigator)[0].cls is None
    assert key_table(Manager)["f5"] is Copy


def test_the_file_lives_beside_navigator_ini(tmp_path):
    assert keybindings.path() == tmp_path / "config" / "navigator" / "keybindings.ini"


def test_a_line_rebinds_and_an_empty_one_unbinds(tmp_path):
    file = tmp_path / "keybindings.ini"
    keybindings.seed(Navigator, file)
    text = file.read_text()
    text = text.replace("\nmake_directory = f7\n", "\nmake_directory = F12, Ctrl+K M\n")
    text = text.replace("\ncopy = f5\n", "\ncopy =\n")
    file.write_text(text)
    assert keybindings.load(Navigator, file) == []
    table = key_table(Manager)
    assert table["f12"] is MakeDirectory and table["ctrl+k m"] is MakeDirectory
    assert "f7" not in table and "f5" not in table
    assert section("manager").current()["copy"] == ()


def test_a_missing_line_keeps_its_default(tmp_path):
    file = tmp_path / "keybindings.ini"
    file.write_text("[manager]\nmake_directory = f12\n")
    assert keybindings.load(Navigator, file) == []
    assert key_table(Manager)["f5"] is Copy and key_table(Manager)["f12"] is MakeDirectory


def test_what_will_not_do_is_a_warning_and_the_default(tmp_path):
    file = tmp_path / "keybindings.ini"
    file.write_text(
        "[manager]\n"
        "make_directory = cmd+x\n"
        "no_such_thing = f1\n"
        "[nowhere]\n"
        "x = f1\n"
        "[viewer]\n"
        "hex_mode = f2\n"
    )
    warnings = keybindings.load(Navigator, file)
    assert len(warnings) == 4
    assert "make_directory" in warnings[0] and "using the default" in warnings[0]
    assert "no_such_thing" in warnings[1]
    assert "[nowhere]" in warnings[2]
    assert "[viewer]" in warnings[3] and "using the defaults" in warnings[3]
    assert key_table(Manager)["f7"] is MakeDirectory


def test_a_file_that_is_not_ini_is_a_warning(tmp_path):
    file = tmp_path / "keybindings.ini"
    file.write_text("no section here\n")
    assert len(keybindings.load(Navigator, file)) == 1
    assert key_table(Manager)["f7"] is MakeDirectory


def test_a_changed_line_says_its_default(tmp_path):
    found = keybindings.sections(Navigator)
    text = keybindings.render(found, {"manager": {"make_directory": ("f12",)}})
    line = next(line for line in text.splitlines() if line.startswith("make_directory"))
    assert line.endswith("# default: f7")


def test_a_comment_character_key_survives_the_file(tmp_path):
    assert keybindings.format_keys(("f1", "#", ";")) == "f1,#,;"
    file = tmp_path / "keybindings.ini"
    found = keybindings.sections(Navigator)
    file.write_text(keybindings.render(found, {"manager": {"make_directory": ("f12", "#")}}))
    assert keybindings.load(Navigator, file) == []
    assert key_table(Manager)["#"] is MakeDirectory


def test_the_menu_shows_a_moved_key(tmp_path):
    file = tmp_path / "keybindings.ini"
    file.write_text("[manager]\nmake_directory = f12\n")
    keybindings.load(Navigator, file)
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = {}
    run_app(app, [lambda a: seen.update(found=a.bindings())])
    assert command_of(seen["found"]["f12"]) == MakeDirectory()
    assert "f7" not in seen["found"]


# -- the dialog ------------------------------------------------------------------------


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr("navigator.subshell.Subshell.start", lambda self, *a, **k: None)
    return Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 25))


def titled(title: str):
    return lambda a: a.modal is not None and str(a.modal.title) == title


def at(group: str, name: str):
    def action(a):
        dialog = a.modal
        dialog.groups.cursor = [s.name for s in dialog.sections].index(group)
    def pick(a):
        dialog = a.modal
        dialog.bindings.cursor = [e.name for e in dialog.section.entries].index(name)
    return [action, lambda a: None, pick, lambda a: None]


def rebind(*keys: KeyEvent):
    return [KeyEvent("r", alt=True), Until(titled("Press a key")), *keys, KeyEvent("enter"),
            Until(titled("Key Bindings"))]


def screen(a) -> str:
    buffer = a._front
    return "\n".join("".join(buffer.get(x, y)[0] for x in range(buffer.width))
                     for y in range(buffer.height))


def test_rebind_and_ok_binds_and_writes(app):
    seen = {}
    run_app(app, [
        lambda a: a.spawn(a.run_command(KeyBindingsSetup)), Until(titled("Key Bindings")),
        *at("manager", "make_directory"),
        *rebind(KeyEvent("k", ctrl=True), KeyEvent("m")),
        lambda a: None, lambda a: seen.update(screen=screen(a)),
        KeyEvent("k", alt=True), lambda a: None, lambda a: None,
    ])
    table = key_table(Manager)
    assert table["ctrl+k m"] is MakeDirectory and "f7" not in table
    text = keybindings.path().read_text()
    assert "\nmake_directory = ctrl+k m" in text
    assert "*Make directory" in seen["screen"] and "Ctrl-K M" in seen["screen"]


def test_a_key_another_command_has_is_asked_about_and_taken(app):
    seen = {}
    run_app(app, [
        lambda a: a.spawn(a.run_command(KeyBindingsSetup)), Until(titled("Key Bindings")),
        *at("manager", "make_directory"),
        KeyEvent("r", alt=True), Until(titled("Press a key")), KeyEvent("f5"), KeyEvent("enter"),
        Until(titled("Key bindings")), lambda a: seen.update(ask=a.modal.prompt),
        KeyEvent("y", alt=True), Until(titled("Key Bindings")), lambda a: None,
        lambda a: seen.update(keys=a.modal.assignments["manager"]),
        KeyEvent("k", alt=True), lambda a: None,
    ])
    assert seen["ask"] == "F5 is bound to Copy.\nReassign it?"
    assert seen["keys"]["copy"] == () and seen["keys"]["make_directory"] == ("f5",)
    assert key_table(Manager)["f5"] is MakeDirectory


def test_a_global_key_is_asked_about(app):
    seen = {}
    run_app(app, [
        lambda a: a.spawn(a.run_command(KeyBindingsSetup)), Until(titled("Key Bindings")),
        *at("manager", "make_directory"),
        KeyEvent("r", alt=True), Until(titled("Press a key")), KeyEvent("o", ctrl=True),
        KeyEvent("enter"), Until(titled("Key bindings")), lambda a: seen.update(ask=a.modal.prompt),
        KeyEvent("n", alt=True), Until(titled("Key Bindings")), lambda a: None,
        lambda a: seen.update(keys=a.modal.assignments["manager"]["make_directory"]),
        KeyEvent("escape"), lambda a: None,
    ])
    assert seen["ask"].startswith("Ctrl-O is the global key for Toggle console")
    assert seen["keys"] == ("f7",)


def test_add_clear_and_default(app):
    seen = []
    keep = lambda a: seen.append(a.modal.assignments["manager"]["make_directory"])  # noqa: E731
    run_app(app, [
        lambda a: a.spawn(a.run_command(KeyBindingsSetup)), Until(titled("Key Bindings")),
        *at("manager", "make_directory"),
        KeyEvent("d", alt=True), Until(titled("Press a key")), KeyEvent("f12"), KeyEvent("enter"),
        Until(titled("Key Bindings")), lambda a: None, keep,
        KeyEvent("l", alt=True), lambda a: None, keep,
        KeyEvent("e", alt=True), lambda a: None, keep,
        KeyEvent("escape"), lambda a: None,
    ])
    assert seen == [("f7", "f12"), (), ("f7",)]


def test_a_chord_on_a_key_bound_alone_is_refused(app):
    seen = {}
    run_app(app, [
        lambda a: a.spawn(a.run_command(KeyBindingsSetup)), Until(titled("Key Bindings")),
        *at("manager", "make_directory"),
        KeyEvent("r", alt=True), Until(titled("Press a key")), KeyEvent("f5"), KeyEvent("x"),
        KeyEvent("enter"), Until(titled("Key bindings")), lambda a: seen.update(said=a.modal.prompt),
        KeyEvent("enter"), Until(titled("Key Bindings")),
        lambda a: seen.update(keys=a.modal.assignments["manager"]["make_directory"]),
        KeyEvent("escape"), lambda a: None,
    ])
    assert seen["said"] == ("Cannot bind that:\nBinds 'f5' both alone and as the start of "
                           "the chord 'f5 x'")
    assert seen["keys"] == ("f7",)


def test_cancel_binds_nothing(app):
    run_app(app, [
        lambda a: a.spawn(a.run_command(KeyBindingsSetup)), Until(titled("Key Bindings")),
        *at("manager", "make_directory"),
        *rebind(KeyEvent("f12")),
        KeyEvent("escape"), lambda a: None,
    ])
    assert key_table(Manager)["f7"] is MakeDirectory
    assert not keybindings.path().exists()


def test_the_capture_box_takes_tab_and_starts_over_after_a_chord(app):
    seen = {}
    run_app(app, [
        lambda a: a.spawn(a.run_command(KeyBindingsSetup)), Until(titled("Key Bindings")),
        *at("manager", "make_directory"),
        KeyEvent("r", alt=True), Until(titled("Press a key")),
        KeyEvent("tab"), lambda a: seen.update(one=a.modal.catcher.spec),
        KeyEvent("x", alt=True), lambda a: seen.update(two=a.modal.catcher.spec),
        KeyEvent("f3"), lambda a: seen.update(three=a.modal.catcher.spec),
        KeyEvent("escape"), Until(titled("Key Bindings")), KeyEvent("escape"), lambda a: None,
    ])
    assert seen == {"one": "tab", "two": "tab alt+x", "three": "f3"}
