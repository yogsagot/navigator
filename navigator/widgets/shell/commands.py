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


class ExecuteCommandLineInWindow(Command):
    """Shift+Enter with something on the command line: run it in a window of
    its own, as ``&`` before it does (``TerminalWindow``).

    Not DOS Navigator's.  Only a terminal speaking the kitty keyboard protocol
    tells Shift+Enter from Enter; elsewhere ``&command`` is the way.
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


class OpenView(Command):
    """File > View > *Open...*: a file chosen in a file box, viewed.

    Not DN's, whose viewer was reached from a panel or the history; here a
    file anywhere can be viewed with no file manager open.
    """

    title = "Open to view"


class OpenEdit(Command):
    """File > Edit > *Open...*: a file chosen in a file box, edited.

    Not DN's, as :class:`OpenView`; unlike Shift+F4's *Edit new file*, the
    box lists the directory and only a file that is there is opened.
    """

    title = "Open to edit"


class OpenTreeWindow(Command):
    """Disk > Directory tree: a *Directory Tree* window on the desktop.

    DOS Navigator's ``cmCreateTree`` -- here opening the ``TTreeWindow`` that
    1.51 defined and never used.
    """

    title = "Tree"


class MountVolume(Command):
    """Volumes > *Mount*: the volume under the cursor mounted through the
    desktop's ``gio`` or KDE's Solid, else ``udisksctl`` -- udisks, no root
    asked.  Not DN's."""

    title = "Mount"


class UnmountVolume(Command):
    """Volumes > *Unmount*: the volume under the cursor unmounted through ``gio``, Solid or udisks."""

    title = "Unmount"


class EjectVolume(Command):
    """Volumes > *Eject*: the volume under the cursor unmounted and its
    medium ejected -- or its drive made safe to remove -- through ``gio``, Solid or udisks."""

    title = "Eject"


class OpenVolumesWindow(Command):
    """Disk > Volumes: every mounted volume, its type, mount point and free space.

    Not DOS Navigator's -- a departure, recorded in ``volumes_window.nml``.
    It takes the place and the letter of DN's ``cmSetVolumeLabel``, *Volume
    label*, which has no POSIX meaning.
    """

    title = "Volumes"


class OpenUsageWindow(Command):
    """Disk > Directory sizes: what takes the room under the active panel's
    directory, biggest first, as ``ncdu`` shows it.

    Not DOS Navigator's -- a departure, asked for, recorded in
    ``navigator/lib/file_ops/dirusage.py``: DN counted a directory's bytes
    (Alt+G, *Directory length*, the tree window's info line) but never ranked
    what is in one by them.
    """

    title = "Directory sizes"


class UsageSortSize(Command):
    """Directory sizes > *Sort by size* (Ctrl+S); again, the other way round."""

    title = "Size"


class UsageSortName(Command):
    """Directory sizes > *Sort by name* (Ctrl+N); again, the other way round."""

    title = "Name"


class UsageSortItems(Command):
    """Directory sizes > *Sort by entries* (Ctrl+E): how many are under each; again, the other way round."""

    title = "Entries"


class ToggleApparentSize(Command):
    """Directory sizes > *Apparent size* (Ctrl+A): the bytes files say they
    hold, or the room they take on the disk (``ncdu``'s ``a``)."""

    title = "Apparent"


class GoToUsage(Command):
    """Directory sizes > *Go*: the active panel to the directory under the
    cursor, or to a file's directory with the cursor on the file."""

    title = "Go"


class OpenProcessWindow(Command):
    """Utilities > Process list: the running processes, sorted and signalled,
    as FAR Manager's process panel lists them.

    Not DOS Navigator's -- a departure, asked for, recorded in
    ``navigator/lib/system/processes.py``: DOS ran one program at a time.
    """

    title = "Processes"


class OpenMonitorWindow(Command):
    """Utilities > System monitor: each processor's load, the memory and the
    sensors, read live.

    Not DOS Navigator's -- a departure, asked for, recorded in
    ``navigator/lib/system/monitor.py``: DOS had one processor and nothing to
    measure it by.
    """

    title = "System monitor"


class ProcessSortPid(Command):
    """Process list > *Sort by PID* (Ctrl+P); again, the other way round."""

    title = "PID"


class ProcessSortUser(Command):
    """Process list > *Sort by user* (Ctrl+U); again, the other way round."""

    title = "User"


class ProcessSortState(Command):
    """Process list > *Sort by state* (Ctrl+E); again, the other way round."""

    title = "State"


class ProcessSortCpu(Command):
    """Process list > *Sort by CPU* (Ctrl+L, the load), busiest first; again, the other way round."""

    title = "CPU"


class ProcessSortMemory(Command):
    """Process list > *Sort by memory* (Ctrl+Z, its size), biggest first; again, the other way round."""

    title = "Memory"


class ProcessSortCommand(Command):
    """Process list > *Sort by command* (Ctrl+N, its name); again, the other way round."""

    title = "Command"


class ProcessTree(Command):
    """Process list > *Tree* (Ctrl+T): each process under its parent, or one flat list."""

    title = "Tree"


class ProcessMineOnly(Command):
    """Process list > *Mine only* (Ctrl+H): only the user's own processes, or everyone's."""

    title = "Mine"


class FilterProcesses(Command):
    """Process list > *Filter* (F4, Ctrl+S): the keyboard to the filter line, htop's F4."""

    title = "Filter"


class SignalProcess(Command):
    """Process list > *Signal* (F7): send the process under the cursor a signal chosen from a box."""

    title = "Signal"


class KillProcess(Command):
    """Process list > *Kill* (F8, Del): ask the process under the cursor to end (SIGTERM), after asking."""

    title = "Kill"


@dataclass(frozen=True, slots=True)
class SendSignal(Command):
    """An entry of *Signal*'s box: *signal* to the process under the cursor."""

    signal: int = 15


class ProcessDetails(Command):
    """Process list > *Details* (F3): what ``/proc`` says of the process under the cursor."""

    title = "Details"


class OpenServiceWindow(Command):
    """Utilities > Services: the system's services (systemd's, OpenRC's, runit's or SysVinit's),
    started, stopped, enabled and followed in their log.

    Not DOS Navigator's -- a departure, asked for, recorded in
    ``navigator/lib/system/services/``: DOS had no service manager.
    """

    title = "Services"


class ServiceVerb(Command):
    """A Services entry that runs ``systemctl VERB`` on the unit under the cursor."""

    verb = ""


class StartService(ServiceVerb):
    """Services > *Start* (F5): ``systemctl start`` on the unit under the cursor."""

    title = "Start"
    verb = "start"


class StopService(ServiceVerb):
    """Services > *Stop* (F8, Del): ``systemctl stop`` on the unit under the cursor, after asking."""

    title = "Stop"
    verb = "stop"


class RestartService(ServiceVerb):
    """Services > *Restart* (F6): ``systemctl restart`` on the unit under the cursor."""

    title = "Restart"
    verb = "restart"


class ReloadService(ServiceVerb):
    """Services > *Reload* (F7): ``systemctl reload``, its configuration read again."""

    title = "Reload"
    verb = "reload"


class EnableService(ServiceVerb):
    """Services > *Enable* (Ctrl+E): ``systemctl enable``, started at boot (or log-in)."""

    title = "Enable"
    verb = "enable"


class DisableService(ServiceVerb):
    """Services > *Disable* (Ctrl+D): ``systemctl disable``, not started at boot."""

    title = "Disable"
    verb = "disable"


class MaskService(ServiceVerb):
    """Services > *Mask*: ``systemctl mask``, never started at all, after asking."""

    title = "Mask"
    verb = "mask"


class UnmaskService(ServiceVerb):
    """Services > *Unmask*: ``systemctl unmask``, a masked unit startable again."""

    title = "Unmask"
    verb = "unmask"


class ServiceJournal(Command):
    """Services > *Journal* (F3): the unit's journal in the viewer, following its end."""

    title = "Journal"


class EditUnitFile(Command):
    """Services > *Edit* (F4): the unit's file in the editor; saved, ``systemctl daemon-reload``."""

    title = "Edit"


class ServiceDetails(Command):
    """Services > *Details* (Enter): what ``systemctl status`` says of the unit under the cursor."""

    title = "Details"


class ServiceUserUnits(Command):
    """Services > *User units* (Ctrl+U): the user's own manager's units, or the system's."""

    title = "User"


class ServiceAllTypes(Command):
    """Services > *All types* (Ctrl+A): timers, sockets, mounts... too, or services only."""

    title = "All"


class FilterServices(Command):
    """Services > *Filter* (F4, Ctrl+S): the keyboard to the filter line."""

    title = "Filter"


class ServiceSortName(Command):
    """Services > *Sort by name* (Ctrl+N); again, the other way round."""

    title = "Name"


class ServiceSortActive(Command):
    """Services > *Sort by state* (Ctrl+L, whether it runs); again, the other way round."""

    title = "State"


class ServiceSortFileState(Command):
    """Services > *Sort by start-up* (enabled, disabled, static...); again, the other way round."""

    title = "Start-up"


class ServiceSortDescription(Command):
    """Services > *Sort by description*; again, the other way round."""

    title = "Description"


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


@dataclass(frozen=True, slots=True)
class OpenCalendar(Command):
    """Utilities > Calendar: a month on the desktop, today marked.

    Not DOS Navigator 1.51's, which had no calendar -- a departure, asked for:
    Turbo Vision's ``TCalendarWindow`` from Borland's TVDEMO, the calendar a
    Turbo Vision desktop of the time offered beside its calculator.
    *under_clock* is a click on the clock, which puts it in the top right
    corner just under the clock rather than in the middle, or closes it when
    it is open (also asked for).
    """

    title = "Calendar"
    under_clock: bool = False


class EnvEdit(Command):
    """Utilities > Edit environment: the environment variables, in an editor.

    DOS Navigator's ``cmEnvEdit`` (``EditDOSEvironment``).
    """


class HistoryList(Command):
    """Alt+F8, Utilities > Commands History: the commands typed, in a box.

    DOS Navigator's ``cmHistoryList`` (``CmdHistory``).
    """


class FuzzyHistory(Command):
    """Alt+Shift+F8, Utilities > Search history (fzf): the commands typed, here
    and in the shell, searched by fzf on the console; the one chosen goes on
    the line.  Not DOS Navigator's (a departure, asked for).
    """


class OpenCommandPalette(Command):
    """Alt+Shift+P, ≡ > Command palette: every command that applies where the
    keyboard is -- the menus' items and the keys bound there -- found by a few
    of its letters and run (``CommandPalette``).  Not DOS Navigator's (a
    departure, asked for).
    """

    title = "Commands"


class MenuFileEdit(Command):
    """Options > Global menu definition: the global ``menu.ini`` in an editor.

    DOS Navigator's ``cmMenuFileEdit``; F4 in the global user menu too.
    """


class LocalMenuFileEdit(Command):
    """Options > Local menu definition: the active panel's ``.navigator-menu.ini`` in an editor.

    DOS Navigator's ``cmLocalMenuFileEdit``; F4 in a local user menu too.
    """


class Game(Command):
    """≡ > Game, Alt+F9: DOS Navigator's ``cmGame`` -- *Navigator's game*,
    Tetris.  No title: DN's status line gave Alt+F9 no caption."""


class ToggleTrashCan(Command):
    """≡ > Trashcan on/off: DOS Navigator's ``cmHideShowTools`` -- the trash
    can files are dropped on to erase them, shown or hidden."""

    title = "Trashcan"


class OpenTrash(Command):
    """Disk > Trash, and a double click on the trash can: the active panel
    on the Trash (``trash:///``).

    Not DOS Navigator's: the double click ran its *Reanimator*, an undelete,
    which the freedesktop Trash is on a POSIX system
    (:mod:`navigator.lib.drives.trash`).
    """

    title = "Trash"


class EmptyTrash(Command):
    """Disk > Empty Trash: everything in the Trash erased for good, once asked."""

    title = "Empty Trash"


class SaversSetup(Command):
    """Options > Configuration > Screen savers: DOS Navigator's ``cmSaversSetup``."""

    title = "Screen Savers"


class CountrySetup(Command):
    """Options > Configuration > Country support: DOS Navigator's
    ``cmCountrySetup`` -- how a file's date and time are written."""

    title = "Country"


class ScreenRest(Command):
    """≡ > Screen rest: DOS Navigator's ``cmScreenRest`` -- a screen saver now
    (``InsertIdler``)."""

    title = "Screen Rest"


__all__ = [
    "About",
    "EditLinks",
    "S3Link",
    "GvfsLink",
    "DockerLink",
    "PodmanLink",
    "AdbLink",
    "DockerShell",
    "PodmanShell",
    "AdbShell",
    "SaversSetup",
    "CountrySetup",
    "ToggleTrashCan",
    "OpenTrash",
    "EmptyTrash",
    "Game",
    "ScreenRest",
    "MenuFileEdit",
    "HistoryList",
    "FuzzyHistory",
    "EnvEdit",
    "SystemInfo",
    "OpenCalendar",
    "ExecuteOsCommand",
    "SaveDesktop",
    "LoadDesktop",
    "LocalMenuFileEdit",
    "ExecuteCommandLine",
    "ExecuteCommandLineInWindow",
    "CompleteCommandLine",
    "InsertName",
    "InsertPath",
    "CommandLineHome",
    "CommandLineEnd",
    "NewManager",
    "OpenTreeWindow",
    "OpenVolumesWindow",
    "OpenUsageWindow",
    "UsageSortSize",
    "UsageSortName",
    "UsageSortItems",
    "ToggleApparentSize",
    "GoToUsage",
    "MountVolume",
    "UnmountVolume",
    "EjectVolume",
    "OpenProcessWindow",
    "OpenMonitorWindow",
    "ProcessSortPid",
    "ProcessSortUser",
    "ProcessSortState",
    "ProcessSortCpu",
    "ProcessSortMemory",
    "ProcessSortCommand",
    "ProcessTree",
    "ProcessMineOnly",
    "FilterProcesses",
    "SignalProcess",
    "KillProcess",
    "ProcessDetails",
    "SendSignal",
    "OpenServiceWindow",
    "ServiceVerb",
    "StartService",
    "StopService",
    "RestartService",
    "ReloadService",
    "EnableService",
    "DisableService",
    "MaskService",
    "UnmaskService",
    "ServiceJournal",
    "EditUnitFile",
    "ServiceDetails",
    "ServiceUserUnits",
    "ServiceAllTypes",
    "FilterServices",
    "ServiceSortName",
    "ServiceSortActive",
    "ServiceSortFileState",
    "ServiceSortDescription",
    "ToggleMarkBySpace",
]


# -- Options > Configuration and Options > File Manager ---------------------------
#
# Each opens *Settings* on its own page -- once a dialog of its own over a
# section of ``navigator.ini`` (:mod:`navigator.settings`) -- and OK saves the
# sections that changed.


class Settings(Command):
    """Options > Settings: every setup page behind one row of tabs.

    Not DN's, which had a dialog to each; it opens on the first page.
    """

    title = "Settings"


class SystemSetup(Command):
    """Options > Configuration > System Setup: DOS Navigator's ``cmSystemSetup``."""

    title = "System Setup"


class StartupSetup(Command):
    """Options > Configuration > Startup: DOS Navigator's ``cmStartup``."""

    title = "Startup"


class InterfaceSetup(Command):
    """Options > Configuration > Interface: DOS Navigator's ``cmInterfaceSetup``."""

    title = "Interface"


class KeyBindingsSetup(Command):
    """Options > Configuration > Key bindings: every key table's keys, and
    ``keybindings.ini`` written with them.  Not DOS Navigator's, which had no
    key editor -- a departure, by request (:mod:`navigator.lib.config.keybindings`)."""

    title = "Keys"


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


class EditHGL(Command):
    """Options > Highlight file edit: DOS Navigator's ``cmEditHGL``, ``highlight.ini`` (DN's ``DN.HGL``)."""

    title = "Highlight File"


class EditMacros(Command):
    """Options > Macro file edit: ``macros.ini``, the editor's macros -- DN
    kept them in ``DN.HGL``, edited by Highlight file edit; a file of their
    own here, beside it (``navigator.lib.config.macros``)."""

    title = "Macro File"


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


class NavyLink(Command):
    """Utilities > *SSH link (SFTP)*, Alt+F11: where DOS Navigator had
    ``cmNavyLink``, *Navigator Link*, which linked two PCs over a cable --
    here an SSH connection to a server, its files over SFTP, and the active
    panel sent there (:mod:`navigator.lib.drives`).  Named for its protocol,
    a departure: *Navigator Link* would not say what is on the wire."""

    title = "SSH"


class Terminal(Command):
    """Utilities > *Remote shell* > *SSH*: where DOS Navigator had
    ``cmTerminal``, the modem's terminal window (``DNUTIL.PAS``
    ``OpenTerminal``) -- here a login shell on a server chosen in SSH's link
    manager, ``ssh -t`` in a command window (``TerminalWindow``).  One still
    running for that server is brought forward instead, as DN's
    ``Term^.Select`` brought back its one terminal.  A departure in what is at
    the other end: a server's shell, not a modem."""

    title = "Term"
    scheme = "sftp"


class DockerShell(Command):
    """Utilities > *Remote shell* > *Docker container*: a shell in a container
    chosen in Docker's link manager, ``docker exec -it``.  Not DN's."""

    title = "Docker shell"
    scheme = "docker"


class PodmanShell(Command):
    """Utilities > *Remote shell* > *Podman container*: ``podman exec -it``."""

    title = "Podman shell"
    scheme = "podman"


class AdbShell(Command):
    """Utilities > *Remote shell* > *Android device*: ``adb shell`` on a
    device chosen in Android's link manager."""

    title = "adb shell"
    scheme = "adb"


class DockerLink(Command):
    """Utilities > *Link* > *Docker container*: a running container's files,
    through ``docker exec`` (:mod:`navigator.lib.drives.docker`), and the
    active panel sent there.  Not DN's."""

    title = "Docker"
    scheme = "docker"


class PodmanLink(Command):
    """Utilities > *Link* > *Podman container*: the same through ``podman exec``."""

    title = "Podman"
    scheme = "podman"


class AdbLink(Command):
    """Utilities > *Link* > *Android device (adb)*: a device's files through
    ``adb shell`` (:mod:`navigator.lib.drives.adb`), and the active panel
    sent there."""

    title = "Android"
    scheme = "adb"


class HangUp(Command):
    """Utilities > *Disconnect*, Alt+H: DN's ``cmHangUp``.  Closes a connection
    -- the one, or one chosen of several -- and its panels go back to the disk,
    as ``cmCloseLinked`` sent them."""

    title = "Discon"


class CloseRootAccess(Command):
    """Utilities > *Close root access*: the root helper closed now, rather
    than ``[system] root_timeout`` minutes after its last step; the panels
    browsing ``root:`` go back to the disk.  Not DN's: DOS refused no one
    (``navigator.lib.system.elevate``)."""

    title = "Unroot"


class ToggleRootAccess(Command):
    """Utilities > *Elevate root access* / *Close root access*: one entry,
    captioned by whether root access is open -- the root helper started
    (asking for the password), or closed as :class:`CloseRootAccess` closes
    it.  Not DN's (``navigator.lib.system.elevate``)."""

    title = "Root"


class EditLinks(Command):
    """Utilities > *Saved links*: the connection profiles in one box -- edited,
    added, deleted, reordered, kept on OK -- and one connected to.

    Ours: DN's link was one cable, with no list of places to keep.
    """


class SetupLink(Command):
    """Options > Configuration > *Communications*: where DN had ``cmSetupModem``
    -- the ``[remote]`` settings."""

    title = "Comms"


class FtpLink(Command):
    """Utilities > *FTP link*: a connection to an FTP server -- FTPS when *Encrypt
    with TLS* is ticked -- and the active panel sent there.  DN had none; its
    link was the cable's (``cmNavyLink``)."""

    title = "FTP"
    scheme = "ftp"


class S3Link(Command):
    """Utilities > *S3 link (Amazon S3)*: a connection to Amazon S3 or an
    endpoint that speaks its protocol (MinIO, Ceph, R2, ...), its buckets
    listed, and the active panel sent there."""

    title = "S3"
    scheme = "s3"


class GvfsLink(Command):
    """Utilities > *GVfs/KIO link*: a place the desktop's GVfs -- or KDE's
    KIO -- reaches -- a phone over MTP, a WebDAV, AFP or NFS share, Google
    Drive -- named by its URI, mounted with ``gio mount``
    (:mod:`navigator.lib.drives.gvfs`) or through kio-fuse
    (:mod:`navigator.lib.drives.kio`), and the active panel sent there.
    Not DN's."""

    title = "GVfs"
    scheme = "gvfs"


class SmbLink(Command):
    """Utilities > *SMB link (Windows share)*: a connection to a Windows -- or
    Samba -- share, and the active panel sent there."""

    title = "SMB"
    scheme = "smb"


class ShowBackground(Command):
    """Window > *Background operation*: the progress box of a copy or an
    erase sent to the background put back up -- the one there is, or, with
    more, the one chosen from a list of them (``Shell.choose_background``;
    ``navigator.lib.system.background``).  Not DN's, whose boxes held the
    screen."""

    title = "Backgr"
