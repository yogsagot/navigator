## The editor

F4 is DOS Navigator's internal editor: `TEditWindow` holding `TXFileEditor` (`MICROED.PAS`, `EDITOR.PAS`). It is
built in phases, and everything DN's editor had is the target. This section records what is written and what each
decision cost. It has the viewer's three layers:

- **`navigator/editor/`**, the model. It is a package rather than one module, and it imports no widget.
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

- A column may lie past the line's end: Turbo Vision's editor allowed it, and typing there pads with blanks.
- A column inside a tab or a wide character belongs to that character, and Left/Right step over it whole.
- `columns.py` holds the mapping. It follows the rules of `viewer.decode_cells`, over `str` instead of `bytes`.

**Undo is groups of primitive changes, and typing merges.**

- A run of characters, of Backspaces or of Dels is one group, as DN's `udInsChar` and `udDelChar` merged. A movement
  seals the run.
- *Modified* is a save point, the group on top when last saved, rather than DN's `UndoTimes` count. Undoing back to
  the save point clears it, and undoing past it and then editing makes the saved state unreachable.
- There is no redo, as there was none in DN.

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

Left for later, by phase:

1. The rest of the `^Q` half of `EDITOR COMMANDS` (key chords and the `^K` block commands are written).
2. Blocks: written, ^K R/W included (their file name is asked in a one-line dialog until item 4's `FileDialog`).
3. Find, Replace, Goto line.
4. `FileDialog`, Save as, SmartPad, the ASCII table. The menu is written (*A window's own menu joins the bar
   while it is in use*); most of its entries wait on the phases here.
5. Autoindent's remaining rules, backspace unindent, autobrackets, autowrap, paragraph format, line drawing.
6. Highlighting and macros from `DN.HGL`.
7. Editor defaults, persisted, edit history, backups, file locking and printing.

Autoindent's first rule is written already: Enter indents the new line as this one is, and leaves only the cursor
at the indent, not blanks, when nothing follows. A Tab inserts blanks to the next stop, as `MakeTab` did.

