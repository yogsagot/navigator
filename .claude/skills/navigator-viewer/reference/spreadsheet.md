# CSV in the dBase window, and DN's spreadsheet

DOS Navigator 1.51 had a small spreadsheet (`CALC.PAS`). `TCalcWindow` held a cell-name box, the cell's text
line, its own menu bar and `TCalcView`'s grid of column letters and row numbers. F3 on a `.WKZ` opened it
(`DNUTIL.PAS` `ViewFile`, `XT = '.WKZ'`), as F3 on a `.DBF` opened the dBase viewer. `.WKZ` was DN's own
format; CSV and TSV are the files a table lives in on POSIX.

## What was built, and then changed

The first version recreated `TCalcWindow`'s look for CSV:
- the name box and text line;
- `Dig` letters centred in each `CellWidth`;
- five-column row numbers;
- the Editor/Spreadsheet palette, `#8#13#14` in `CUniWindow`.

It was dropped on request, so that the three table viewers (dBase, SQLite, CSV) share one window and one
style. A CSV opens in `TDBWindow`, the dBase viewer's window.

What survives of the spreadsheet:
- DN's column letters, for a file without a header;
- `cmChangeWidth`'s modal Left/Right loop, as *Column width*, now for every source;
- *View as Spreadsheet*, as the menu entry *As Spreadsheet*.

F6 *Go to Cell Number* and the spreadsheet's *Find* went with the window. The dBase viewer's F7 search
(`dlgDbFind`) covers a CSV.

## Departures kept from that work

- **Sort** (F8). It orders the rows shown and never the file; a numeric column sorts as numbers. It applies
  to dBase and SQLite as well.
- **Format** (Shift+F6). The delimiter, the header and the encoding, which a CSV leaves to guessing.
- **Shift+F3.** It goes to the text and back, as *Markup view* goes between rendered and source.

## Why a walk, not a parse

A CSV of millions of rows must open at once, as the viewer opens a gigabyte. Each record's start is noted by
one thread scanning for quotes and line endings, which is all that bounds a record. A record is parsed only
when shown. Line numbers would not do, because a quoted field may hold line breaks.
