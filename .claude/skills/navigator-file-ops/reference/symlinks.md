### Symbolic links

Shift+F5, *File > Create symlink…*, is a **departure**: DOS had no links, so DOS Navigator had no such command.
It borrows everything it can from Copy.

- **`navigator/lib/file_ops/filelink.py`** is the model: `LinkRequest`, `link_path` and `make_link`. The target line is read by
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


#### Changing links that are there

File > *Symlinks* holds Shift+F5 and four more, each a departure for the same reason. None has a key: F-keys and
Alt/Ctrl+letters are DN's, and these are rare enough for the menu, the panel's context menu and Key bindings.

- **No system call changes a link**, so `filelink.retarget` makes the new one beside it (`.navlink-<n>`, a dot-file,
  a short name so a 255-byte link name still fits) and renames it over the old: `rename(2)` replaces atomically, so a
  program reading the link sees the old or the new, never nothing. A failed rename unlinks the temporary.
- **Relative to what**: a relative target is read by the kernel from the directory the link is really in. A panel in
  `~/www`, itself a link to `/srv/www`, would otherwise turn `../x` into `~/x` where the kernel means `/srv/x`; so
  `link_base` asks `drive.realpath(parent)`.
- **By the letters, then checked**: `normpath` takes a `..` out as if the part before it were a directory. Behind a
  link it is not (`hop/..` is `hop`'s target's parent), so `switched` stats the new target -- joined with its `..`
  kept, which the kernel resolves properly -- and compares it with the link's (`same_file`). A mismatch is skipped
  and said, never written. A broken link has nothing to compare with and is converted by its letters, which is what
  `ln -sr` does too.
- **Several links** are not each asked: a replacement over all their targets (the moved-tree case: `/old/root` to
  `/new/root`) is previewed, as Multi-rename's rule is. Whether a new target exists is not shown: the preview is
  pure, re-planned on every key, and a `stat` per row per key would put the disk on the loop.


#### Hard links

Shift+F5's dialog makes them too: a *Symbolic link* / *Hard link* choice rather than a second command, because the
target, the history, the Tree button and the *Skip* box are all the same. Each choice is a departure, as the symlinks
are.

- **`ln -P`, not `-L`**: `os.link(..., follow_symlinks=False)` links a symlink named as itself. That is GNU `ln`'s
  default, and it is the only reading under which every row of the panel can be hard-linked as shown.
- **`EISDIR`, not the kernel's `EPERM`**: a directory cannot be hard-linked by anyone, but `EPERM` is in
  `elevate.REFUSED`, so the *Skip* box would offer *As root* for something root cannot do. `make_hard_link` checks
  with `lstat` first. A file the user does not own under `fs.protected_hardlinks` still gets `EPERM`, and there
  *As root* does help.
- **Only the disk**: `HARDLINK` is a capability of its own, not `SYMLINK`'s, since SFTP and the archives can hold a
  symlink but not a second name.

#### A file's other names

The kernel counts a file's names (`st_nlink`, the *Links* column) but does not list them. *Show hard links* walks the
whole file system the file lives on, from its mount point, because a name may be anywhere on it and nowhere else.
Two things keep that tolerable: `os.DirEntry.inode()` comes with the directory read, so only a match costs an
`lstat`; and the walk ends once it has found as many names as `st_nlink` says, which on a typical file with two
names is long before the end. A name that only another mount of the same file system reaches (a bind mount), or one
in a directory that cannot be read, is not found, and the toast says how many were.
