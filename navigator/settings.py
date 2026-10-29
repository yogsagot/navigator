"""Navigator's settings: ``navigator.ini``, and the one object that holds them.

DOS Navigator kept its setup in ``DN.CFG``, a binary file of tagged records
(``DNUTIL.PAS``'s ``WriteConfig``, the records in ``STARTUP.PAS``).  **Storing
them as an ini file is a departure**: a text file under ``~/.config`` is what a
POSIX user expects to read, edit and keep in a dotfiles repository, and a
record layout copied byte for byte from Turbo Pascal would be none of those.

What is DN's is everything else.  The sections are DN's setup records, one
per *Options > Configuration* dialog, and their fields are those dialogs'
check boxes and lines **in the dialog's order**, so a dialog maps item *i* of
its ``CheckBoxes`` to field *i* (:meth:`Section.to_bits`).  The items that
only meant something on DOS -- XMS/EMS, video modes, overlays, Int28, the CD
player, the per-drive list, "fast" execution, advanced copy, blinking,
timeslicing, the drive line, ``descript.ion`` descriptions, the quick search
key and Alt/Ctrl difference -- are left out of both; :data:`OBSOLETE` names
the ones an older ``navigator.ini`` may still hold.

How it works:

* :data:`SETTINGS` is the one instance, the way :data:`navml.history.HISTORY`
  is.  ``main()`` loads it before anything is built; tests reset it.
* Every field is a navkit reactive attribute, so markup can bind to one
  (``visible: SETTINGS.interface.clock``) and follows a dialog's OK at once.
  That replaces DN's ``cmUpdateConfig`` broadcast.
* The schema is the class body: the attribute's name is the ini key, the
  default's type is how the value is read, and :class:`Setting`'s *doc* is the
  comment written above it.
* :meth:`Settings.save` writes through :class:`navml.coder.Coder`, to a
  temporary file renamed over the old one.  Saving one section re-reads the
  file first and replaces only that section, so an edit made by hand while
  Navigator runs survives a dialog's OK.  Keys and sections it does not know
  are carried over, but comments written by hand are not: the generated ones
  replace them.  Each option's comment sits on its line at
  :data:`COMMENT_COLUMN`, and each section's right under its header.
"""

from __future__ import annotations

import configparser
import contextlib
import os
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any, ClassVar

from navkit.i18n import tr
from navkit.reactive import Reactive
from navml.coder import Coder

from navigator.lib.appearance import filetypes
#: The file's name, in the directory :func:`config_dir` names.
FILE_NAME = "navigator.ini"

#: The column every option's comment starts at, after ``key = value``.  A
#: longer line pushes its comment along, two spaces after the value.
COMMENT_COLUMN = 44

#: What starts a comment after a value -- so a value cannot contain `` #`` or
#: `` ;``, since everything from there on is read as the comment.
INLINE_COMMENT_PREFIXES = ("#", ";")


#: The database's file name, in :func:`state_dir`.
DATABASE_NAME = "navigator.db"


def config_dir() -> Path:
    """``$XDG_CONFIG_HOME/navigator``, or ``~/.config/navigator`` without one.

    The XDG Base Directory rule, which macOS terminal tools follow as well;
    an unset or relative ``XDG_CONFIG_HOME`` is ignored, as the spec says.
    """
    base = os.environ.get("XDG_CONFIG_HOME", "")
    root = Path(base) if base and os.path.isabs(base) else Path.home() / ".config"
    return root / "navigator"


def config_path() -> Path:
    """Where ``navigator.ini`` lives unless ``--config`` says otherwise."""
    return config_dir() / FILE_NAME


def state_dir() -> Path:
    """``$XDG_STATE_HOME/navigator``, or ``~/.local/state/navigator`` without one.

    Where XDG puts what a program remembers rather than what it is told --
    histories, recently used -- which is what the database holds.  The same
    rule as :func:`config_dir` for an unset or relative variable.
    """
    base = os.environ.get("XDG_STATE_HOME", "")
    root = (
        Path(base) if base and os.path.isabs(base)
        else Path.home() / ".local" / "state"
    )
    return root / "navigator"


def database_path() -> Path:
    """Where the database lives unless ``--database`` says otherwise."""
    return state_dir() / DATABASE_NAME


#: SmartPad's file: DN's ``'SmartPad' + '.DN'``.
SMARTPAD_NAME = "SmartPad.DN"


def smartpad_path() -> Path:
    """SmartPad's file: in the directory ``$SMARTPAD`` names, as DN read it, else
    beside the database -- where DN's fell back to its own directory."""
    directory = os.environ.get("SMARTPAD", "").strip()
    return (Path(directory).expanduser() if directory else state_dir()) / SMARTPAD_NAME


class Setting(Reactive):
    """One key of ``navigator.ini``: a reactive attribute that knows how to be written.

    *doc* is the comment above the key.  *choices* limits a string to a set of
    words, and *aliases* maps a word an older file may hold to the choice
    that replaced it, so it is read without a warning and written back new.
    *honoured* false says nothing reads the setting yet, which the comment
    then tells whoever edits the file.
    """

    def __init__(
        self,
        default: bool | int | str,
        *,
        doc: str,
        choices: tuple[str, ...] | None = None,
        aliases: Mapping[str, str] | None = None,
        honoured: bool = True,
    ) -> None:
        super().__init__(default)
        self.doc = doc
        self.choices = choices
        self.aliases = dict(aliases or {})
        self.honoured = honoured

    def parse(self, text: str) -> bool | int | str:
        """*text* as this key's type; ``ValueError`` if it is not one."""
        text = text.strip()
        if isinstance(self.default, bool):
            value = configparser.ConfigParser.BOOLEAN_STATES.get(text.lower())
            if value is None:
                raise ValueError(f"expected yes or no, not {text!r}")
            return value
        if isinstance(self.default, int):
            return int(text)
        if self.choices is not None:
            word = text.lower()
            word = self.aliases.get(word, word)
            if word not in self.choices:
                raise ValueError(f"expected one of {', '.join(self.choices)}, not {text!r}")
            return word
        return text

    def format(self, value: Any) -> str:
        """*value* as the ini file spells it."""
        if isinstance(value, bool):
            return "yes" if value else "no"
        return str(value)

    def comment(self) -> str:
        text = self.doc
        if self.choices is not None:
            text += f" ({' / '.join(self.choices)})"
        if not self.honoured:
            text += " -- stored, not yet honoured"
        return text


class Section:
    """One ``[section]`` of the file, and one DN setup record."""

    #: The ``[name]`` in the file and the attribute on :class:`Settings`.
    name: ClassVar[str] = ""
    #: The comment above the section header: what DN called the dialog.
    title: ClassVar[str] = ""

    @classmethod
    def fields(cls) -> list[Setting]:
        """Every :class:`Setting` of this section, in declaration order."""
        found: dict[str, Setting] = {}
        for klass in reversed(cls.__mro__):
            for key, value in vars(klass).items():
                if isinstance(value, Setting):
                    found[key] = value
        return list(found.values())

    @classmethod
    def field(cls, key: str) -> Setting | None:
        value = getattr(cls, key, None)
        return value if isinstance(value, Setting) else None

    def values(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in self.fields()}

    def update(self, values: Mapping[str, Any]) -> None:
        """Assign *values* by key; each a reactive write, so bindings follow."""
        for key, value in values.items():
            if self.field(key) is None:
                raise KeyError(f"[{self.name}] has no setting {key!r}")
            setattr(self, key, value)

    def reset(self) -> None:
        for field in self.fields():
            setattr(self, field.name, field.default)

    def to_bits(self, names: Iterable[str]) -> int:
        """The boolean fields *names* as a ``CheckBoxes.value``: bit *i* is name *i*."""
        return sum(1 << i for i, name in enumerate(names) if getattr(self, name))

    @staticmethod
    def from_bits(names: Iterable[str], bits: int) -> dict[str, bool]:
        """A ``CheckBoxes.value`` back into ``{name: ticked}``."""
        return {name: bool(bits >> i & 1) for i, name in enumerate(names)}

    @classmethod
    def tooltip(cls, name: str) -> str:
        """Setting *name*'s doc, the ``navigator.ini`` comment, translated: a
        setup page's tooltip for the control that sets it."""
        field = cls.field(name)
        return tr(field.doc) if field is not None else ""

    @classmethod
    def tooltips(cls, names: Iterable[str]) -> list[str]:
        """:meth:`tooltip` for each of *names*: a ``CheckBoxes.tooltips``
        in step with the value :meth:`to_bits` gives it."""
        return [cls.tooltip(name) for name in names]

    @classmethod
    def bit_groups(cls) -> list[tuple[str, ...]]:
        """The tuples of setting names a page turns into check boxes
        (``OPTIONS``, ``DISPLAY``...): the class's upper-case tuples of names."""
        return [value for key, value in vars(cls).items()
                if key.isupper() and isinstance(value, tuple)
                and value and all(isinstance(name, str) and cls.field(name) for name in value)]


# -- the sections ---------------------------------------------------------------


#: What ``--colors`` and ``[appearance] colors`` accept: detect, or a depth.
COLOR_DEPTHS = ("auto", "mono", "8", "16", "256", "truecolor")
#: What ``--glyphs`` and ``[appearance] glyphs`` accept: detect, or a tier.
GLYPH_TIERS = ("auto", "ascii", "unicode", "nerd")
#: What ``--marks`` and ``[appearance] marks`` accept: the looks of
#: :data:`navkit.glyphs.MARKS` but ``ascii``, which ``--glyphs ascii`` gives.
MARK_LOOKS = ("dos", "brackets", "boxes")


class AppearanceData(Section):
    """What the command line's flags set, which DN kept under *Colors*.

    A flag still wins for the session it is given in, and is never written
    back here.
    """

    name = "appearance"
    title = "Appearance -- the --theme, --palette, --colors, --glyphs, --marks and --dim-modal flags"

    theme: str = Setting("default", doc="Colour scheme, one of `nav --list-themes`")
    palette: str = Setting(
        "dos", choices=("dos", "terminal"),
        doc="What a colour name means: DN's VGA value, or the terminal's own scheme",
    )
    colors: str = Setting(
        "auto", choices=COLOR_DEPTHS,
        doc="How many colours the terminal shows; auto reads COLORTERM and TERM",
    )
    glyphs: str = Setting(
        "auto", choices=GLYPH_TIERS,
        doc="Which characters the terminal's font draws",
    )
    #: Not DN's, whose marks were Turbo Vision's ``[X]`` and ``(•)`` -- still
    #: there as ``dos``.  The default keeps the brackets and puts Unicode's
    #: check mark and filled circle in them; ``boxes`` drops the brackets.
    marks: str = Setting(
        "brackets", choices=MARK_LOOKS,
        doc="How check boxes and radio buttons are drawn: dos [X] (•), brackets [✓] (●), boxes without brackets",
    )
    dim_modal: bool = Setting(True, doc="Paint what lies behind a dialog faint")


#: What an unexpected exception does: a box, or quitting with a traceback.
ON_ERROR = ("dialog", "crash")
#: What *As root* asks for root with (``navigator.lib.system.elevate.CHOICES``).
ELEVATE = ("auto", "sudo", "pkexec", "off")
#: ``[system] desktop_vfs``: whose desktop plumbing is asked
#: (navigator.lib.system.desktop) -- auto is KDE's KIO in a KDE session, else GIO.
DESKTOP_VFS = ("auto", "gio", "kio", "off")


class SystemData(Section):
    """``dlgSystemSetup`` / ``TSystemData``."""

    name = "system"
    title = "Options > Configuration > System Setup (DN's dlgSystemSetup)"

    OPTIONS: ClassVar[tuple[str, ...]] = (
        "internal_editor", "internal_viewer", "system_clipboard", "show_hidden",
        "flush_buffers", "internal_terminal", "command_window_zoomed", "command_window_modal",
    )

    internal_editor: bool = Setting(True, doc="F4 opens the internal editor; off runs $EDITOR")
    internal_viewer: bool = Setting(True, doc="F3 opens the internal viewer; off runs $PAGER")
    #: DN's default was off, its own clipboard; Navigator has always used the
    #: desktop's, so on.
    system_clipboard: bool = Setting(
        True, doc="Copy to and paste from the desktop's clipboard; off, Navigator's own",
    )
    #: DN's default was off; Navigator's panels have always shown them.
    show_hidden: bool = Setting(True, doc="A new panel shows hidden files (Ctrl+H toggles one)")
    #: DN flushed DOS's disk caches; on POSIX that is an fsync of what was written.
    flush_buffers: bool = Setting(True, doc="Sync each file to disk as it is copied")
    #: Not DN's: Midnight Commander's Ctrl+O, for whoever prefers it.
    internal_terminal: bool = Setting(
        True, doc="Ctrl+O shows the console inside Navigator; off hands the real terminal to the shell, as mc does",
    )
    #: Not DN's: how a command run in a window of its own opens (``&command``,
    #: Shift+Enter, a user menu item's ``<&``), unless it says otherwise.
    command_window_zoomed: bool = Setting(True, doc="A command run in a window opens it zoomed")
    command_window_modal: bool = Setting(
        False, doc="A command run in a window holds every key until the window is closed",
    )
    #: DN's ``SwpDir``: where the shell's rc files and the user menu's script go.
    temp_dir: str = Setting("", doc="Temporary directory; empty means $TMPDIR")
    #: Not DN's, whose failures were Pascal's ``Runtime error NNN at``: what an
    #: exception escaping Navigator's code does.  Never nothing -- either
    #: way it is appended to ``errors.log`` beside ``navigator.db`` as well.
    on_error: str = Setting(
        "dialog", choices=ON_ERROR,
        doc="An unexpected error shows a box with its traceback, or quits printing it",
    )
    #: Not DN's: a frame loop busy this long is written to ``errors.log``
    #: with the input before it and every stack (``errorlog.Watchdog``).
    stall_report: int = Setting(
        2, doc="Seconds Navigator may stop responding before errors.log records why; 0 never",
    )
    #: Not DN's (DOS refused no one): what *As root* asks for root with
    #: (``navigator.lib.system.elevate``).
    elevate: str = Setting(
        "auto", choices=ELEVATE,
        doc="A step refused permission may be done again as root through sudo or pkexec; auto is sudo, else pkexec",
    )
    #: Not DN's: sudo's own timestamp, for the root helper.
    root_timeout: int = Setting(
        5, doc="Minutes root access stays open after its last use; 0 closes it after each operation",
    )
    #: Not DN's: the desktop's GIO (``gio``) or KDE's KIO (``kioclient``,
    #: ``solid-hardware``, kio-fuse) -- Volumes' Mount/Unmount/Eject, opening
    #: a file in the desktop's application, GVfs/KIO links and the trash's
    #: fallback (navigator.lib.system.desktop).  One of them a session; set on
    #: *Communications*' page, the System Setup page having no room left.  It was ``use_gio``,
    #: whose ``false`` still reads as ``off``.
    desktop_vfs: str = Setting(
        "auto", choices=DESKTOP_VFS,
        doc="The desktop's plumbing for volumes, links and opening files: GIO, KIO, or off; auto is KIO under KDE, else GIO",
    )


class StartupData(Section):
    """``dlgStartupSetup`` / ``TStartupData``: its Load and Unload words."""

    name = "startup"
    title = "Options > Configuration > Startup (DN's dlgStartupSetup)"

    STARTUP: ClassVar[tuple[str, ...]] = ("auto_user_menu", "clear_history")
    SHUTDOWN: ClassVar[tuple[str, ...]] = (
        "inactivity_exit", "autosave_desktop", "preserve_directory",
    )

    auto_user_menu: bool = Setting(False, doc="Auto run the User Menu")
    #: ``ClearHistories``: what is pinned stays.
    clear_history: bool = Setting(False, doc="Clear the unpinned history entries on startup")
    inactivity_exit: bool = Setting(False, doc="Exit after an hour of inactivity")
    #: Saving on exit and restoring at the next start, both: DN restored
    #: ``DN.DSK`` at every start whenever there was one.
    autosave_desktop: bool = Setting(False, doc="Save the desktop on exit and restore it at the next start")
    #: DN's ``osuPreserveDir`` (``TFilePanelRoot.Store``): off, the active
    #: panel follows the shell's directory after a command and opens in the
    #: start directory in a restored desktop; on, it keeps its own.
    preserve_directory: bool = Setting(
        False, doc="The active panel keeps its directory after a command and in a restored desktop",
    )


class InterfaceData(Section):
    """``dlgInterfaceSetup`` / ``TInterfaceData.Options``."""

    name = "interface"
    title = "Options > Configuration > Interface (DN's dlgInterfaceSetup)"

    OPTIONS: ClassVar[tuple[str, ...]] = (
        "clock", "hide_menu_bar", "hide_status_line", "esc_user_screen",
        "hide_command_line", "auto_hide_command_line", "block_insert_cursor",
        "store_editor_position", "store_viewer_position", "track_editing",
        "track_viewing", "track_directories",
    )

    clock: bool = Setting(True, doc="Show the clock at the menu bar's right end")
    #: DN's default hid it; Navigator has always shown it.
    hide_menu_bar: bool = Setting(False, doc="Hide the menu bar until F10")
    hide_status_line: bool = Setting(False, doc="Hide the key bar")
    esc_user_screen: bool = Setting(False, doc="Esc on an empty command line toggles the console")
    hide_command_line: bool = Setting(False, doc="Hide the command line, and type nothing on it")
    auto_hide_command_line: bool = Setting(False, doc="Hide the command line while it is empty")
    block_insert_cursor: bool = Setting(False, doc="Block cursor on the command line")
    #: Track records a file and lists it; these put a tracked file's window,
    #: scroll and cursor back when it opens again.  On by default, as the
    #: Track pair is, for the same reason.
    store_editor_position: bool = Setting(
        True, doc="Reopen a tracked file in the editor at its window, scroll and cursor",
    )
    store_viewer_position: bool = Setting(
        True, doc="Reopen a tracked file in the viewer at its window, scroll and cursor",
    )
    #: On by default, a departure from the option's place in the setup
    #: dialog's original record: a history nobody turned on is one nobody
    #: knows exists.
    track_editing: bool = Setting(True, doc="Track editing history: Alt+PgUp, modes restored")
    track_viewing: bool = Setting(True, doc="Track viewing history: Alt+PgDn, modes restored")
    #: On, a departure as the two above: DN's default was off.
    track_directories: bool = Setting(True, doc="Track directories: Alt+Backspace lists where the panels have been")
    #: A departure: DN fixed these at 20 (``MaxHistorySize``,
    #: ``MaxEditHistorySize``), when every list sat in 64K of DOS memory.
    #: One size for every history; pinned entries are never counted out.
    history_size: int = Setting(
        50, doc="Entries kept per history list: input lines, viewed and edited files",
    )
    #: Not DN's: its language was the resource set it was installed with.
    #: Empty follows the environment's ``$LANG``.
    language: str = Setting(
        "", doc="The language captions and messages are in: a catalogue's code "
                "(en, lv, ...), or empty to follow $LANG",
    )
    #: Not DN's, which had no Options > Settings to put tabs in.
    settings_tabs: str = Setting(
        "simple", choices=("top", "left", "simple"),
        doc="Where Options > Settings shows its tabs: a row on top, a column on the left, "
            "or simple, a plain row of captions on top",
    )
    #: Not DN's: OSP put a window's number in its close icon instead.  On by
    #: default, asked for: unlike most additions that change the screen, it
    #: shows nothing until a second window opens.
    window_strip: str = Setting(
        "numbers", choices=("off", "numbers", "full"),
        doc="The windows listed on the menu bar, Win+1 .. Win+9's numbers: "
            "off, numbers alone, or numbers and titles",
    )
    #: Not DN's, which had no tooltips: how long the mouse pointer rests on
    #: something before its tooltip shows (navkit's ``tooltip_delay``).
    tooltip_delay: int = Setting(
        1000, doc="Milliseconds the mouse pointer rests on something before its tooltip shows, 0 for none",
    )


class ConfirmsData(Section):
    """``dlgConfirmations`` / the ``Confirms`` word."""

    name = "confirmations"
    title = "Options > Configuration > Confirmations (DN's dlgConfirmations)"

    OPTIONS: ClassVar[tuple[str, ...]] = (
        "erase_single", "erase_multiple", "erase_non_empty_dir", "erase_read_only",
        "create_dir", "drag_and_drop", "exit", "save", "delete_bookmark", "close_command_window",
    )

    erase_single: bool = Setting(True, doc="Ask before erasing a single file")
    erase_multiple: bool = Setting(True, doc="Ask before erasing several files")
    erase_non_empty_dir: bool = Setting(True, doc="Ask before erasing a non-empty directory")
    erase_read_only: bool = Setting(True, doc="Ask before erasing a read-only file")
    create_dir: bool = Setting(False, doc="Ask before creating a missing target directory")
    drag_and_drop: bool = Setting(False, doc="The Copy dialog before files dropped with the mouse are copied")
    exit: bool = Setting(True, doc="Ask before quitting Navigator")
    #: A departure, asked for: DN's F2 wrote at once and had no such box.
    save: bool = Setting(True, doc="Ask before the editor's F2 (Ctrl+S) saves a file")
    #: A departure, asked for: SelectDrive's box had no Del to ask about.
    delete_bookmark: bool = Setting(True, doc="Ask before Del in the bookmarks box deletes a bookmark")
    #: A departure, asked for: DN had no command windows (``TerminalWindow``).
    close_command_window: bool = Setting(
        True, doc="Ask before closing a window whose command is still running",
    )


class EditorDefaultsData(Section):
    """``dlgEditorDefaults``' editor half / ``TEditorDefaultsData``."""

    name = "editor"
    title = "Options > Configuration > Editor/Viewer -- the editor (DN's dlgEditorDefaults)"

    OPTIONS: ClassVar[tuple[str, ...]] = (
        "create_backup", "backspace_unindents", "auto_brackets", "auto_indent",
        "autowrap", "justify_on_wrap", "vertical_blocks", "optimal_fill",
        "highlight_line", "highlight_column", "persistent_blocks",
        "overwrite_blocks", "lock_file", "show_options",
    )
    #: DN's order was CR+LF, CR, LF; POSIX's own ending comes first here.
    LINE_DIVISORS: ClassVar[tuple[str, ...]] = ("lf", "crlf", "cr")

    create_backup: bool = Setting(False, doc="F2 keeps the old file as NAME.bak")
    backspace_unindents: bool = Setting(
        True, doc="Backspace in the leading blanks goes back to the indent of a line above",
    )
    auto_brackets: bool = Setting(
        False, doc="A new editor types ( { [ with their partner after them",
    )
    auto_indent: bool = Setting(True, doc="Enter indents the new line as the one above")
    autowrap: bool = Setting(False, doc="A new editor wraps a line typed past the right margin")
    justify_on_wrap: bool = Setting(False, doc="A new editor widens the line a wrap leaves to the margin")
    vertical_blocks: bool = Setting(False, doc="Column blocks rather than stream ones")
    optimal_fill: bool = Setting(
        False, doc="A new editor writes blanks reaching a tab stop as a tab",
    )
    highlight_line: bool = Setting(False, doc="A new editor highlights the cursor's line")
    highlight_column: bool = Setting(False, doc="A new editor highlights the cursor's column")
    #: DN's ``HiLite``, which ``DN.HGL`` turned on for the files it named:
    #: here which lexer is ``highlight.ini``'s, and this is on or off for all.
    #: No checkbox, as ``dlgEditorDefaults`` had none; Editor > Options switches it.
    syntax_highlight: bool = Setting(
        True, doc="A new editor colours its text by syntax, as highlight.ini says",
    )
    persistent_blocks: bool = Setting(
        True, doc="The block stays when the cursor moves; off, typing replaces it",
    )
    overwrite_blocks: bool = Setting(
        False, doc="With persistent blocks off, typing, pasting and Del replace the block",
    )
    lock_file: bool = Setting(
        False, doc="An editor holds its file with an advisory lock other programs can see",
    )
    #: A departure: DN had no such strip.  Last in ``OPTIONS`` so the bits of
    #: the original's options stay where they were.
    show_options: bool = Setting(
        True, doc="The editor's bottom frame shows its options, lit while on; a click switches one",
    )
    #: A departure too, with no checkbox: Editor > Options switches it per editor.
    show_hidden: bool = Setting(
        False, doc="A new editor shows spaces, tabs and line ends",
    )
    left_margin: int = Setting(0, doc="Left margin a new editor formats paragraphs to")
    right_margin: int = Setting(78, doc="Right margin a new editor formats paragraphs to")
    paragraph: int = Setting(5, doc="A justified paragraph's first-line indent in a new editor")
    #: DN's default was CR+LF; on POSIX a new line is LF.
    line_divisor: str = Setting(
        "lf", choices=LINE_DIVISORS, doc="Line ending of a file with none yet, a new one",
    )
    tab_size: int = Setting(8, doc="Tab size")


class ViewerDefaultsData(Section):
    """``dlgEditorDefaults``' viewer half / ``ViOpt``."""

    name = "viewer"
    title = "Options > Configuration > Editor/Viewer -- the viewer (DN's dlgEditorDefaults)"

    OPTIONS: ClassVar[tuple[str, ...]] = ("hex_mode", "wrap_lines", "show_options")

    hex_mode: bool = Setting(False, doc="F3 opens in hex mode")
    wrap_lines: bool = Setting(False, doc="Wrap long lines")
    #: A departure: DN's viewer had no highlighting.  No checkbox either;
    #: View > Syntax highlight switches it.
    syntax_highlight: bool = Setting(
        True, doc="F3 colours a text by syntax, as highlight.ini says",
    )
    #: A departure: DN had no such strip.
    show_options: bool = Setting(
        True, doc="The viewer's bottom frame shows its options, lit while on; a click switches one",
    )
    #: A departure too, with no checkbox: View > Hidden characters switches it.
    show_hidden: bool = Setting(False, doc="F3 shows spaces, tabs and line ends")
    #: A departure too, with no checkbox: View > Markup view switches it for a
    #: file.  Read by markdown-it-py.
    render_markdown: bool = Setting(
        True, doc="F3 renders a Markdown file -- headings, lists, tables -- rather than showing its source",
    )
    markdown_masks: str = Setting(
        "*.md;*.markdown", doc="The files F3 renders as Markdown, as masks separated by ';'",
    )
    #: The same for reStructuredText, read by docutils.
    render_rst: bool = Setting(
        True, doc="F3 renders a reStructuredText file -- sections, lists, tables -- rather than its source",
    )
    rst_masks: str = Setting(
        "*.rst;*.rest", doc="The files F3 renders as reStructuredText, as masks separated by ';'",
    )
    #: The same for HTML, read by the standard library's parser.
    render_html: bool = Setting(
        True, doc="F3 renders an HTML file as a text browser would -- headings, lists, tables -- rather than its source",
    )
    html_masks: str = Setting(
        "*.html;*.htm;*.xhtml", doc="The files F3 renders as HTML, as masks separated by ';'",
    )
    #: The same for PDF, its text read by pypdf.
    render_pdf: bool = Setting(
        True, doc="F3 shows a PDF file's text, page by page, rather than its source",
    )
    pdf_masks: str = Setting(
        "*.pdf", doc="The files F3 renders as PDF, as masks separated by ';'",
    )


class FMSetupData(Section):
    """``dlgFMSetup`` / ``TFMSetup``."""

    name = "file_manager"
    title = "Options > File Manager > Setup (DN's dlgFMSetup)"

    BEHAVIOR: ClassVar[tuple[str, ...]] = (
        "auto_change_dir", "drag_drop_columns", "beep_after_copy", "enter_opens_archive",
        "space_toggles_selection", "del_erases", "use_arrows", "bs_upper_dir", "auto_refresh",
        "use_trash", "open_unassociated",
    )
    DISPLAY: ClassVar[tuple[str, ...]] = (
        "column_titles", "info_divider", "tag_character", "link_line", "show_options",
        "git_status",
    )

    auto_change_dir: bool = Setting(True, doc="The panel follows the tree's cursor once it rests")
    # On by default, a departure: DN's fmoDragAndDrop was off.
    drag_drop_columns: bool = Setting(True, doc="Files can be dragged out of a panel with the mouse")
    beep_after_copy: bool = Setting(False, doc="Ring the terminal's bell after a copy")
    #: DN's ``fmoEnterArchives``: zip and tar (``navigator/lib/drives/archive.py``).
    enter_opens_archive: bool = Setting(True, doc="Enter opens an archive (zip, tar) as a directory")
    space_toggles_selection: bool = Setting(
        True, doc="Space tags the cursor's file while the command line is empty",
    )
    del_erases: bool = Setting(True, doc="Del erases files while the command line is empty")
    use_arrows: bool = Setting(
        True, doc="Left, Right, Home and End edit a command line with text; off, with Shift",
    )
    #: DN's default was off; Navigator's Backspace has always gone up.
    bs_upper_dir: bool = Setting(
        True, doc="Backspace goes to the parent directory while the command line is empty",
    )
    #: Not DN's: it re-read a panel only on ``cmRereadDir`` from whatever
    #: changed the directory (navigator.lib.system.dirwatch).
    auto_refresh: bool = Setting(True, doc="A panel re-reads its directory when it changes on disk")
    #: Not DN's, which erased for good: the freedesktop Trash
    #: (navigator.lib.file_ops.trash), off as DN's behaviour is.
    use_trash: bool = Setting(False, doc="F8 moves files on the disk to the Trash")
    #: Not DN's, where Enter on a file DN.EXT had no line for did nothing:
    #: the desktop's default application, through ``gio open``.
    open_unassociated: bool = Setting(
        True, doc="Enter on a file extensions.ini has no section for opens it in the desktop's application",
    )
    column_titles: bool = Setting(True, doc="Column titles in the detailed and list modes")
    info_divider: bool = Setting(True, doc="A divider over the lines under the listing")
    tag_character: bool = Setting(True, doc="Mark a tagged file with the tag sign")
    #: Not DN's, which had no symlinks: a line under *Current file* as its
    #: find panel gave a file's directory one.
    link_line: bool = Setting(True, doc="A second info line shows where a symlink points")
    #: Not DN's either, as the editor's and viewer's strips are not.
    show_options: bool = Setting(
        True, doc="A panel's bottom frame shows its options, lit while on; a click switches one",
    )
    #: Not DN's, which knew no git (navigator.lib.system.gitstatus).
    git_status: bool = Setting(
        True, doc="In a git work tree, each file's status and the branch in the panel title",
    )
    tag_sign: str = Setting("√", doc="Tag sign; empty means √")
    #: Not DN's choice to make: its right button always selected
    #: (``FLPANELX.PAS``), and Navigator's opens the context menu unless this
    #: says ``select``.  The keyboard's Menu key and Shift+F10 open the menu
    #: either way.
    right_button: str = Setting(
        "menu", choices=("menu", "select"),
        doc="The right mouse button in a panel: its context menu, or DN's selecting",
    )
    #: Not DN's, which had no Miller columns (Alt+F12, ``navigator/widgets/manager/miller``).
    miller_width: int = Setting(24, doc="Width of a Miller column (Alt+F12), at least 12")


class PanelDefaultsData(Section):
    """``dlgFMDefaults`` / ``TPanelDefaultsData``: *New Manager defaults*."""

    name = "panel_defaults"
    title = "Options > File Manager > New Manager defaults (DN's dlgFMDefaults)"

    #: DN's *Group* was the file-type group; "type" says so, where "group"
    #: would read as the file's Unix group.  "attributes" and "owner" are
    #: Navigator's (DN never sorted by attributes; DOS had no owners), after
    #: DN's four by a property of the file.
    SORT_BY: ClassVar[tuple[str, ...]] = (
        "name", "extension", "size", "time", "attributes", "owner", "type", "unsorted",
    )
    DISPLAY: ClassVar[tuple[str, ...]] = (
        "directory_length", "current_file", "selected_files", "totals",
        "free_space", "files_highlight", "executables_first", "archives_first",
    )
    #: DN's first choice was *Drive*, a panel of files; there are no drives here.
    LEFT_PANEL: ClassVar[tuple[str, ...]] = ("files", "info", "tree", "absent")
    #: ``Panel.VIEW_MODES``, the order Ctrl+Y steps through.
    VIEW_MODE: ClassVar[tuple[str, ...]] = ("simple", "detailed", "list")

    #: DN's default was the extension; Navigator's panels sort by name.
    sort_by: str = Setting(
        "name", choices=SORT_BY, aliases={"group": "type"}, doc="A new panel's order (Alt+B changes one panel's)",
    )
    #: Not DN's, which had no descending order: :attr:`sort_by` turned round.
    sort_reverse: bool = Setting(False, doc="A new panel's order runs the other way (largest, newest, Z first...)")
    #: ``fmiDirLen``: each directory's bytes counted at every read (Esc stops it).
    directory_length: bool = Setting(False, doc="Count each directory's bytes into its size at every read")
    current_file: bool = Setting(True, doc="The info line names the current file")
    selected_files: bool = Setting(True, doc="The info line totals the selected files")
    totals: bool = Setting(False, doc="A line under the listing totals its files")
    free_space: bool = Setting(True, doc="A line under the listing gives the free space")
    files_highlight: bool = Setting(True, doc="Colour files by type")
    executables_first: bool = Setting(True, doc="Executables before the other files, by name, extension and type")
    archives_first: bool = Setting(True, doc="Archives before the other files, by name, extension and type")
    left_panel: str = Setting(
        "files", choices=LEFT_PANEL, aliases={"drive": "files"},
        doc="Left panel in a new Manager",
    )
    #: Not DN's: its panels took their mode from the saved ``ShowFlags``.
    view_mode: str = Setting(
        "detailed", choices=VIEW_MODE, doc="A new panel's mode (Ctrl+Y changes one panel's)",
    )


# -- the whole file ---------------------------------------------------------------

class DriveInfoData(Section):
    """``dlgDriveInfoSetup`` / ``DriveInfoData``: what Ctrl+L's information panel shows.

    DN's eleven boxes less its *EMS* and *XMS Information*, which only meant
    something on DOS; the memory three are read for POSIX (``InfoPanel``).
    *File under the cursor* is Navigator's, not DN's.
    """

    name = "drive_info"
    title = "Options > File Manager > Information panel (DN's dlgDriveInfoSetup)"

    OPTIONS: ClassVar[tuple[str, ...]] = (
        "directory_title", "totals", "current_file", "volume_size", "volume_free", "volume_label",
        "total_memory", "user_memory", "navigator_memory", "information_file",
    )

    directory_title: bool = Setting(True, doc="The directory's name")
    totals: bool = Setting(True, doc="How many files it holds, and their bytes")
    current_file: bool = Setting(True, doc="The file under the cursor: its type, size, times, attributes and owner")
    volume_size: bool = Setting(True, doc="The file system's size")
    volume_free: bool = Setting(True, doc="Its free space")
    volume_label: bool = Setting(True, doc="Its label, or its device and type")
    total_memory: bool = Setting(True, doc="The machine's memory (DN's conventional memory)")
    user_memory: bool = Setting(True, doc="Memory available to programs (DN's memory for user)")
    navigator_memory: bool = Setting(True, doc="Memory Navigator takes")
    information_file: bool = Setting(True, doc="The directory's DirInfo or File_ID.DIZ")


class ColumnDefaultsData(Section):
    """``dlgColumnsDefaults`` / ``ColumnsDefaults``: the detailed columns a new listing shows.

    DN kept a ``ShowFlags`` word for each kind of drive -- *Disk Drive*,
    *File find*, *TEMP:*, *Archives* and *TDR View* -- and each new drive took
    its kind's.  Three of them are listings here: a directory, a *Find:*
    listing (Alt+F7, Panel > Directory Branch, Read file list), and an
    archive (``TArcDrive.Init``'s ``ColumnsDefaults.Arc``).  *TEMP:* and *TDR
    View* only meant something on DOS.  The boxes are *Columns Setup*'s
    (Alt+K), POSIX's size, attributes, owner and date where DN's were size,
    date, time and descriptions; an archive adds DN's packed size and ratio.
    DN's defaults were 0, its brief panel; Navigator's panels always showed
    every column, so every box defaults on.
    """

    name = "column_defaults"
    title = "Options > File Manager > Column defaults (DN's dlgColumnsDefaults)"

    #: *Disk Drive*'s boxes, in their order.
    DISK: ClassVar[tuple[str, ...]] = ("disk_size", "disk_attributes", "disk_owner", "disk_date")
    #: *File find*'s boxes, in their order.
    FIND: ClassVar[tuple[str, ...]] = ("find_size", "find_attributes", "find_owner", "find_date", "find_path")
    #: *Archives*' boxes, in their order.
    ARC: ClassVar[tuple[str, ...]] = ("arc_size", "arc_packed", "arc_ratio", "arc_attributes", "arc_owner",
                                      "arc_date")

    disk_size: bool = Setting(True, doc="A directory shows the size")
    disk_attributes: bool = Setting(True, doc="A directory shows the attributes")
    disk_owner: bool = Setting(True, doc="A directory shows the owner")
    disk_date: bool = Setting(True, doc="A directory shows the date")
    find_size: bool = Setting(True, doc="A Find: listing shows the size")
    find_attributes: bool = Setting(True, doc="A Find: listing shows the attributes")
    find_owner: bool = Setting(True, doc="A Find: listing shows the owner")
    find_date: bool = Setting(True, doc="A Find: listing shows the date")
    find_path: bool = Setting(True, doc="A Find: listing shows each file's directory")
    arc_size: bool = Setting(True, doc="An archive shows the original size")
    arc_packed: bool = Setting(True, doc="An archive shows the packed size")
    arc_ratio: bool = Setting(True, doc="An archive shows the packed size as a percentage of the original")
    arc_attributes: bool = Setting(True, doc="An archive shows the attributes")
    arc_owner: bool = Setting(True, doc="An archive shows the owner")
    arc_date: bool = Setting(True, doc="An archive shows the date")

    def columns(self, listing: bool, *, archive: bool = False) -> frozenset[str]:
        """The columns a new directory (*listing* false), *Find:* listing or
        archive shows, as ``Panel.columns`` names them."""
        names = self.ARC if archive else self.FIND if listing else self.DISK
        return frozenset(name.split("_", 1)[1] for name in names if getattr(self, name))


class HighlightGroupsData(Section):
    """``dlgHighlightGroups`` / ``CustomMask1``..``5``: which files take each colour.

    DN's five *Custom* masks, which coloured a row Custom 1 to 5 and sorted
    it among them by *Group*.  Navigator named its five (``filetypes.CUSTOM``)
    and filled them in, so the dialog's lines are those names, and a mask is
    the panel's own syntax -- ``;``-separated shell patterns, ``*.ext`` for
    DN's bare extensions -- matched without regard to case.  The *Archives*
    mask was never in this dialog in DN, and is not here.
    """

    name = "highlight_groups"
    title = "Options > File Manager > Highlight groups (DN's dlgHighlightGroups)"

    image: str = Setting(filetypes.CATEGORIES["image"], doc="Images")
    media: str = Setting(filetypes.CATEGORIES["media"], doc="Audio and video")
    document: str = Setting(filetypes.CATEGORIES["document"], doc="Documents")
    source: str = Setting(filetypes.CATEGORIES["source"], doc="Source code")
    temp: str = Setting(filetypes.CATEGORIES["temp"], doc="Backups and temporary files")


class SaversData(Section):
    """``TSaversData``: Options > Configuration > Screen savers (DN's
    ``TSaversDialog``) -- which savers take turns, after how long, and
    whether the mouse's corners call one (``cfgSaversData``)."""

    name = "savers"
    title = "Options > Configuration > Screen savers (DN's TSaversDialog)"

    #: DN's *Time*: never, or 1, 2, 5 or 10 minutes without a key or a click.
    TIMES: ClassVar[tuple[str, ...]] = ("never", "1", "2", "5", "10")

    #: Empty, as DN's list began: no saver comes until one is chosen.
    selected: str = Setting("", doc="The savers taking turns, by name, separated by commas")
    time: str = Setting("1", choices=TIMES, doc="Minutes idle before a saver comes, or never")
    mouse: bool = Setting(
        False, doc="The pointer in the top right corner calls a saver; in the bottom right, none comes",
    )

    def names(self) -> list[str]:
        """:attr:`selected` as a list."""
        return [name for name in (part.strip() for part in self.selected.split(",")) if name]


class CountryData(Section):
    """``CountryInfo``: Options > Configuration > Country support (DN's
    ``dlgCountrySetup``) -- how a file's date and time are written.

    DN took the order from DOS's country information and let the dialog
    change it -- Month-Day-Year, Day-Month-Year or Year-Month-Day, a
    separator of its own, and 12 or 24 hours (``cfgCountryInfo``).  A
    departure, asked for: each order comes with its usual separator --
    European ``DD-MM-YYYY``, US ``MM/DD/YYYY``, ISO ``YYYY-MM-DD`` -- and a
    fourth is any ``strftime`` format.  The thousands, decimal and currency
    boxes and the uppercase table are left out: nothing here writes money,
    and case is Unicode's.
    """

    name = "country"
    title = "Options > Configuration > Country support (DN's dlgCountrySetup)"

    DATES: ClassVar[tuple[str, ...]] = ("european", "us", "iso", "custom")
    TIMES: ClassVar[tuple[str, ...]] = ("24h", "12h")
    WEEKS: ClassVar[tuple[str, ...]] = ("monday", "sunday")

    #: DN's default order (Day-Month-Year), with a four-digit year.
    date_format: str = Setting(
        "european", choices=DATES,
        doc="A file's date: DD-MM-YYYY, MM/DD/YYYY, YYYY-MM-DD, or custom_date",
    )
    custom_date: str = Setting(
        "%d.%m.%Y", doc="The date when date_format is custom, in strftime's %-directives",
    )
    time_format: str = Setting("24h", choices=TIMES, doc="A file's time and the clock: 24 or 12 hours")
    #: Not DN's, which had no calendar: ISO's Monday, as navml's calendar began.
    first_day: str = Setting("monday", choices=WEEKS, doc="The day a calendar's week starts on")


class TetrisData(Section):
    """``TetrisRec``: ≡ > Game's *Setup game* (DN's ``dlgGameSetup``), kept
    as DN kept it (``cfgTetrisRec``)."""

    name = "tetris"
    title = "≡ > Game > Setup (DN's dlgGameSetup)"

    STYLES: ClassVar[tuple[str, ...]] = ("tetris", "pentix")

    #: DN's ``L: 4``, the fifth level, *Never mind*.
    level: int = Setting(5, doc="The level a game starts at, 1 to 10")
    style: str = Setting("tetris", choices=STYLES, doc="Classic Tetris, or Pentix's 27 figures")
    preview: bool = Setting(False, doc="Show the next piece (it scores less)")


class UUCodeData(Section):
    """``TUUEncodeData`` and ``UUDecodeOptions``: what File > UU Encode and
    UU Decode were last accepted with, kept as DN kept them (``cfgUUEData``)."""

    name = "uucode"
    title = "File > UU Encode / UU Decode (DN's dlgUUEncode, dlgUUDecode)"

    #: The *Prefixes* boxes, in bit order (``ckFileTime``, ``ckMapTable``, ``ckStatistic``).
    PREFIXES: ClassVar[tuple[str, ...]] = ("file_time", "map_table", "statistics")
    #: ``ckNone`` .. ``ck64``: each level includes the ones before it.
    CHECKSUMS: ClassVar[tuple[str, ...]] = ("none", "entire", "section", "line", "crc64")
    LINE_ENDS: ClassVar[tuple[str, ...]] = ("crlf", "lf")
    #: *UU Decode*'s three boxes, in bit order.
    DECODE: ClassVar[tuple[str, ...]] = ("check_existing", "display_errors", "save_broken")

    file_time: bool = Setting(True, doc="Encoding writes the file's date and time first")
    map_table: bool = Setting(False, doc="Encoding writes the character mapping table")
    statistics: bool = Setting(True, doc="Encoding writes the statistics block")
    checksum: str = Setting("section", choices=CHECKSUMS, doc="Encoding's checksum level")
    lines_per_section: int = Setting(100, doc="Encoded lines per section (at least 10)")
    #: DN's default was DOS's ``<CR><LF>``; a POSIX text file ends its lines in ``<LF>``.
    line_ends: str = Setting("lf", choices=LINE_ENDS, doc="Encoded files' line ends")
    check_existing: bool = Setting(True, doc="Decoding asks before writing over a file")
    display_errors: bool = Setting(True, doc="Decoding shows each error as it finds it")
    save_broken: bool = Setting(False, doc="Decoding keeps a file it could not decode whole")


class ChecksumData(Section):
    """File > Checksums > *Calculate*'s last choices.  Not DN's: a departure,
    asked for -- DOS Navigator had no checksums to keep anything of."""

    name = "checksum"
    title = "File > Checksums > Calculate (not DN's)"

    ALGORITHMS: ClassVar[tuple[str, ...]] = ("md5", "sha1", "sha256", "sha512", "blake2b")
    MODES: ClassVar[tuple[str, ...]] = ("combined", "each")

    algorithm: str = Setting("sha256", choices=ALGORITHMS, doc="The digest Calculate writes")
    mode: str = Setting("combined", choices=MODES, doc="One list for all the files, or one beside each file")


class RemoteData(Section):
    """Connections to other drives: Options > Configuration > *Communications*,
    where DN set up the modem and the cable its Navigator Link ran over
    (``cmSetupModem``).  What it holds is Navigator's own -- DN's link had
    none of it to keep."""

    name = "remote"
    title = "Options > Configuration > Communications (DN's cmSetupModem)"

    UPLOAD: ClassVar[tuple[str, ...]] = ("ask", "always", "never")

    keepalive: int = Setting(30, doc="Seconds between keep-alive messages to a server; 0 sends none")
    idle_disconnect: int = Setting(
        0, doc="Minutes a connection nothing uses stays open before it is closed; 0 keeps it",
    )
    upload_changed: str = Setting(
        "ask", choices=UPLOAD,
        doc="A file from another drive that a program changed goes back: ask, always or never",
    )
    timeout: int = Setting(15, doc="Seconds to wait for a server to answer when connecting")
    #: Not DN's: no server says when a directory changed, so *Auto refresh
    #: panels* asks again this often.  Off by default, as every look is traffic.
    refresh: int = Setting(0, doc="Seconds between looks at a server's directory for Auto refresh; 0 never")


#: Every section, in the order the file lists them.
SECTIONS: tuple[type[Section], ...] = (
    AppearanceData, SystemData, StartupData, InterfaceData, ConfirmsData,
    EditorDefaultsData, ViewerDefaultsData, FMSetupData, PanelDefaultsData,
    DriveInfoData, ColumnDefaultsData, HighlightGroupsData, SaversData, CountryData, TetrisData,
    UUCodeData, ChecksumData, RemoteData,
)

#: ``{section: keys}`` an older ``navigator.ini`` may hold for DN options that
#: only meant something on DOS.  :meth:`Settings.load` drops them rather than
#: keeping them as extras, so the next save leaves them out of the file.
OBSOLETE: dict[str, frozenset[str]] = {
    "system": frozenset({"fast_execution", "advanced_copy", "use_gio"}),
    "startup": frozenset({"enable_blinking", "sleep_when_inactive"}),
    "file_manager": frozenset({
        "alt_difference", "ctrl_difference", "keep_descriptions", "drive_line",
        "quick_search", "description_files",
    }),
}


class Settings:
    """Every section, plus what the file held that no section claims."""

    appearance: AppearanceData
    system: SystemData
    startup: StartupData
    interface: InterfaceData
    confirmations: ConfirmsData
    editor: EditorDefaultsData
    viewer: ViewerDefaultsData
    file_manager: FMSetupData
    panel_defaults: PanelDefaultsData
    drive_info: DriveInfoData
    column_defaults: ColumnDefaultsData
    highlight_groups: HighlightGroupsData
    savers: SaversData
    country: CountryData
    tetris: TetrisData
    uucode: UUCodeData
    checksum: ChecksumData
    remote: RemoteData

    def __init__(self) -> None:
        for cls in SECTIONS:
            setattr(self, cls.name, cls())
        #: ``{section: {key: text}}`` the file held and no :class:`Setting` claims,
        #: kept verbatim so a save does not lose them.
        self.extras: dict[str, dict[str, str]] = {}
        #: The file this was last loaded from or saved to.
        self.path: Path | None = None

    def sections(self) -> list[Section]:
        return [getattr(self, cls.name) for cls in SECTIONS]

    def section(self, name: str) -> Section:
        for section in self.sections():
            if section.name == name:
                return section
        raise KeyError(name)

    def reset(self) -> None:
        """Every setting back to its default, and nothing remembered of a file."""
        for section in self.sections():
            section.reset()
        self.extras = {}
        self.path = None

    # -- reading -------------------------------------------------------------------

    def load(self, path: Path) -> list[str]:
        """Read *path* over the current values; one warning per line that will not do.

        A missing key keeps what it had, and a value that does not parse keeps
        it too -- a typo in the file must not stop Navigator starting.  A file
        that is not an ini file at all raises ``configparser.Error``.
        """
        parser = configparser.ConfigParser(
            interpolation=None, inline_comment_prefixes=INLINE_COMMENT_PREFIXES
        )
        with open(path, encoding="utf-8") as file:
            parser.read_file(file)
        warnings: list[str] = []
        extras: dict[str, dict[str, str]] = {}
        known = {cls.name: cls for cls in SECTIONS}
        for name in parser.sections():
            cls = known.get(name)
            if cls is None:
                extras[name] = dict(parser.items(name))
                continue
            section = self.section(name)
            for key, text in parser.items(name):
                if name == "system" and key == "use_gio" and not parser.has_option(name, "desktop_vfs"):
                    # ``desktop_vfs``'s predecessor: off stays off.
                    if text.strip().lower() in ("false", "no", "off", "0"):
                        section.desktop_vfs = "off"
                if key in OBSOLETE.get(name, ()):
                    continue
                field = cls.field(key)
                if field is None:
                    extras.setdefault(name, {})[key] = text
                    continue
                try:
                    setattr(section, key, field.parse(text))
                except ValueError as error:
                    warnings.append(f"{path}: [{name}] {key}: {error}; using {field.format(field.default)}")
        self.extras = extras
        self.path = Path(path)
        return warnings

    # -- writing -------------------------------------------------------------------

    def render(self) -> str:
        """The whole file, comments and all."""
        coder = Coder("ini")
        coder.comment(0, "Navigator settings.")
        coder.comment(0, "Read when nav starts, and rewritten by the dialogs under Options. Edit it")
        coder.comment(0, "freely: values and unknown keys are kept, but these comments are regenerated.")
        for section in self.sections():
            coder.new_line()
            coder.add(0, f"[{section.name}]")
            coder.comment(0, section.title)
            for field in section.fields():
                option = f"{field.name} = {field.format(getattr(section, field.name))}"
                padding = max(COMMENT_COLUMN - len(option), 2)
                coder.add(0, f"{option}{' ' * padding}# {field.comment()}")
            for key, text in self.extras.get(section.name, {}).items():
                coder.add(0, f"{key} = {text}")
        for name, values in self.extras.items():
            if any(cls.name == name for cls in SECTIONS):
                continue
            coder.new_line()
            coder.add(0, f"[{name}]")
            for key, text in values.items():
                coder.add(0, f"{key} = {text}")
        return coder.render()

    def save(self, path: Path | None = None, section: str | None = None) -> Path:
        """Write the file; with *section*, only that section's values replace the file's.

        The file on disk is read first in that case, so whatever was edited in
        it by hand since Navigator started is what the other sections keep.
        Written to a temporary file in the same directory and renamed over the
        old one, so a crash mid-write leaves the old file whole.
        """
        target = Path(path) if path is not None else self.path or config_path()
        content = self
        if section is not None and target.exists():
            content = Settings()
            content.load(target)
            content.section(section).update(self.section(section).values())
        write_atomically(target, content.render())
        self.path = target
        return target


def write_atomically(target: Path, text: str) -> None:
    """*text* as *target*'s whole content, its directory made if need be.

    Written to a temporary file in the same directory and renamed over the
    old one, so a crash mid-write leaves the old file whole.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=target.parent, prefix=f".{target.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(text)
        os.replace(temporary, target)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(temporary)
        raise


#: The settings, shared by everything that reads one.
SETTINGS = Settings()
