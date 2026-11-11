# Anchors

## Why the block exists

Before anchors, every child in a document set its own `x`, `y`, `width` and `height`. A survey of the 161 documents
found 681 expression lines. About 80% of them were three idioms written by hand:

- `width: max(0, parent.width - 4)`: fill the parent minus a margin, about 330 lines;
- `y: max(0, parent.height - 4)`: pin to the bottom, about 126 lines;
- `x: max(0, parent.width - 12)`: pin to the right, with the widget's width folded into the constant, about 46 lines.

These lines hide intent. You cannot tell from `parent.width - 12` that the 12 is a 10-column button plus a 2-cell
margin. They also go stale when the width changes.

The layouts (`HorizontalLayout`, `DockLayout`, ...) do not answer this. A dialog is DOS Navigator's absolutely placed
`TDialog`, transcribed cell by cell. Packing it into boxes would move things.

## Sugar, not a run-time system

QML's anchors are a run-time object attached to every item. Here an `anchors:` block is read by the parser and expanded
into property lines (`navml/anchors.py`, called at the end of `parse()`) before the generator sees the document:

- nothing new runs in navkit or in the generated code;
- every existing rule holds unchanged: the names an expression may read, `_bind`, `.pyi` stubs, source-map comments
  (pointing at the anchor's line), and `unbind()` before re-placing from Python;
- `--check` compares the same kind of output as before.

The cost is that an anchor cannot express anything a property line could not.

## Simpler than QML

- **An edge is an inset, not a reference.** `right: 2` means two cells in from the parent's right edge. QML would say
  `anchors.right: parent.right; anchors.rightMargin: 2`. Parent-relative edges are nearly every case, so they get the
  short spelling.
- **Siblings get named words**: `after`, `before`, `below`, `above`, with `+ gap`. Which edge of the sibling is meant
  follows from the word, so nothing needs a `.right` property, and widgets grew none.
- **Siblings only.** A sibling's coordinates share the anchored widget's space; anything else would need a coordinate
  conversion the bindings do not do. Aligning to another widget's internal column (`bits.column_x(1)`,
  `processes.command_x`) stays an expression.
- **No anchors under a layout.** A layout arranges its children from an effect and steps around a bound side, so an
  anchor there would half-work silently. It is refused instead.
- **Everything clamps at 0**, which is the `max(0, ...)` the hand-written lines carried.
- **Two literal insets are folded**: `left: 2` and `right: 2` write `max(0, parent.width - 4)`, the line they replace.

## Not offered yet

- **A visibility-aware sibling list** such as `before: macro_mark, root_mark, clock`, meaning "the first visible one".
  The Shell's status-line chains need it (`x: macro_mark.x if macro_mark.visible else root_mark.x if ...`). It is worth
  adding when those are converted, not before.
- **Converting Navigator's documents.** This round converted navml's library: Modal, Dialog, FileDialog, ListViewer.
  Navigator's files follow file by file. A hand-placed row of buttons whose DOS Navigator x values are centred becomes
  a `ButtonRow` (`navml-library`); one that is not centred keeps its literals, for fidelity.
