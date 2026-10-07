---
name: navigator-desktop
description: Saving and restoring the desktop -- Options > Save desktop / Load desktop (DN's cmSaveDesk/cmLoadDesk, SaveDesktop/RetrieveDesktop), navigator/desktop_state.py (snapshot, save, load, restore), the SavedDesktop model, and Startup's Autosave desktop (save on exit in Navigator.on_stop, restore in on_start, the command line's directories winning). Use when changing what a saved desktop keeps or when it comes back.
---

# The saved desktop

- **What it is**: DN streamed every window to `DN.DSK`; here `navigator/desktop_state.py` makes a dict --
  `{"version", "windows": [...bottom to top], "front": index}` -- kept as JSON in the `SavedDesktop` model
  (`desktops` table, one row a name, `default`). A `version` other than `VERSION` is not read.
- **What a window keeps** (`_window`): its rectangle (`file_history.window_values`, put back by `place_window`), and
  - `Manager`: per panel `path` (a *Find:* listing's origin), `view_mode`, `sort_mode`, `show_hidden`,
    `file_mask`, `columns`, `display`, `cursor` (entry name, via `_return_to`); `active` side, `hidden` side, `view`
    standing in (tree/quick/info, put back through `switch_view` after the active panel is focused);
  - `EditWindow`: `path` (cursor and scroll are the edit history's), SmartPad as SmartPad; `FileWindow`: `path`,
    `mode`; `TreeWindow`: the directory and hidden; `CalculatorWindow`: the expression.
  Anything else is not kept. A window that cannot be made again (a file or directory gone) is left out.
- The trash can's showing and place are kept too (`snapshot`'s `trash`), as `SaveDesktop` wrote them.
- **Save desktop** (`SaveDesktop`) writes over the saved one. **Load desktop** (`LoadDesktop`) says *No desktop has
  been saved* with none, else closes every window as Close all does (`close_all_asking`; a Cancel keeps the desktop)
  and `restore`s.
- **Startup's *Autosave desktop*** (off by default; a departure: DN restored `DN.DSK` at every start whenever there was
  one) saves in `Navigator.on_stop` -- the windows are still open there, as quitting only asks -- and restores in
  `on_start`, replacing the file manager the start opened once a manager has come back. Directories given on the
  command line (`Navigator(given=True)`) go to the first manager restored, its cursors dropped.
- **The topmost manager's active panel opens in the current directory** (`restore(here=)`: the start directory, or
  the active panel's for Load desktop) unless Startup's *Preserve directory* is ticked -- DN's `TFilePanelRoot.Store`
  wrote that panel's drive as nil. Decided at restore rather than save, so the saved directory is never lost.
