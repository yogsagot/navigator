"""navigator.ini: where it lives, how it reads and writes, and the setup dialogs over it."""

from __future__ import annotations

import pytest

from conftest import FakeTerminal, run_app
from navkit.events import KeyEvent
from navigator import __main__ as entry
from navigator.__main__ import Navigator, load_settings
from navigator.settings import (
    SETTINGS,
    ConfirmsData,
    InterfaceData,
    Settings,
    config_path,
)
from navigator.widgets.shell.commands import EditorDefaults, InterfaceSetup, SetupConfirmation


@pytest.fixture
def quiet_console(monkeypatch):
    monkeypatch.setattr("navigator.widgets.shell.console.Console.start", lambda self, argv=None: None)


# -- the file -------------------------------------------------------------------------


def test_the_file_lives_under_xdg_config_home(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert config_path() == tmp_path / "navigator" / "navigator.ini"


def test_without_xdg_config_home_it_is_dot_config(monkeypatch, tmp_path):
    monkeypatch.delenv("XDG_CONFIG_HOME")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert config_path() == tmp_path / ".config" / "navigator" / "navigator.ini"


def test_a_relative_xdg_config_home_is_ignored(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", "relative")
    monkeypatch.setenv("HOME", str(tmp_path))
    assert config_path() == tmp_path / ".config" / "navigator" / "navigator.ini"


def test_a_missing_file_is_written_with_every_default():
    path = config_path()
    assert not path.exists()
    load_settings()
    text = path.read_text(encoding="utf-8")
    for section in SETTINGS.sections():
        assert f"[{section.name}]" in text
        for field in section.fields():
            assert f"\n{field.name} = " in text
    # The option's comment on its line at a fixed column; the section's under its header.
    assert "\nclock = yes" + " " * 33 + "# Show the clock at the menu bar's right end\n" in text
    assert "[interface]\n# Options > Configuration > Interface" in text
    assert SETTINGS.path == path


def test_what_is_written_reads_back_the_same(tmp_path):
    path = tmp_path / "n.ini"
    SETTINGS.interface.clock = False
    SETTINGS.editor.tab_size = 4
    SETTINGS.panel_defaults.sort_by = "size"
    SETTINGS.save(path)
    other = Settings()
    assert other.load(path) == []
    for mine, theirs in zip(SETTINGS.sections(), other.sections()):
        assert mine.values() == theirs.values()


def test_a_value_edited_by_hand_is_read(tmp_path):
    path = tmp_path / "n.ini"
    path.write_text(
        "[interface]\nclock = off   # mine\n[editor]\ntab_size = 2 ; also mine\n", encoding="utf-8"
    )
    assert SETTINGS.load(path) == []
    assert SETTINGS.interface.clock is False
    assert SETTINGS.editor.tab_size == 2
    # Keys the file left out keep their defaults.
    assert SETTINGS.confirmations.erase_single is True


def test_a_bad_value_keeps_its_default_and_says_so(tmp_path):
    path = tmp_path / "n.ini"
    path.write_text(
        "[interface]\nclock = maybe\n[editor]\ntab_size = wide\n[panel_defaults]\nsort_by = colour\n",
        encoding="utf-8",
    )
    warnings = SETTINGS.load(path)
    assert len(warnings) == 3
    assert "clock" in warnings[0] and "yes or no" in warnings[0]
    assert SETTINGS.interface.clock is True
    assert SETTINGS.editor.tab_size == 8
    assert SETTINGS.panel_defaults.sort_by == "name"


def test_unknown_keys_and_sections_survive_a_save(tmp_path):
    path = tmp_path / "n.ini"
    path.write_text("[interface]\nclock = no\nfuture = 1\n[mine]\nx = y\n", encoding="utf-8")
    SETTINGS.load(path)
    SETTINGS.save(path)
    text = path.read_text(encoding="utf-8")
    assert "future = 1" in text
    assert "[mine]\nx = y" in text
    assert "clock = no" in text


def test_saving_one_section_keeps_an_edit_made_to_another(tmp_path):
    path = tmp_path / "n.ini"
    SETTINGS.save(path)
    # Edited by hand while Navigator runs ...
    path.write_text(
        path.read_text(encoding="utf-8").replace("tab_size = 8", "tab_size = 3"),
        encoding="utf-8",
    )
    # ... and then a dialog's OK saves another section.
    SETTINGS.interface.clock = False
    SETTINGS.save(path, section="interface")
    other = Settings()
    other.load(path)
    assert other.editor.tab_size == 3
    assert other.interface.clock is False


def test_an_unreadable_file_leaves_the_defaults(tmp_path, capsys):
    path = tmp_path / "n.ini"
    path.write_text("not an ini file\n", encoding="utf-8")
    SETTINGS.interface.clock = False
    load_settings(path)
    assert SETTINGS.interface.clock is True
    assert "using the default settings" in capsys.readouterr().err


def test_check_boxes_map_to_fields_in_the_dialogs_order():
    section = InterfaceData()
    section.reset()
    # Clock (bit 0) on by default, Hide status line (bit 2) set here.
    section.hide_status_line = True
    assert section.to_bits(InterfaceData.OPTIONS) == 0b101
    values = InterfaceData.from_bits(InterfaceData.OPTIONS, 0b10)
    assert values["clock"] is False and values["hide_menu_bar"] is True
    assert set(values) == set(InterfaceData.OPTIONS)


# -- the command line over the file ----------------------------------------------------


def test_a_flag_wins_over_the_file_and_is_not_written_back(monkeypatch, tmp_path):
    path = tmp_path / "n.ini"
    path.write_text("[appearance]\ndim_modal = no\n", encoding="utf-8")
    built = {}

    class Fake:
        def __init__(self, left, right, scheme, **kwargs):
            built.update(kwargs)

        def run(self):
            pass

    monkeypatch.setattr(entry, "Navigator", Fake)
    entry.main(["--config", str(path), str(tmp_path)])
    assert built["dim_modal"] is False
    entry.main(["--config", str(path), "--dim-modal", str(tmp_path)])
    assert built["dim_modal"] is True
    assert "dim_modal = no" in path.read_text(encoding="utf-8")


# -- the dialogs ----------------------------------------------------------------------------


def test_interface_ok_applies_and_saves(tmp_path, quiet_console):
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []

    def untick_clock(a):
        seen.append(a.modal)
        a.modal.options.value = a.modal.options.value & ~1

    run_app(app, [
        lambda a: a.spawn(a.run_command(InterfaceSetup)),
        lambda a: None,
        untick_clock,
        KeyEvent("enter"),
        lambda a: None,
        lambda a: seen.append(a.shell.clock.visible),
    ])
    dialog, clock_visible = seen
    assert type(dialog).__name__ == "InterfaceDialog"
    assert SETTINGS.interface.clock is False
    assert clock_visible is False
    assert "clock = no" in config_path().read_text(encoding="utf-8")


def test_cancel_changes_nothing(tmp_path, quiet_console):
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))

    def untick_everything(a):
        a.modal.options.value = 0

    run_app(app, [
        lambda a: a.spawn(a.run_command(SetupConfirmation)),
        lambda a: None,
        untick_everything,
        KeyEvent("escape"),
        lambda a: None,
    ])
    assert SETTINGS.confirmations.to_bits(ConfirmsData.OPTIONS) != 0
    assert not config_path().exists()


def test_editor_viewer_saves_both_its_sections(tmp_path, quiet_console):
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))

    def change(a):
        a.modal.tab_size.value = "004"
        a.modal.viewer.value = 0b10  # Wrap lines

    run_app(app, [lambda a: a.spawn(a.run_command(EditorDefaults)), lambda a: None, change, KeyEvent("enter"), lambda a: None])
    assert SETTINGS.editor.tab_size == 4
    assert SETTINGS.viewer.wrap_lines is True
    text = config_path().read_text(encoding="utf-8")
    assert "tab_size = 4" in text and "wrap_lines = yes" in text


def test_hiding_the_status_line_hides_the_key_bar(tmp_path, quiet_console):
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []
    run_app(app, [
        lambda a: seen.append(a.shell.keybar.visible),
        lambda a: setattr(SETTINGS.interface, "hide_status_line", True),
        lambda a: None,
        lambda a: seen.append(a.shell.keybar.visible),
    ])
    assert seen == [True, False]


# -- what the settings change ------------------------------------------------------------


def test_a_new_panel_takes_show_hidden_from_the_settings(tmp_path):
    from navigator.widgets.manager.panel import Panel

    SETTINGS.system.show_hidden = False
    assert Panel(tmp_path).show_hidden is False


def test_exit_confirmation_asks_and_no_keeps_running(tmp_path, quiet_console):
    SETTINGS.confirmations.exit = True
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []
    run_app(app, [
        KeyEvent("x", "x", alt=True),
        lambda a: None,
        lambda a: seen.append((a.modal and a.modal.title, a.is_running)),
        KeyEvent("n", alt=True),
        lambda a: None,
        lambda a: seen.append((a.modal, a.is_running)),
    ])
    assert seen == [("Exit", True), (None, True)]


def test_without_erase_confirmation_f8_deletes_without_asking(tmp_path, quiet_console):
    SETTINGS.confirmations.erase_single = False
    (tmp_path / "one.txt").write_text("x")
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []

    def delete(a):
        panel = a.manager.left
        panel.cursor = next(i for i, e in enumerate(panel.items) if e.name == "one.txt")
        a.post_event(KeyEvent("f8"))

    run_app(app, [delete, lambda a: seen.append(a.modal), lambda a: None], settle=0.2)
    assert seen == [None]
    assert not (tmp_path / "one.txt").exists()
