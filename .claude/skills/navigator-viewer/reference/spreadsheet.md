# The spreadsheet: DN's TCalcWindow on a CSV

DOS Navigator 1.51 had a small spreadsheet (`CALC.PAS`). `TCalcWindow` was a `TUniWindow` holding a cell-name
box (`TInfoView`), an input line with the cell's text (`TCalcInfo`), its own menu bar (`dlgWkzMenuBar`: File,
Edit, Search, Table) and `TCalcView`. F3 on a `.WKZ` opened it (`DNUTIL.PAS` `ViewFile`, `XT = '.WKZ'`), as
F3 on a `.DBF` opened the dBase viewer. `.WKZ` was DN's own format, so the menu entry was dropped. CSV and TSV
are the POSIX files a table lives in, so the window came back for them.

## What was kept

- **The look**, from `TCalcView.Draw`:
  - the name box and the cell's text on top;
  - the letters `Dig`, centred in each `CellWidth`;
  - the five-column row numbers;
  - `│` and `─` rules;
  - values right-aligned;
  - the palette `#8#13#14` in `CUniWindow`.
- **The keys of `StatusDef hcSpreadSheet`** that viewing needs:
  - F6 `cmGotoCell` (`dlgGotoCellNumber`, `A1` seeded);
  - F7 `cmFindCell` (`dlgFindCell`: Pattern, Search as String/Value, Case sensitive, Whole words only);
  - `cmSearchAgain`;
  - `cmChangeWidth`'s modal Left/Right loop;
  - Home to A1, End to the last cell.
- **The window list's name**: `cmGetName`'s *Speadsheet -*, with the typo mended.

## What was left out, and why

- **The editing half: Save, Save as, Recalc, cell formats, insert and delete row and column, and the
  clipboard.** The window is view-only. Rewriting a CSV keeping its quoting and line endings is its own
  feature, not asked for.
- **`TCalcInfo` as an input line.** Here it is a painted line.

## Departures

Each was asked for.
- **The header row.** A CSV's first record often names the columns, so it is a frozen row of titles under
  the letters.
- **Sort.** F5 was *Recalc*. Sorting orders the rows shown and never the file; a numeric column sorts as
  numbers.
- **Format.** The delimiter, the header and the encoding, which a `.WKZ` stored for itself and a CSV leaves
  to guessing.
- **Shift+F4.** It goes to the text and back, as *Markup view* goes between rendered and source.
- **Enter.** It shows the cell whole, since DN's Enter began editing.

## Why a walk, not a parse

A CSV of millions of rows must open at once, as the viewer opens a gigabyte. Each record's start is noted by
one thread scanning for quotes and line endings, which is all that bounds a record. A record is parsed only
when shown. Line numbers would not do, because a quoted field may hold line breaks.
