## The file viewer

F3 is DOS Navigator 1.51's internal viewer, `FVIEWER.PAS`, in three places:

- `navigator/viewer.py` is the model: `Seek`, `MakeLines`, `CountUp`, `CountDown` and `SearchFileStr`, with no
  widget in it.
- `navigator/widgets/viewer/file_viewer/` is `TFileViewer`, Python-only because everything it shows is painted.
- `navigator/widgets/viewer/file_window/` is `TFileWindow`. It is markup: the viewer inside the frame, `TViewScroll` as
  navml's `ScrollBar` on the right frame column, and `TViewInfo` as a `StaticText` over the bottom frame row.

It is the application's, not the library's, because `TFileViewer` was DN's and never Turbo Vision's.

- **Positions are byte offsets**, as in DN. The view's `top` is the offset of its first row, the scroll bar's value
  is that offset, and nothing ever counts lines. So a gigabyte opens, and reaches its end with Ctrl+PgDn, at once.
  Going up is DN's `ScrollUp`: back past the terminator, back to the previous one, then forward row by row when
  wrapping.
- **The file is read with `os.pread` into a small cache of 64 KiB chunks, not mapped.** `mmap` would have handed
  `rfind` and `re` the whole file, and a log truncated while mapped then kills the process with `SIGBUS` on the
  next repaint. The size is taken once, at open, as DN took it. A read past what is left comes back short.
  - A non-regular file is refused, because a fifo would block the loop.
  - A regular file reporting size 0 (`/proc`) is read whole, up to 16 MiB.
  - The search runs on a thread through a descriptor of its own, so it never touches the cache the loop paints
    from.
- **Text is UTF-8, and an undecodable byte is its CP437 glyph.** So is a C0 control, which DN drew from the same
  font: a binary looks as it did in DN, and a UTF-8 file looks as it does in a terminal. A wide character takes two
  columns. A combining mark is dropped, because navkit paints one character per cell. Hex and dump are byte-exact,
  one CP437 cell per byte, as `DumpStr` and `XDumpStr` drew them, down to `.` for a zero byte in hex.
- **F6's three filters are DN's**: none, `{ASCII}` (below 32 and non-ASCII become `·`) and `{Printable}` (only below
  32 does; DN's `{32-255}`, renamed because UTF-8 has no one-byte code page to count to 255 in). In text mode "non-ASCII" means a whole UTF-8 character, which becomes one `·`.
- **`LINE_LIMIT` is DN's 255-byte `Len` cut made modern** (64 KiB). An unwrapped line longer than that is cut into
  pieces, so a minified megabyte on one line is never scanned whole for every row painted. Going up re-aligns to the
  pieces coming down for lines up to 1 MiB (`BACK_LIMIT`); past that, the two may disagree.
- **The row layouts are DN's arithmetic**:
  - hex is `(width-12) div 4` bytes per row, `AAAAAAAA: XX XX … │ chars`
  - dump is `((width-9) div 16)*16`, `AAAAAAAA chars`
  - the info line is `TViewInfo.Draw`: `[<=>][42% of 12,345 Bytes]{ASCII}`, `>=<` when wrapped, and in hex the
    cursor's offset and a column ruler
- **The key bar is `StatusDef hcView`.** Its captions are the commands' titles, bound in `file_window.nml`.
  - At 80 columns the plain row is 81 wide, so `F10 Menu` falls off the end, exactly as `DrawSelect` dropped it.
  - F5 *Goto* is enabled only in hex and dump, and F2 only in text: the `EnableCommands` calls in DN's `Draw`,
    written as `FileWindow.enables`.
  - Ctrl+L continues a search with no caption, through `SearchAgain`, a separate command with an empty title.
- **Search is a bytes regular expression.** Each character becomes the alternation of its case variants' UTF-8
  encodings, so *Case sensitive* off finds `Ä` for `ä`, which `re.IGNORECASE` on bytes would not. *Whole words*
  treats every byte ≥ 0x80 as a word byte. The last search is shared by every viewer, as `SearchString` was.
- **Its text is #D8D8D8 in the default theme**, between light grey and white, and the dimmest grey a sixteen-colour
  terminal rounds to white rather than back to light grey. DEFAULT.PAL's [117] is `$87`: light grey on dark grey,
  #AAAAAA on #555555, a contrast of 2.6:1. The departure lives in `tools/palconv.py`'s `DEPARTURES`, so a regeneration
  keeps it and the theme's comment says what the `.PAL` had. Every other theme is as its palette says.
- **F3 closes it again**, as Midnight Commander's viewer does. DN's `hcView` bound nothing to F3, so this is a
  departure. It is bound with no caption (`CloseViewer`, empty title) beside DN's Esc, so the status line stays
  DN's.
- **It opens zoomed**, like the file manager. DN reused the last viewer's rectangle (`LastViewerBounds`) and filled
  the desktop only the first time. That was the user's choice, and it is a departure.

**A search that outlives two timer ticks shows DOS Navigator's `TWhileView`** (`navigator/widgets/viewer/search_progress/`).
That is `NewTimer(Tmr, 2)` at 18.2 Hz, `PROGRESS_DELAY`.

- **The box:** *Search Progress* on a double frame with no close icon. Inside are `StrGrd`'s gauge (`█` done, `▒`
  to go, a `ProgressBar` thirty columns wide at 34), the percentage, and one `~S~top` button. Esc and Enter press it, as in DN. DN opened it 29
  wide and let the gauge widen it to 34, and 34 is where it starts here.
- **How the thread and the loop talk.** The thread and the loop share a `SearchJob`. The thread writes `position`
  after every 1 MiB window and reads `stopped`; the loop reads the one and sets the other. Nothing reactive crosses
  the thread, and a `call_every` tick copies the position into the box.
- **What the gauge measures:** where the search is reading, backwards or forwards, which is how DN's measured it,
  not how much work is done.
- **Stopping:** a stopped search is DN's `-2`, so nothing is said about finding nothing.

**Ctrl+Q is `SwitchView(dtView)`** (`navigator/widgets/viewer/quick_viewer/`). The viewer is the F3 window's `FileViewer`,
in the passive panel's place, and it works exactly as Ctrl+T does, because both now go through one
`Manager.switch_view`:

- **One side at a time stands in for a panel.** `replaced` is that panel and `replacement` is the tree or the quick
  view, which is DN's `LType`/`RType`. Asking for the other one swaps it in where the first stood and hands the
  keyboard back to the active panel. `tree_replaces` survives as a computed over the two.
- **It follows the active panel's cursor** (`SendLocated`, `cmLoadViewFile`). A file already showing keeps its scroll
  position. A directory, `..` or an unreadable file shows nothing, which is what DN's failed `ReadFile` left.
- **Tab moves the keyboard in and out.** While the view has it, the movement keys are the viewer's and the frame goes
  double. The scroll bar on its right edge shows only then, as `TFileViewer.SetState` showed `TViewScroll`. F3, F4
  and the rest stay the file panel's, whose status line DN kept.
- **It is coloured with CHViewer**, `CDoubleWindow`'s 13 and 14: *Quick View* [92] and [93]. It is framed and titled
  like a panel, with the file's name as its title. That title is Navigator's: DN's view sat inside the double
  window's frame and had none.

Left for later, in the order DN's status line lists them:

- hex editing, with Tab between the columns, Shift+F2 *Store* and Shift+F5 *Save as*
- Shift+F6 *XLat* tables, as an encoding chooser (*View > Encoding...*)
- the *Find* dialog's linked `He~x~` line
- view history (Alt+PgDn, and reopening at the last position)
- external viewers (`dn.vwr`)
- F3 on a directory, which counted its size (`CountLen`)
- viewing inside archives


