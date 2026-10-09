---
name: navigator-editor
description: The internal editor (F4, DN's MICROED.PAS) -- navigator/editor/ (Document, columns, EditBuffer with undo, save), FileEditor and EditWindow, byte-for-byte round-tripping, editor commands named after DN's cm*, closing with must_ask, the Editor menu, and syntax highlighting (navigator/highlight.py, Pygments, highlight.ini, the ::token part) for the editor and the viewer. Use when changing the editor or highlighting.
---

# The editor

- **F4 is DN's internal editor** (`MICROED.PAS`), being built in phases toward everything DN's editor had.
  `navigator/editor/` is the model (`Document`, `columns`, `EditBuffer` with undo, `save`); `FileEditor` is `TFileEditor`
  and `EditWindow` is `TEditWindow`, zoomed on the desktop with `TInfoLine` over the bottom frame.
- **A file round-trips byte for byte** -- tabs, each line's own terminator, non-UTF-8 bytes (`surrogateescape`) -- a
  departure from DN's rewriting. Saving renames a new file over the old one.
- **Reading and writing run on a thread, behind DN's `WriteMsg`** (`ReadBlock`, `SaveFile`). `read_document`
  (`navigator/editor/document.py`) reads 4 MiB chunks through `LineReader`, which splits exactly as `from_bytes` does
  however the bytes are cut (a CR ending a chunk waits for the next -- DN's `ReadBlock` stepped back for it), in a few
  C calls per chunk so the loop keeps painting. `navigator/widgets/editor/loading.py` runs it through
  `navigator.progress.run_with_progress`: `open_editor` is **async** and returns None when cancelled; F3 (`load_text`),
  ^K R and SmartPad go the same way. Saving snapshots the lists (`FileEditor.snapshot`), writes them as chunks on a
  thread (`encode_lines`, `write_file(path, chunks, job)`) under one `EditWindow._saving` lock, and marks the
  snapshot's save point (`EditBuffer.save_point`/`mark_saved(point)`) -- what is typed meanwhile leaves the text
  changed. **Too large is refused** with DN's `erNotEnoughMemory` (`navigator/memory.py`): against 75% of
  `MemAvailable` before reading, then after every chunk projected from the lines so far (DN's
  `4*(LCount+50)+FFSize`). Departures: the box (`WriteWin`, `file_ops/write_win`) waits `SLOW_PROGRESS_DELAY` (1 s)
  before it appears, has a spinner, a gauge with a percentage and *Cancel* (DN's was a still message read past by Esc);
  a cancelled save removes its temporary and leaves the file as it was, except a write in place (hard links), which
  cannot stop half way and hides *Cancel* (`job.cancellable`).
- **The cursor stays within the line's text** (a departure, asked for; DN's stood anywhere): movements go through
  `_move_to`, which clamps the column unless `_free` (line drawing, or extending a column block -- Shift+movement, Shift+click, a
  drag, flagged by `_extending`; a plain click or move clamps in column mode too, *Vertical blocks* being per file).
  A column block's corner takes `_goal` during Up/Down so Shift+Down across a short line keeps its width; Right/Left cross line ends;
  vertical moves keep a goal column (`_move_vertically`, `_goal`). `_go_column` itself still places anywhere -- edits
  that leave the cursor on an indent rely on it.
- **Every key is a command named after DN's `cm*`** in `FileEditor.keys` (`navigator/widgets/editor/commands.py`).
  `Widget.edits_text` makes the command line's Enter/Home/End/Tab and pastes step aside.
- **Stream blocks and the clipboard.** Shift with any movement marks (`_marking` wraps the movement handlers; the
  block grows from the cursor, or from its other end when the cursor stood on one). `FileEditor.block` is
  `(start, end)` in `Pos`, start first, or None; it persists while the cursor moves under *Persistent blocks* (DN's
  default). Off, it goes (`_block_off`, DN's `BlockOff`) on a movement without Shift, typing, Enter, Backspace and Del.
  *Overwrite blocks* only counts with *Persistent blocks* off (DN's `(ebfPbl + ebfObl) = ebfObl`, both read live from
  the setup): then typing and pastes replace the block in one undo group (`_begin_typed`, `InputChar`'s and
  `PasteBlock`'s `DeleteBlock`), and Del deletes it alone (`_deleting_block`); Backspace never takes it, and Tab,
  ^Q D/T and ^K R leave it be. **A departure, asked for: with the cursor in the block** (`_cursor_in_block`, either
  end included, a column block's rectangle with the column past its right edge) typing and pastes replace it, Del
  and Backspace delete it alone, and Enter (inserting) replaces it with the break, one undo group each, whatever the
  two settings say (`_takes_block`). Outside it DN's rules above stand. Likewise Tab with the cursor in the block is
  ^K I by a tab stop (`on_tab_key`, `IndentBlock(stop=True)`), and Shift+Tab is bound to ^K U by up to a tab stop
  (`UnindentBlock(stop=True)`, `unindent_block_stop` in `keybindings.ini`, always enabled): with the cursor in the
  block it unindents the block, otherwise the cursor's line alone, the cursor moving left with its text; nothing indented, no edit at all
  (the typing run before it goes on, `_blank_at`) --
  departures too; ^K I/U keep DN's one blank. Either way it follows every edit, undo's included, through
  `EditBuffer.listeners` and `document.shifted` -- text inserted at the block's end stays outside it. Painted with
  `FileEditor::selected`. Ctrl+Ins (`ClipboardCopy`, `cmCopy`), Shift+Del (`ClipboardCut`), Shift+Ins
  (`ClipboardPaste`, which asks the application and types the `PasteEvent` that comes back), Ctrl+Del (`Clear`,
  `cmClear`); also Editor > Edit. Copies hand out plain `\n` breaks, pastes take the file's own. Not `Cut`/`Copy`/`Paste`:
  F5's `Copy` and `on_paste` (the paste event) already own those handler names. Ctrl+C/Ctrl+V stay WordStar's.
  The ^K/^Q commands are named after their `cm*` in `DN.DNR`'s `EDITOR COMMANDS` table (`BlockStart`, `Clear`,
  `UpcaseBlock`, `MoveBlockStart`, `BlockRead`...); the clipboard four keep their own names (above). Every ^K/^Q
  command in the table is here.
- **WordStar's ^K and ^Q** are navkit chords, each letter bound plain and with Ctrl (`_wordstar`): ^K B/K mark the
  start/end (with no block, the first waits for the other -- `_half_mark`, dropped by any edit), H (and Alt+H) hides the block or shows it again, C copies
  the block to the cursor and marks the copy, V moves it (refused with the cursor inside it), Y deletes it, I/U
  indent/unindent its lines by one blank (a column block at its left column; a leading tab gives way to spaces), `[`
  `]` `\` upper/lower/capitalise it, T marks the word, L the line; ^Q B/K go to its ends, ^Q Y deletes to the line's
  end, ^Q L undoes.
- **^K R / ^K W are DN's `BlockRead`/`BlockWrite`** (`MICROED.PAS`), also Editor > Edit's *Paste from...*/*Copy
  to...*, handled by `EditWindow` (dialogs and I/O; `FileEditor.block_file_text`/`read_block` are the text). The name
  comes from navml's `FileDialog` (`GetFileNameDialog`: titles *Copy block to*/*Paste from File*, labels *File
  ~N~ame*/*~P~aste from*, the shared `hsEditPasteFrom` history `edit_paste_from`), listing the active panel's
  directory. Writing joins lines with the Editor setup's *Line divisor* and ends without one; a column block, or a
  one-line block, writes its columns unpadded. An existing file is `CheckForOver`'s Yes/A~p~pend/Cancel (`Dialog`
  `yes-no-cancel` with `no` relabelled), a read-only one asks *Modify it anyway?* and gets its mode back afterwards;
  the write emits `FileSaved` (`cmRereadDir`). Reading turns column blocks off (`VertBlock := Off`) and marks what it
  put in.
- **Sort, ^K S / Alt+T** (`SortBlock`, DN's `SortBlock` in `EDITOR.PAS`, also Block > Sort): the lines a *column*
  block spans, ordered by its columns' text as plain strings (case-sensitive, as Pascal's `<`); a stream block gets
  `dlED_VertNeed`, "Vertical blocks need for this operation", word for word. Each line keeps the ending of the place it
  lands in. Departures: stable (DN's quicksort was not) and one undo step (DN dropped its undo record).
- **Calculate sum, Alt+Ins** (`CalcBlock`, DN's `CalcBlock`, also Block > *Calculate sum*): the numbers in a column
  block's columns, each with its blanks removed (`DelSpaces`) and read as `Val` would (a non-number counts 0),
  added up and put on the clipboard (`cmPutInClipboard`); the text is untouched and nothing is shown. Written as
  `Str(R:0:20)` less trailing zeros, but summed with `Decimal` (a departure: DN's `Real` printed binary error).
  DN's table also gave ^K^U to it, but `cmUnindentBlock` had ^K^U first and the menu shows Unindent there, so ^K U
  stays Unindent. A stream block gets `dlED_VertNeed`.
- **Print block, ^K P / Shift+F8** (`PrintBlock`, DN's `Print(On)` in `EDITOR.PAS`, also Editor > File > *Print
  block*): *Print N lines?* (`dlED_PrintQuery`), then the block's lines (`FileEditor.block_lines`, DN's
  `GetSelection`) to `navigator/printing.py`, which hands them to `lp` (else `lpr`) in an executor -- the system
  spooler standing for DN's `.PRN` file and print manager. LF line ends, no closing form feed. A refusal (no
  printer, no default destination) is shown as the spooler's own words.
- **Print file, F8** (`PrintFile`, DN's `Print(Off)`, also Editor > File > *Print*): the whole text the editor holds,
  saved or not (DN printed `FileLines`), less the empty line after a final break; same question and spooler as
  Print block (`EditWindow.print_lines`). `PrintFile` is one command, as `cmPrintFile` was: it lives in
  `navigator/commands.py` (re-exported by `manager/commands.py`) because the file manager's Ctrl+F9 answers it too
  (`navigator-file-ops`).
- **Bracket pair, Alt+Left / Alt+Right / ^Q[ / ^Q^]** (`BracketPair`, DN's `cmBracketPair`, `SearchFwd`/`SearchBwd`
  in `EDITOR.PAS`): on `(` `[` `{` the cursor goes forward to the matching close, on `)` `]` `}` back to the opener,
  across lines, counting only brackets of the same kind and blind to strings and comments, as DN was; no bracket under
  the cursor or no pair, and it stays. ^Q[ and ^Q^] are bound only in the forms the table gives.
- **The info line is `InfoLine`** (DN's `TInfoLine`, a `StaticText` beside `FileEditor`, styled by
  `EditWindow StaticText#info`): a left click on its block indicator runs `SwitchBlock` and one on its line:column
  `GotoLineNumber`, as `TInfoLine.HandleEvent` turned them into `cmSwitchBlock`/`cmGotoLineNumber`.
  Under *Vertical blocks* the `(↕)` is painted as `InfoLine::column_block` (the info line reversed, a departure:
  the mode is kept per file and DN's plain arrow was missed). `FileEditor.block_indicator()`/`place_indicator()` say where they stand, worked out from the text since the code
  may outgrow three digits; `code_indicator()` is its third place, `[nnn]` (`cmSpecChar`), which opens the
  character table. Every press on the line is the line's, so none reaches the frame.
- **The character table, Ctrl+P** (`AsciiTable`, DN's `cmASCIITable`/`cmSpecChar`, also Editor > Misc > *Character
  table* and the info line's code): `AsciiChart` (`shell/ascii_chart`, DN's `TASCIIChart`, 34 by 12) around
  `CharTable` (`shell/char_table`, `TTable`: 32 by 8 CP437 glyphs from `viewer.cp437`, block caret) and a report line
  (`TReport`). Arrows/Home/End move, a press or drag picks, Esc cancels, Enter/Ctrl+B/Ctrl+P or a double click take;
  a character typed that code page 437 has is taken at once. It reopens on the code last taken (`p` at first). The
  editor types what the chart shows -- the glyph, `│` for 179, the text being Unicode -- and a NUL for 0. Departure:
  centred, where DN reopened it where it was left. `AsciiTable` lives in `navigator/commands.py`: the shell answers
  it too (`console-command-line`), and an editor's ^B^V chord keeps Ctrl+B in the editor, as DN's table did.
- **Open, F3, and Save as, Shift+F2** (`LoadText`/`SaveTextAs`, DN's `cmLoadText`/`cmSaveTextAs`, `OpenFile` and
  `SaveFileAs`; also Editor > File): the name from navml's `FileDialog` via `EditWindow._ask_file` -- *Open a File*,
  *~N~ame*, an *~O~pen* button (`fdOpenButton`), history `edit_open`; *Save File As*, *~S~ave File As*, OK,
  `edit_save` -- listing the active panel's directory. Open offers a changed text a save first (Cancel keeps all),
  records the file being left, loads the new one into the same window and brings its record back; a file that will
  not open is said and the text stays (DN closed the window). Save as asks `_check_for_over`'s question without
  *Append* (a departure: appending the whole text elsewhere and then editing that file under its name lost what was on
  disk at the next F2), puts a read-only file's mode back, and the window takes the new name; `FileSaved` re-reads
  panels. `_check_for_over` is shared with ^K W, which keeps *Append*.
- **Save all, Ctrl+F2** (`SaveAll`, DN's `cmSaveAll`, a `GlobalMessage` of `cmSaveText`; also Editor > File): every
  editor window, this one first and the rest front to back, saved as F2 saves, each failure said and the rest going
  on. A departure: only changed texts are written, where DN's `SaveFile` rewrote every one. The application's Ctrl+F2
  (Hide right) is disabled with no console showing a file manager, so the key reaches the editor window.
- **SmartPad, Alt+Q** (`OpenSmartpad`, DN's `cmOpenSmartpad`, ≡ > *SmartPad (TM)*; `navigator/smartpad.py`): one
  editor window on `settings.smartpad_path()` -- `SmartPad.DN` in `$SMARTPAD`, else beside the database (DN's fell
  back to its own directory). Each opening stamps the end, `InsertInfo`'s `──────< date time >──…` (`FileEditor.stamp`)
  with the cursor on an empty line under it; a stamp alone is not a change (a text already changed stays so). A second
  Alt+Q brings the one pad up and stamps again. The window is the desktop less two cells all round (not zoomed),
  titled *SmartPad(TM) - path*; `EditWindow(smartpad=True)` keeps no edit history, saves unasked on closing (Esc,
  Close all, Alt+X) and sends no `FileSaved`. Alt+Q is on `Navigator.keys`; the Shell answers it, putting the console
  away first.
- **Find and Replace** (`StartSearch` F7 / ^Q F, `Replace` Ctrl+F7 / ^Q A, `ContSearch` Shift+F7, `ReverseSearch`
  Alt+F7 / ^Q R; DN's `StartSearch` in `EDITOR.PAS` and `TFileEditor.Search` in `MICROED.PAS`). The model is
  `navigator/editor/search.py` (`SearchData`, the record `SEARCH` kept between searches as DN's typed constant was --
  look it up as `search.SEARCH` at call time; `find`/`find_in_line`; `BREAK_CHARS` now lives there). Line by line:
  forward from a place, backward a match ending at or before it; *Case sensitive* off ignores case, *Whole words only*
  wants `BREAK_CHARS` or a line's edge round it, *Selected text* searches only the block's part of each line
  (`FileEditor._search_bounds`, stream or column). `FindDialog` (`editor/find_dialog`) is both `dlgEditorFind` and
  `dlgEditorReplace` (property `replace`, every rectangle the resource's), opening on the word at the cursor
  (`StartSearch`'s guess), history `find_text` for both lines; *Change all* answers `"all"`. *Entire scope* starts at
  the text's start (its end, backward); nothing found says *Search string not found* and puts the cursor back. A
  match puts the cursor after it (before it, backward) and is lit while the cursor and text stay
  (`show_found`/`found_on_display`); a reversed search with it lit starts from its far side (`SearchOnDisplay`).
  Replacing asks `ReplaceQuery` (`dlQueryReplace`, Yes/All/No/Cancel; *All* stops the asking) while *Prompt on
  replace* is ticked, each replacement its own undo step (`udReplace`); only *Change all* goes on past the first;
  replacements made unasked end with *N replaces made*. Shift+F7 repeats the last search, replacement included, from
  the cursor. Departure: the query box is centred, where DN put it clear of the line found.
- **Paragraph formatting, Alt+J/R/L/C** (`FJustify`/`FRight`/`FLeft`/`FCenter`, DN's `cmF*` and `FormatBlock`; also
  ^B^J/R/L/C and Editor > Paragraph): `navigator/editor/paragraph.py`. The stream block's whole lines (one ending at a
  line's start leaves that line out) are one paragraph -- blank lines are no break, runs of blanks one -- laid out
  between `FileEditor.margins` (`LeftSide`, `RightSide`, `InSide`): a line takes a word while `length + word + blank`
  stays under its room; right ends against the right margin, center sits midway, justify widens every line but the
  last gap by gap from the left and indents the first. One undo step; the block then covers the new lines, the cursor
  at its start. Disabled for a column block. *Margins...* (`SetMargins`, `MarginsDialog`, `dlgEditorFormat` 39 by 11)
  changes this editor's margins only, seeded from the Editor setup, a number that does not read kept, then
  `fix_margins` (`SetFormat`'s corrections). DN's line-only `cmL*` had no key in the English resource and are not here.
- **Auto wrap and Justify on wrap** (`FileEditor.autowrap`/`justify_on_wrap`, DN's `AutoWrap`/`AutoJustify`, seeded from
  the Editor setup, switched per editor by Editor > Options -- `SwitchSave` is DN's own name, `cmSwitchSave`, for
  *Auto wrap*, `SwitchWrap` (`cmSwitchWrap`) for *Justify on wrap* -- and ticked through `checks`): a character typed
  at or past the right margin (`type_text`, `InputChar`'s `LastX >= RightSide`) wraps the line, its own undo step
  after the typing's (`_wrap`, `paragraph.wrap_line`, DN's `SplitString`). Trailing blanks go; a line still past the
  margin is cut after its last blank or `,:.?!+;` at or before it -- so a word ending on the margin with no break
  there moves too, as in DN -- the rest put under the left margin; *Justify on wrap* widens what stays to the margin.
  The cursor follows its text. Departure: a line with no break before the margin is cut at the margin, where DN's
  search stopped at the first character. Pastes do not wrap, as DN's `InputChar` alone did.
- **AutoBrackets** (`FileEditor.auto_brackets`, DN's `AutoBrackets`, seeded from the Editor setup, switched per editor
  by Editor > Options > *AutoBrackets* -- `SwitchBrackets`, `cmSwitchBrackets` -- and ticked): `(`, `{` or `[` typed
  at a line's end or before a blank goes in with its partner, the cursor between (`_bracket_pair`, `InputChar`'s
  `LastX >= WL or WorkString[LastX+1] = ' '`); before anything else -- its own closing bracket included -- and in
  overwrite, the character alone. One undo step with the typing.
- **Autoindent and Backspace indents** are DN's `MakeEnter` and `MakeBack`, per editor (`auto_indent`/`back_indent`,
  seeded from the setup's *Auto indent* and *Backspace unindents*, switched by Editor > Options *Autoindent*
  (`SwitchIndent`, `cmSwitchIndent`) and *Backspace indents* (`SwitchBack`, `cmSwitchBack`), ticked). **Enter**
  (`on_new_line`): in overwrite only to the next line's start (a line added past the last). Inserting, the part kept
  loses its trailing blanks and the part moved the line's last ones; with Autoindent the moved part's leading blanks
  give way to the indent of the part kept -- the whole line's if that part is blank -- the cursor at it, and a new line
  with nothing after the indent is left empty with the cursor waiting there; without, it moves as it is, the cursor at
  column 0. Edits go right to left so a block's ends follow. **Backspace** (`_unindent`): only on a line's first
  character (blanks before, none under) or anywhere on an all-blank line, never on the first line; back to the indent
  of the nearest line above with text and a narrower indent, the blanks before the cursor becoming that many spaces;
  no such line, a plain Backspace. Departure from DN, which expanded tabs: a leading tab is indentation by its width.
- **Line drawing, F4 / ^Q^M** (`SwitchDrawMode`, DN's `cmSwitchDrawMode` and `DrawLine`; also Editor > Misc > *Line
  Drawing*; `navigator/editor/linedraw.py`): F4 cycles `FileEditor.draw_mode` off, single, double; the info line shows
  `{┼}`/`{╬}` where the block's kind was, and the pen is lifted. While on, the arrows (and ^E ^D ^X ^S) are
  `DrawLine`'s before any key table -- `FileEditor._run_key` looks at the raw key, since a command does not carry the
  modifier that decides: Shift draws, Ctrl erases, neither only moves a cell. Drawing picks the cell's character from
  a 15-entry mask table (up 1, right 2, down 4, left 8) of the arms its neighbours reach it with, the way the pen came
  and the way it goes, in DN's four tables (`Line00/01/10/11`, so a line crossing one of the other weight gets the
  mixed junction); going straight back the way it came draws nothing. Erasing blanks the cell and takes the arm into it
  off any neighbouring junction (three or four arms; a plain line beside is left). Down off the last line adds one.
  Each stroke is one undo step. ^Q^M is bound as `ctrl+q enter` too, Ctrl+M arriving as Enter.
- **Duplicate line, F6** (`DuplicateLine`, DN's `cmDuplicateLine`, also Editor > Misc): a copy of the cursor's line
  under it, put after the line's own text so the line keeps its ending and the copy takes the file's usual break; the
  cursor stays; one undo step.
- **Word and line case** (`UpWord`/`LowWord`/`CapWord`, DN's `cmUpWord`.., and `UpString`/`LowString`/`CapString`;
  Editor > Misc > Uppercase/Lowercase/Capitalize > *Word*/*Line*): Ctrl+[ / Ctrl+] / Ctrl+\ (and Alt+/ for Capitalize)
  change the word the cursor is in or just after -- back to a `BREAK_CHARS` character and on to the next -- and with
  Shift the whole line (`_recase_here`). A blank line is left alone; the line loses its trailing blanks either way; the
  cursor stays; one undo step. `capitalize` is `CapCaseStr`, shared with ^K \. Ctrl+[ is Esc's byte and the Ctrl+Shift
  forms need the kitty protocol; Ctrl+], Ctrl+\ and Alt+/ arrive from any terminal, and the menu works everywhere.
- **Optimal fill** (`FileEditor.optimal_fill`, DN's `OptimalFill`, seeded from the setup, switched by Editor > Options >
  *Optimal fill* -- `SwitchFill`, `cmSwitchFill` -- and ticked): what is written goes through `columns.optimal_fill`,
  DN's `CompressString` -- chunk by chunk of the tab size from the line's start, a chunk ending in two blanks or more
  has that run made one tab; a lone blank and a last partial chunk stay. Applied in `FileEditor.snapshot` (every save
  path) and `block_file_text` (^K W); the text in the editor keeps its blanks. With it on, saving rewrites blanks in
  lines nobody touched -- the option's point, and the one exception to byte-for-byte, off by default. Departure: chunks
  are measured in columns, keeping a tab already there, where DN met only spaces (tabs expanded on loading).
- **Current line and column highlight** (`FileEditor.highlight_line`/`highlight_column`, DN's `HiliteLine`/
  `HiliteColumn`, seeded from the setup, switched by Editor > Options -- `SwitchHiLine`/`SwitchHiColumn`,
  `cmSwitchHiLine`/`cmSwitchHiColumn` -- and ticked): `render` paints the cursor's row in `FileEditor::current_line`
  ([182]), a block or match on it in `::current_line_selected` ([183]), and the cursor's column on every row of the
  window, text or not, in `::current_column` ([185]), laid last as DN's `Draw` set `CC[7]` over all else.
- **Syntax highlight** (`FileEditor.syntax_highlight`, DN's `HiLite`; `editor.syntax_highlight` in `navigator.ini`,
  on by default, no checkbox since `dlgEditorDefaults` had none; switched by Editor > Options > *Syntax highlight*,
  `SwitchHighLight`/`cmSwitchHighLight`, ticked; kept in `EditRecord.highlight`). **Pygments lexes**, in token mode
  (`navigator/highlight.py`), where DN had `DoHighlite` and `DN.HGL` -- a departure: multi-line comments and strings
  come out whole. **`highlight.ini`** beside `navigator.ini` is `DN.HGL` (seeded through `associations.TEMPLATES`,
  Options > *Highlight file edit...*, `EditHGL`/`cmEditHGL`): mask sections with `lexer = <Pygments alias>`, `none`,
  or `auto` (Pygments' guess by name and first line, even under `[*] lexer = none`), first match wins. **Its template
  lists every language Pygments knows** -- `navigator/assets/highlight.ini`, written by `tools/highlight_ini.py`
  (`--check`; rerun after upgrading Pygments): Navigator's own head (`*.nml` -> `nml`, `*.nss` -> `nss`, `*.log` none), then a pattern
  two lexers can claim (case folded: `*.c`/`*.C`) in an `auto` section naming the candidates, then one section per
  lexer, and a hand-kept `[#!]` of ~35 interpreters. `test_the_template_lexes_every_pattern_as_pygments_would` holds
  it to Pygments' own choice for each pattern. `default_rules()` parses it lazily (~70 ms). **`navigator/lexers.py` is Navigator's own two lexers**:
  `NssLexer` (a `RegexLexer`; colour names and `Style` fields read from `navkit.stylesheet`, so they cannot drift) and
  `NmlLexer` (line by line, since indentation decides what a line is: heads, directives, `id`, `on_*` handlers,
  properties whose values go to Pygments' `PythonLexer` and run on while a bracket is open, `keys:` lines, and
  `style:` lines whose values go to `NssLexer.value_tokens`; `#` a comment only before a blank, an end or `:`). They
  keep no state on the instance -- `_lexer_named` shares one across threads -- and live in `navigator` because it is
  the layer that depends on Pygments. `_lexer_named` finds them by alias before asking Pygments; installed, the
  `pygments.lexers` entry points in `pyproject.toml` make them Pygments' too. A test lexes every `.nml`/`.nss` in the
  tree and refuses an `Error` token or a gap; `[#!]` maps interpreters (`env` and its options looked through, a
  trailing version optional); `[*] lexer = auto` falls to Pygments' guess by name, `none` stops there. Missing or
  broken, the template's rules (`DEFAULT_RULES`); re-read when its mtime changes, and saving it (`FileSaved`) makes
  every editor and viewer `rehighlight()`. **A token is painted as `FileEditor::token` with its Pygments type's pieces
  as classes** (`String.Double` -> `.literal.string.double`), and `:current_line` on the highlighted line;
  `navigator.nss` maps comments [164] ([184] on the current line), operators/punctuation [189], strings [190] and
  numbers [191], the last three foreground only as DN's `Draw` did. Keywords (and `Operator.Word`: `and`, `not`,
  `in`) are `$keyword`, a `DERIVED` alias of Normal text [76] -- plain, as DN left them -- which `default` gives
  yellow. A block or found
  match paints over tokens, the current column over everything. **Lexing runs on a thread** (`_LEXER`, from `render`
  as `DirectoryTree` asks for counts): the whole text from line 0 to `LEX_AHEAD` lines past the screen, the lexer
  chosen there each time from the name and first line. Edits shift the spans (`highlight.shift_spans`, typing inside a
  span widens it) and drop `_lexed` to the edited line; an answer keeps only the lines before any edit made while it
  ran, and `render` asks again. Over `LEX_LIMIT` (2 M characters; Pygments lexes about 0.5 M a second) a text stays plain. Use `lex_lines` and the
  `get_tokens_unprocessed` it walks -- never `get_tokens`, which strips and expands and so moves indices.
- **File type** (Editor > Options > *File type*, View > *File type* in the viewer; `SetFileType(file_type)`, a
  departure -- DN chose a `DN.HGL` section by mask alone): *Automatic* (`""`, `highlight.ini`'s choice), a submenu
  each for *Programming*, *Scripting* and *Markup languages* and *Miscellaneous*, and *None* (`none`). The languages
  are `highlight.FILE_TYPES` (group name, then caption and Pygments/own lexer name), short enough that each box fits
  24 rows; the menus are empty `SubMenu`s in the markup filled by `file_type_menu.fill_file_types` (hotkeys picked
  by `_marked`, the first character not yet taken; group captions bound live through `tr`). `FileEditor.file_type`/
  `FileViewer.file_type` go to `lexer_for(..., file_type=)`, which then decides alone, and are part of what the tokens
  were lexed for. Choosing switches highlighting on (*None* leaves it), is ticked through the window's `checks`, and
  is written to the record at once (`remember_history`); kept as `EditRecord.file_type`/`ViewRecord.file_type`. F3's
  *Open* into the same editor resets it before the new file's record is read. **Ctrl+Shift+H** (`ChooseFileType`, on `EditWindow.keys` and
  `FileWindow.keys`, so in `keybindings.ini`) opens the same menu as a `PopupMenu` centred on the window
  (`file_type_menu.choose_file_type`), and both *File type* submenus show it through `key_command`; it needs the kitty keyboard protocol, Ctrl+H being Backspace's byte.
- **Go to line, Alt+G** (`GotoLineNumber`, DN's `GotoLine`, also Editor > Search > *Go to line number...* and the
  info line): `GotoLineDialog` (`dlgGotoLine`'s *Goto Line*, a row taller like the viewer's *Goto Address*, history
  `goto_line`) opens with the number last typed, as `GotoLine`'s `const S` kept it; a number above 0 puts the cursor
  on that line at the same column (`FileEditor.go_to_line`, `ScrollTo(Delta.X, I-1)`), past the end on the last;
  anything else does nothing. DN shared its history with *Goto Address* (`hsdbSearch`); here each has its own.
- **A hidden block** (`block_hidden`, DN's `not BlockVisible`; ^K H / Alt+H toggle it): still marked (`marked`) and
  still following edits, but not painted and not acted on -- `has_block`, which the block commands' `enables` read,
  is DN's `BlockVisible and ValidBlock`. Marking anew shows it (`_set_block`/`_set_ordered`, `read_block`, `_unmark`).
- **Markers, ^K1-9 / ^Q1-9** (`PlaceMarker(n)`/`GotoMarker(n)`, DN's `cmPlaceMarker`/`cmGotoMarker` over `MarkPos`):
  `FileEditor.markers`, nine fixed `(line, col)` -- not moved by edits, as DN's were not. Going to one centres it
  (`Pos := Delta - Size div 2`) and, being a movement, unmarks under *Persistent blocks* off; an unset one does
  nothing. Kept in the edit history as `EditRecord.marks` (`fMarks`), `line:col` nine times comma-separated, and
  brought back whatever *Store editor position* says. The digit is bound alone, as the table has it.
- **^Q D/T** insert the date/time (`fileattr.DATE_FORMAT`/`TIME_FORMAT`, DN's D-M-Y and H:M:S, as the attributes
  dialog writes them; inserted even in overwrite; `_now` is the test hook). Column blocks take all the ^K commands.
  A pending chord shows as `^K` at the info line's end (a departure).
- **Column blocks** under `vertical_blocks` (Editor setup's *Vertical blocks*, seeded per editor and kept in the edit
  history; `SwitchBlock`, DN's `cmSwitchBlock`, switches it -- ^B^V and Editor > Options > *Vertical blocks*,
  ticked through `FileEditor.checks`. DN's block was two points either way, so the switch keeps it and reads it the
  other way: a stream block becomes the rectangle between its ends, a rectangle the stream from top-left to
  bottom-right; one enclosing nothing goes).
  `FileEditor.column_block` is two corner *cells* `(line, col)` -- columns, not indices, since a rectangle runs past
  short lines and across tabs -- and `rectangle` is `(top, left, bottom, right)`, right exclusive. Only one of
  `block`/`column_block` is ever set; marking code speaks of "ends" (`_here`, `_block_ends`, `_set_block`) so keys,
  Shift+click, drags and double-clicks serve both. A character belongs to the column it starts in
  (`columns.span`), so a tab straddling the left edge stays out. A copy hands out each line's piece without padding
  blanks, and remembers the padded pieces in `_COLUMN_CLIP` (newest only): pasting exactly that text back inserts a
  rectangle (`_insert_rectangle`: short lines padded to the column, lines added past the end, the cursor left at the
  top-left). A column block keeps its columns through edits and moves only by whole lines.
- **The mouse marks too.** A left press puts the cursor there and unmarks; a drag (captured, and only once the
  pointer leaves the pressed cell -- terminals report motion inside it, `_press_cell`) marks from the press,
  scrolling a line at a time past the top or bottom row; Shift+click extends the block as Shift+movement does; a
  double-click marks the word between `BREAK_CHARS`. A block marked by the mouse becomes the primary selection on
  release (`copy_to_clipboard(primary=True)`), and a middle click pastes the primary selection -- what the console and
  the input lines do. Ctrl+Ins still copies the block to the clipboard. Checked on a pty with SGR mouse bytes and
  `xclip -o`, not only with posted events.
- **Closing asks** through `Window.must_ask`/`ask_to_close` (`Valid(cmClose)`), which `request_close`, Close all and
  Alt+X all go through; `Dialog.buttons` has `yes-no-cancel`.
- **Shift+F4, *Edit new file*** (`cmXEditFile`, `EditNamed`, also File > Edit > Edit new file): `EditFileDialog` asks for a
  name (history `editfile`), relative to the active panel, `~` expanded; `Manager.edit_named` opens it with
  `open_editor(..., new=True)`, so a name that does not exist is an empty text saving creates. A directory or a missing
  parent directory is refused up front. With *Internal editor* off it goes to `$EDITOR`. DN's own dialog was not to
  hand; this one is shaped as F7's.
- **File Edit History (Alt+PgUp)**: DN's `TEditRecord`, the `EditRecord` model. It holds the window rectangle, cursor
  (`line`, `col`), scroll (`top`, `left`), `overwrite` and `vertical_blocks`, and is stored and restored as the
  viewer's is (see `navigator-viewer`); the rectangle, cursor and scroll only under *Store editor position*. **Open editors through `navigator.file_history.open_editor`**, awaited from a spawned task. DN's
  block, auto-indent and margins get columns when the editor has them: add the `field` lines to
  `edit_record.nml`, rebuild, and the table migrates itself.
- **While an editor window is active the bar has an *Editor* menu after *File***: DN's `dlgEditorMenu`, its seven menus
  nested as submenus, greyed where the feature is still to come.

## Read when

| Reference | Read when |
|---|---|
| `reference/editor.md` | the full design and the phases left |
