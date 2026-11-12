# navml: generated
"""Generated from ``shell.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

#: Everything the generator needs for itself is underscored, so a document may
#: import any name at all without colliding with it -- there is no reserved
#: word.  A bare ``Label:`` head is what asks for ``_Component``; markup
#: never names it.  See *Importing another component* in navml/DESIGN.md.
from typing import Any as _Any

from navkit.events import Event as _Event
from navkit.reactive import bind as _bind
from navkit.reactive import reactive as _reactive

from navml.component import Component as _Component
from navigator.widgets.shell.clock import Clock    # shell.nml:1
from navigator.widgets.shell.command_line import CommandLine    # shell.nml:2
from navigator.widgets.shell.console import Console    # shell.nml:3
from navigator.widgets.shell.keybar import KeyBar    # shell.nml:4
from navigator.widgets.shell.job_mark import JobMark    # shell.nml:5
from navigator.widgets.shell.macro_mark import MacroMark    # shell.nml:6
from navigator.widgets.shell.main_menu import MainMenu    # shell.nml:7
from navml.widgets.menu.commands import MainMenu as MainMenuCommand    # shell.nml:8
from navigator.widgets.shell.root_mark import RootMark    # shell.nml:9
from navigator.widgets.shell.trash_can import TrashCan    # shell.nml:10
from navigator.lib.config import country    # shell.nml:11
from navigator.settings import SETTINGS    # shell.nml:12
from navml.widgets.desktop import Desktop    # shell.nml:13
from navml.widgets.layout.dock_layout import DockLayout    # shell.nml:14
from navml.widgets.window_strip import WindowStrip    # shell.nml:15
from navigator.widgets.shell.commands import AdbShell, ChangeColors, CloseRootAccess, ColumnDefaults, CommandLineEnd    # shell.nml:16
from navigator.widgets.shell.commands import CommandLineHome, CompleteCommandLine, CountrySetup, DockerShell    # shell.nml:17
from navigator.widgets.shell.commands import DriveInfoSetup, EditHistory, EditQuickRun, EditorDefaults, EnvEdit    # shell.nml:18
from navigator.widgets.shell.commands import ExecuteCommandLine, ExecuteOsCommand, ExtFileEdit, ExternalEditors    # shell.nml:19
from navigator.widgets.shell.commands import ExternalViewers, FileManagerDefaults, FileManagerSetup, FuzzyHistory    # shell.nml:20
from navigator.widgets.shell.commands import HangUp, HighlightGroups, HistoryList, InsertName, InsertPath    # shell.nml:21
from navigator.widgets.shell.commands import InterfaceSetup, KeyBindingsSetup, LoadColors, LoadDesktop    # shell.nml:22
from navigator.widgets.shell.commands import OpenCommandPalette, OpenEdit, OpenView, PodmanShell, SaversSetup    # shell.nml:23
from navigator.widgets.shell.commands import ScreenRest, Settings, SetupConfirmation, SetupLink, StartupSetup    # shell.nml:24
from navigator.widgets.shell.commands import StoreColors, SystemInfo, SystemSetup, Terminal, ToggleMarkBySpace    # shell.nml:25
from navigator.widgets.shell.commands import ToggleRootAccess, ToggleTrashCan, ViewHistory    # shell.nml:26
from navigator.commands import AsciiTable, ScreenGrab, ShowUserScreen    # shell.nml:27
from navigator.widgets.manager.commands import HideLeft, HideRight, UserMenu    # shell.nml:28
from navigator.lib.config.associations import EDITORS, EXTENSIONS, QUICK_RUN, VIEWERS    # shell.nml:29

__navml_component__ = "Shell"

__all__ = ["Shell"]


class Shell(DockLayout, _Component):
    """The Navigator screen: the console, the desktop over it, the menu bar and

    clock over that, the command line, key bar.

    The band between the two bars holds two layers, and the order of the
    children is the whole of how they stack.  The console is the bottom one and
    is **always showing** -- it is the background the windows float over, as the
    user screen was in DOS Navigator.  The desktop is the layer above it and
    holds every window; it paints nothing of its own, so the console shows
    between them.  Ctrl+O hides the desktop, which is one reactive flag and one
    ``visible`` line.  The key bar is last so nothing covers it, and a modal is
    overlaid on this root, which puts it above the desktop by construction.

    The bars dock against the top and bottom edges, and the two layers both
    *fill*, which a dock layout gives them as one shared rectangle -- it places
    every fill after every edge, so the key bar can come last in the child
    order, and so last in the paint, and still be carved off first.

    The command line docks after the key bar, which is what puts it on the row
    above it: edges are carved in child order, so the key bar takes the last
    row and the line the one left at the bottom.  DOS Navigator's
    ``InitCommandLine`` put it there, and gave up that row from the desktop.
    """

    #: The document this class was generated from.
    __navml_source__ = "shell.nml"

    #: Whether Ctrl+O has put the windows away.  One flag that the desktop's
    #: ``visible`` line reads, which is the whole of Ctrl+O.
    console_visible: bool = _reactive(False)    # shell.nml:55

    #: Ids, annotated so the hand-written half completes them.
    console: Console    # shell.nml:134
    desktop: Desktop    # shell.nml:137
    menu: MainMenu    # shell.nml:153
    window_strip: WindowStrip    # shell.nml:168
    clock: Clock    # shell.nml:187
    root_mark: RootMark    # shell.nml:200
    macro_mark: MacroMark    # shell.nml:213
    job_mark: JobMark    # shell.nml:228
    trash: TrashCan    # shell.nml:239
    keybar: KeyBar    # shell.nml:247
    key_root_mark: RootMark    # shell.nml:260
    command_line: CommandLine    # shell.nml:278

    #: The commands this component handles itself.
    async def on_load_desktop(self, event: _Any) -> bool:    # shell.nml:58
        """``LoadDesktop``."""
        self.spawn(self.load_desktop())
        return True

    async def on_change_colors(self, event: _Any) -> bool:    # shell.nml:59
        """``ChangeColors``."""
        self.spawn(self.change_colors())
        return True

    async def on_store_colors(self, event: _Any) -> bool:    # shell.nml:60
        """``StoreColors``."""
        self.spawn(self.store_colors())
        return True

    async def on_load_colors(self, event: _Any) -> bool:    # shell.nml:61
        """``LoadColors``."""
        self.spawn(self.load_colors())
        return True

    async def on_execute_os_command(self, event: _Any) -> bool:    # shell.nml:62
        """``ExecuteOsCommand``."""
        self.spawn(self.execute_os_command())
        return True

    async def on_system_info(self, event: _Any) -> bool:    # shell.nml:63
        """``SystemInfo``."""
        self.spawn(self.system_info())
        return True

    async def on_env_edit(self, event: _Any) -> bool:    # shell.nml:64
        """``EnvEdit``."""
        self.spawn(self.edit_environment())
        return True

    async def on_fuzzy_history(self, event: _Any) -> bool:    # shell.nml:65
        """``FuzzyHistory``."""
        self.fuzzy_history()
        return True

    async def on_open_command_palette(self, event: _Any) -> bool:    # shell.nml:66
        """``OpenCommandPalette``."""
        self.spawn(self.command_palette())
        return True

    async def on_history_list(self, event: _Any) -> bool:    # shell.nml:67
        """``HistoryList``."""
        self.spawn(self.command_history())
        return True

    async def on_screen_grab(self, event: _Any) -> bool:    # shell.nml:68
        """``ScreenGrab``."""
        self.spawn(self.screen_grab())
        return True

    async def on_show_user_screen(self, event: _Any) -> bool:    # shell.nml:70
        """Alt+F5, ≡ > *User screen*: :meth:`show_user_screen`."""
        self.show_user_screen()
        return True

    async def on_main_menu(self, event: _Any) -> bool:    # shell.nml:73
        """``cmMainMenu``, Editor > File > *Main menu*: the bar's first entry, highlighted and not dropped, as ``cmMenu`` left the main bar."""
        self.menu.open(0)
        return True

    async def on_command_line_home(self, event: _Any) -> bool:    # shell.nml:74
        """``CommandLineHome``."""
        self.command_line.home()
        return True

    async def on_command_line_end(self, event: _Any) -> bool:    # shell.nml:75
        """``CommandLineEnd``."""
        self.command_line.end()
        return True

    async def on_complete_command_line(self, event: _Any) -> bool:    # shell.nml:81
        """Tab: ask the shell what the word at the caret could become.  The answer comes back later, posted from the pty's reader, and is applied by :meth:`completions_ready` -- only if the line is still what it was asked about."""
        self._ask_completions()
        return True

    async def on_toggle_mark_by_space(self, event: _Any) -> bool:    # shell.nml:82
        """``ToggleMarkBySpace``."""
        self.active_manager.active_panel.toggle_mark()
        return True

    async def on_user_menu(self, event: _Any) -> bool:    # shell.nml:84
        """F2, Utilities > *User menu*: ``cmUserMenu``, DN's ``ExecUserMenu``."""
        self.spawn(self.user_menu())
        return True

    async def on_edit_quick_run(self, event: _Any) -> bool:    # shell.nml:85
        """``EditQuickRun``."""
        self.spawn(self.edit_associations(QUICK_RUN))
        return True

    async def on_ext_file_edit(self, event: _Any) -> bool:    # shell.nml:86
        """``ExtFileEdit``."""
        self.spawn(self.edit_associations(EXTENSIONS))
        return True

    async def on_external_viewers(self, event: _Any) -> bool:    # shell.nml:87
        """``ExternalViewers``."""
        self.spawn(self.edit_associations(VIEWERS))
        return True

    async def on_external_editors(self, event: _Any) -> bool:    # shell.nml:88
        """``ExternalEditors``."""
        self.spawn(self.edit_associations(EDITORS))
        return True

    async def on_ascii_table(self, event: _Any) -> bool:    # shell.nml:90
        """Ctrl+B, Utilities > *Character table*: DN's ``ASCIITable``."""
        self.spawn(self.ascii_table())
        return True

    async def on_insert_name(self, event: _Any) -> bool:    # shell.nml:91
        """``InsertName``."""
        self._insert_entry(whole=False)
        return True

    async def on_insert_path(self, event: _Any) -> bool:    # shell.nml:92
        """``InsertPath``."""
        self._insert_entry(whole=True)
        return True

    async def on_execute_command_line(self, event: _Any) -> bool:    # shell.nml:99
        """Enter: run the line in the shell, with the console up while it runs.  The console takes the keyboard for the length of the command, so a program that reads the terminal -- an editor, a pager, a password prompt -- gets what is typed.  The windows come back when the shell reports its prompt, in :meth:`command_finished`."""
        self.run_command(self.command_line.value)
        return True

    async def on_hide_left(self, event: _Any) -> bool:    # shell.nml:100
        """``HideLeft``."""
        self.show_manager_side('left')
        return True

    async def on_hide_right(self, event: _Any) -> bool:    # shell.nml:101
        """``HideRight``."""
        self.show_manager_side('right')
        return True

    async def on_settings(self, event: _Any) -> bool:    # shell.nml:102
        """``Settings``."""
        self.spawn(self.settings())
        return True

    async def on_system_setup(self, event: _Any) -> bool:    # shell.nml:103
        """``SystemSetup``."""
        self.spawn(self.settings('system'))
        return True

    async def on_startup_setup(self, event: _Any) -> bool:    # shell.nml:104
        """``StartupSetup``."""
        self.spawn(self.settings('startup'))
        return True

    async def on_interface_setup(self, event: _Any) -> bool:    # shell.nml:105
        """``InterfaceSetup``."""
        self.spawn(self.settings('interface'))
        return True

    async def on_setup_link(self, event: _Any) -> bool:    # shell.nml:106
        """``SetupLink``."""
        self.spawn(self.settings('remote'))
        return True

    async def on_terminal(self, event: _Any) -> bool:    # shell.nml:107
        """``Terminal``."""
        self.spawn(self.open_remote_shell('sftp'))
        return True

    async def on_docker_shell(self, event: _Any) -> bool:    # shell.nml:108
        """``DockerShell``."""
        self.spawn(self.open_remote_shell('docker'))
        return True

    async def on_podman_shell(self, event: _Any) -> bool:    # shell.nml:109
        """``PodmanShell``."""
        self.spawn(self.open_remote_shell('podman'))
        return True

    async def on_adb_shell(self, event: _Any) -> bool:    # shell.nml:110
        """``AdbShell``."""
        self.spawn(self.open_remote_shell('adb'))
        return True

    async def on_hang_up(self, event: _Any) -> bool:    # shell.nml:111
        """``HangUp``."""
        self.spawn(self.hang_up())
        return True

    async def on_close_root_access(self, event: _Any) -> bool:    # shell.nml:112
        """``CloseRootAccess``."""
        self.spawn(self.close_root_access())
        return True

    async def on_toggle_root_access(self, event: _Any) -> bool:    # shell.nml:113
        """``ToggleRootAccess``."""
        self.spawn(self.close_root_access() if self.root_mark.open else self.open_root_access())
        return True

    async def on_key_bindings_setup(self, event: _Any) -> bool:    # shell.nml:114
        """``KeyBindingsSetup``."""
        self.spawn(self.key_bindings())
        return True

    async def on_setup_confirmation(self, event: _Any) -> bool:    # shell.nml:115
        """``SetupConfirmation``."""
        self.spawn(self.settings('confirmations'))
        return True

    async def on_editor_defaults(self, event: _Any) -> bool:    # shell.nml:116
        """``EditorDefaults``."""
        self.spawn(self.settings('editor_viewer'))
        return True

    async def on_file_manager_setup(self, event: _Any) -> bool:    # shell.nml:117
        """``FileManagerSetup``."""
        self.spawn(self.settings('file_manager'))
        return True

    async def on_drive_info_setup(self, event: _Any) -> bool:    # shell.nml:118
        """``DriveInfoSetup``."""
        self.spawn(self.settings('drive_info'))
        return True

    async def on_column_defaults(self, event: _Any) -> bool:    # shell.nml:119
        """``ColumnDefaults``."""
        self.spawn(self.settings('column_defaults'))
        return True

    async def on_toggle_trash_can(self, event: _Any) -> bool:    # shell.nml:121
        """≡ > Trashcan on/off: ``cmHideShowTools``."""
        self.trash.shown = not self.trash.shown
        return True

    async def on_savers_setup(self, event: _Any) -> bool:    # shell.nml:122
        """``SaversSetup``."""
        self.spawn(self.settings('savers'))
        return True

    async def on_country_setup(self, event: _Any) -> bool:    # shell.nml:123
        """``CountrySetup``."""
        self.spawn(self.settings('country'))
        return True

    async def on_screen_rest(self, event: _Any) -> bool:    # shell.nml:124
        """``ScreenRest``."""
        self.spawn(self.rest(asked=True))
        return True

    async def on_highlight_groups(self, event: _Any) -> bool:    # shell.nml:125
        """``HighlightGroups``."""
        self.spawn(self.settings('highlight_groups'))
        return True

    async def on_file_manager_defaults(self, event: _Any) -> bool:    # shell.nml:126
        """``FileManagerDefaults``."""
        self.spawn(self.settings('panel_defaults'))
        return True

    async def on_view_history(self, event: _Any) -> bool:    # shell.nml:127
        """``ViewHistory``."""
        self.spawn(self.file_history('view'))
        return True

    async def on_edit_history(self, event: _Any) -> bool:    # shell.nml:128
        """``EditHistory``."""
        self.spawn(self.file_history('edit'))
        return True

    async def on_open_view(self, event: _Any) -> bool:    # shell.nml:129
        """``OpenView``."""
        self.spawn(self.open_chosen('view'))
        return True

    async def on_open_edit(self, event: _Any) -> bool:    # shell.nml:130
        """``OpenEdit``."""
        self.spawn(self.open_chosen('edit'))
        return True

    # One stub per (id, emitted event), each wired in ``__init__``
    # below.  They return False, so a component that overrides none
    # of them is exactly a component that never mentioned them: the
    # event carries on up to whatever the document's own handler
    # does with it.  The hand-written half is the *derived* class,
    # so its override wins over the stub without either half naming
    # the other.

    async def on_desktop_opened(self, event: _Event) -> bool:    # shell.nml:137
        """``desktop`` raised an event whose handler is ``on_opened``."""
        return False

    def __init__(self, **kwargs: _Any) -> None:
        super().__init__(**kwargs)
        self.console = Console(parent=self)    # shell.nml:133
        self.desktop = Desktop(parent=self)    # shell.nml:136
        self.menu = MainMenu(parent=self)    # shell.nml:152
        self.window_strip = WindowStrip(parent=self)    # shell.nml:167
        self.clock = Clock(parent=self)    # shell.nml:186
        self.root_mark = RootMark(parent=self)    # shell.nml:199
        self.macro_mark = MacroMark(parent=self)    # shell.nml:212
        self.job_mark = JobMark(parent=self)    # shell.nml:227
        self.trash = TrashCan(parent=self)    # shell.nml:238
        self.keybar = KeyBar(parent=self)    # shell.nml:246
        self.key_root_mark = RootMark(parent=self)    # shell.nml:259
        self.command_line = CommandLine(parent=self)    # shell.nml:277

        self.desktop.visible = _bind(lambda _o: not _o.parent.console_visible)    # shell.nml:138

        async def _on_emptied(event):    # shell.nml:140
            self.show_console()
            return True
        self.desktop.on_emptied = _on_emptied
        self.desktop.on_opened = self.on_desktop_opened    # shell.nml:137

        self.menu.context = _bind(    # shell.nml:154
            lambda _o: None if _o.parent.console_visible else self.desktop.active_window
        )
        self.menu.width = _bind(lambda _o: _o.parent.width)    # shell.nml:155
        self.menu.height = 1    # shell.nml:156
        self.menu.inline_style = _bind(    # shell.nml:157
            lambda _o: 'dock: none' if SETTINGS.interface.hide_menu_bar else 'dock: top; basis: 1'
        )
        self.menu.visible = _bind(    # shell.nml:158
            lambda _o: not SETTINGS.interface.hide_menu_bar or _o.current >= 0
        )
        self.menu.reserve = _bind(    # shell.nml:159
            lambda _o: max(0, _o.width - self.clock.x + 1) if self.clock.visible else 0
        )

        self.window_strip.desktop = _bind(lambda _o: _o.parent.desktop)    # shell.nml:169
        self.window_strip.align = 'right'    # shell.nml:170
        self.window_strip.x = _bind(    # shell.nml:171
            lambda _o: self.menu.item_span(len(self.menu.entries()))[0] + 1 + (self.job_mark.width if self.job_mark.visible else 0)
        )
        self.window_strip.y = 0    # shell.nml:172
        self.window_strip.height = 1    # shell.nml:173
        self.window_strip.labels = _bind(    # shell.nml:177
            lambda _o: SETTINGS.interface.window_strip == 'full'
        )
        self.window_strip.visible = _bind(    # shell.nml:178
            lambda _o: SETTINGS.interface.window_strip != 'off' and (not SETTINGS.interface.hide_menu_bar) and (not _o.parent.console_visible)
        )
        self.window_strip.width = _bind(    # shell.nml:175
            lambda _o: max(0, (self.macro_mark.x - 1 if self.macro_mark.visible and self.macro_mark.width else self.root_mark.x - 1 if self.root_mark.visible and self.root_mark.width else self.clock.x - 1 if self.clock.visible and self.clock.width else _o.parent.width - 1) - _o.x)
        )
        self.window_strip.inline_style = 'dock: none'    # shell.nml:179

        self.clock.visible = _bind(lambda _o: SETTINGS.interface.clock)    # shell.nml:188
        self.clock.width = _bind(lambda _o: 7 if country.twelve_hours() else 5)    # shell.nml:189
        self.clock.y = 0    # shell.nml:190
        self.clock.x = _bind(lambda _o: max(0, _o.parent.width - _o.width))    # shell.nml:192
        self.clock.inline_style = 'dock: none'    # shell.nml:193

        self.root_mark.y = 0    # shell.nml:201
        self.root_mark.width = _bind(lambda _o: _o.natural_width)    # shell.nml:202
        self.root_mark.visible = _bind(    # shell.nml:206
            lambda _o: _o.open and (not SETTINGS.interface.hide_menu_bar) and (not _o.parent.console_visible)
        )
        self.root_mark.x = _bind(    # shell.nml:204
            lambda _o: max(0, (self.clock.x - 1 if self.clock.visible and self.clock.width else _o.parent.width) - _o.width)
        )
        self.root_mark.inline_style = 'dock: none'    # shell.nml:207

        self.macro_mark.y = 0    # shell.nml:214
        self.macro_mark.width = _bind(lambda _o: _o.natural_width)    # shell.nml:215
        self.macro_mark.visible = _bind(    # shell.nml:219
            lambda _o: _o.slot > 0 and (not SETTINGS.interface.hide_menu_bar) and (not _o.parent.console_visible)
        )
        self.macro_mark.x = _bind(    # shell.nml:217
            lambda _o: max(0, (self.root_mark.x - 1 if self.root_mark.visible and self.root_mark.width else self.clock.x - 1 if self.clock.visible and self.clock.width else _o.parent.width - 1) - _o.width)
        )
        self.macro_mark.inline_style = 'dock: none'    # shell.nml:220

        self.job_mark.x = _bind(lambda _o: self.strip_start() - _o.width)    # shell.nml:229
        self.job_mark.y = 0    # shell.nml:230
        self.job_mark.width = _bind(lambda _o: _o.natural_width)    # shell.nml:231
        self.job_mark.visible = _bind(    # shell.nml:232
            lambda _o: _o.busy and (not SETTINGS.interface.hide_menu_bar) and (not _o.parent.console_visible)
        )
        self.job_mark.inline_style = 'dock: none'    # shell.nml:233

        self.trash.desktop = _bind(lambda _o: _o.parent.desktop)    # shell.nml:240
        self.trash.inline_style = 'dock: none'    # shell.nml:241

        self.keybar.visible = _bind(    # shell.nml:248
            lambda _o: not SETTINGS.interface.hide_status_line
        )
        self.keybar.reserve = _bind(    # shell.nml:250
            lambda _o: self.key_root_mark.width + 1 if self.key_root_mark.visible else 0
        )
        self.keybar.inline_style = 'dock: bottom; basis: 1'    # shell.nml:251

        self.key_root_mark.open = _bind(lambda _o: self.root_mark.open)    # shell.nml:261
        self.key_root_mark.y = _bind(lambda _o: self.keybar.y)    # shell.nml:262
        self.key_root_mark.width = _bind(lambda _o: _o.natural_width)    # shell.nml:263
        self.key_root_mark.visible = _bind(    # shell.nml:266
            lambda _o: _o.open and self.keybar.visible and (SETTINGS.interface.hide_menu_bar or _o.parent.console_visible)
        )
        self.key_root_mark.x = _bind(    # shell.nml:265
            lambda _o: max(0, _o.parent.width - _o.width)
        )
        self.key_root_mark.inline_style = 'dock: none'    # shell.nml:267

        self.command_line.prompt = _bind(lambda _o: _o.parent.command_prompt)    # shell.nml:279
        self.command_line.prompt_cells = _bind(    # shell.nml:280
            lambda _o: _o.parent.command_prompt_cells
        )
        self.command_line.visible = _bind(    # shell.nml:281
            lambda _o: not SETTINGS.interface.hide_command_line and (not SETTINGS.interface.auto_hide_command_line or _o.value != '')
        )
        self.command_line.inline_style = 'dock: bottom; basis: 1'    # shell.nml:282
