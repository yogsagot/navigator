---
name: navigator-kio
description: KDE's KIO and Solid through their commands -- navigator/lib/system/kio.py (COMMANDS with KF6/KF5 names, program()/command(), run() and _reason, open_file via kioclient exec, content_type via kmimetypefinder, applications via ktraderclient6 and parse_trader, launch via kstart, KioVolume and parse_solid/parse_devices for solid-hardware6 list details, mount_device/unmount/eject by UDI, KIO_SCHEMES/kio_schemes/plugin_dirs, HOSTLESS/kio_url, kio-fuse's mountUrl/remoteUrl over dbus-send and parse_reply, trash via kioclient move), KIO drives (navigator/lib/drives/kio.py: KioDrive over kio-fuse, root_of, with_password, NeedPassword from an authentication refusal), and how [system] desktop_vfs picks it over GIO (navigator/lib/system/desktop.py). Use when touching any of these, or when something works under GNOME but not under KDE.
---

# KIO (KDE's commands)

**Not DOS Navigator's**, and the KDE counterpart of `navigator-gio`: the same four features -- volumes, the desktop's
applications, links through a FUSE bridge, the trash's fallback -- through KDE Frameworks' **command-line tools**,
not the libraries (compiled). `navigator/lib/system/kio.py` is the one module that runs them; callers reach it only
through `navigator/lib/system/desktop.py` (`navigator-gio` skill has the facade and `[system] desktop_vfs`).

## Rules

- **One backend a session.** `desktop.backend()` is `kio` when `desktop_vfs = kio`, or `auto` under a KDE session
  (`$XDG_CURRENT_DESKTOP` contains `KDE`) with `kioclient` installed, or `auto` with no `gio` at all.
- **`kio.program()` is `kioclient`**; the other commands are looked up per call with `kio.command(name)`, which tries
  `COMMANDS[name]` in order (KF6 first, then KF5's `…5` names). A missing one is an `OSError` naming it, said in the
  caller's box. `shutil.which` is looked up at the call, so tests replace it.
- **Every call blocks** (`asyncio.to_thread`, a `Background` or a `Job`): `TIMEOUT` 15 s, `MOUNT_TIMEOUT` 60 s.
- **A failure is `OSError` carrying the tool's own words** (`_reason`: last stderr line, less `kioclient: ` and
  dbus-send's `Error org.….Failed: `).
- **`kioclient` runs with `--noninteractive`**, so its errors reach stderr rather than a KDE message box.
- **The suite runs with `desktop_vfs` off**; `tests/test_kio.py` sets it to `kio` (autouse) and installs one fake
  script under every KDE name on a temporary `PATH`.

## The commands

| Feature | Call | Command |
|---|---|---|
| open | `open_file(path)` | `kioclient --noninteractive exec PATH` (run to its end, not detached) |
| type | `content_type(path)` | `kmimetypefinder PATH` (first word of the last line, needs a `/`) |
| apps | `applications(mime)` | `ktraderclient6 --mimetype M --servicetype Application` → `parse_trader` |
| launch | `launch(app, path)` | `kstart --application DESKTOP --url PATH` (`kstart5 --service …`), detached |
| volumes | `volumes()` | `solid-hardware6 list details` → `parse_solid` |
| mount etc. | `mount_device(v)`, `unmount(w)`, `eject(w)` | `solid-hardware6 mount\|unmount\|eject UDI` |
| links | `mount_url(uri)`, `remote_url(path)` | `dbus-send --session --print-reply --dest=org.kde.KIOFuse /org/kde/KIOFuse org.kde.KIOFuse.VFS.mountUrl string:URL` |
| trash | `trash(path)` | `kioclient --noninteractive move PATH trash:/` |

- `parse_trader`: offers start at `---- Offer N ----`; `Key : 'value'` lines; the id is `DesktopEntryPath`'s file name,
  else `DesktopEntryName.desktop`; each id once, in KDE's order (the user's preferred first). Names fall back to the
  `.desktop` file's `Name=` (`desktop_entry.desktop_name`).
- `parse_devices`: a device starts at `udi = '…'` in column 0; indented `Key = value  (type)` lines, the trailing
  `(…)` groups stripped and quotes removed. `parse_solid` keeps `StorageVolume.usage = 'FileSystem'` not `ignored`:
  - `local` = `StorageAccess.filePath` when `accessible`; `can_mount` = has StorageAccess and is not accessible;
  - `can_eject` = an `OpticalDisc.*` property, or a `StorageDrive.removable`/`hotpluggable` up the `parent` chain;
  - `can_unmount` = mounted and (ejectable or under `/media/`, `/run/media/`, `/mnt/`) -- `/` and `/home` offer none.
  - `target` is the UDI; `unmount`/`eject` also take a mount point, mapped back through a fresh list.

## KIO drives (`navigator/lib/drives/kio.py`)

- **Schemes**: `KIO_SCHEMES` maps each scheme KIO reaches but Navigator does not (mtp, afc, webdav, webdavs, fish,
  gdrive, nfs, kdeconnect) to its worker plugin's file name (`webdav` is `http.so`). `kio_schemes()` keeps those
  found under `<qt plugins>/kf6/kio/` or `kf5/kio/` (`$QT_PLUGIN_PATH`, `/usr/lib*/qt6/plugins`...).
- **Routing** (`sessions.module_name`): a KIO-only scheme always goes to `sessions.KIO`; one both reach goes to the
  backend in use. `kio.available()` is `NO_KIO` or `NOT_IN_USE` (the backend is not kio).
- **`HOSTLESS`** (`mtp`, `gdrive`): KIO writes `mtp:/Phone/Storage`; Navigator keeps GVfs's `mtp://Phone/Storage`
  (host case kept, `location._host`) and `kio_url` turns it round for kio-fuse.
- **`connect`**: `mount_url(uri of the start)` gives the FUSE path. kio-fuse mirrors the URL's path under it, so
  `root_of` takes the start's names off the end: the root, prefix `/`. If they do not match, the path stands for the start.
- **Passwords**: kio-fuse has no prompt protocol. KIO shows its own password window where there is a display. A
  refusal matching `_AUTH` (authentication, password, 401...) raises `NeedPassword` (`wrong` once one was given).
  The box's password then goes into the URL (`with_password`). `can_keep` stays false.
- **`KioDrive`** is `GvfsDrive` with `describe()` saying `KIO` and a `close()` that does nothing: kio-fuse has no
  call to let one URL go (it drops idle ones itself). A departure from GVfs's `gio mount -u`.
- **Ways in**: the same as GVfs's -- `nav webdav://host/`, Utilities > *GVfs/KIO link* (`GvfsLink`; the box is titled
  *GVfs/KIO link* either way, and its caption's examples and refusal list `KIO_SCHEMES` when the backend is kio,
  `desktop.link_name()`), the Alt+F1/F2 *New GVfs/KIO link*.

## Not checked on a real KDE

Written against the KF sources' formats; the canned text in `tests/test_kio.py` stands for them. Check these on a
Plasma install and correct both the parser and the canned text if they differ:

- `solid-hardware6 list details`'s layout;
- `ktraderclient6`'s offer lines;
- `kstart`'s `--application`/`--url`;
- the layout of kio-fuse's mount directory for hostless schemes;
- the words of its authentication errors.
