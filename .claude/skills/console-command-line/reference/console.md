## The console: the screen is owned, never read back

Ctrl+O in DOS Navigator hid the panels and showed the last program's output *as the desktop background*, with the menu
bar and key bar still painted over it. Reproducing that is the question that produced `console.py`, `process.py` and
`Surface.blit`, and the answer turned out to be about where the cells live rather than about how to fetch them.

**DN had no special capability; it had a special position.** DOS had one screen — the video RAM at `B800:0000` — and
every program shared it. The previous program's cells were still sitting there, so DN read them. Nothing about that is
portable to a terminal, where the grid lives in another process and the protocol has no request that returns it.

**Every read-back route was surveyed and rejected**, so that it is not surveyed again:

- **DECRQCRA** (`CSI Pi;Pg;Pt;Pl;Pb;Pr * y`) returns a *checksum* of a rectangle, not its text. It is xterm's, gated
  behind `allowWindowOps` — off by default — and absent from VTE, Terminal.app and most others. Recovering characters
  would mean one synchronous round trip per cell, on one terminal, with a non-default setting.
- `CSI 18 t` and `CSI 21 t` report window size and title; `CSI 6 n` reports where the cursor is, not what is under it.
  Nothing in the protocol reports content.
- `/dev/vcsa<N>` on a Linux virtual console *is* the exact analogue — four header bytes, then one character byte and one
  attribute byte per cell, the layout DN read. It works only on a real VT, never inside a terminal emulator or over ssh,
  and needs group `tty`. It survives as one branch of `seed_from_host`, which is the honest scope for it.
- `tmux capture-pane -p -e`, `screen -X hardcopy -h` and `kitty @ get-text` return real text with attributes, but each
  only inside its own host and each needs opt-in. Also
  `seed_from_host` branches.

**Midnight Commander is the control experiment.** It owns a pty for its subshell and still cannot do this, because it
pipes the child's output straight through to the real terminal and so never holds the cells either. All it can do is
flip the alternate screen and let the terminal show what it kept — which is why its Ctrl+O cannot composite a key bar
over the output. Its own manual page is candid that the feature needs "the subshell or a terminal that can save the
output".

**So the output is received rather than fetched.** A child runs on a pty this application owns, its bytes go through an
emulator into a grid, and Ctrl+O becomes an ordinary compositing question the render tree already answers:
`console.visible` and the two panels' bind to one reactive flag, the bars are simply left alone, and no layout pass
runs. The buffer is load-bearing well past one key — a command line, a Terminal window and F3/F4 all want it.

### Why pyte rather than a parser of our own

`InputParser` was written by hand because decoding *input* is a few hundred lines and there is no library shaped like
navkit's events. Decoding *output* is a different size of problem — cursor motion, scroll regions, insert/delete,
character sets, an alternate buffer — and pyte already does it, tested, in pure Python. It is the one run-time
dependency, and it brings only
`wcwidth`.

Three things made the adapter thin enough to be worth it, and are worth recording because they are what a replacement
would have to match:

- **The wide-character representation is already identical.** pyte writes the character, then
  `data=""` into the cell after it; navkit's `set_cell` writes `("", style)`. The two grids can be copied into each
  other without reconciliation.
- **`Screen.buffer` is a `StaticDefaultDict`, which does not materialise on a miss.** Reading every cell of a screen
  allocates nothing, so the conversion can be a plain loop.
- **`Screen.dirty` is a set of changed line numbers** — the same row-granular idea `render_diff`
  uses to skip untouched rows.

**The colour names are the one real seam**, and it is where the palette work above is cashed in. pyte stores `fg`/`bg`
as names (`"brown"` for 33, `"brightbrown"` for 93) or six-digit hex. The names map onto navkit's *indices*, not its
constant names, because an index is what a pinned palette resolves — so a child's `ESC [ 33 m` comes out in the DOS
Navigator brown the theme asked for. Two details are easy to get wrong and are pinned by tests:

- The first sixteen entries of pyte's 256-colour table are mapped **back** to their indices. Without that,
  `ESC [ 38;5;4 m` would arrive as an `(r, g, b)` triple and step around the pinned palette, so the same blue would
  paint two different colours depending on which escape asked for it.
- pyte 0.8.2 misspells bright magenta as `"bfightmagenta"` in `BG_AIXTERM`. The typo is carried in the table, so
  `ESC [ 105 m` keeps its colour; the correct spelling is there too, so a fixed release costs nothing.

**The style cache is keyed on appearance, not on the cell.** A `Char` carries its character, so memoising the whole of
it keys the table by `(character, appearance)` and misses on every new letter. Thousands of cells share a handful of
appearances, and that ratio is the entire point of the cache.

### The mirror, and why the conversion and the paint are split

pyte's grid is a sparse mapping and navkit's is a list of rows, so something has to convert. Doing it in `render()`
would cost a lookup per cell per frame; doing it on every feed would cost a full screen per byte. `ConsoleScreen` keeps
a real `ScreenBuffer` beside pyte's and converts only the rows pyte reports dirty, clearing the mark afterwards as pyte
documents. Painting is then one `blit`, which `_View` forwards whole so it reaches `ScreenBuffer`'s row-slice copy
rather than a Python call per cell.

**`blit` blanks a double-width character cut in half at either edge** — a stub whose owner was clipped off the left, and
a wide character whose trailing half was clipped off the right. That is the same bargain `set_cell` already makes at the
edge of the screen, and it is why the fast path can be a slice with two fixups rather than a loop with a state machine.

### What owning the pty costs

A child only ever talks to what the emulator implements, and pyte does not implement `?1049` — a program that switches
to its own alternate screen draws over the same buffer. For the line-oriented output a file manager runs, that is
everything; for a full-screen program it is wrong, and `run_on_terminal` is the escape hatch that hands over the real
terminal and accepts that the output then cannot be captured. The two are genuinely exclusive: either the pty is owned
and the emulation has to be good enough, or the child gets the terminal and the cells are gone. There is no third
option, which is the whole finding above.

**`set_winsize` on the master is the whole of resize handling.** The kernel carries the size to the slave and raises
`SIGWINCH` on the foreground process group itself, so nothing signals the child by hand. **EOF on the master is the
child's exit**: a pty reports `EIO` rather than an empty read once the last process holding the slave is gone, which is
where the reader is detached and the child reaped.

