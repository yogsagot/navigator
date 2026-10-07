"""The shell's commands: what ``Shell`` handles.

The command line's own -- run, complete, Home and End, the name typed onto it
-- and the screen-wide ones: About, a new file manager, the tree window, and
Space's tag, which is the command line's rule.  See ``navigator/commands.py``
for where the rest live.
"""

from __future__ import annotations

from dataclasses import dataclass

from navkit.commands import Command


class About(Command):
    """≡ > About: DOS Navigator's ``cmAbout``, the name, version and author."""

    title = "About"


class ExecuteCommandLine(Command):
    """Enter with something on the command line: run it.

    DOS Navigator's ``cmExecCommandLine``, which the panel's own Enter sent
    first and fell back from when the line was blank (``FLPANELX.PAS``).
    Here that is a key table's rule rather than the panel's: bound on the
    application, so it is asked before the panel sees Enter, and disabled
    while the line is empty, so the key falls through to the panel.
    """


class CompleteCommandLine(Command):
    """Tab with something on the command line: complete the word at the caret.

    Not DOS Navigator's -- ``TCommandLine`` completed nothing, and Tab only
    ever switched panels.  Bound the way Enter is, so the rule is Enter's:
    with the line empty the command is disabled and Tab falls through to the
    panels, and with text on it the shell is asked what the word could be.
    """


class InsertName(Command):
    """Ctrl+Enter: the name under the panel's cursor, typed onto the command line.

    DOS Navigator's ``_CtrlEnter`` (``FLPANELX.PAS``) sending ``cmInsertName``.
    On ``..`` it is the panel's own directory, whole.  Alt+Enter is bound to
    it as well, Midnight Commander's key for the same thing, because a
    terminal that does not speak the kitty keyboard protocol sends Ctrl+Enter
    as a plain Enter.
    """


class InsertPath(Command):
    """Ctrl+Shift+Enter: as :class:`InsertName`, but the whole path.

    ``_CtrlEnter`` with Shift held, which prefixed the panel's directory.
    """


class CommandLineHome(Command):
    """Home with something on the command line: to its start, not the list's top."""


class CommandLineEnd(Command):
    """End with something on the command line: to its end, not the list's bottom."""


class NewManager(Command):
    """Ctrl+F3: another file manager window, the size of the desktop.

    DOS Navigator's ``cmCreatePanel``, Manager > New.
    """

    title = "New Manager"


class ViewHistory(Command):
    """Alt+PgDn: *File View History*, DOS Navigator's ``cmViewHistory``.

    The files viewed, newest first; *Open* views one again as it was left.
    """

    title = "View History"


class EditHistory(Command):
    """Alt+PgUp: *File Edit History*, DOS Navigator's ``cmEditHistory``."""

    title = "Edit History"


class OpenTreeWindow(Command):
    """Disk > Directory tree: a *Directory Tree* window on the desktop.

    DOS Navigator's ``cmCreateTree`` -- here opening the ``TTreeWindow`` that
    1.51 defined and never used.
    """

    title = "Tree"


class ToggleMarkBySpace(Command):
    """Space with the command line empty: :class:`ToggleMark`.

    DN's ``fmoSpaceToggle``, on by default: ``kbSpace`` shared ``kbIns``'s
    branch but gave up whenever ``CmdLine.Str`` was not empty, so that a blank
    typed into a command still reached it.  A command of its own because that
    condition is the command line's, and ``Shell`` -- which owns the line --
    is what handles it.
    """


class SaveDesktop(Command):
    """Options > Save desktop: the windows kept, to be had back.

    DOS Navigator's ``cmSaveDesk`` (``SaveRealDsk``).
    """


class LoadDesktop(Command):
    """Options > Load desktop: the windows last kept, in place of these.

    DOS Navigator's ``cmLoadDesk`` (``RetrieveDesktop``).
    """


class ChangeColors(Command):
    """Options > Colors: every entry's colours and attributes, edited.

    DOS Navigator's ``cmChangeColors`` (``ChangeColors``, COLORS.PAS).
    """


class StoreColors(Command):
    """Options > Store palette: the palette written to a file of one's own.

    DOS Navigator's ``cmStoreColors`` (``StoreColors``, DNUTIL.PAS).
    """


class LoadColors(Command):
    """Options > Load palette: a palette read from a file, in place of this one.

    DOS Navigator's ``cmLoadColors`` (``LoadColors``, DNUTIL.PAS).
    """


class ExecuteOsCommand(Command):
    """File > Execute OS command: a command line asked in a box, and run.

    DOS Navigator's ``cmExecuteDOSCmd`` (``ExecDOSCmd``).  *Os*, not *OS*,
    so its handler is ``on_execute_os_command`` -- the reason
    :class:`FileManagerSetup` is spelled out.
    """


class SystemInfo(Command):
    """Utilities > System Information: the machine, its disks, memory and system.

    DOS Navigator's ``cmSystemInfo`` (``SystemInfo``).
    """


class EnvEdit(Command):
    """Utilities > Edit environment: the environment variables, in an editor.

    DOS Navigator's ``cmEnvEdit`` (``EditDOSEvironment``).
    """


class HistoryList(Command):
    """Alt+F8, Utilities > Commands History: the commands typed, in a box.

    DOS Navigator's ``cmHistoryList`` (``CmdHistory``).
    """


class MenuFileEdit(Command):
    """Options > Global menu definition: the global ``dn.mnu`` in an editor.

    DOS Navigator's ``cmMenuFileEdit``; F4 in the global user menu too.
    """


class LocalMenuFileEdit(Command):
    """Options > Local menu definition: the active panel's ``dn.mnu`` in an editor.

    DOS Navigator's ``cmLocalMenuFileEdit``; F4 in a local user menu too.
    """


__all__ = [
    "About",
    "MenuFileEdit",
    "HistoryList",
    "EnvEdit",
    "SystemInfo",
    "ExecuteOsCommand",
    "SaveDesktop",
    "LoadDesktop",
    "LocalMenuFileEdit",
    "ExecuteCommandLine",
    "CompleteCommandLine",
    "InsertName",
    "InsertPath",
    "CommandLineHome",
    "CommandLineEnd",
    "NewManager",
    "OpenTreeWindow",
    "ToggleMarkBySpace",
]


# -- Options > Configuration and Options > File Manager ---------------------------
#
# Each opens one setup dialog over a section of ``navigator.ini``
# (:mod:`navigator.settings`) and saves that section when it is accepted.


class SystemSetup(Command):
    """Options > Configuration > System Setup: DOS Navigator's ``cmSystemSetup``."""

    title = "System Setup"


class StartupSetup(Command):
    """Options > Configuration > Startup: DOS Navigator's ``cmStartup``."""

    title = "Startup"


class InterfaceSetup(Command):
    """Options > Configuration > Interface: DOS Navigator's ``cmInterfaceSetup``."""

    title = "Interface"


class SetupConfirmation(Command):
    """Options > Configuration > Confirmations: DOS Navigator's ``cmSetupConfirmation``."""

    title = "Confirmations"


class EditorDefaults(Command):
    """Options > Configuration > Editor/Viewer: DOS Navigator's ``cmEditorDefaults``."""

    title = "Editor/Viewer"


class FileManagerSetup(Command):
    """Options > File Manager > Setup: DOS Navigator's ``cmFMSetup``.

    Spelled out because ``FMSetup`` would be handled by ``on_f_m_setup``.
    """

    title = "File Manager Setup"


class DriveInfoSetup(Command):
    """Options > File Manager > Information panel: DOS Navigator's ``cmDriveInfoSetup``."""

    title = "Information Panel"


class ColumnDefaults(Command):
    """Options > File Manager > Column defaults: DOS Navigator's ``cmColumnDefaults``."""

    title = "Column Defaults"


class HighlightGroups(Command):
    """Options > File Manager > Highlight groups: DOS Navigator's ``cmHighlightGroups``."""

    title = "Highlight Groups"


class EditQuickRun(Command):
    """Options > Quick run file edit: DOS Navigator's ``cmEditQuickRun``, ``quickrun.ini`` (DN's ``DN.XRN``)."""

    title = "Quick Run File"


class ExtFileEdit(Command):
    """Options > Extension file edit: DOS Navigator's ``cmExtFileEdit``, ``extensions.ini`` (DN's ``DN.EXT``)."""

    title = "Extension File"


class ExternalViewers(Command):
    """Options > Viewers: DOS Navigator's ``cmExternalViewers``, ``viewers.ini`` (DN's ``DN.VWR``)."""

    title = "Viewers"


class ExternalEditors(Command):
    """Options > Editors: DOS Navigator's ``cmExternalEditors``, ``editors.ini`` (DN's ``DN.EDT``)."""

    title = "Editors"


@dataclass(frozen=True, slots=True)
class QuickRun(Command):
    """Ctrl+Shift+F1 .. F10: DOS Navigator's ``QuickExecExternal``, *number*'s
    section of ``quickrun.ini``.  DN's own help said Ctrl+Alt; its code read
    Shift, which is also what a Linux console leaves alone."""

    number: int = 1


class FileManagerDefaults(Command):
    """Options > File Manager > New Manager defaults: DOS Navigator's ``cmFMDefaults``.

    Spelled out for the reason :class:`FileManagerSetup` is.
    """

    title = "Panel Defaults"
