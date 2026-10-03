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


def test_a_dropped_dos_option_is_read_quietly_and_not_written_back(tmp_path):
    path = tmp_path / "n.ini"
    path.write_text("[system]\nfast_execution = yes\nfuture = 1\n"
                    "[file_manager]\ndescription_files = descript.ion\n", encoding="utf-8")
    assert SETTINGS.load(path) == []
    SETTINGS.save(path)
    text = path.read_text(encoding="utf-8")
    assert "fast_execution" not in text and "description_files" not in text
    assert "future = 1" in text


def test_a_renamed_choice_is_read_quietly_and_written_new(tmp_path):
    path = tmp_path / "n.ini"
    path.write_text("[panel_defaults]\nsort_by = group\nleft_panel = Drive\n", encoding="utf-8")
    assert SETTINGS.load(path) == []
    assert (SETTINGS.panel_defaults.sort_by, SETTINGS.panel_defaults.left_panel) == ("type", "files")
    SETTINGS.save(path)
    text = path.read_text(encoding="utf-8")
    assert "sort_by = type" in text and "left_panel = files" in text


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
    # Clock (bit 0), the two stored positions (bits 7, 8) and the two
    # histories (bits 9, 10) on by default, Hide status line (bit 2) set here.
    section.hide_status_line = True
    assert section.to_bits(InterfaceData.OPTIONS) == 0b111_1000_0101
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


def test_nav_refuses_to_start_inside_navigator(monkeypatch, tmp_path, capsys):
    def refuse(*args, **kwargs):
        raise AssertionError("Navigator was built")

    monkeypatch.setattr(entry, "Navigator", refuse)
    monkeypatch.setenv("NAVIGATOR", "1")
    assert entry.main([str(tmp_path)]) == 1
    assert "already running" in capsys.readouterr().err
    assert entry.main(["--list-themes"]) == 0


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


def test_history_size_is_typed_in_interface_setup_and_sizes_every_history(tmp_path, quiet_console):
    from navml.history import HISTORY

    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []

    def type_size(a):
        seen.append(a.modal.history_size.value)
        a.modal.history_size.value = "007"

    run_app(app, [
        lambda a: seen.append(HISTORY.limit),
        lambda a: a.spawn(a.run_command(InterfaceSetup)),
        lambda a: None,
        type_size,
        KeyEvent("enter"),
        lambda a: None,
        lambda a: seen.append(HISTORY.limit),
    ])
    assert seen == [50, "050", 7]
    assert SETTINGS.interface.history_size == 7
    assert "history_size = 7" in config_path().read_text(encoding="utf-8")


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


def test_a_hidden_menu_bar_gives_its_row_and_shows_only_while_open(tmp_path, quiet_console):
    SETTINGS.interface.hide_menu_bar = True
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []

    def look(a):
        seen.append((a.shell.menu.visible, a.shell.desktop.y))

    run_app(app, [look, KeyEvent("f10"), lambda a: None, look, KeyEvent("escape"), lambda a: None, look])
    # The desktop keeps the top row throughout: the open bar floats over it.
    assert seen == [(False, 0), (True, 0), (False, 0)]


def test_a_shown_menu_bar_is_docked_above_the_desktop(tmp_path, quiet_console):
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []
    run_app(app, [lambda a: seen.append((a.shell.menu.visible, a.shell.menu.y, a.shell.desktop.y))])
    assert seen == [(True, 0, 1)]


def test_a_hidden_command_line_gives_its_row_and_takes_no_keys(tmp_path, quiet_console):
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []

    def look(a):
        seen.append((a.shell.command_line.visible, a.shell.desktop.height, a.shell.command_line.value))

    run_app(app, [
        look,
        lambda a: setattr(SETTINGS.interface, "hide_command_line", True),
        lambda a: None,
        KeyEvent("x", "x"),
        lambda a: None,
        look,
    ])
    (shown, height, _), (hidden_visible, hidden_height, typed) = seen
    assert shown is True and hidden_visible is False
    assert hidden_height == height + 1
    assert typed == ""


def test_an_auto_hidden_command_line_shows_only_while_it_has_text(tmp_path, quiet_console):
    SETTINGS.interface.auto_hide_command_line = True
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []

    def look(a):
        seen.append((a.shell.command_line.visible, a.shell.desktop.height))

    run_app(app, [
        look,
        KeyEvent("x", "x"),
        lambda a: None,
        look,
        KeyEvent("escape"),
        lambda a: None,
        look,
    ])
    (empty, height), (typed, typed_height), (cleared, cleared_height) = seen
    assert (empty, typed, cleared) == (False, True, False)
    assert typed_height == height - 1 and cleared_height == height


@pytest.mark.parametrize("ticked", [True, False])
def test_esc_on_an_empty_line_shows_the_user_screen_only_when_ticked(tmp_path, quiet_console, ticked):
    SETTINGS.interface.esc_user_screen = ticked
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []

    def look(a):
        seen.append(a.shell.console_visible)

    run_app(app, [KeyEvent("escape"), lambda a: None, look, KeyEvent("escape"), lambda a: None, look])
    assert seen == ([True, False] if ticked else [False, False])


def test_esc_on_a_line_with_text_clears_it_instead(tmp_path, quiet_console):
    SETTINGS.interface.esc_user_screen = True
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []
    run_app(app, [
        KeyEvent("x", "x"),
        KeyEvent("escape"),
        lambda a: None,
        lambda a: seen.append((a.shell.command_line.value, a.shell.console_visible)),
    ])
    assert seen == [("", False)]


def test_block_insert_cursor_makes_the_command_lines_caret_a_block(tmp_path, quiet_console):
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []

    def look(a):
        seen.append(a._cursor()[2])

    run_app(app, [
        KeyEvent("x", "x"),
        lambda a: None,
        look,
        lambda a: setattr(SETTINGS.interface, "block_insert_cursor", True),
        lambda a: None,
        look,
    ])
    assert seen == ["default", "block"]


# -- Use internal terminal: Midnight Commander's Ctrl+O -----------------------------------


class _Pty:
    """What a Subshell writes to, kept."""

    def __init__(self):
        self.written = []

    def write(self, data):
        self.written.append(data)


def _relayable_subshell():
    from navkit.console import ConsoleScreen
    from navigator.subshell import Subshell

    shell = Subshell(ConsoleScreen(80, 24))
    shell.process = _Pty()
    shell._ready = True
    shell._prompt = b"$ "
    return shell


def test_the_relay_shows_the_held_back_prompt_once():
    shell, out = _relayable_subshell(), []
    shell.start_relay(out.append)
    shell.stop_relay()
    shell.start_relay(out.append)
    assert out == [b"$ "]


def test_a_line_typed_and_abandoned_is_cleared_and_the_prompt_shown_anew():
    shell, out = _relayable_subshell(), []
    shell.start_relay(out.append)
    shell.relay_input(b"ls")
    shell.stop_relay()
    # Ctrl+E, Ctrl+U: the shell's editor forgets it ...
    assert shell.process.written == [b"ls", b"\x05\x15"]
    # ... and the next time the prompt starts a line of its own.
    shell.start_relay(out.append)
    assert out == [b"$ ", b"\r\n", b"$ "]


def test_a_line_entered_at_the_relayed_shell_waits_for_its_next_prompt():
    shell, out = _relayable_subshell(), []
    shell.start_relay(out.append)
    shell.relay_input(b"vim\r")
    shell.stop_relay()
    assert shell.process.written == [b"vim\r"]
    # Not ready: a command the command line sends now waits for the prompt.
    assert shell._ready is False


def test_the_relayed_shell_does_not_answer_queries_the_real_terminal_answers():
    shell = _relayable_subshell()
    shell.start_relay(lambda data: None)
    shell.screen.respond(b"\x1b[1;1R")
    shell.stop_relay()
    shell.screen.respond(b"\x1b[1;1R")
    assert shell.process.written == [b"\x1b[1;1R"]


def _relaying_app(tmp_path):
    SETTINGS.system.internal_terminal = False
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    return app


def test_without_the_internal_terminal_ctrl_o_lends_the_real_one(tmp_path, quiet_console):
    app = _relaying_app(tmp_path)
    seen = []

    def tty(a):
        a.terminal.is_tty = True

    def look(a):
        seen.append((a.released, a.terminal.suspended, a.shell.console_visible, a.shell.console.relayed))

    def type_and_return(a):
        seen.append(a.shell._relayed_input(b"ls\x0fX"))

    run_app(app, [tty, KeyEvent("o", ctrl=True), lambda a: None, look, type_and_return, look])
    assert seen == [(True, True, False, True), b"X", (False, False, False, False)]


def test_a_command_from_the_line_runs_on_the_real_terminal_and_comes_back(tmp_path, quiet_console, monkeypatch):
    app = _relaying_app(tmp_path)
    ran = []
    monkeypatch.setattr(
        "navigator.widgets.shell.console.Console.run",
        lambda self, command, cwd=None: ran.append(command),
    )
    seen = []

    def tty(a):
        a.terminal.is_tty = True

    run_app(app, [
        tty,
        lambda a: a.shell.run_command("make"),
        lambda a: seen.append(a.released),
        lambda a: a.shell.command_finished(0, tmp_path),
        lambda a: seen.append(a.released),
    ])
    assert ran == ["make"] and seen == [True, False]


def test_without_a_real_terminal_ctrl_o_falls_back_to_the_console(tmp_path, quiet_console):
    app = _relaying_app(tmp_path)
    seen = []
    run_app(app, [
        KeyEvent("o", ctrl=True),
        lambda a: None,
        lambda a: seen.append((a.released, a.shell.console_visible)),
    ])
    assert seen == [(False, True)]


@pytest.mark.parametrize("tick, answer, asks_again, quits", [
    (True, "y", False, True),    # Don't ask again, Yes: saved, and gone
    (True, "n", True, False),    # ... with No: nothing changes
    (False, "y", True, True),    # Yes alone: asked next time too
])
def test_dont_ask_again_on_exit(tmp_path, quiet_console, tick, answer, asks_again, quits):
    SETTINGS.confirmations.exit = True
    app = Navigator(tmp_path, tmp_path, terminal=FakeTerminal(80, 24))
    seen = []

    def tick_box(a):
        seen.append(type(a.modal).__name__)
        if tick:
            a.modal.options.value = 1

    actions = [KeyEvent("x", "x", alt=True), lambda a: None, tick_box, KeyEvent(answer, answer, alt=True), lambda a: None]
    if not quits:
        actions.append(lambda a: seen.append(a.is_running))
    run_app(app, actions)
    assert seen[0] == "ExitDialog"
    if not quits:
        assert seen[1] is True
    assert SETTINGS.confirmations.exit is asks_again
    saved = config_path().exists() and "exit = no" in config_path().read_text(encoding="utf-8")
    assert saved is (not asks_again)


# -- File Manager Setup, New Manager defaults, the editor's Auto indent ------------------


@pytest.fixture
def listing(tmp_path, quiet_console):
    (tmp_path / "alpha").mkdir()
    (tmp_path / "pack.zip").write_text("x")
    (tmp_path / "plain").write_text("    indented\n")
    return tmp_path


def _left(app):
    return app.manager.left


def test_without_space_toggles_space_types(listing):
    SETTINGS.file_manager.space_toggles_selection = False
    app = Navigator(listing, listing, terminal=FakeTerminal(80, 24))
    run_app(app, [KeyEvent("down"), KeyEvent(" ", " ")])
    assert _left(app).marked == frozenset()
    assert app.shell.command_line.value == " "


def test_without_bs_upper_dir_backspace_stays(listing):
    SETTINGS.file_manager.bs_upper_dir = False
    app = Navigator(listing, listing, terminal=FakeTerminal(80, 24))
    run_app(app, [lambda a: setattr(_left(a), "path", listing / "alpha"),
                  lambda a: a.post_event(KeyEvent("backspace"))])
    assert _left(app).path == listing / "alpha"


def test_without_del_erases_del_is_disabled_and_f8_is_not(listing):
    from navigator.widgets.manager.commands import Delete

    SETTINGS.file_manager.del_erases = False
    app = Navigator(listing, listing, terminal=FakeTerminal(80, 24))
    seen = []

    def look(a):
        _left(a).cursor = 2
        seen.append((a.manager.enables(Delete(by_key=True)), a.manager.enables(Delete())))

    run_app(app, [lambda a: None, look])
    assert seen == [(False, True)]


def test_column_titles_come_and_go_with_the_setting(listing):
    app = Navigator(listing, listing, terminal=FakeTerminal(80, 24))
    seen = []
    run_app(app, [
        lambda a: _left(a).cycle_view_mode(),
        lambda a: seen.append(_left(a).header),
        lambda a: setattr(SETTINGS.file_manager, "column_titles", False),
        lambda a: None,
        lambda a: seen.append(_left(a).header),
    ])
    assert seen == [1, 0]


def test_the_tag_sign_is_the_settings_and_can_be_switched_off(listing):
    SETTINGS.file_manager.tag_sign = "*"
    app = Navigator(listing, listing, terminal=FakeTerminal(80, 24))
    seen = []
    run_app(app, [
        lambda a: seen.append(_left(a).tag_char),
        lambda a: setattr(SETTINGS.file_manager, "tag_character", False),
        lambda a: seen.append(_left(a).tag_char),
    ])
    assert seen == ["*", ""]


def test_without_files_highlight_every_file_is_plain(listing):
    SETTINGS.panel_defaults.files_highlight = False
    app = Navigator(listing, listing, terminal=FakeTerminal(80, 24))
    seen = []

    def look(a):
        panel = _left(a)
        index = next(i for i, e in enumerate(panel.items) if e.name == "pack.zip")
        seen.append(panel.row_style(index, panel.items[index]) == panel.part_style("row"))

    run_app(app, [lambda a: None, look])
    assert seen == [True]


def test_the_info_line_shows_only_what_the_defaults_ask_for(listing):
    app = Navigator(listing, listing, terminal=FakeTerminal(80, 24))
    seen = []

    def look(a):
        seen.append(_left(a).footer_text())

    def tag(a):
        panel = _left(a)
        panel.cursor = next(i for i, e in enumerate(panel.items) if e.name == "plain")
        panel.marked = frozenset({"pack.zip"})

    run_app(app, [
        tag, lambda a: None, look,
        lambda a: setattr(SETTINGS.panel_defaults, "selected_files", False), look,
        lambda a: setattr(SETTINGS.panel_defaults, "current_file", False), look,
    ])
    assert "selected files" in seen[0]
    assert seen[1:] == [" plain ", ""]


def test_without_auto_indent_enter_starts_the_new_line_at_the_margin(listing):
    SETTINGS.editor.auto_indent = False
    app = Navigator(listing, listing, terminal=FakeTerminal(80, 24))
    seen = {}

    def open_plain(a):
        panel = _left(a)
        panel.cursor = next(i for i, e in enumerate(panel.items) if e.name == "plain")
        a.post_event(KeyEvent("f4"))

    run_app(app, [open_plain, lambda a: None, KeyEvent("end"), KeyEvent("enter"),
                  KeyEvent("x", "x"),
                  lambda a: seen.update(text=a.shell.desktop.active_window.editor.document.encode())])
    assert seen["text"] == b"    indented\nx\n"
