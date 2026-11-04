# Follow end, Filter lines and the structured view

Three departures from DOS Navigator's viewer, asked for together in the third round of suggestions. DN's viewer
took a file's size once, hid characters (F6) but never lines, and showed bytes and lines only.

## Follow end (Ctrl+T)

- **Why poll instead of watching the directory.** `dirwatch` watches directories, not files, and is not told which
  file changed. A `FOLLOW_TICK` (0.5 s) `call_every` that runs `fstat` on the open descriptor costs one syscall and
  works for every source. A file across a network, or one opened as root, is a `ChunkedSource`: it is stat'ed through
  its drive on a thread (`ChunkedSource.stat_size`, the drive being `source.drive` for the root helper), and a tick
  is skipped while the last one is still in flight.
- **What a new size invalidates.** The last chunk was cached short and would stay short, so it is dropped, along
  with `_eol_cache`. A file that shrank (rotated, truncated) drops every chunk. An empty file opened as `_data`, the
  `/proc` path because its stat said 0, becomes an ordinary file once it has a size. A real `/proc` file never does,
  and following it is refused.
- **Letting go.** Any move back up (`scroll_rows` < 0, `to_start`, `seek` before `top`, the hex cursor moving back,
  or the filtered cursor moving up) clears `follow`, as `less`'s `F` stops on a key. The next tick sees it off and
  cancels the timer. Ctrl+T turns it on again and goes to the end. Unlike `less`, End does not turn it back on: in
  text mode End scrolls sideways, as DN's did.
- **Refused for** a materialized copy (`use_set`, which a re-fetch would be needed to follow), bytes typed over in
  hex and not stored (`FileChanged` compares sizes), and a rendered markup or picture view.

## Filter lines (Ctrl+G)

- **Nothing in the viewer counts lines**; `navigator/lib/viewer/lines.py` does, once, on a thread, on its own
  descriptor (`Reader`): 1 MiB windows, split on `\n`, each line decoded in the viewer's encoding and matched as
  text. Every encoding offered is UTF-8 or a one-byte code page, so a line always ends at a `\n` byte.
- **A scan goes on from `scanned_to`**: what *Follow end* uses to keep a filtered log filtered. An unended last line
  is matched (`tail`) but not passed, so the next scan reads it again, longer.
- **Limits**: `HIT_LIMIT` (200 000) matching lines are kept, and `+` after the count says more were not looked for.
  `TEXT_LIMIT` characters of each are kept. A run of `LONG_LINE` (4 MiB) with no ending is taken as a line of its
  own, as the viewer cuts at `LINE_LIMIT`.
- **Painted by the viewer itself** (`FileViewer._paint_lines`, `filtering`, `lines_row`/`lines_cursor`), not
  through the markup's `Layout`. A row is a number gutter (`::lines.number`, the cursor's `::lines.cursor`) and the
  text with what matched marked (`::lines.match`), in one `draw_runs`. `top` follows the cursor's line, so the scroll
  bar and switching back stay in place. Enter goes to the line in the whole file, Esc puts the whole file back where
  it was, and Ctrl+G opens the box on the pattern in force, where an empty line and OK take it off. F7 finds a hit
  among the rows shown, or else leaves the filter for the hit.

## The structured view (Shift+F4 on a JSON, YAML, TOML, XML or plist file)

- **A window of its own** (`StructWindow`, `DataTree(TreeView)`), opened in the text viewer's place
  (`FileWindow.as_tree`, `db_window.take_place`), as a CSV's spreadsheet is. `Markup view`'s `Layout` has no fold
  state, and a tree with its own keys, quick search and path line did not fit FileViewer's byte rows.
- **Parsers**: `json` (with `object_pairs_hook`, so order and repeated keys survive), `tomllib`, `xml.etree`,
  `plistlib`, and PyYAML's **composer**, never `yaml.load`. Composing runs no constructor, so a tag
  (`!Ref`, `!!python/object`) is shown, never acted on. Its nodes also keep their marks, which gives YAML nodes an
  offset for Shift+F4 back to the text. The other parsers keep no places, but every parse error's line and column is
  kept (`ParseFailed`), and the text goes to that line.
- **Lazy both ways**: a model `Node` wraps what the parser made and makes its children when first asked
  (under `_MAKING`, so a search on a thread and the tree on the loop get the same nodes), and a `TreeNode` is made
  when its parent opens. A YAML alias is the node it names, shared; `walk` and *Expand all* pass a branch once by
  `identity`, so one holding itself ends.
- **Search (F7)** looks in every branch, opened or not, on a thread (`structured.find`), then `DataTree.show`
  opens the branches down to the match. Quick search (Ctrl+S, `/` to descend) matches keys among the rows shown.
- **Only local files**, or a copy fetched from another drive: `shows_tree` refuses a `ChunkedSource`, as
  `shows_table` does, since going back to the text opens the viewer on a path.
- `STRUCT_LIMIT` is 32 MiB. *Expand all* opens at most `EXPAND_LIMIT` (5 000) nodes, and refuses more.
- **No checkbox** for `[viewer] render_structured` (F3 opens the tree) or `structured_masks`, as the other render
  switches have none.
