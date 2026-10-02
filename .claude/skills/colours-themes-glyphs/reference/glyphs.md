## Terminal capabilities: characters, and why a font cannot be detected

Colour asks how many colours a terminal can name. The other half of the same question is which *characters* arrive as
shapes rather than as replacement boxes, and it is answered the same way: once, at the edge, by
`TerminalInfo.glyphs`. Three tiers, ordered and compared with `>=` exactly as the colour depths are —
`GLYPHS_ASCII`, `GLYPHS_UNICODE`, `GLYPHS_NERD`.

### The detection is honest about what it cannot know

**No escape sequence reports the font a terminal is using.** The usual proposal is to print a glyph, ask for the cursor
column with `CSI 6n` and infer from how far it moved. That measures the terminal's own width table and *not* whether
the font has an outline for the codepoint, so on precisely the terminals where the answer is unknown it reports the
same column either way. It would also be the first query round-trip in the codebase, and would have to run before raw
mode. It was rejected on the first ground alone; the second only makes it worse.

What can be known is which *emulators ship a Nerd Font fallback of their own* — kitty, WezTerm and Ghostty each bundle
`Symbols Nerd Font Mono` and map the icon ranges onto it, so the glyphs render whatever font the user configured. That
is a fact about the emulator rather than a guess about the font, which is what makes it safe to act on. Everything else
has to say so itself, through `NERD_FONT` or `NAVKIT_GLYPHS`.

The guess is conservative in the same direction the colour guess is, and for a sharper reason: a colour guessed too high
is a slightly wrong shade, but a glyph guessed too high is a replacement box on every line of every frame. So a
non-UTF-8 locale gets ASCII rather than the benefit of the doubt, and a multiplexer — where `TERM` becomes
`screen-256color` and the marker variables are not forwarded — reports Unicode and is documented as needing the override
rather than being guessed at.

### The vocabulary lives apart from both the buffer and the capability

`navkit/glyphs.py` holds the box character sets and the tiers, and imports nothing. That placement is what keeps two
existing rules intact at once: `screen.py` still has no runtime import of `capabilities.py`, because `draw_box` takes
the **six characters themselves** rather than a name for them and so never learns that tiers exist; and
`capabilities.py` still describes the terminal rather than the drawing.

This answers the two questions the *Still open* section carried. `draw_box`'s `double=` keyword **did** become a
charset argument, and the `border` vocabulary is `single`, `double`, `round`, `ascii`. Resolution happens in the widget
— `Widget.box_charset()` — because that is the one place both halves are in hand: the sheet says which set is *wanted*
and the tier says which can be *shown*, and either vetoes, the same shape as `Terminal(mouse=False)` against
`info.mouse`.

Note what the tier does **not** do: no tier above `GLYPHS_UNICODE` changes a box frame, because box drawing is ordinary
Unicode and a Nerd Font adds nothing to it. The tier matters at the lower boundary, where every set collapses to
`+-|`. Icons are where the top tier earns its place, and icons are an application's vocabulary rather than the kit's.

`Widget.glyphs` is a plain property and not a `computed`. The tier is settled when the terminal is detected and never
changes, so there is nothing for a dependency to invalidate; a detached widget assumes Unicode, which is what the kit
assumes whenever it has no terminal to ask.

### Icons in the file manager are a departure, and a deliberate one

DOS Navigator had no icons and could not have had them — CP437 has no such glyphs, and the original distinguished a
directory by colour and by the word `DIR` in the size column, which Navigator still does. Showing a Nerd Font icon
beside each name therefore cuts against the project's standing rule of preferring the original's behaviour to a modern
alternative. It was taken anyway, on the grounds that a terminal shipping the font makes it free, and it is reversible
in two ways rather than one: `icons: none` in a sheet, or `--glyphs unicode` on the command line.

The gutter is **two cells, not one**. A Nerd Font *Mono* build patches its icons to a single cell and `char_width`
agrees with it, the Private Use Area measuring as ambiguous — but the plain build draws some of them two cells wide and
no table records which of the two is installed. Spending the second cell on a space means a glyph that comes out
double-width covers the space instead of shoving the name along.

**Without the icon the gutter is one cell, and it is always kept.** It holds Midnight Commander's file-type mark
(`DirEntry.type_mark`: `/` directory, `*` executable, `@` symlink, `~` symlink to a directory, `!` stale symlink, `=`
socket, `-` character device, `+` block device, `|` FIFO, a blank for a plain file) -- a second and smaller departure,
since DN had none, taken at the user's request and pure ASCII so it holds in every tier. It is read off the mode bits,
never `os.access`, so painting a row costs no system call, and `mode` is the target's except for a stale link, whose
own `S_IFLNK` mode is what says it is stale. In the Nerd tier the same mark picks the icon (`icons.BY_TYPE`, which
beats the directory and the extension icons), so the two tiers say the same thing, one in glyphs and one in MC's
characters. The column is reserved even where every mark is a blank because a
tagged entry's marker is drawn in it: Insert (`ToggleMark`, DN's `kbIns`) tags the entry and steps down, and a tagged
entry shows DN's default `TagChar`, `√` (`+` in the ASCII tier), in place of its mark *or its icon* -- the colour,
`[87]`/`[89]`, says it too, but not on a monochrome terminal. DN drew its tag after the 8.3 name; a POSIX name has no
fixed width to draw after. The tags are `Panel.marked`, a set of *names*, because a rescan builds new entries; a
re-read of the same directory keeps them less the names that went (as DN's `RereadDir` did) and a move drops them.

