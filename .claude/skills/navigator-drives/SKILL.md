---
name: navigator-drives
description: Remote and virtual drives -- navigator/lib/drives/ (Location and Site, Drive/LocalDrive/MemoryDrive/SftpDrive/FtpDrive/SmbDrive/ArchiveDrive/TrashDrive (trash:///), capabilities, zip and tar archives (and 7z/rar through 7-Zip's command line) entered with Enter (DN's TArcDrive), Extract to / Test / Shift+F2, archive columns, drive_of/mount/unmount, listing.py with DirEntry and the local scan), SESSIONS (connect and its NeedPassword/NeedPassphrase/UnknownHostKey questions, the SFTP channel pool, the transport watcher and one silent reconnect, idle reaping, closing → panels fall back like DN's cmCloseLinked), credentials (ssh config/agent/keys, known_hosts, optional keyring), RemoteProfile, UseFile temp copies and upload-back, copy/erase across drives through the one copier, Panel.location vs Panel.path, Manager's _LOCAL_ONLY gate, Utilities > SSH link (SFTP) (Alt+F11) / Disconnect (Alt+H), the Link part of the Alt+F1/F2 box, Options > Configuration > Communications, and how to add a protocol. Use when touching anything that may not be a local path.
---

# Drives

DOS Navigator's panel held a **`TDrive`** (`DRIVES.PAS`): the disk, an archive (`TArcDrive`), a *Find:* listing
(`TFindDrive`), `TEMP:` (`TTempDrive`), or the PC at the other end of a cable (`TLinkDrive`, `NAVYLINK.PAS`, *Navigator
Link*, Alt+F11). `navigator/lib/drives/` is that object for a modern system. There are the disk, an in-memory drive
(the tests', later `TEMP:`), SFTP, FTP/FTPS, SMB, S3, archives (`ARCVIEW.PAS`) and the Trash (`trash:///`). NFS is only
ever a kernel mount, which Disk > Volumes already lists. `reference/design.md` has the plan and the phases.

## Rules

- **A `Location` is not a path.** `Location(site, path, outer)`; `Location.of(Path)` for the disk,
  `Location.parse(text)` for what `str()` wrote. It has **no `__fspath__`**, so an `os.*` call handed one fails at once
  instead of running on the local disk with a remote name. `.local` is the way back, and raises `RemoteLocation` (a
  `TypeError`) off the disk. **`str()` of a local location is exactly `str(Path)`**, so histories, bookmarks and a
  saved desktop keep the same bytes; a remote one is `sftp://user@host:port/path` (`file://` parses to the disk).
- **`Panel.location` is what a panel navigates** (reactive, seeded never bound). `Panel.path` is a property: the
  `Path` on the disk, `RemoteLocation` elsewhere -- so code not yet taught about drives fails loudly. Code that works
  anywhere reads `location`, `entry_location(entry)`, `drive`, `title_location`. `local_anchor` is the last local
  directory the panel read (set in `_apply`), where it goes back when its drive closes.
- **Every `Drive` method blocks and runs on a thread** (a remote one is a round trip; a local one may be a dead
  mount). The exceptions are the existing local single-syscall ones, which stay on `location.is_local` branches
  verbatim. `change_up()` is the one drive method a handler may call on the loop: it must be lexical.
- **Failures are `OSError`** with `errno`/`filename` where known; a drive gone is `DriveGone` (`ENOTCONN`, *Remote drive
  X is not accessible* -- DN's `TLinkDrive` free-space text). `filecopy.error_message` shows any of them.
- **The local fast path is unchanged.** `LocalDrive` makes the very calls the code made before drives (`os.lstat`,
  `os.scandir`, `os.replace`, `shutil.copystat`, `statvfs`, `fsync`); the listing functions moved verbatim to
  `drives/listing.py` and `panel.py` re-exports them. A test that patched `panel_module.scan_directory` patches
  `navigator.lib.drives.listing` now.
- **One copier and one eraser for every drive.** `filecopy._Copier`/`fileerase._Eraser` ask each end's drive
  (`drive_of`) for every step; a rename between sites raises `EXDEV`, so a move between drives copies and deletes
  like a move across file systems. `filecopy.stream` is the byte loop. Questions and `done` lists carry
  `shown(location)`: the plain `Path` on the disk, the `Location` elsewhere -- so `_watch_job`, `OverwriteQuery` and
  `untag_paths` are unchanged. `resolve_target`: `://` is remote, a bare absolute path is the disk (DN: only a
  prefix left it), a relative one is on the working directory's drive.
- **Capabilities grey commands, not errors.** `Manager._LOCAL_ONLY` is **empty**: every command asks the drive or
  works on a fetched copy; it is where a new command that cannot goes until it is taught to. What a drive cannot do
  at all its capabilities grey (`enables`): rename/move/delete/mkdir/F4 need `write`, Shift+F5 needs `symlink`.
- **The last ones, and how**: Shift+F4 reads its name as a copy's target line does (`target_location`: a URL, an
  archive place, or relative to the panel's drive) -- an existing file there is fetched and edited, a new one is an
  empty copy (`usefile.blank`) that F2 makes there (`$EDITOR` only for one already there). Shift+F5 makes a link on
  the destination's drive (`filelink.make_link` → `Drive.symlink`, relative by `posixpath`), only to a file on the
  same drive -- `EXDEV` otherwise -- the steps on a thread. *Make list* writes its file on the drive with that drive's
  own paths in it (`_make_list_elsewhere`); *Read file list* reads one there (`filefind.read_list_on_drive`: `/` the
  drive's top, a mask matched against a listing, `~` just a name). UU encode/decode (`Manager._staged`) fetch the
  input, write into a staging directory under `private_dir()`, and `usefile.put_files` the results up into the
  directory asked for -- its `ask` hook given those already there first, before anything is written:
  `uucode.ask_over_encoded` (anything but Yes/All abandons, as `encode` asks of the disk) and `ask_over_decoded`
  (*Check existing files*; No leaves one, Cancel it and the rest), `FileExists.path` then a `Location`. The
  dBase view fetches the file (`use_file.database_elsewhere`) and puts it back after every field edited.
- **What works anywhere, and how** (Phase 4): Alt+G counts through `Drive.children`
  (`dirlength._count_on_drive`); *Auto refresh* polls a drive with `polled = True` (SFTP, FTP, SMB) every
  *Communications* *Look for changes every* seconds (`[remote] refresh`, 0 off -- every look is traffic) through
  `base.PollWatch`, which lists on its own thread and calls only when names, sizes or times changed; Find and
  Directory branch walk the drive (`filefind._search_drive`, text by `holds_on_drive`; *disk*/*all* scopes start at
  the drive's top; links not followed), found entries carry `Location` directories (`DirEntry.path_in`,
  `listing._entry_elsewhere` re-reads them); the trees (Ctrl+T, Alt+T) root on the drive and read on threads
  (navml `TreeView.load_in_background`/`children_of`; `DirectoryTree.use_drive_of`, `show_elsewhere` walks the
  path on a thread and opens the branches when it lands; Alt+T's box makes directories through the drive);
  Ctrl+Q fetches the first `usefile.HEAD_LIMIT` (1 MiB) and shows that (`QuickViewer._show_elsewhere`); the
  information panel shows the place and `Drive.describe()` (server, host key, cipher, TLS, shares; an archive's
  kind, files, packed and unpacked) under *Connection* -- every name in `base.DESCRIBED`, which the catalogues list;
  *Compare* reads contents side by side (`dircompare.same_bytes`); *Print* spools a fetched copy; *File
  attributes* stats, chmods, chowns and utimes through the drive (`fileattr._stat`/`_children`/`_apply_elsewhere`),
  owners as numbers there (a server's ids are not this system's), changeable only where the drive can `chown`;
  the viewer's *Save as* takes a URL or an archive place (navml `FileDialog.raw`, a test for names handed back as
  typed; `viewer._save_elsewhere`, written beside and renamed over).
- **F3 reads a remote file a chunk at a time** (`viewer.ChunkedSource`), where the drive can read anywhere in it
  (`Drive.open_random` -- `SeekingReader` over a seekable `open_read` for SFTP (no `prefetch`), SMB and memory;
  `REST` + `RETR`, cut off with `ABOR`, for FTP; None for archives, which are fetched whole as before). The window
  is up at once, whatever the size. A chunk not in the cache (`REMOTE_CACHED_CHUNKS`, 32 MiB) raises **`NotYet`**
  after asking for it and `READ_AHEAD` more on the `nav-view-fetch` threads; when it lands, `arrived` tells the
  viewer (`FileViewer._chunk_arrived` → `call_from_thread` → `_chunk_landed`), which repaints and does again what
  was interrupted. **The rule that makes that safe**: every viewer method that reads is wrapped `@_when_here`
  (`seek`, `scroll_rows`, `to_end`, `show_hit`, `_snap_top`, `_to_longest_end`), and each reads everything before
  it changes anything -- so an interrupted one did nothing, and doing it again is doing it once; a caller above
  one carries on harmlessly. `render` catches `NotYet` (*Reading...*) and a failed fetch's `OSError`; `percent()`
  falls back to the offset. Search reads through the drive on its own thread (`ChunkedSource.find`, blocking);
  *Save as* streams the whole file from the drive (`stream()`); nothing is lexed (it would read everything); no
  view record is kept. A new method that reads must be wrapped the same way, or it raises `NotYet` into a handler.
- **The shell never follows a panel off the disk.** `_front_directory()` is None for a remote panel, so the subshell
  stays in its last local directory; the prompt stand-in names the panel's place (`drive.get_dir`, `SFTP:host:/path$`) and
  the shell's own prompt is hidden. `_follow_shell` moves a remote panel back to the disk only when the command
  `cd`'d (the shell's cwd changed during it) -- and never into a `UseFile` directory.
- **No secrets on disk from Navigator.** A typed password lives in the connection (`Answers`) until it closes. *Save
  in keyring* is offered only when `credentials.keyring_available()` (the `keyring` package with a real backend), and
  every keyring call is on a thread. Host keys are `ssh`'s: unknown → `HostKeyQuery` (Accept once / Save into
  `~/.ssh/known_hosts` as `[host]:port type base64`), changed → refused, no button accepts it.
- **Closing is DN's `cmCloseLinked`.** `SESSIONS.close(site, why)` unmounts the drive and tells every listener (on the
  closing thread); `Shell._heard_closed` hands it to the loop and `close_linked` sends each panel on the site to its
  `local_anchor`, saying *Remote drive X is not accessible* once for `"lost"`.

## Pieces

- **`location.py`** `Site`, `Location`, `LOCAL_SITE`, `RemoteLocation`. `normalized()` is by the letters (`..`, `.`).
- **`base.py`** `Drive` (TDrive's names: `get_dir` title, `real_name` copy target, `use_file`/`change_up`), `FileStat`
  (an `os.stat_result` look-alike; `st_dev`/`st_ino` 0 where there are none -- the copier's loop check falls back to
  site+path), capability constants, `DriveGone`.
- **`__init__.py`** `drive_of(location)` (`LOCAL` for the disk, the mounted drive for its site, else `DriveGone`),
  `mount`/`unmount`/`mounted`.
- **`memory.py`** `MemoryDrive("name")`, site `mem://name`; `make(path, data)`/`read(path)` for tests. POSIX errors where
  cheap; no owners.
- **`trash.py`** `TrashDrive`/`TRASH` on `TRASH_SITE` (`trash:///`): the freedesktop Trash
  (`navigator.lib.file_ops.trash`, `navigator-file-ops` *The Trash*). **No connection**: `drive_of` answers `TRASH`
  for the scheme without mounting and `Shell.reach` lets it through, so SESSIONS never sees it. The root lists every
  trash directory's items (a name shown already gets `.N`; `item(name)` re-reads when unknown), below it is the disk
  through `LOCAL`. Erasing only: `unlink`/`rmdir` of a root item also `forget()` its info file; making, writing,
  renaming are `EROFS`. `DirEntry.trashed` (origin, deletion time) is the panel's second info line. Watches the home
  trash's `files/`. Title `TRASH:/path`. The root lists `..` too: it and Backspace leave for
  `Panel.local_anchor`, the last local directory read (`Drive.leaves_to_anchor`, which `_go_up_elsewhere` reads where
  `change_up` answers None).
- **`sessions.py`** `SESSIONS.connect(site, answers)` (blocks; raises `NeedPassword`, `NeedPassphrase`,
  `UnknownHostKey`, `HostKeyChanged`, `DriveGone`), `close`, `close_all`, `reap(in_use, idle)`, listeners;
  `SCHEMES` (scheme → module with `available()` and `connect()`), `available(scheme)`, `EXTRA_HINT`.
- **`sftp.py`** (paramiko, the `navigator-fm[sftp]` extra, imported only when connecting). `_Connection`: one
  `SSHClient`, `~/.ssh/config` through `credentials.host_config` (hostname, user, port, IdentityFile, ProxyCommand),
  agent and keys, then the keyring's password, then the answers. A pool of ≤ `CHANNELS` `SFTPClient`s, each checked out
  by one thread (`_channel()`); a file opened keeps its channel until closed (`_HeldFile`). A watcher thread joins the
  paramiko `Transport` and, when it ends unasked, connects again once, else calls `on_lost` → `SESSIONS.close(site,
  "lost")`. `take()` makes a dropped connection again once too. Reads `prefetch()`, writes `set_pipelined(True)`;
  `replace` is `posix-rename@openssh.com`, falling back to remove+rename. `mkdir` turns SFTP v3's bare *Failure* into
  `EEXIST` when the name is there. Owners come from the server's `ls -l` line (`DirEntry.owner`).
- **`ftp.py`** (`ftp://`, `ftps://`; stdlib `ftplib`, nothing to install). `_Pool`: up to `CONNECTIONS` logged-in
  control connections, each one thread's (`FtpDrive._client()`); a file read or written (`_Transfer`, `RETR`/`STOR`/
  `APPE` over `transfercmd`) holds its connection until the reply after it. A connection is `NOOP`ed when taken and
  made again once if the server dropped it (servers drop idle ones); failing that, `on_lost`. No user is anonymous
  (empty password); a user without a password is `NeedPassword` (keyring first). Listing is `MLSD` (facts
  `type size modify unix.mode unix.owner unix.group`), else `LIST -a`, else `LIST` -- each learnt once
  (`pool.mlsd`, `pool.list_a`) -- parsed `ls -l` style (`_parse_list`); `stat` is `MLST`, else the parent's listing.
  Replies map to `OSError` (`_os_error`: 530 → `EACCES`, 550 → `ENOENT`/`EEXIST` by its words, 421 → reconnect).
  `chmod` is `SITE CHMOD` (also after `STOR` for a new file), `utime` is `MFMT`; no symlinks. FTPS is explicit
  TLS (`AUTH TLS`, `PROT P`) checked against the system's certificates. Title `FTP:host:/path`.
- **`smb.py`** (`smb://user@host/share/path`; `smbprotocol`'s `smbclient`, the `navigator-fm[smb]` extra). **The
  first name of a path is the share**; the root lists the server's disk shares, asked once per drive over RPC
  (`_ask_shares`: `smbclient.open_file("\\\\host\\IPC$\\srvsvc", mode="r+b", buffering=0, file_type="pipe")` and
  **`dcerpc.share_enum`**, a hand-written bind + `NetrShareEnum` level 1 -- smbprotocol has no RPC, impacket is
  large), `IPC$`, printers and the `$`-special ones left out, plus the shares known (the one opened on --
  `Answers.start`'s first name -- and any reached since). Any failure (guest refused, RPC off) leaves only the
  known ones, silently. `dcerpc.py` speaks to anything with `read`/`write`, keeps what one read brought past a
  fragment (`_Fragments`), and was checked against impacket's NDR (bind byte-identical, the request so but for
  referent ids, impacket's response decoded); no Samba was at hand to try it on. Each drive has its own
  `connection_cache` and passes `username`/`password`/`port` on every call; names are UNC (`_unc`). A failure of
  the connection itself (not an `OSError`) is `DriveGone`; `LogonFailure`/`AccessDenied` on connecting is
  `NeedPassword`. No user is the guest, or Kerberos with a ticket. No chmod or owners (Windows ACLs). `smb.CLIENT`
  is the module spoken through -- a test puts a stand-in there. Title `SMB:host:/share/path`.
- **`s3.py`** (`s3://[key@]endpoint[:port]/bucket/key`, `s3+http://` for plain HTTP; boto3, one of
  Navigator's own dependencies). **No new `Site` fields**: the scheme is the transport, the host the endpoint
  (`s3.amazonaws.com` / `s3.REGION.amazonaws.com` is Amazon's -- virtual-hosted, a bucket's region learnt once from
  `head_bucket`'s `x-amz-bucket-region` and a client per region; any other host an endpoint of its own by URL,
  path-style, region `us-east-1` unless `~/.aws` says), the user who (empty: the AWS chain; a `~/.aws` profile's
  name: that profile; else an access key ID whose secret is `NeedPassword`'s, keyring first). `connect` proves the
  keys with `list_buckets` (a refused one on `answers.start`'s bucket with `head_bucket`); bad keys
  (`InvalidAccessKeyId`, `SignatureDoesNotMatch`, ...) are a wrong password. **The first name is the bucket**; the
  root lists the account's buckets plus those reached by name; F7 there makes a bucket, rmdir deletes an empty one.
  **Directories are prefixes** (`list_objects_v2`, `/` delimiter, the `dir/` marker F7 leaves skipped). Writes are a
  multipart upload as they come (`_Upload`, `PART_SIZE` 8 MiB, one `put_object` when smaller; its `__exit__`
  aborts on an exception, so Stop or a failure leaves nothing); no append. A file's rename is a managed server-side
  copy and a delete; a directory's is `EXDEV`, the copier then copying and deleting. `open_random` is ranged GETs
  (F3 by chunks). No modes, owners, links or times. Unreachable after botocore's retries is `DriveGone`.
  `make_client` is the hook a test replaces. Title `S3:endpoint:/bucket/dir`; `describe` adds `Region`.
- **Each protocol is named and has its own entry**: Utilities > *SSH link (SFTP)...* (Alt+F11, `NavyLink`), *FTP
  link...* (`FtpLink`), *SMB link (Windows share)...* (`SmbLink`), *S3 link (Amazon S3)...* (`S3Link`), each
  `Shell.navy_link(panel, scheme=)`; the
  `ConnectDialog(scheme=)` is that protocol's (`titles(scheme)`), FTP's with *Encrypt with TLS (FTPS)* (`secure`,
  the scheme then `ftps`), SMB's *Directory* captioned *Share/dir* (a share typed without `/` is made `/share`),
  S3's *Endpoint* (opening on `s3.amazonaws.com`), *Access key* and *Bucket/dir*, its `secure` box *Encrypt with
  TLS (HTTPS)* (unticked: `s3+http`); `reach()` asks S3's password as *Secret key for ...*.
  The recent list is the protocol's (`recent.recent(("ftp", "ftps"))` for FTP's box). The Link list has a *New ...
  link* per protocol (its mapping is the scheme), each greyed with its extra when missing. `sessions.PROTOCOLS`
  names them all.
- **SSH extras**: `ProxyJump` in `~/.ssh/config` (`a,b`, `user@host:port`, `ssh://` hops; `credentials.jump_site`)
  is `HostConfig.jumps`, and `_Connection.open` chains them natively: each hop logged into by `_login` (its own
  `host_config`; the first hop's own `ProxyCommand` honoured, a hop's own `ProxyJump` not followed), the next one
  reached over its `direct-tcpip` channel (`_forward`), the server last. Every hop's host key, password and
  passphrase are asked as the server's are, the question's `hop` naming it (`(host, port)`, None for the server)
  and its answer kept in `Answers.for_hop(hop)`; a jump host's password is saved to the keyring at once, the
  server's by `connect`. The hops' clients are `_Connection.chain`, closed after the server's in reverse; `_watch`
  watches only the last transport (a dying hop ends it, and the one reconnect rebuilds the chain). An explicit
  `ProxyCommand` still wins, through `paramiko.ProxyCommand`. **Keyboard-interactive** (a one-time
  code, a PIN): `Answers.interactive` -- set by `Shell.reach` (`_interactive_asker`) -- is called on the connecting
  thread with the server's prompts and waits while the loop shows a box per prompt (masked unless the server says
  echo), as a copy's worker waits for its questions; tried after a password fails or when there is nothing else to
  try. paramiko's own fallback for a second factor after a key, `auth_interactive_dumb`, reads **stdin** -- the
  screen -- so `connect` is given a `transport_factory` whose `Transport` routes it through `interactive` too.
  Cancelling a prompt is `DriveGone` ("Cancelled"), not a password box.
- **`credentials.py`** `host_config`, `fingerprint` (`SHA256:...`), `save_host_key`, `keyring_available`,
  `saved_password`/`save_password`/`forget_password` (service `navigator-fm`, account `str(site)`).
- **`profiles.py`** over `navigator/models/remote_profile/` (`remote_profiles`: name unique, scheme, host, port, user,
  path, seq). `location_of(profile)`; a path of `.` (`profiles.HOME`) opens on the server's home (`drive.home`).
  **Utilities > *Saved links*** (`EditLinks`, `Shell.edit_links`; also *Edit links...* at the foot of the *Link*
  list, `link_section`'s `EDIT_LINKS`) is `widgets/drives/links_dialog`: the profiles copied in as
  `profiles.Entry`s (`entries()`), edited -- F2/*Edit* and Ins/*Add* (a protocol menu first; *New GVfs/KIO link* asks the URI
  first, `navigator-gio` skill) in `ConnectDialog(editing=True)`, Del/*Delete* asked, Ctrl+Up/Down moved (its `LinkList` lets those keys past the
  list to the `links_dialog` key table) -- and written back on OK in one transaction (`profiles.store`: gone names
  deleted, `seq` the list's order); Cancel changes nothing; *Connect* stores, then `go_remote`s the active panel.
- **`recent.py`** over `navigator/models/recent_link/` (`recent_links`: scheme, host, user, port, path, seq; unique
  by scheme+host+user+port, the directory the last one used). The SSH link box's Host `▐↓▌` drops these as
  `choices`, not a `HistoryEntry` list: `ConnectDialog` replaces its `host.history.choose`, so a pick fills host,
  login, port and directory together. `Shell.navy_link` remembers a connection only once it worked. As long as
  Interface's *History size*.
- **`archive.py`** DN's `TArcDrive` (`ARCVIEW.PAS`): `ArchiveDrive` over `zipfile`/`tarfile` (any compression
  `tarfile.open` reads), and over **`arctool.ToolArchive`** for 7z and rar, told by signature (`arctool.kind_of`):
  7-Zip's command line (`7zz`, `7z`, `7za` -- no rar codec in `7za`; `unrar` for rar where no 7-Zip reads it),
  listed with `7z l -slt -ba` (`parse_slt`; `unrar lta`, `parse_unrar`, untried against a real unrar), each member
  read through a pipe from `7z x -so -spd --` (`-spd`: a name is never a wildcard; `_Piped` kills the tool on an
  early close and turns its exit status into `OSError`), links' targets read as their contents. Nothing bundled:
  no tool is **`NeedsTool`** (a `NotAnArchive`), which Enter says rather than running the file. A 7z is rewritten by
  `_write_7z` -- the old one unpacked once into a tree (solid blocks are whole), the index laid out over it, packed
  anew by `arctool.write_7z` (`7z a -snl`); `.7z` is in `NEW_KINDS`. A rar is read-only (`capabilities` empty on the
  instance). `_Member.packed`/`DirEntry.packed` carry the packed size (a zip's `compress_size`, 7-Zip's *Packed
  Size* -- blank for a solid block's later members; None for a tar). A place in one is `Location(Site("arc"), inner, outer=<the archive's location>)` -- `outer`
  is DN's `Prev` -- printing as `/dir/a.zip#/inner`; `Location.parse` reads that back when the name before `#/` is in
  the *archive* file type (`a.zip#//` is the root too), and so does the copy target line (`filecopy.target_location`).
  `drive_of` finds it by its `outer` (`archive.find`). `open_archive(outer, job, create=)` reads the whole index (a
  compressed tar: the whole file), fetching one on another drive first (`UseFile`; the copy goes with the drive).
  Implied directories are listed; a tar's owners are `uname:gname`; links are followed inside the archive; devices,
  FIFOs and hard links in a tar are not listed (and a rewrite drops them). Reads share one file, one at a time
  (`_Locked`). Title `ZIP:a.zip:/inner` (`get_dir`, DN's `ZIP:C:A.ZIP\INNER`). `..` is always listed; at the root
  `change_up` is `(outer.parent, outer.name)`, so the cursor lands on the archive.
- **Writing an archive is a rewrite** (DN's packers rewrote too): every step -- `open_write`, `mkdir`, `rmdir`,
  `unlink`, `rename`/`replace`, `symlink`, `chmod`, `utime` -- changes the in-memory index under `_tree`, a new file's
  bytes staged in `private_dir()/archive/<pid>/`; **`Drive.finish()`** (a no-op elsewhere) writes the whole archive
  anew beside it (`.name.XXXX`), each zip member keeping its compression, a tar its compression (`_compression_of`,
  by magic bytes) and owners, then `os.replace`s it over, re-reads it, and for a fetched one uploads it back.
  **Whoever makes the steps calls `finish` once at the end**: the copier and eraser (`filecopy.finish_drives` over
  sources and target, also after Stop -- what went in full stays), `Manager.make_directory`/`_rename_entry`, and
  `usefile.upload` (the editor's F2). A copy whose target names an archive not open opens it, or -- named but not
  there, with a name in `NEW_KINDS` -- makes an empty one (DN's `ArchiveFiles`, packing by the target's name), and
  lets go of it after (`release_unheld`). A panel holds the archive it is in (`Panel._hold_archive`;
  `archive.hold`/`leave`), the last one out closes it on a thread (which finishes first); `Navigator.on_stop` closes
  the rest.
- **Entering**: Enter (`Panel.choose` → `_may_enter_archive`) with File Manager Setup's *Enter opens an archive*
  (`enter_opens_archive`, DN's `fmoEnterArchives`), on a file the *archive* file type names, from a panel not in an
  archive (DN opened none from inside another): `widgets/drives/archives.enter_archive` opens it under *Reading
  archive*; `NotAnArchive` (a `.zip` that is not, a `.deb`) runs it as a file instead, as `ArcViewer`
  failing fell through to `ExecFile`. The name test is a departure: DN tried every file by signature, which would
  take a `.docx` (a zip) in. Inside one, F5/F6/F8/F7/rename/F4 work as anywhere; no bookmark or quick directory is
  kept there, history skips it, and a saved desktop keeps the archive's directory with the cursor on it.
- **Extract to, Test, Shift+F2** (`ARCVIEW.PAS` `HandleCommand`/`ExtractFiles`, `FLPANELX.PAS` `cmExtractArchive`):
  Panel > *Extract to...* (`ExtractTo`, cmExtractTo) and *Test archive* (`ArcTest`, cmArcTest), enabled only in an
  archive; Files > *Extract archive...* (`ExtractArchive`, Shift+F2) only outside one, on archive-type files.
  `ExtractDialog` is `dlgExtract` (*Extract to* on the Copy history, *Extract with path names* ticked, *Test only*,
  Tree) less *Password* (zipfile knows only ZipCrypto); an empty line is the archive's own directory. Extracting is
  the copier (`Manager._extract` → `_run_copy`), the Copy dialog's session mode and options, without paths
  `CopyRequest.flatten` (`_Copier._flattened`: every file under a directory into the target). Shift+F2 opens each
  archive on a thread, extracts its root's children, then `release_unheld`. Test is **`ArchiveDrive.test(job,
  locations)`**: every member read through (zip CRCs, tar reads; 7z/rar `7z t` whole), `(path, why)` per failure,
  said in a box. **Departure, recorded**: DN put Extract/Test/Password on F4/F6/F7 of an archive panel's key bar
  (`hcArchives`); here F4 and F6 stay Edit and Rename/Move, which work in an archive.
  **Shift+F2 extracts everywhere** (a departure, asked for): outside an archive it is *Extract archive*, inside one
  `Manager.on_extract_archive` runs *Extract to...* -- so Panel > *Extract to...* shows Shift-F2 as a static key (the
  binding is `ExtractArchive`'s). The panel's right-click menu offers *Extract to...* and *Test archive* in an
  archive, and *Extract archive...* on an archive file outside one (`panel._archive_file`). **Shift+F1, File > *Copy
  to archive...*** (`ArchiveFiles`, `cmPanelArcFiles`) is F5's Copy dialog with the target a new `.zip`'s root
  (`Manager._archive_target`: named after the one entry, else the directory; in the other panel's place when it is on
  the disk, else this one's), which the copy makes and packs into -- DN asked in an archiver's own box.
- **Archive columns** (`TArcDrive.Init`'s `ColumnsDefaults.Arc`): `Panel.archive_columns`, seeded from *Column
  defaults*' *Archives* (`[column_defaults] arc_*`) each time an archive is entered (`_hold_archive`), is
  `shown_columns` in an archive; `packed` (*Packed*, `display_packed`) and `ratio` (*%*, `display_ratio`, DN's
  `Percent(Size, PSize)`, 100 for an empty file) count only there (`Panel.ARCHIVE_ONLY`) and drop before the path
  and date. Alt+K in an archive is `dlgArcParms`' boxes (`ColumnsDialog(archive=True)`); *Full* is `ALL_COLUMNS`.
- **Not done, on purpose**: a symbolic link from one drive to another (Shift+F5 across drives is `EXDEV`) -- a path
  on one drive means nothing on another, and DN had no such thing.
- **`usefile.py`** DN's `UseFile`: `fetch(origins, job)` into `private_dir()/remote/<pid>/<site-hash>/<mkdtemp>/`,
  `changed`, `conflicts` (the original changed since), `upload` (written beside as `.name.nav-XXXXXX`, chmod, `replace`
  over), `discard`, `sweep` (dead processes' directories, at start, on a thread; nothing is made just to look).
- **Loop side** `navigator/widgets/drives/`: `use_file.py` (`materialize`, `put_back` under `[remote] upload_changed`
  ask/always/never, `view_elsewhere`, `edit_elsewhere`), `connect_dialog` (`ConnectRequest`, `split_host`),
  `password_dialog` (navml `InputLine.password`: stars, nothing copied), `host_key_query` ("once"/"save"/None).
- **`Shell`**: `reach(location)` (the connect loop: progress box, then each question, retried), `go_remote(panel,
  location)`, `navy_link(panel)`, `hang_up()`, `close_linked`, `reap_connections` (Navigator's `call_every(60)`),
  `_use_panel_files`/`_open_elsewhere`/`_put_back` (Enter, F2's menu and associations on fetched copies; `run_command`
  takes `cwd=` and `uses=`, which `command_finished` offers back). `Navigator.on_stop` closes every connection.
- **`Manager`**: `link_section(menu, before=toggle)` in the bookmark box -- the bookmarks' keys act on a profile
  there (`_profile_key`): F2 edits it (`ConnectDialog(editing=True)`: saved through `profiles.replace`, never
  connected, no paramiko needed), Del removes it unasked, Ctrl+Up/Down `profiles.move` it; the box opens again
  with *Link* dropped on the same row (navml `PopupMenu(submenu=(index, current))`); with any profile there, the
  key bar says *F2 Edit*, *Del Delete*, *Ctrl+↑↓ Move* while the list is open (`SubMenu.hints`; `Up/Down` in the ASCII tier); `_go_to` connects a URL through
  `app.shell.reach`; F3/F4/Alt+F3/Alt+F4/`$PAGER`/`$EDITOR` fetch first. `EditWindow.use_set`: F2 writes the copy and
  `put_back(ask=False)`; the title names the origin; no edit record; closing discards. `FileWindow.use_set` the same.
- **Commands** `NavyLink` (Utilities > *SSH link (SFTP)...*, Alt+F11 -- DN's *Navigator Link*, renamed for its
  protocol), `HangUp` (*Disconnect*, Alt+H; greyed with
  nothing mounted), `SetupLink` (Options > Configuration > *Communications...* → `CommunicationsPage`, `[remote]`
  keepalive, timeout, idle_disconnect, upload_changed).
- **Start and desktop**: `nav sftp://host/dir` opens that side on the disk and `go_remote`s it in `on_start`; a saved
  desktop keeps the URL plus `"local"` (the anchor) and reconnects the same way.

## Departures (each recorded where it is made)

- **The protocol is always named.** DN's single *Navigator Link* becomes *SSH link (SFTP)*; the boxes say
  `{protocol}` (`sessions.protocol_name`, ``SFTP (SSH)``) and a panel's title starts with the sign
  (`sessions.protocol_sign`, ``SFTP:host:/path``, as DN's said ``LINK:``). A new protocol adds its pair to
  `sessions.PROTOCOLS` and its own menu entry.

- Remote edit uploads back (DN's `TLinkDrive.UseFile` refused to edit across the cable).
- *Auto refresh* is local only: no watch on a remote directory (`Drive.watch` answers a `Watch` that never calls).
- Enter on a remote executable opens it as a file: nothing there can be run from here.
- URLs stand where DN wrote `LINK:C:\...`; the title is `SFTP:host:/path` (`SftpDrive.get_dir`).
- The prompt names the remote place while commands still run in the last local directory.
- *Communications* holds connection settings, not a modem's.

- **GVfs and KIO schemes** (mtp, dav, afp, google-drive...; webdav, fish, gdrive, kdeconnect...) are not in `SCHEMES`
  but reached through `sessions.module_name`: `navigator/lib/drives/gvfs.py` mounts with `gio`, `navigator/lib/drives/kio.py`
  through kio-fuse, and both work on the FUSE path (`navigator-gio`, `navigator-kio` skills). A scheme both reach
  (`mtp`, `afc`, `nfs`) goes to the backend in use. Test a connection's kind with `sessions.is_connection`, never `in SCHEMES`.

## Adding a protocol

1. A module with `available() -> str | None` (the extra that is missing) and `connect(site, answers) -> Drive`; add it
   to `sessions.SCHEMES` and `EXTRA_HINT`, and an extra in `pyproject.toml` (plus `suggests` in `nfpm.yaml` if it is
   compiled).
2. A `Drive` subclass: at least `scan`, `stat`, `lstat`, `children`, `names`, `open_read`; `open_write`, `mkdir`,
   `rmdir`, `unlink`, `rename`, `replace` for `write`/`rename`. Raise `OSError` with errno; `DriveGone` when the link is
   dead, after calling `on_lost`. Set `capabilities` honestly -- the menus follow them.
3. The Connect dialog's protocol (only SFTP has a field today) and `split_host`'s defaults.
4. A server fixture in `tests/` (as `tests/sftp_server.py`), `pytest.importorskip` for the extra.

## Tests

- `tests/test_drives.py`: `Location`, the in-memory drive through the copier and eraser, a `Panel` on it (call
  `panel.mounted()` for its effects, then `settle()`), and the whole file manager over it (`desk` fixture: F5, F8, F3,
  F4+F2, greying). `UseFile` round trip.
- `tests/test_archives.py`: zip and tar.gz built in the test, the drive, copying out, the panel in and out, an
  archive on the in-memory drive, Extract to / Test / Shift+F2, the archive columns. `tests/test_arctool.py`: the
  7-Zip and unrar listings parsed from captured output (everywhere), and a real 7z entered, written, made and
  tested -- skipped without 7-Zip (the official `7zz` tarball unpacked onto `PATH` is enough).
  `tests/test_dcerpc.py`: `NetrShareEnum` against a pipe answering in fragments; `tests/test_smb.py` puts that pipe
  behind its stand-in `smbclient`. `tests/test_s3.py` (skipped without moto) runs moto's
  `ThreadedMotoServer` once per module and reaches it as an endpoint of its own over `s3+http` (path-style, as a
  MinIO); moto checks no keys, so a refused secret is a stand-in client (`s3.make_client`).
- `tests/test_ftp.py` (skipped without pyftpdlib) against `tests/ftp_server.py` run **as a process of its own**
  (pyftpdlib's timers are per process: two servers in one trip over each other), with an MLSD and a LIST-only
  server (`[mlsd]`/`[list]`); `drop()` kills and restarts it on its port. `tests/test_smb.py` puts a stand-in
  `smbclient` over a local directory into `smb.CLIENT` -- no SMB server is written in Python.
- `tests/test_sftp.py` (skipped without paramiko) against `tests/sftp_server.py`, paramiko's own server on
  `127.0.0.1:0` rooted in a temp directory, password `secret`. The `isolated` fixture points `HOME` at a temp
  directory, drops `SSH_AUTH_SOCK` and turns the keyring off, so nothing of the user's `~/.ssh` or keyring is read or
  written. `SftpServer.drop()` cuts connections; `stop()` shuts the listener (a bare `close()` leaves `accept()`
  listening).
