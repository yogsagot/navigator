---
name: navigator-viewer
description: The internal file viewer (F3, DN's FVIEWER.PAS) -- navigator/viewer.py (ViewSource, pread chunks), FileViewer in FileWindow, text/hex/dump modes, wrap, filters, bytes-regex search on a thread with SearchJob and SearchProgress, go to address, the View menu, and Ctrl+Q QuickViewer. Use when changing the viewer or quick view.
---

# The file viewer

- **F3 is DN's internal viewer** (`FVIEWER.PAS`). `navigator/viewer.py` is the model: `ViewSource` uses `pread` into
  cached chunks, **never `mmap`**, so a truncated log cannot `SIGBUS` Navigator. `FileViewer` inside `FileWindow` is
  `TFileViewer` inside `TFileWindow`; it opens zoomed on the desktop with the scroll bar on the frame and `TViewInfo` over
  the bottom edge.
- **Positions are byte offsets and nothing counts lines**, so a gigabyte opens at once. Text is UTF-8; an undecodable byte
  or a control is its CP437 glyph.
- Keys: F4 cycles text/hex/dump, F2 wraps, F6 filters, F7/Shift+F7/Ctrl+F7 search (a bytes regex, on a thread), F5 goes
  to a hex address. Esc closes, and so does F3, uncaptioned (mc's key, a departure). File > View > As Text / As Hex open
  it in either mode. Read-only for now.
- **While a viewer window is active the bar has a *View* menu after *File*** (modes, filters and wrap ticked, search, go
  to, close) -- see `navml-windows-menus` for how a window's menu joins the bar.
- A search still running after two ticks shows DN's *Search Progress* box (`TWhileView`: gauge, percentage, Stop), fed
  through a `SearchJob` the thread writes and the loop reads. It uses the library's `ProgressBar`.
- **Ctrl+Q is DN's quick view** (`QuickViewer`, a framed `FileViewer`), standing in the passive panel's place through
  `Manager.switch_view`; it follows the active panel's cursor, and Tab moves the keyboard in and out.
- **File View History (Alt+PgDn)**: DN's `TViewRecord`. Each file's window rectangle (scaled to the desktop, as
  `AdjustToDesktopSize` did), mode, wrap, filter, `top`, `x_delta` and hex `cursor` are written to the `ViewRecord`
  model. That happens when a viewer opens on a file with no record, and when it closes by any route, Alt+X included
  (`Navigator.on_stop`). The record is restored by `FileWindow.recall_history()` once the window is on its desktop.
  **Open viewers through `navigator.file_history.open_viewer`**, never `desktop.open(FileWindow(...))`, or nothing is
  restored. As Text / As Hex pass a mode, which wins over the record's. Gated on Interface's *Track viewing history*.
  The dialog and the list are `FileHistoryDialog`/`FileRecordList` (`shell/`). The Ctrl+Q quick viewer records nothing.
- Commands: `navigator/widgets/viewer/commands.py`.

## Read when

| Reference | Read when |
|---|---|
| `reference/file-viewer.md` | the full design and what is deferred |
