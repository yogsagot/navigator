# Remote and virtual drives: the design and its phases

## Why a drive object

Before drives, the panel's directory was a `pathlib.Path` that `enter`/`go_up` `.resolve()`d, and every reader and
writer -- the panel's scan, the copier, the eraser, the viewer, the editor -- called `os.*` on it. DOS Navigator had the
answer already: `TDrive` (`DRIVES.PAS`), whose descendants the panel held and whose virtual methods it called --
`GetDirectory`, `CopyFiles`, `EraseFiles`, `MakeDir`, `GetDir` (the title), `GetRealName` (what the other panel offers
as a copy's target), `UseFile` (a file made local before F3/F4), `ChangeUp` (`..` at the top of the drive: an archive's
returns to the drive it was opened from, the cursor on the archive). Archive and *Find:* drives stacked on the one
below through `Prev`; a disk or link drive replaced the stack (`InsertDrive`, `FLPANELX.PAS:725`). Navigator's
`Location.outer` is reserved for that stack.

## Why the steps, not the operations

DN's drives did whole operations, so each archiver had its own copy and erase. Here a drive does steps (stat, list,
open, rename, unlink) and the operations are written once. A copy from a server to the disk asks the same
questions, keeps the same sticky answers and untags the same way as one between two directories; a new drive gets
F5, F6 and F8 by answering a dozen methods.

## Decisions

- Own drivers per protocol, each an optional extra (`navigator-fm[sftp]` → paramiko; FTP on stdlib `ftplib`; SMB on
  `smbprotocol`), rather than fsspec (coarser cancel/progress, more dependencies) or FUSE mounts (external binaries).
- Credentials: ssh config, agent and keys first; a password box otherwise; the keyring only when installed and only
  when asked; nothing secret in `navigator.db`.
- The local shell stays put when a panel is remote; Enter, associations, the user menu, `$PAGER`/`$EDITOR`, F3 and F4
  work on a fetched copy (`UseFile`), offered back when changed.
- One copier for all drives rather than a local copier and a drive copier side by side: `LocalDrive` makes the same
  calls the local copier made, so the existing copy and erase tests guard local behaviour directly.

## Phases

0. Plumbing: `Location`, the listing moved to `drives/listing.py`, `LocalDrive`, `Panel.location`, the copier and
   eraser over drives. Done.
1. The file manager over `MemoryDrive` (copy/erase/mkdir/rename across drives, greying, shell rules, `UseFile`,
   bookmarks/history/desktop/command line taking URLs); SFTP with sessions, credentials, profiles, the Connect,
   password and host-key boxes, Navigator Link / Disconnect, the Link section, *Communications*; F3/F4 on fetched
   copies. Done.
2. Archives (`ARCVIEW.PAS` `TArcDrive`): a zip/tar drive on `zipfile`/`tarfile`, `Location.outer` as `Prev`, Enter
   on an archive pushes it, `change_up` at its root returns `(outer.parent, outer.name)`; writing into one, erasing,
   renaming and making directories in one as a rewrite at `Drive.finish`, and a new archive made by naming it on a
   copy's target line (DN's `ArchiveFiles`). Done. Still to come: the Archives menu (`HandleCommand`'s *Extract to*,
   *Test*), *Archives* column defaults (DN kept a `ShowFlags` word for them), and 7z/rar through external tools.
3. FTP (`ftplib`: MLSD with LIST parsing as fallback, `ftps://` via `FTP_TLS`, a pool of control connections) and
   SMB (`smbclient`'s `scandir`/`open_file`/`stat`/`rename`, `smb://user@host/share/path`), each with its own
   Utilities entry and link box. Done. SMB's root lists only the shares named so far; listing a server's shares
   (srvsvc over RPC) is left.
4. Parity: background `TreeView` loading (remote Alt+T/Ctrl+T), Find and Branch over a drive walk, Alt+G, content
   compare by streams, attributes with owners by number, a polling refresh, Ctrl+Q on a fetched head, the
   information panel's `Drive.describe`, printing a fetched copy, the viewer's *Save as* to a URL or into an
   archive, `ProxyJump`, keyboard-interactive auth. Done, and F3 reading a remote file a chunk at a time
   (`ChunkedSource`: a read of a missing chunk raises `NotYet`, the viewer's reading methods are retried once it
   lands, each reading before it changes anything). Then Shift+F4, symlinks on a drive that has them, list files,
   UU and the dBase view off the disk: `Manager._LOCAL_ONLY` is empty. Still open: syntax highlighting of a file
   read by chunks; a link from one drive to another (a path means nothing across them); UU's *already exists*
   question for a remote target.
