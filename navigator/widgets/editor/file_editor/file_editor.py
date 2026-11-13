"""F4's text: DOS Navigator's ``TFileEditor``, editing what ``navigator.lib.editor`` holds.

**Written in Python alone**, as ``FileViewer`` is: everything it shows is
painted, and the window around it, ``EditWindow``, is the half with markup.

**Its state is the cursor, the view and one counter.**  ``line`` and ``col``
are the cursor -- a line, and a *column* on screen, which a movement keeps
within the line's text (a departure: DN's could stand anywhere past the end;
drawing lines and marking a column block still can, both needing the room)
-- and ``top`` and ``left`` are the first line and column shown.  The text itself is a great deal of mutable state that
changes together, so ``revision`` stands in for all of it, the way
``Console.revision`` stands for a console's screen: every edit bumps it, and
everything painted from the text reads it.

**Every key is a command**, bound in :attr:`FileEditor.keys` from ``DN.DNR``'s
``EDITOR COMMANDS`` table and handled here under DN's own name.  The table
is the editor's rather than the window's because DN's was too: ``LoadCommands``
filled ``TFileEditor``'s, and the window's status line only captioned some.
What is left to :meth:`on_key` is what the table could not name -- a
printable character.

**The methods are split by feature into mixins** (``navkit.widget.Mixin``),
one module each beside this one -- ``cursor``, ``block``, ``edits``,
``search``, ``painting`` and the rest -- with the module-level helpers they
share in ``helpers``.  What stays here is the state, the keys, the file and
``checks``/``refusal``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from navkit import commands
from navkit.capabilities import GLYPHS_UNICODE
from navkit.events import MouseClickEvent
from navkit.i18n import tr
from navkit.reactive import computed, reactive
from navkit.screen import Surface
from navkit.tooltip import with_keys
from navkit.widget import Widget

from navml.widgets.dialog.static_text import StaticText
from navml.widgets.menu.context_menu import ContextMenuHost

from navigator.widgets.editor.commands import (
    ReopenWithEncoding,
    SaveWithEncoding,
    SetLineEnding,
    ShowFindBar,
    ShowReplaceBar,
    SwitchHiColumn,
    SwitchHiLine,
    SwitchHighLight,
    SwitchHiddenChars,
    SwitchFill,
    SwitchTabs,
    SwitchLineNumbers,
    SwitchSoftWrap,
    CapString,
    CapWord,
    LowString,
    LowWord,
    UpString,
    UpWord,
    DuplicateLine,
    SwitchDrawMode,
    SwitchBack,
    SwitchIndent,
    SwitchBrackets,
    SwitchSave,
    SwitchWrap,
    FCenter,
    FJustify,
    LCenter,
    LJustify,
    LLeft,
    LRight,
    FLeft,
    FRight,
    AsciiTable,
    SelectMacro,
    GotoLineNumber,
    BracketPair,
    CalcBlock,
    SortBlock,
    GotoMarker,
    InsertDate,
    InsertTime,
    CapitalizeBlock,
    CopyBlock,
    MoveBlockEnd,
    MoveBlockStart,
    HideBlock,
    IndentBlock,
    LowcaseBlock,
    MoveBlock,
    UnindentBlock,
    UpcaseBlock,
    Clear,
    ClipboardCopy,
    ClipboardCut,
    ClipboardPaste,
    SelectAll,
    DeleteBack,
    DeleteChar,
    DeleteLine,
    DeleteWordLeft,
    InsertLine,
    LineEnd,
    LineStart,
    MoveDown,
    MoveLeft,
    MoveRight,
    MoveUp,
    NewLine,
    PageDown,
    PageUp,
    ScreenBottom,
    ScreenTop,
    ScrollDown,
    ScrollUp,
    SwitchInsert,
    TabKey,
    TextEnd,
    TextStart,
    Undo,
    Redo,
    SwitchBlock,
    WordLeft,
    WordRight,
)
from navigator.lib.editor import columns
from navigator.lib.editor import encodings
from navigator.lib.editor.buffer import EditBuffer
from navigator.lib.editor.document import NEWLINES, Document, Pos, encode_lines
from navigator.lib.editor import lock
from navigator.lib.editor.save import write_file
from navigator.lib.editor.paragraph import fix_margins
from navigator.lib.editor.search import SearchData
from navigator.settings import SETTINGS
from navigator.widgets.editor.file_editor.helpers import WORDSTAR

from navigator.widgets.editor.file_editor.cursor import Cursor
from navigator.widgets.editor.file_editor.block import Block
from navigator.widgets.editor.file_editor.drawing import Drawing
from navigator.widgets.editor.file_editor.switches import Switches
from navigator.widgets.editor.file_editor.edits import Edits
from navigator.widgets.editor.file_editor.line_format import LineFormat
from navigator.widgets.editor.file_editor.mouse import Mouse
from navigator.widgets.editor.file_editor.search import Search
from navigator.widgets.editor.file_editor.painting import Painting


class FileEditor(Cursor, Block, Drawing, Switches, Edits, LineFormat, Mouse, Search, Painting, ContextMenuHost, Widget):
    """The inside of an editor window: a text, its cursor, and the keys that edit it."""

    #: Kept left to right on a right-to-left screen (``Widget.mirrors``):
    #: the file's own text, edited left to right.
    mirrors = False

    #: ``CFileEditor``'s ten colours, by what they paint.  Its comments,
    #: symbols, strings and numbers -- and comments on the current line --
    #: are all ``token``, told apart by the token's classes and the
    #: ``current_line`` state (:mod:`navigator.lib.highlight`).
    parts = (
        "selected",
        "token",
        "current_line",
        "current_line_selected",
        "current_column",
        "match",
        # DN's column ruler (``RulerVisible``): ``GetColor($4240)``, slots [64]
        # and [66], the digits and the highlighted tens.
        "ruler",
        "ruler_tens",
    )

    #: ``EDITOR COMMANDS``, the keys that need no second one.  A binding with
    #: Shift is the same movement dragging a block along.
    #:
    #: **A departure, asked for:** DN's table was WordStar's as much as Turbo
    #: Vision's -- the Ctrl+E/S/D/X diamond, Ctrl+A/F words, Ctrl+R/C pages,
    #: Ctrl+W/Z scrolling, Ctrl+G and Ctrl+T deleting, and the two-key Ctrl+K,
    #: Ctrl+Q and Ctrl+B commands.  Those keys are the ones every editor since
    #: uses to save, find and undo, so they are not bound by default; the
    #: shipped ``keybindings_wordstar.ini`` (and ``keybindings_dn151.ini``, DN's
    #: own to the key) puts them back, from Options > Configuration > Key
    #: bindings > Load.  :data:`WORDSTAR` keeps those keys as DN had them.
    keys = {
        "left": MoveLeft,
        "shift+left": MoveLeft(extend=True),
        "right": MoveRight,
        "shift+right": MoveRight(extend=True),
        "up": MoveUp,
        "shift+up": MoveUp(extend=True),
        "down": MoveDown,
        "shift+down": MoveDown(extend=True),
        "ctrl+left": WordLeft,
        "ctrl+shift+left": WordLeft(extend=True),
        "ctrl+right": WordRight,
        "ctrl+shift+right": WordRight(extend=True),
        "home": LineStart,
        "shift+home": LineStart(extend=True),
        "end": LineEnd,
        "shift+end": LineEnd(extend=True),
        "pageup": PageUp,
        "shift+pageup": PageUp(extend=True),
        "pagedown": PageDown,
        "shift+pagedown": PageDown(extend=True),
        "ctrl+up": ScrollUp,
        "ctrl+down": ScrollDown,
        "ctrl+home": ScreenTop,
        "ctrl+shift+home": ScreenTop(extend=True),
        "ctrl+end": ScreenBottom,
        "ctrl+shift+end": ScreenBottom(extend=True),
        "ctrl+pageup": TextStart,
        "ctrl+shift+pageup": TextStart(extend=True),
        "ctrl+pagedown": TextEnd,
        "ctrl+shift+pagedown": TextEnd(extend=True),
        "enter": NewLine,
        "ctrl+enter": NewLine,
        "ctrl+m": NewLine,
        "ctrl+n": InsertLine,
        "tab": TabKey,
        "ctrl+i": TabKey,
        #: ^K U by a tab stop on Shift+Tab, as Tab in the block is ^K I by one
        #: -- a departure, asked for; DN bound nothing to Shift+Tab here.
        "shift+tab": UnindentBlock(stop=True),
        "backspace": DeleteBack,
        "ctrl+h": DeleteBack,
        "delete": DeleteChar,
        "ctrl+backspace": DeleteWordLeft,
        "ctrl+y": DeleteLine,
        "insert": SwitchInsert,
        "alt+backspace": Undo,
        "alt+shift+backspace": Redo,
        # ``cmCut``, ``cmCopy``, ``cmPaste`` and ``cmClear``: Turbo Vision's
        # keys, and two more sets that are not DN's.  Ctrl+X/C/V, which every
        # other editor uses, were WordStar's cursor down, Page Down and insert
        # toggle here; they are the clipboard's instead, and those three keep
        # Down, PgDn and Ins (^X still draws down in drawing mode).  And VTE
        # (xfce4-terminal, GNOME Terminal, Tilix) keeps Ctrl+Ins and Shift+Ins
        # for its own copy and primary paste with no setting to give them
        # back, so Ctrl+Alt+X/C/V reach the clipboard there too.
        "shift+delete": ClipboardCut,
        "ctrl+x": ClipboardCut,
        "ctrl+alt+x": ClipboardCut,
        "ctrl+insert": ClipboardCopy,
        "ctrl+c": ClipboardCopy,
        "ctrl+alt+c": ClipboardCopy,
        "shift+insert": ClipboardPaste,
        "ctrl+v": ClipboardPaste,
        "ctrl+alt+v": ClipboardPaste,
        "ctrl+delete": Clear,
        "alt+h": HideBlock,
        "alt+t": SortBlock,
        # Keys for what DN reached by ^K and ^Q chords alone, which the
        # WordStar presets bind back -- a departure, asked for, so the Block
        # and Misc menus show a key that works.  Alt+Shift+letter arrives as
        # Esc and the capital from any terminal, and the editor answers before
        # the menu bar's Alt+letter does, as for Alt+C.
        "alt+shift+v": MoveBlock,
        "alt+shift+k": CopyBlock,
        "alt+shift+i": IndentBlock,
        "alt+shift+o": UnindentBlock,
        "alt+shift+u": UpcaseBlock,
        "alt+shift+l": LowcaseBlock,
        "alt+shift+c": CapitalizeBlock,
        "alt+shift+d": InsertDate,
        "alt+shift+t": InsertTime,
        "alt+insert": CalcBlock,
        "alt+g": GotoLineNumber,
        "f4": SwitchDrawMode,
        #: ``StatusDef hcEditor``'s *F5 Block*: ``cmSwitchBlock``.
        "f5": SwitchBlock,
        "f6": DuplicateLine,
        # ``$1A1B``, ``$1B1D``, ``^\\`` and ``kbAltSlash``; with Shift, the line.
        # Ctrl+[ is Esc's byte, so it and the Ctrl+Shift forms need the kitty
        # keyboard protocol to arrive as themselves.
        "ctrl+[": UpWord,
        "ctrl+]": LowWord,
        "ctrl+\\": CapWord,
        "alt+/": CapWord,
        # ``kbAltSlash`` with Shift: the line.  ``alt+?`` from a terminal that
        # sends ``ESC ?``, ``alt+shift+/`` from one reporting the base key.
        "alt+?": CapString,
        "alt+shift+/": CapString,
        "ctrl+shift+[": UpString,
        "ctrl+shift+]": LowString,
        "ctrl+shift+\\": CapString,
        "ctrl+p": AsciiTable,
        #: DN's Ctrl+J 0, ``cmSelectMacro``: the file type's macros.  Ctrl+J 1..9,
        #: which played them in DN, play key macros now -- the application's.
        "ctrl+j 0": SelectMacro,
        "alt+left": BracketPair,
        "alt+right": BracketPair,
        "alt+j": FJustify,
        "alt+r": FRight,
        "alt+l": FLeft,
        "alt+c": FCenter,
        # What the freed keys do in every editor since: the Find bar (a
        # departure; F7 and Ctrl+F7 keep DN's dialogs), ``cmGotoLineNumber``
        # (Alt+G stays) and ``cmUndo`` (Alt+Backspace stays).  Ctrl+S, *Save*,
        # is the editor window's, which owns ``SaveText``.
        "ctrl+f": ShowFindBar,
        "ctrl+r": ShowReplaceBar,
        "ctrl+g": GotoLineNumber,
        "ctrl+z": Undo,
        "ctrl+shift+z": Redo,
        # What Ctrl+A is everywhere since; WordStar's *word left* in DN, which
        # the WordStar presets give back.
        "ctrl+a": SelectAll,
    }

    #: Every command :data:`WORDSTAR` binds, those no key above reaches among
    #: them, listed so Key bindings -- and the WordStar presets -- can still
    #: bind them, under the names they had (``unindent_block`` beside
    #: ``unindent_block_stop``).  Most are on the Editor menu as well.
    #: DN's ``cmL*`` had no key in any table, only its macros' names: listed so
    #: Key bindings offers them, bound by no preset.
    keyless_commands = (*WORDSTAR.values(), LJustify, LRight, LLeft, LCenter)

    #: What typing reaches: the command line's Enter, Home, End and Tab step
    #: aside while this holds the keyboard.  See ``Shell.enables``.
    edits_text = True

    #: The file, or None for a text never saved.
    path: Path | None = reactive(None)

    #: One counter standing for the whole text.
    revision: int = reactive(0)

    #: What the Find bar searches for, every match of it on screen painted as
    #: ``FileEditor::match`` -- the one found as ``::selected`` -- or None.  A
    #: departure, with the bar.  Replaced, never changed in place.
    highlight_query: SearchData | None = reactive(None)

    #: The cursor: a line, and a column on screen.
    line: int = reactive(0)
    col: int = reactive(0)

    #: The first line and column shown.
    top: int = reactive(0)
    left: int = reactive(0)

    #: Overwrite rather than insert: the ``:overwrite`` state, which gives the
    #: caret DN's ``BlockCursor``.
    overwrite: bool = reactive(False)

    #: Column blocks rather than stream ones: DN's ``VertBlock``.
    vertical_blocks: bool = reactive(False)

    #: ``AutoWrap``: a line typed past the right margin wraps; ``AutoJustify``:
    #: the line it leaves is widened to the margin.  Seeded from the Editor
    #: setup, switched for this editor alone from Editor > Options.
    autowrap: bool = reactive(False)
    justify_on_wrap: bool = reactive(False)

    #: ``AutoBrackets``: an opening bracket typed with its partner after it.
    auto_brackets: bool = reactive(False)

    #: ``OptimalFill``: runs of blanks written to the file as tabs where they
    #: end on a tab stop (``columns.optimal_fill``); the text here keeps its
    #: blanks.  Seeded from the Editor setup, switched by Editor > Options.
    optimal_fill: bool = reactive(False)

    #: ``HiliteLine``: the cursor's line in *Current line*; ``HiliteColumn``:
    #: its column, on every row, in *Current column*.  Seeded from the Editor
    #: setup, switched by Editor > Options.
    highlight_line: bool = reactive(False)
    highlight_column: bool = reactive(False)

    #: ``HiLite``: the text coloured by syntax (:mod:`navigator.lib.highlight`).
    #: Seeded from the setting, switched by Editor > Options.
    syntax_highlight: bool = reactive(True)
    #: *File type*: the lexer chosen from the menu, ``none``, or empty for
    #: ``highlight.ini``'s choice (:func:`navigator.lib.highlight.lexer_for`).
    file_type: str = reactive("")

    #: ``AutoIndent``: Enter indents the new line; ``BackIndent``: Backspace on
    #: a line's first character goes back to an indent above.  Seeded from the
    #: Editor setup, switched for this editor alone from Editor > Options.
    auto_indent: bool = reactive(True)
    back_indent: bool = reactive(True)

    #: *Tab characters* (not DN's): Tab, Backspace's unindent and a stream
    #: block's Tab write tab characters to each stop, then blanks
    #: (:func:`~navigator.lib.editor.columns.fill`).  Seeded from
    #: ``[editor] insert_tabs``, set per file by ``highlight.ini``, switched by
    #: Editor > Options.
    insert_tabs: bool = reactive(False)

    #: *Line numbers* (not DN's): the window shows a :class:`LineGutter`
    #: beside this editor.  Seeded from ``[editor] line_numbers``, set per file
    #: by ``highlight.ini``, switched by Editor > Options.
    line_numbers: bool = reactive(False)

    #: *Soft wrap* (not DN's, whose *Auto wrap* put real breaks in the text):
    #: a line too wide for the area is shown on as many rows as it needs, the
    #: text unchanged (:mod:`navigator.lib.editor.softwrap`).  No sideways
    #: scrolling meanwhile, and never with column blocks.  Seeded from
    #: ``[editor] soft_wrap``, set per file by ``highlight.ini``, switched by
    #: Editor > Options.
    soft_wrap: bool = reactive(False)
    #: Soft wrapped, which of line :attr:`top`'s rows is the first on screen.
    top_row: int = reactive(0)

    #: Spaces, tabs and each line's ending drawn faintly (:data:`HIDDEN_MARKS`):
    #: a departure, DN had no such option.  Seeded from ``[editor] show_hidden``.
    show_hidden: bool = reactive(False)

    #: The name of the lexer colouring the text, "" for none, None until the
    #: lexing thread has said: what the option strip shows as the file type.
    lexer_name: str | None = reactive(None)

    #: ``DrawMode``: 0 off, 1 single lines, 2 double.  While on, the arrows
    #: draw (with Shift), erase (with Ctrl) or only move (:meth:`_draw_key`).
    draw_mode: int = reactive(0)

    #: The marked stream block, its start before its end, or None: from one
    #: place in the text to another.  It stays when the cursor moves, as
    #: DN's *Persistent blocks* kept it, and follows the edits made around it
    #: (:meth:`_follow_edit`).
    block: tuple[Pos, Pos] | None = reactive(None)
    #: :attr:`block` while it is the one the cursor marked (Shift+movement, a
    #: drag, ^K B and ^K K), the very tuple: its ends are then read as painted
    #: cells and it holds what lies between them on screen, which on a line
    #: Hebrew or Arabic reorders is not one stretch of the text
    #: (:meth:`_block_runs`).  A block a command puts in -- ^K C's copy, ^K R's
    #: read -- is the stretch it is.  A departure: DN knew no reordered line.
    _painted_block: tuple[Pos, Pos] | None = None
    #: :meth:`_block_runs`'s last answer and what it was for.
    _runs_cache: tuple[Any, list[tuple[Pos, Pos]]] | None = None

    #: The marked column block, or None: two opposite corners as screen
    #: cells ``(line, col)``, the one marking started from first.  Columns,
    #: not string indices, because a rectangle runs past short lines' ends
    #: and across tabs; :attr:`rectangle` is what it covers.  Only one of the
    #: two blocks is ever marked, the one :attr:`vertical_blocks` says.
    column_block: tuple[tuple[int, int], tuple[int, int]] | None = reactive(None)

    #: ``not BlockVisible``: the block marked but hidden by ^K H / Alt+H.  It is
    #: neither painted nor acted on, follows the edits all the same, and shows
    #: again at a second ^K H or as soon as anything marks.
    block_hidden: bool = reactive(False)

    #: ``RulerVisible``: DN's column ruler, shown on the cursor's row while
    #: the right button drags (:meth:`_right_button`).
    ruler: bool = reactive(False)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._use(EditBuffer())
        #: Where a Tab stops, and how far a tab character reaches.
        self.tab_size = SETTINGS.editor.tab_size
        self.vertical_blocks = SETTINGS.editor.vertical_blocks
        self.autowrap = SETTINGS.editor.autowrap
        self.auto_brackets = SETTINGS.editor.auto_brackets
        self.optimal_fill = SETTINGS.editor.optimal_fill
        self.highlight_line = SETTINGS.editor.highlight_line
        self.highlight_column = SETTINGS.editor.highlight_column
        self.syntax_highlight = SETTINGS.editor.syntax_highlight
        self.auto_indent = SETTINGS.editor.auto_indent
        self.back_indent = SETTINGS.editor.backspace_unindents
        self.insert_tabs = SETTINGS.editor.insert_tabs
        self.line_numbers = SETTINGS.editor.line_numbers
        self.soft_wrap = SETTINGS.editor.soft_wrap
        #: Each line's rows, by its text, the width and the tab size.
        self._wrap_cache: dict[tuple[str, int, int], list[tuple[int, int]]] = {}
        self.settle_modes()
        self.justify_on_wrap = SETTINGS.editor.justify_on_wrap
        self.show_hidden = SETTINGS.editor.show_hidden
        #: ``LeftSide``, ``RightSide`` and ``InSide``: this editor's margins and
        #: paragraph indent, seeded from the Editor setup and changed by
        #: *Format Margins* for this editor alone, as ``SetFormat`` did.
        self.margins = (
            SETTINGS.editor.left_margin, SETTINGS.editor.right_margin, SETTINGS.editor.paragraph,
        )
        #: ``ForcedCRLF``: the ``NEWLINES`` key every line is written with, from
        #: ``highlight.ini``'s ``line_ending`` (:meth:`apply_defaults`), or "".
        self.forced_ending = ""
        #: The right press while its button is down: a click until it moves.
        self._right_press: MouseClickEvent | None = None
        #: Another view's edit in progress: this cursor as a place in the
        #: text, carried through each step of it (:meth:`_edit_here`).
        self._anchor: Pos | None = None
        #: :meth:`_window_marks`' last answer, and what it was for.
        self._marks_cache: tuple[Any, dict[int, list[tuple[int, int]]]] | None = None
        # In __init__, not the class body: a plain class attribute would
        # shadow the reactive descriptor, as `Console` learned.
        self.can_focus = True
        #: The match the last search showed, and the cursor and text it was shown
        #: for: ``SearchActive``'s highlight lasts only while both stand.
        self._found: tuple[Pos, Pos] | None = None
        self._found_for: tuple[int, int, int] | None = None
        #: The block indicator's and the line:column's places in the info line,
        #: set as it is written.
        self._block_at = (0, 0)
        self._place_at = (0, 0)
        self._code_at = (0, 0)
        #: The block's fixed end while the left button drags, else None: a
        #: ``Pos``, or a ``(line, col)`` cell for a column block.
        self._drag_from: Any = None
        #: The line a Ctrl+press was on: a drag from it marks whole lines.
        self._line_from: int | None = None
        #: The cell the left button went down on, until the drag leaves it:
        #: terminals report motion inside that cell too, which is no drag.
        self._press_cell: tuple[int, int] | None = None
        #: The word a double-click marked, ``(start, stop)`` as ``Pos``, while
        #: the button stays down: the drag after it then marks whole words.
        self._drag_word: tuple[Pos, Pos] | None = None
        #: Whether the movement under way drags the block along (Shift, or a
        #: mouse drag): a column block's corner may then go past a line's end.
        self._extending = False
        #: The column Up/Down/PgUp/PgDn aim for while they pass shorter lines,
        #: or None after any other movement or edit.
        self._goal: int | None = None
        #: ``LastDir``: where the pen came into the cell it is on, or None.
        self._pen: int | None = None
        #: DN's ``MarkPos``: markers 1 to 9, each a ``(line, col)`` or None.
        #: Fixed places, as DN's were -- an edit above one does not move it.
        self.markers: list[tuple[int, int] | None] = [None] * 9
        #: ^K B or ^K K pressed with no block marked: the end it set, and
        #: whether it was the start, waiting for the other.  Any edit drops it.
        self._half_mark: tuple[Any, bool] | None = None
        #: ``Locker``: what ``lock.take`` gave while this editor holds its
        #: file (*Lock edited files*), else None.
        self._lock: tuple[int, int] | None = None

    # -- the file ----------------------------------------------------------------

    def open(self, path: Path | str, *, new: bool = False) -> None:
        """Edit *path* from its start.  Raises ``OSError`` if it cannot be read.

        With *new*, a file that does not exist is an empty text that saving
        will create -- Shift+F4's *Edit new file*.  A text with no line break
        to follow, new or not, breaks lines as the Editor setup's *Line
        divisor* says.
        """
        path = Path(path)
        try:
            document = Document.load(path, SETTINGS.editor.fallback_encoding)
        except FileNotFoundError:
            if not new:
                raise
            document = Document()
        self.use_document(path, document)

    def use_document(self, path: Path | str, document: Document) -> None:
        """Edit *document*, already read from *path*, from its start.

        What :meth:`open` does once the file is read -- for a caller that read
        it on a thread (``navigator.widgets.editor.loading``).  DN's
        ``LoadFile`` (``MICROED.PAS:1197``): insert mode, line drawing off and
        the pen lifted, whatever the text before had (``InsertMode := On``,
        ``DrawMode := 0``, ``LastDir := -1``).
        """
        path = Path(path)
        if not any(document.endings):
            document.newline = NEWLINES[SETTINGS.editor.line_divisor]
        self.apply_defaults(document)
        self._use(EditBuffer(document))
        self._unmark()
        self.markers = [None] * 9
        self.overwrite = False
        self.draw_mode = 0
        self._pen = None
        self.path = path
        self.line = self.col = self.top = self.left = 0
        self.revision += 1
        self.lock_file()

    #: ``highlight.ini``'s key for each editor attribute it may set
    #: (:data:`navigator.lib.highlight.EDITOR_KEYS`), the margins aside.
    MASK_KEYS = {
        "syntax_highlight": "syntax_highlight", "auto_indent": "auto_indent",
        "auto_brackets": "auto_brackets", "backspace_unindents": "back_indent",
        "highlight_line": "highlight_line", "highlight_column": "highlight_column",
        "autowrap": "autowrap", "justify_on_wrap": "justify_on_wrap",
        "insert_tabs": "insert_tabs", "line_numbers": "line_numbers",
        "soft_wrap": "soft_wrap",
    }

    def apply_defaults(self, document: Document) -> None:
        """``InitHighLight`` at the end of ``LoadFile``: what ``highlight.ini``'s
        masks say for this file (``document.defaults``, read with it) over
        what the editor has.  A key they do not name keeps its value, as DN's
        did; the edit history, restored after, wins over both.

        ``line_ending`` is DN's ``ForcedCRLF``, reset on every load: every line
        is *written* with it (:meth:`snapshot`), and new lines take it, but the
        text is not changed by opening it.
        """
        defaults = document.defaults
        for key, name in self.MASK_KEYS.items():
            if key in defaults:
                setattr(self, name, defaults[key])
        margins = tuple(defaults.get(key, old) for key, old in
                        zip(("left_margin", "right_margin", "paragraph"), self.margins))
        if margins != self.margins:
            self.margins = fix_margins(*margins)
        self.settle_modes()
        self.forced_ending = defaults.get("line_ending", "")
        if self.forced_ending:
            document.newline = NEWLINES[self.forced_ending]

    def lock_file(self) -> None:
        """``LockFile``: hold :attr:`path` against other programs, if the
        Editor setup's *Lock edited files* says so -- read now, as DN read
        ``EditorDefaults`` each time.  Whatever was held before is let go."""
        self.unlock_file()
        if SETTINGS.editor.lock_file and self.path is not None:
            self._lock = lock.take(self.path)

    def unlock_file(self) -> None:
        """``UnLockFile``: let other programs at the file again."""
        lock.release(self._lock)
        self._lock = None

    def _use(self, buffer: EditBuffer) -> None:
        self._leave_buffer()
        self.buffer = buffer
        buffer.listeners.append(self._follow_edit)
        buffer.listeners.append(self._follow_tokens)
        buffer.views.append(self)
        self.rehighlight()

    def _leave_buffer(self) -> None:
        """Stop showing the text this editor shows: its other views, if it has
        any, keep it."""
        buffer = getattr(self, "buffer", None)
        if buffer is None:
            return
        for listener in (self._follow_edit, self._follow_tokens):
            if listener in buffer.listeners:
                buffer.listeners.remove(listener)
        if self in buffer.views:
            buffer.views.remove(self)
            # The views left repaint: a title may no longer say which it is.
            for view in buffer.views:
                view.revision += 1

    def siblings(self) -> list[FileEditor]:
        """The other editors showing this text (Window > *New view*)."""
        return [view for view in self.buffer.views if view is not self]

    def _edit_here(self) -> None:
        """About to edit: this view is the one editing, and every other view's
        cursor is taken as a place in the text before anything changes -- the
        edits are heard after they are made, when its column no longer says
        where it was (:meth:`_follow_edit`)."""
        self.buffer.editing = self
        for view in self.siblings():
            view._anchor = view._mark_pos()

    #: What a new view takes over from the one it is opened from, besides the
    #: text: where it is, and every mode.
    VIEW_STATE = (
        "path", "tab_size", "margins", "forced_ending", "file_type",
        "overwrite", "vertical_blocks", "autowrap", "justify_on_wrap", "auto_brackets", "optimal_fill",
        "highlight_line", "highlight_column", "syntax_highlight", "auto_indent", "back_indent",
        "show_hidden", "insert_tabs", "line_numbers", "soft_wrap",
    )

    def share(self, source: FileEditor) -> None:
        """Window > *New view* (not DN's): show *source*'s text -- its buffer,
        so one undo history and one save -- from where *source* is, with its
        modes, and a cursor, a block and markers of its own from here on."""
        for name in self.VIEW_STATE:
            setattr(self, name, getattr(source, name))
        self._use(source.buffer)
        self.markers = list(source.markers)
        self.top, self.top_row, self.left = source.top, source.top_row, source.left
        self.line, self.col = source.line, source.col
        # Every view repaints: a title says which of them it is now.
        for view in self.buffer.views:
            view.revision += 1
        self.lock_file()

    def save(self) -> None:
        """Write the text to :attr:`path`, here and now.  Raises ``OSError``.

        The window writes on a thread instead (``EditWindow._write``), through
        :meth:`snapshot` and :meth:`saved`.
        """
        if self.path is None:
            raise OSError(tr("no file name"))
        lines, endings, _ = self.snapshot()
        write_file(self.path, encode_lines(lines, endings, encoding=self.document.encoding))
        self.buffer.mark_saved()
        self.revision += 1
        self.lock_file()

    def snapshot(self) -> tuple[list[str], list[str], object]:
        """The text as it is now, for a thread to write: lines, endings, and
        the point :meth:`saved` is to be given once it is written.

        Copies of the two lists, which edits change in place; the strings in
        them never change, so the copies are the text whatever is typed next.
        """
        document = self.buffer.document
        lines = self.filled(document.lines)
        endings = list(document.endings)
        if self.forced_ending:
            # ``WriteBlock``'s ``ForcedCRLF``: every line written with it.
            forced = NEWLINES[self.forced_ending]
            endings = [forced if ending else "" for ending in endings]
        return lines, endings, self.buffer.save_point()

    def filled(self, lines: list[str]) -> list[str]:
        """*lines* as they are written: through ``CompressString`` with *Optimal fill*
        on, a copy as they stand without."""
        if not self.optimal_fill:
            return list(lines)
        return [columns.optimal_fill(line, self.tab_size) for line in lines]

    def saved(self, point: object) -> None:
        """The text as :meth:`snapshot` took it is on disk now -- in every view of it."""
        self.buffer.mark_saved(point)
        for view in self.buffer.views:
            view.revision += 1

    @computed
    def modified(self) -> bool:
        self.revision
        return self.buffer.modified

    @property
    def document(self) -> Document:
        return self.buffer.document

    @computed
    def line_count(self) -> int:
        self.revision
        return len(self.buffer.document)

    # -- what the frame's scroll bars show (a departure, asked for: DN's editor
    # had both always; shown only while there is more than the area holds, as
    # the viewer's) --------------------------------------------------------------

    @computed
    def overflows(self) -> bool:
        """Whether there are more lines than the area shows, or it is scrolled
        down from the first: what shows the right frame's bar."""
        if self.soft_wrap:
            self.revision
            return self.top > 0 or self.top_row > 0 or self._rows_from(0, 0, max(1, self.height) + 1) > self.height
        return self.top > 0 or self.line_count > max(1, self.height)

    @computed
    def row_span(self) -> int:
        """How many columns the widest line on screen takes -- or the cursor's
        column, past a line's end -- what the bottom bar's range is."""
        self.revision
        lines = self.document.lines
        widest = self.col + 1
        for number in range(self.top, min(len(lines), self.top + max(1, self.height))):
            text = lines[number]
            span = len(text) if text.isascii() and "\t" not in text else self._line_width(number)
            widest = max(widest, span)
        return widest

    @computed
    def overflows_across(self) -> bool:
        """Whether a line on screen is wider than the area, or it is scrolled
        sideways: what shows the bottom frame's bar."""
        if self.soft_wrap:
            return False
        return self.left > 0 or self.row_span > max(1, self.width)

    def refusal(self, command: Any) -> str:
        no_block = tr("No block is marked")
        if isinstance(command, Undo):
            self.revision
            return "" if self.buffer.can_undo else tr("Nothing to undo")
        if isinstance(command, Redo):
            self.revision
            return "" if self.buffer.can_redo else tr("Nothing to redo")
        if isinstance(command, GotoMarker):
            # Greyed on the menu until placed; DN's ^Q N did nothing either.
            placed = 1 <= command.marker <= len(self.markers) and self.markers[command.marker - 1] is not None
            return "" if placed else tr("Marker {n} is not placed").format(n=command.marker)
        if isinstance(command, HideBlock):
            return "" if self.marked else no_block
        if isinstance(command, ClipboardPaste):
            # DN greyed cmPaste on an empty clipboard.  Only the application's own
            # copy can be looked at without a process or a terminal round trip, so
            # with the system clipboard on, Paste stays enabled (a departure).
            app = self.application
            if app is not None and not app.system_clipboard and not app.private_clipboard():
                return tr("The clipboard is empty")
            return ""
        if isinstance(command, UnindentBlock) and command.stop:
            # Shift+Tab: the cursor's line, when no block is there to take it.
            return ""
        if isinstance(command, SelectAll):
            self.revision
            return "" if any(self.document.lines) else tr("The text is empty")
        if isinstance(command, SwitchBlock) and self.soft_wrap:
            # A rectangle over wrapped rows would be ragged pieces.
            return tr("Not with soft wrap")
        if isinstance(command, SwitchSoftWrap) and self.vertical_blocks:
            return tr("Not with column blocks")
        if isinstance(command, (LJustify, LRight, LLeft, LCenter)):
            # ``FormatBlock``'s ``VertBlock`` exit, said rather than done silently.
            return tr("Line format works on line blocks") if self.vertical_blocks else ""
        if isinstance(command, (FJustify, FRight, FLeft, FCenter)):
            # ``not (ValidBlock and BlockVisible) or VertBlock``: a stream block only.
            if self.block is None or self.block_hidden:
                return no_block
            return ""
        if isinstance(command, (
            ClipboardCut, ClipboardCopy, Clear, CopyBlock, MoveBlock,
            IndentBlock, UnindentBlock, UpcaseBlock, LowcaseBlock, CapitalizeBlock, SortBlock,
            CalcBlock,
            MoveBlockStart, MoveBlockEnd,
        )):
            return "" if self.has_block else no_block
        return super().refusal(command)

    def checks(self, command: Any) -> bool | None:
        """Editor > Options ticks *Vertical blocks*, *Auto wrap*, *Justify on wrap* and
        *AutoBrackets* while they are on (``SetM``)."""
        if isinstance(command, SwitchBlock):
            return self.vertical_blocks
        if isinstance(command, SwitchSoftWrap):
            return self.soft_wrap
        if isinstance(command, SwitchSave):
            return self.autowrap
        if isinstance(command, SwitchBrackets):
            return self.auto_brackets
        if isinstance(command, SwitchFill):
            return self.optimal_fill
        if isinstance(command, SwitchTabs):
            return self.insert_tabs
        if isinstance(command, SwitchLineNumbers):
            return self.line_numbers
        if isinstance(command, SwitchHiLine):
            return self.highlight_line
        if isinstance(command, SwitchHiColumn):
            return self.highlight_column
        if isinstance(command, SwitchHighLight):
            return self.syntax_highlight
        if isinstance(command, SwitchHiddenChars):
            return self.show_hidden
        if isinstance(command, SwitchInsert):
            # Ticked in overwrite: what the option strip lights.
            return self.overwrite
        if isinstance(command, SwitchIndent):
            return self.auto_indent
        if isinstance(command, SwitchBack):
            return self.back_indent
        if isinstance(command, SwitchWrap):
            return self.justify_on_wrap
        if isinstance(command, SetLineEnding):
            return self.document.line_ending == command.ending.upper()
        if isinstance(command, (ReopenWithEncoding, SaveWithEncoding)):
            return self.document.encoding == command.encoding
        return super().checks(command)

    @computed
    def format_text(self) -> str:
        """The bottom frame's markers: the line ending and the encoding,
        ``[LF]═[UTF-8]``, bracketed as the option strip's items are, a frame
        cell between -- a departure, asked for (``FormatMarks``)."""
        self.revision
        bar = "═" if self.glyphs >= GLYPHS_UNICODE else "="
        ending = self.document.line_ending
        label = encodings.label(self.document.encoding)
        # Each zone takes its brackets too: a click on one is the marker's.
        self._ending_at = (0, len(ending) + 2)
        self._encoding_at = (len(ending) + 3, len(ending) + 5 + len(label))
        return f"[{ending}]{bar}[{label}]"

    # -- the info line -------------------------------------------------------------

    @computed
    def info_text(self) -> str:
        """``TInfoLine``: modified mark, line:column, the code under the cursor, block mode, a pending chord.

        ``☼══12:34 [065] (↔)``.  The code is the character's own number, which
        was a byte in DN and is a code point here -- three digits until it
        needs more -- and a byte that was not UTF-8 gives the byte.
        """
        self.revision
        unicode = self.glyphs >= GLYPHS_UNICODE
        bar = "═" if unicode else "="
        mark = ("☼" if unicode else "*") if self.modified else bar
        text = self.document.lines[self.line] if self.line < len(self.document) else ""
        index, past = columns.index_at(text, self.col, self.tab_size)
        code = 0
        if not past and index < len(text):
            char = text[index]
            code = ord(char) - 0xDC00 if columns.is_escaped(char) else ord(char)
        block = ("(↕)" if unicode else "(|)") if self.vertical_blocks else ("(↔)" if unicode else "(-)")
        if self.draw_mode:
            # ``{┼}``/``{╬}``: the pen's weight, where the block's kind was.
            block = ("{┼}", "{╬}")[self.draw_mode - 1] if unicode else ("{+}", "{#}")[self.draw_mode - 1]
        elif SETTINGS.editor.show_options:
            # A departure: the option strip shows the block's kind, with the
            # editor's other options, so the info line leaves it out.
            block = ""
        # A departure: the keys of a chord still waiting for its last, WordStar's
        # ``^K``, so a key about to be swallowed is not a surprise.
        app = self.application
        pending = ""
        if app is not None and app.chord:
            pending = " " + " ".join(
                f"^{key[5:].upper()}" if key.startswith("ctrl+") else key for key in app.chord.split()
            )
        place = f"{self.line + 1}:{self.col + 1}"
        head = f"{mark}{bar}{bar}{place} [{code:03d}]" + (" " if block else "")
        self._block_at = (len(head), len(head) + len(block))
        self._place_at = (3, 3 + len(place))
        code_start = 3 + len(place) + 1
        self._code_at = (code_start, code_start + len(f"[{code:03d}]"))
        return f"{head}{block}{pending}"


def gutter_width(line_count: int) -> int:
    """The columns :class:`LineGutter` takes for *line_count* lines: the
    digits of the last number, two at least so a text reaching its tenth line
    does not move, and a blank before the text."""
    return max(2, len(str(max(1, line_count)))) + 1


class LineGutter(Widget):
    """*Line numbers* (not DN's, which numbered no lines): each row's line
    number beside the editor's text, the cursor's in ``::current``.

    A widget of its own beside :class:`FileEditor`, which the window narrows
    by its width, so nothing inside the editor learns of an offset.  It keeps
    the default ``mirrors``: on a right-to-left screen it lands on the right
    of the text, where its right-aligned lines start, its blank against them
    and its digits still read left to right.  A click on a number takes the
    cursor to that line's start.  Soft wrapped, a line's first row alone is
    numbered (:meth:`FileEditor.visible_rows`), the rows it runs on blank.
    """

    parts = ("current",)

    #: The editor whose lines are numbered.  Not ``editor``: in the window's
    #: markup that name is the editor's id, and binding it to itself cycles.
    target: Any = reactive(None)

    def render(self, surface: Surface) -> None:
        editor = self.target
        normal = self.style
        surface.fill(0, 0, self.width, self.height, " ", normal)
        if editor is None or self.width < 2:
            return
        current = self.part_style("current")
        digits = self.width - 1
        cursor = editor.line
        for y, (number, row) in enumerate(editor.visible_rows()[:self.height]):
            if row:
                continue
            surface.draw_text(0, y, str(number + 1).rjust(digits)[-digits:],
                              current if number == cursor else normal)

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        editor = self.target
        if editor is None or event.button != "left" or event.action != "press":
            return False
        rows = editor.visible_rows()
        if not 0 <= event.y < len(rows):
            return True
        editor.focus()
        editor._moved()
        editor._move_to(rows[event.y][0], 0)
        return True


class InfoLine(StaticText):
    """``TInfoLine``: the editor's line over the bottom frame, and what a click on it asks.

    DN gave it three places to click: the line and column (``cmGotoLineNumber``),
    the character's code (``cmSpecChar``, *ASCII Chart*) and the block indicator
    (``cmSwitchBlock``).  A press anywhere on the line is the line's, as
    ``ClearEvent`` made it, so it never reaches the frame beneath.

    A departure: under *Vertical blocks* the block indicator ``(↕)`` is painted
    as ``InfoLine::column_block`` (reversed), since the mode is kept per file and DN's
    plain arrow was easy to miss.
    """

    parts = (*StaticText.parts, "column_block")

    def render(self, surface: Surface) -> None:
        super().render(surface)
        editor = getattr(self.parent, "editor", None)
        if isinstance(editor, FileEditor) and editor.vertical_blocks and not editor.draw_mode:
            start, end = editor.block_indicator()
            surface.draw_text(start, 0, self.text[start:end], self.part_style("column_block"),
                              max(0, self.width - start))

    def tooltip_at(self, x: int, y: int) -> str:
        """What a click on each place does, with its key; elsewhere the whole
        name of the file, which the title may have cut."""
        window = self.parent
        editor = getattr(window, "editor", None)
        if not isinstance(editor, FileEditor):
            return super().tooltip_at(x, y)
        app = self.application

        def keyed(text: str, command: Any) -> str:
            key = commands.key_for(app, command, editor) if app is not None else None
            return with_keys(text, commands.key_label(key) if key else "")

        for (start, end), text, command in (
            (editor.place_indicator(), tr("Line and column: a click goes to a line"), GotoLineNumber),
            (editor.code_indicator(), tr("The character's code: a click opens the character table"), AsciiTable),
            (editor.block_indicator(), tr("Vertical blocks: a click makes them stream blocks")
             if editor.vertical_blocks else tr("Stream blocks: a click makes them vertical"), SwitchBlock),
        ):
            if start <= x < end:
                return keyed(text, command)
        use_set = getattr(window, "use_set", None)
        if use_set is not None:
            return str(use_set.copies[0].origin)
        return str(editor.path) if editor.path is not None else ""

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.action != "press":
            return True
        editor = getattr(self.parent, "editor", None)
        if event.button == "left" and isinstance(editor, FileEditor):
            start, end = editor.block_indicator()
            if start <= event.x < end:
                await editor.emit(SwitchBlock())
            start, end = editor.place_indicator()
            if start <= event.x < end:
                await editor.emit(GotoLineNumber())
            start, end = editor.code_indicator()
            if start <= event.x < end:
                await editor.emit(AsciiTable())
        return True


class FormatMarks(StaticText):
    """The line ending and the encoding over the bottom frame, after the info
    line: ``[LF]═[UTF-8]`` -- a departure, asked for: DN wrote every text in
    ``CR+LF`` and the screen's code page, so it had nothing to show.

    A left press on the line ending makes it the next of LF, CRLF and CR
    (``FileEditor.next_line_ending``) and a right press asks for its box
    (:class:`ChooseLineEnding`); either press on the encoding asks for its box
    (:class:`ChooseEncoding`).  The window opens a box over the marker.  Every
    press on the line is the line's, as on the info line.
    """

    def _zones(self) -> tuple[tuple[tuple[int, int], Any], ...]:
        from navigator.widgets.editor.commands import ChooseEncoding, ChooseLineEnding

        editor = getattr(self.parent, "editor", None)
        if not isinstance(editor, FileEditor):
            return ()
        return ((editor.ending_indicator(), ChooseLineEnding),
                (editor.encoding_indicator(), ChooseEncoding))

    def tooltip_at(self, x: int, y: int) -> str:
        from navigator.widgets.editor.commands import ChooseLineEnding

        editor = getattr(self.parent, "editor", None)
        app = self.application
        for (start, end), command in self._zones():
            if start <= x < end:
                if command is ChooseLineEnding:
                    text = tr("Line endings: a click makes them the next kind, a right click offers them all")
                else:
                    text = tr("Encoding: a click reopens or saves the text in another")
                key = commands.key_for(app, command, editor) if app is not None else None
                return with_keys(text, commands.key_label(key) if key else "")
        return super().tooltip_at(x, y)

    async def on_mouse_click(self, event: MouseClickEvent) -> bool:
        if event.action != "press":
            return True
        from navigator.widgets.editor.commands import ChooseLineEnding, SetLineEnding

        editor = getattr(self.parent, "editor", None)
        if event.button in ("left", "right") and isinstance(editor, FileEditor):
            for (start, end), command in self._zones():
                if start <= event.x < end:
                    if command is ChooseLineEnding and event.button == "left":
                        await editor.emit(SetLineEnding(editor.next_line_ending()))
                    else:
                        await editor.emit(command())
        return True
