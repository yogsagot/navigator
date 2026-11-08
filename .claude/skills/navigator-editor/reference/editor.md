## The editor

F4 is DOS Navigator's internal editor: `TEditWindow` holding `TXFileEditor` (`MICROED.PAS`, `EDITOR.PAS`).
Everything DN's editor had is written, and the departures asked for beside it; the few things still not there are
listed at the end (*What is still not DN's, or not there*). This section records the design and what each decision
cost. It has the viewer's three layers:

- **`navigator/lib/editor/`**, the model. It is a package rather than one module, and it imports no widget.
- **`FileEditor`**, a Python-only widget that paints the text and answers the keys.
- **`EditWindow`**, markup plus handlers: the frame, the scroll bars, the info line, saving and closing.

**A file round-trips byte for byte, and that is the one departure underneath everything.** DN rewrote what it
edited:

- `ReadBlock` expanded tabs.
- `ModifyLine` trimmed trailing blanks from every line it touched.
- `WriteBlock` wrote one line ending for the whole file (CRLF unless `DN.HGL` forced another).
- The loader split a line at 254 characters.

Here none of that happens:

- A line keeps its own terminator (`Document.endings`), so a file mixing CRLF and LF is written back mixed. A typed
  line break takes the ending the file uses most.
- A tab stays a tab and is drawn to the next eighth column.
- There is no length limit.
- A byte that is not UTF-8 survives as a lone surrogate (`surrogateescape`) and is drawn as its CP437 glyph, as the
  viewer draws it.

`encode(from_bytes(b)) == b` for any bytes, and the tests try it on random ones.

**Text crossing the model's edge is a plain string whose line breaks are the terminators themselves.** What a delete
returns is exactly what an insert of it restores, endings included, which is all undo needs. Every edit is one of the
two primitives, `Document.insert` and `Document.delete`.

**The cursor lives in columns, not string indices**, as in DN, where the two were the same because every tab had been
expanded.

- A column may lie past the line's end -- Turbo Vision's editor allowed it, and typing there pads with blanks -- but
  no movement puts it there any more (a departure, asked for): `FileEditor._move_to` holds the column to the line's
  end, Right at the end goes to the next line's start and Left at a line's start to the previous one's end, and
  Up/Down/PgUp/PgDn aim for the column a run of them began on (`_goal`). Line drawing and the extending of a column block
  (Shift+movement, Shift+click, a drag: `_extending`) keep the old freedom (`_free`), both needing the cells past
  the end -- a plain click or movement clamps under *Vertical blocks* too; edits such as Autoindent's empty indented line still leave
  the cursor where the indent is.
- A column inside a tab or a wide character belongs to that character, and Left/Right step over it whole.
- `columns.py` holds the mapping. It follows the rules of `viewer.decode_cells`, over `str` instead of `bytes`.

**Undo is groups of primitive changes, and typing merges.**

- A run of characters, of Backspaces or of Dels is one group, as DN's `udInsChar` and `udDelChar` merged. A movement
  seals the run.
- *Modified* is a save point, the group on top when last saved, rather than DN's `UndoTimes` count. Undoing back to
  the save point clears it, and undoing past it and then editing makes the saved state unreachable.
- **Redo is a departure** (DN had none; Borland's IDE had it on these keys): Alt+Shift+BkSp and Ctrl+Shift+Z, both
  needing the kitty protocol, redo what undo took back, group by group, until the next change empties
  `EditBuffer.redo_stack`. The save point holds while redo can still reach it.

**Every key is a command, named after DN's `cm*`**, bound in `FileEditor.keys` from `DN.DNR`'s `EDITOR COMMANDS`
(`MoveLeft` for `cmMoveLeft`, `DeleteBack` for `cmDelBackChar`).

- The table is the editor's, not the window's, because DN's was: `LoadCommands` filled `TFileEditor`'s. The window's
  `keys:` holds what `StatusDef hcEditor` captions, and Esc/Alt+F3.
- The movements carry `extend`, which is what Shift makes of them. DN read the shift state off the BIOS
  (`BMarking`); a key table says it with a second binding.
- Only a printable character is left to `on_key`.
- Home is the line's first column (DN reached it through the horizontal scroll bar's `kbHome`). End is after the
  last non-blank (`cmEnd`). Ctrl+Home and Ctrl+End are the screen's top and bottom rows, and Ctrl+PgUp and Ctrl+PgDn
  are the text's first and last lines.

**An editor holding the keyboard takes Enter, Home, End, Tab and pastes from the command line.** The application's
key table is asked before the tree, and the command line binds those keys whenever it has text. `Widget.edits_text`
is navkit's flag for "this takes typed text as a whole"; `Shell.enables` and `Navigator.on_paste` step aside for it.
DN never had the question: its command line lived in the panel window.

**Closing asks, and so does everything that closes.**

- `Window.must_ask()` and `ask_to_close()` are Turbo Vision's `Valid(cmClose)`, split in two. The synchronous half
  keeps closing a window with nothing to lose one call; the asynchronous half may show a dialog.
- `request_close()` is what the close icon, Esc, Ctrl+F4 and the window manager's *Close* call. `close()` stays the
  unconditional one.
- Window > Close all and Alt+X ask each window that must, front to back, and a Cancel stops the whole command, as it
  did in DN.
- The question is `dlQueryModified`, *File %s was modified. Save?*. `Dialog.buttons` gained `yes-no-cancel`
  (`mfYesNoCancel`), whose *No* answers False where Cancel answers None.

**Saving replaces the file in one rename.**

- The new text is written beside the old, given its mode and owner, flushed and renamed over it. DN wrote in place,
  which cost nothing on a floppy and costs a file when a disk fills half way through.
- Two cases cannot be renamed over and are written in place: a file with other hard links, and a directory Navigator
  may not create in.
- A symlink is followed, so the link stays a link.
- *Create backup files* (`ebfCBF`) keeps the old file as `NAME.bak` on F2 (`SaveFile`) alone: Save as and ^K W
  went through `CheckForOver`, whose `CreateBackup` ran only when the file did not exist. The old file is hard-linked
  under the backup's name just before the new one is renamed over it, so a stopped write leaves the old backup, and
  a write in place copies it. `.bak` goes after the name, where DN's `.BAK` replaced the extension (8.3 had no room),
  so `foo.c` and `foo.h` keep a backup each. A backup that cannot be made does not stop the save, as `ClrIO` let it.
- *Lock edited files* (`ebfLck`) is DN's `Locker`, the file kept open in DOS's compatibility mode so `SHARE` kept
  other programs from writing it. POSIX has only advisory locks, so it is an exclusive `flock` (`editor/lock.py`):
  it keeps off what asks -- another Navigator, `flock(1)` -- and not `vi`. Within the program a lock is one
  descriptor, counted, so two windows on one file share it as DN's own editors did. It is taken on open, Open and
  Save as, re-taken after every save (the rename leaves the old inode holding it), and let go on close. Every write
  the editor makes (F2, Save as, ^K W) is refused on a file another program holds (`refuse_if_locked`, DN's
  `CantWrite`), whatever this editor's own setting says, as `SHARE` refused DN.
- A save emits `FileSaved`, and `Shell` re-reads every panel showing that directory (`FileChanged` → `cmRereadDir`).

**The caret is DN's**: `NormalCursor`, an underline, while inserting, and `BlockCursor` while overwriting (Ins). It
comes from the sheet's `caret`, keyed on the `:overwrite` state.

**`TInfoLine`** is drawn over the bottom frame at column 2, and only while the window is active:

- `☼` replaces the first `═` while the text is modified.
- Then `line:column`, both counted from 1, and `[nnn]`, the code of the character under the cursor (0 past the
  end). The code is a code point here, where DN's was a byte, and it grows past three digits when it needs to; a
  byte that was not UTF-8 gives the byte.
- Then `(↔)` for stream blocks, `(↕)` for column blocks.

The horizontal scroll bar runs from column 24 to the corner, as `ChangeBounds` sized it, over DN's 0 to 255 until
the cursor goes further. The vertical one's value is the cursor's line, as `VScroll` was `Delta.Y`.

**What is still not DN's, or not there** -- the editor backlog's open items (numbered as
`/home/juris/.claude/plans/editor-backlog.md`), each with where DN had it; an item's line goes when it is done:

10. (Not DN's) two views of one document.
11. (Not DN's) the find bar's regex across lines.

Everything else -- blocks with ^K R/W, Find/Replace and the find bar, files and encodings, SmartPad, the character
table, the menu, autoindent and its kin, paragraph format, line drawing, highlighting (`highlight.ini` for
`DN.HGL`), its macros (`macros.ini`, Ctrl+J 0), editor defaults, the edit history, backups, locking and printing --
is written.

Autoindent is DN's `MakeEnter`: the part kept loses its trailing blanks, the part moved its leading ones, and it is
indented as the part kept -- as the whole line when that part is blank -- with the cursor at the indent and no blanks
left behind when nothing follows. Enter in overwrite only moves to the next line.

**Tab is DN's `DoTab`** (`MICROED.PAS:2441`), the line *directly* above read: past the rest of the word over the
cursor (at least one column -- DN's `repeat` moves before it looks, so from under a blank it passes the next word
too), on over the blanks after it, then one more, onto the next word's start, or one past the end where the word ran
to it. On the first line, or past the end of the one above, `MakeTab`'s next stop. Blanks, as DN -- unless
*Tab characters* is on (below); in overwrite it moves there instead, kept within the line's text as overwrite keeps the cursor.
`columns.smart_tab(above, column, tab)` is the rule, pure; `FileEditor._tab_stop` applies it. A departure: the line
above is read by display column (a tab there as the blanks it shows, a wide character as two), where DN had every tab
expanded on reading. DN had no switch for it, nor has Navigator.

**Tab characters** (`insert_tabs`; a departure, opt-in: DN's Tab wrote blanks): `[editor] insert_tabs`, the Editor
defaults page's *Tab key inserts tabs* (the cluster's 15th box, the page a row taller), `highlight.ini`'s
`insert_tabs` per mask (the template's example `[Makefile;GNUmakefile;*.mk]`, commented out), Editor > Options >
*Tab characters* (`SwitchTabs`, ticked), the strip's `Tab`/`↹` -- there only while on (an `OptionItem` whose label
is `""` is left out), since a wider strip squeezes the horizontal scroll bar under 4 columns on an 80-column CRLF
file -- and the edit history's nullable `insert_tabs`.
While on, the blanks typed are `columns.fill(start, stop, tab)` -- a tab to each stop on the way, then spaces: Tab
(the column still `_tab_stop`'s, so Smart tab lines up by width; past the line's end filled from where the text
ends, no `_pad` spaces before the tabs), Backspace's unindent, the virtual columns Enter carries off an all-blank
line, and a stream block's Tab (one `\t` a line). A column block's Tab keeps blanks (a tab in a rectangle widens by
where it lands), ^K I keeps DN's one blank, and paragraph format, Auto wrap and Optimal fill are untouched.

**Line numbers** (`line_numbers`; a departure, off by default: DN numbered no lines, its info line said the cursor's):
`LineGutter` (in `file_editor.py`, beside `InfoLine`) is a widget of its own left of the editor, and the window
binds the editor's `x`/`width` around it -- so nothing inside `FileEditor` (mouse, ruler, current column, scrolling,
bidi rows) learns of an offset. Its width is `gutter_width(line_count)`: the digits, two at least so the tenth line
moves nothing, and a blank; 0 while off. Each row's number is right-aligned, the cursor's in `LineGutter::current`;
a left press on one takes the cursor to that line's start. It keeps the default `mirrors`, `FileEditor` does not:
on a right-to-left screen it lands right of the text, where right-aligned Hebrew/Arabic lines start, digits in order.
Its property is `target`, not `editor`: in the window's markup that name is the editor's id, and `editor: editor`
binds the property to itself (`CycleError`). Switched like *Tab characters*: `[editor] line_numbers`, the Editor
defaults page's 16th box (no hot key: the page has none of its letters left), `highlight.ini`'s `line_numbers`,
Editor > Options > *Line numbers* (`SwitchLineNumbers`), the edit history's nullable field -- and not on the option
strip, whose width is the horizontal scroll bar's room. Colours: `$gutter`/`$gutter-current`, `DERIVED` aliases of
[70]/[71]. Soft wrapped, it numbers a line's first row alone (`FileEditor.visible_rows`).

**Soft wrap** (`soft_wrap`; a departure, off by default: DN's *Auto wrap* put real breaks in the text). The rules,
decided first because they touch the cursor model:

1. The text never changes: `line`/`col`, every `Pos`, undo, blocks, markers, the history's cursor and the info line
   stay logical; only painting and vertical movement know rows.
2. `navigator/lib/editor/softwrap.py` (pure): `rows(cells, width)` cuts a line's `columns.cells` at the last blank
   that fits (the blank on the row it ends), a longer word where the row ends, never inside a wide character; an
   empty line is one row, and a full last row gets an empty one more for the caret at the end. `locate` and
   `column_at` map a column to `(row, x)` and back.
3. No sideways scrolling: `left` held at 0, `overflows_across` False, the hbar hidden.
4. The view's top is `(top, top_row)`; `_step_rows`, `_rows_from` and `_row_offset` walk rows, bounded by the
   screen. `_follow_rows` keeps the cursor's row on screen; `_scroll_view` serves the wheel, both drags,
   Ctrl+Up/Down and PgUp/PgDn. Whatever else sets `top` lands a line at row 0 (`top_row` clamped).
5. Up/Down (`_move_rows`) go by row keeping the screen column in `_goal`; PgUp/PgDn a screen of rows; screen top and
   bottom the first and last row shown. Home/End stay the line's (DN's `cmHome`/`cmEnd`).
6. Column blocks and soft wrap exclude each other ("Not with soft wrap" on *Vertical blocks*, "Not with column
   blocks" on *Soft wrap*); `settle_modes` turns wrap off when both arrive (setup, mask, history).
7. A right-to-left line is cut on its logical cells, then each row ordered on its own (`_row_layout`: UBA orders
   after breaking) and right-aligned; `_locate`/`_column_at` map through that order.
8. `render` paints `_painted_rows()`: each `(line, cells, order, shift, base, last)`, *base* the line's column the
   row starts at, what lies past the text (the break in a block, the line-end mark, the RTL past-end fill) on the
   *last* row alone. Unwrapped it is one row a line at base 0, exactly as before. Tokens, matches and the block
   are told by index or by column less *base*, so the highlight cache is untouched.
9. The caret, the ruler and *Current column* read `cursor_cell()`; the mouse and the context menu `cell_at(x, y)`;
   the gutter `visible_rows()`. The vertical bar stays in lines; `overflows` counts rows, no further than the screen.

Switched by `[editor] soft_wrap` (no box: the Editor defaults page is full), Editor > Options > *Soft wrap*
(`SwitchSoftWrap`), `highlight.ini`'s `soft_wrap` and the history's nullable field. Rows are cached by
`(text, width, tab)` in `_wrap_cache`.

