### Symbolic links

Shift+F5, *File > Create symlink…*, is a **departure**: DOS had no links, so DOS Navigator had no such command.
It borrows everything it can from Copy.

- **`navigator/filelink.py`** is the model: `LinkRequest`, `link_path` and `make_link`. The target line is read by
  `filecopy.resolve_target`, so a directory, a name ending in `/`, a `MkName` mask and a single new name mean what
  they mean to F5. A link is one system call, so there is no thread, no job and no progress box.
- **`LinkDialog`** (`navigator/widgets/file_ops/link_dialog/`) is the Copy dialog cut down. It has the same prompt shape
  (`Create symlink to file NAME in`), a line seeded from the passive panel with its own `"link"` history, and one
  *Relative link* check box. Tree and F10 go through `copy_dialog.choose_target_line`, the Tree logic both dialogs
  share.
- **Relative is remembered for the session**, as Copy's mode and options are (`ccCopyMode`). It is off at the start,
  because an absolute link is what `ln -s` makes from a full path. A relative link points from the link's own
  directory (`../a/f`), so a tree moved as a whole keeps working.
- **`Manager.make_links`** follows `copy_files`'s shape without the worker. It offers to create a missing directory
  in Copy's words, and it treats a link that cannot be made, one already in the way included, with Copy's
  *Skip*/*Cancel* box (`Manager._ask_skip`, now shared). What was linked is untagged, and both panels re-read.
- **Why Shift+F5.** Ctrl+F5 is DN's Size/Move and stays so; Alt+F5 is User screen and Alt+F6 FastRename. Midnight
  Commander's Ctrl+X S would need prefix chords, which navkit's key tables do not have. Shift+F5 was a placeholder
  for a floppy-era feature, and it sits beside F5.

