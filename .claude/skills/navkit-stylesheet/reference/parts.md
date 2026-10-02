## Parts: listing rows do **not** become widgets

A `Panel` keeps painting its own rows, and the stylesheet reaches them through a **part** —
`Panel::row`, with states and classes of its own:

```
Panel::row               { fg: white }
Panel::row.directory     { fg: white; bold: true }
Panel:active::row:selected { fg: black; bg: cyan }
```

### Why not row widgets

**Because row widgets would not have finished the job.** The menu hotkey letter (`navigator/__main__.py`) and the key
bar's digit (`navigator/__main__.py`) are substrings inside a single
`draw_text` run; no widget granularity reaches them short of a widget per character run. A mechanism for styling what a
widget paints rather than what it *is* was therefore needed whatever was decided about rows — and once it exists, rows
need nothing further.

The precedent is not an analogy but the same problem, solved twice. Qt's style sheets have sub-controls —
`QComboBox::drop-down`, `QScrollBar::handle` — precisely for a complex widget painted as one unit whose parts need
styling. CSS has pseudo-elements — `::first-line`,
`::selection`, `::marker` — for styling things that are not elements at all. `::` is their spelling and it is the right
one to borrow.

Fidelity agrees, and here it is a direct precedent rather than a parallel: TurboVision's
`TListViewer` draws its own items and picks a palette entry per item according to its state. One view, many items, no
per-item objects. Rows were never objects in the original.

The costs avoided are real. Rows as widgets means a recycled pool sized to the visible count, resynced on every scroll
and resize, each row carrying ten reactive cells — and this project has already declined per-widget overhead once on
benchmark evidence, when per-widget buffers lost to surface views. Mouse hit-testing does not argue back: the row under
a click is
`y - 1 + scroll`.

### How a part resolves

A part is not a widget and has no place in the tree. It inherits from its **owner's resolved style** — `self.style` is
the `derive` base — and then the matching `::part` rules cascade over it exactly as rules cascade for a widget. Owner
state composes with part state, which is what
`Panel:active::row:selected` says and what `navigator/__main__.py`'s real condition
(`index == self.cursor and self.active`) actually needs.

A sub-control counts in the **type** column of the specificity tuple, as CSS counts a pseudo-element.

The widget names its own parts and supplies their state when it paints, since it is the only thing that knows a row is
selected:

```python
style = self.part_style("row", selected=..., classes=("directory",) if entry.is_dir else ())
```

**Caching needs one wrinkle.** A part lookup takes arguments, so it cannot be a plain
`computed`. Make the computed return a *resolver* instead — rebuilt whenever the sheet or the widget's own style
changes, memoising combinations internally. Measured at 120 rows against 50 rules, naive rescanning costs 0.35 ms per
frame and the memoised resolver 0.019 ms. Against a frame budget neither is a problem, so this is an optimisation to
reach for rather than a condition of the design working.

