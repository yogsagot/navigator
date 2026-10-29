---
name: navkit-bidi
description: Right-to-left text and the mirrored screen -- navkit/bidi.py (layout, order_cells for the viewer's and editor's rows, cells with logical indices, python-bidi's pure-Python UBA run step by step, arabic-reshaper and the lam-alef ligature, marks folded into their letter, caret_column/index_at/text_rtl), Surface.rtl and Surface.draw_runs, ScreenBuffer.mirrored and FLIP, Widget.mirrors (console, command line, viewer, editor, diff view, clock kept left to right) and arrows_mirrored, Application.direction/rtl/_unmirror (mouse and Left/Right), catalogue [meta] direction = "rtl" and i18n.is_rtl, --direction, TerminalInfo.bidi ("app"/"words", NAVKIT_BIDI), VTE's CSI 8 l, kitty's for_words. Use when text in Hebrew or Arabic looks wrong, a widget paints wrong on a mirrored screen, or adding a widget that paints text cell by cell.
---

# Right-to-left text and the mirrored screen

**Navigator lays right-to-left text out itself; no terminal is trusted to.** Measured (Oct 2026): VTE reorders a whole
screen row as one paragraph (columns, frames and overlapping windows trade places), kitty reverses glyphs of some runs
whatever order they arrive in, ghostty reorders nothing and joins no Arabic letter.

**Mirroring is a departure** from DOS Navigator, which never mirrored anything; asked for by the user (a right-to-left
language reads its screen right to left). It is the second standing exception beside the icon gutter.

## Text: `navkit/bidi.py`

- `layout(text, rtl) -> ((logical_index, cell), ...)`, visual order left to right, cached. Pure-LTR text short-cuts.
  Paragraph direction is the first strong letter's, else *rtl* (the surface's) -- so `( )` on a mirrored screen is laid
  out as inside Hebrew. Explicit format characters take part and get no cell.
- Arabic is shaped by `arabic-reshaper` **with ligatures off** (one letter in, one form out, indices kept); lam+alef
  is folded into its ligature by `_shape`, keeping the lam's index. Marks are folded into the letter before them
  before ordering, so a reversed run cannot put niqqud/harakat first. Brackets are mirrored at odd levels (L4).
- python-bidi is **held below 0.5**: 0.5+ is a Rust extension returning only the display string; Navigator needs each
  character's place (style, caret) and the Linux packages are `arch: all`. Its `bidi.algorithm` steps are run one by
  one with an `at` index stamped on each char dict.
- `caret_column(text, index, rtl)` / `index_at(text, column, rtl)`: columns as `draw_runs` paints them (reversed on a
  mirrored surface). The caret sits on the character it is before; at the end, past the end the paragraph grows from.
- `char_width`: marks and every `Cf` (marks of direction, joiners, soft hyphen) are 0 wide.

## Painting: `Surface.rtl`, `draw_runs`, the mirror

- `Surface.draw_runs(x, y, [(text, style), ...], max_width)` is the one text primitive; `draw_text` is one run (ASCII
  on an LTR surface keeps a fast path). **A caption with a highlighted letter is one `draw_runs` call**
  (`draw_caption`, `shortcut_runs` in `navml/widgets/dialog/control`), or the letter lands in the wrong cell.
- The application composes the frame left to right with `_back.rtl` set, then `ScreenBuffer.mirrored()` flips it on
  the way out: rows reversed, wide characters kept owner-first, glyphs through `FLIP` (corners, tees, half blocks,
  pointers, arrows, brackets). `draw_runs` on an rtl surface writes reversed and FLIP-swapped, so the mirror puts text
  back the right way and against the right-hand edge of its span. **A glyph that points the layout's way is a
  `set_cell`, not text** (the submenu arrow), so it flips.
- **Text painted cell by cell with `set_cell` comes out reversed on a mirrored screen.** Use `draw_runs`, or keep the
  widget left to right.
- `Widget.mirrors = False` keeps a widget's content left to right inside the mirrored frame: `render_tree` gives it a
  view with `rtl=False` and `mirror()`s its rectangle afterwards, which the screen's mirror cancels. Set on
  `ScreenView` (console), `CommandLine`, `FileViewer`, `FileEditor`, `DiffView`, `Clock` (a blinked colon makes the
  time two numbers, which an RTL line swaps).
- **File contents** (viewer, editor) are left to right *widgets* but their lines are still laid out: each painted row's
  cells go through `bidi.order_cells(chars)` -- the row as columns (`""` second halves, tabs already spread), returned
  as `(column, shown)` in visual order, or None when nothing changes (cached). Every per-cell decision keeps using the
  original column/offset: the viewer's search hit and tokens (looked up per cell once reordered, the one-pointer walk
  assumes growing offsets), the rendered view's marks, the editor's block/match (lit per cell by original column; the
  fill covers only what is past the text) and tokens. `FileEditor._visual_column`/`_logical_column` map the cursor
  and a click. Lines keep left alignment and the editor's columns stay logical, but Left/Right on a reordered line move to the
  neighbouring *painted* cell (`FileEditor._step_visually`; off the left end it stays, off the right end past the text
  and then on to the next line, as Right always did), and Ctrl+Left/Right to the nearest word start that way on screen
  (`_word_visually`: each word's first letter in the text, plus the line's end; none left, DN's move to the next
  line).
- **A block the cursor marked is what is painted between its ends** (Word's visual selection): `FileEditor._painted_block`
  is the very `block` tuple `_set_block`/`_set_ordered` made (kept through `_follow_edit`); any other block -- ^K C's
  copy, ^K R's read, a recase that changed lengths -- is the stretch it is. `_block_runs()` turns it into the text
  stretches it holds (`_painted_spans` per reordered line: between the ends on one line; from the start's cell towards
  the end the line reads to on the first; from the line's beginning to the end's cell on the last; whole lines
  between). **Every stream-block command goes through the runs** -- `block_text`, `_take_block`, ^K C/V, `_recase`,
  `block_lines`, `_cursor_in_block`, the right-click test; render lights a reordered line by `_block_picked`. A new
  stream-block command must use `_block_runs()`, never `document.text(*self.block)`. Line-based ones (indent, format) are
  unchanged.
- **A column block's columns are painted columns** (rectangle straight on screen): its corners are made painted --
  `_here` (Shift+movement, `_visual_column`), `_mark_span`/switch block (`_painted_column`), ^K C/V; `_rect_spans`
  gives what a line paints in them (scattered text stretches on a reordered line, `columns.span` elsewhere), used by
  pieces, delete, recase, sort keys, calc, `block_lines`, the cursor-in-block test; render compares the painted
  column for a rectangle (a match stays lit by the text's columns). `_line_spans(number)` is any block's stretches on
  a line; *Selected text* search covers first..last stretch and `find` passes over a match not wholly inside one.
  ^K I/U at a column block's left edge work on what is painted there: `_painted_insert` tries the blanks before
  and after the character painted at the edge, lays each out, and keeps the one that paints them there (else by the
  character's direction); `_text_column` maps the edge for the unindent. A stream block and the lone-line unindent
  still work at the line's start in the text (a Hebrew line's right-hand end). Combining
  marks join their letter's cell in both rows (`viewer.decode_cells`, `editor.columns.cells`).
- `Application._unmirror` runs on every event as it comes off the queue (once, so derived double-clicks are already
  converted; the original event's id is what `_posted` tracks): a mouse x is flipped, and flipped again inside an
  unmirrored widget (`Widget.unmirrored()`); Left/Right swap when the focused widget `arrows_mirrored()` -- InputLine
  says so only while its text is a right-to-left paragraph. `_cursor` maps the caret through `_mirror_x` the same way.
- Direction: `Application.direction` (`auto`/`ltr`/`rtl`, `--direction`); `auto` is `i18n.is_rtl()`, a catalogue's
  `[meta] direction = "rtl"` (he, ar). A change repaints everything (no underlay reuse).

## Terminals: `TerminalInfo.bidi`

- `"app"` (default): cells are sent as laid out; `Terminal` sends `CSI 8 l` (ECMA-48 BDSM reset, explicit) before the
  screen is cleared -- VTE keeps the mode per line from when the line is made -- and `CSI 8 h` when it gives the screen
  back, so the console's programs get VTE's own bidi. Ignored (logged) by kitty/ghostty.
- `"words"` (kitty: `TERM=xterm-kitty` or `KITTY_WINDOW_ID`; `NAVKIT_BIDI` overrides): `screen.for_words` sends kitty
  glyphs pre-reversed for it to put back, **styles left in place** (kitty moves glyphs, not colours). A run is broken by
  a space, a box/block character or a bold/italic change, not by colour; a run starting with Arabic is reversed to its
  end (Latin after it included); Hebrew is reversed a stretch of Hebrew letters at a time. Found by probing kitty,
  undocumented: re-probe (lamed/final kaf, Latin markers) if kitty changes.

## Checking it

`tests/test_bidi.py`. By eye: `nav --language he` / `--language ar` (or `--direction rtl`) in a VTE terminal, kitty
and ghostty; xdotool + `import` can capture windows (kitty: capture after `windowactivate --sync`, or it comes out
black). Reading Hebrew order off a screenshot is unreliable; use letters with ascenders/descenders (ל, ך) or Latin
next to Arabic.

## What is left

`reference/backlog.md` lists what is still to do for right-to-left text, by priority. Update it as items are done.
