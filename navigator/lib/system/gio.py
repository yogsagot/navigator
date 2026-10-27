"""The desktop's GIO, through its ``gio`` command.

Not DOS Navigator's: DOS had no desktop to ask.  Where GLib's ``gio`` is
installed -- every GNOME, Cinnamon, MATE and Xfce system, most others -- it
does four things Navigator would otherwise not:

* **Volumes** (:func:`volumes`, :func:`mount_device`, :func:`unmount`,
  :func:`eject`): what udisks and GVfs know of, mounted or not, and
  mounting one without root, as the desktop's file manager does.
* **The desktop's applications** (:func:`open_file`, :func:`applications`,
  :func:`launch`): what a file opens in, by its MIME type.
* **GVfs** (:func:`gvfs_schemes`, :func:`mount_uri`, :func:`local_path`):
  phones over MTP, WebDAV, AFP, Google Drive, NFS..., each reached through
  the FUSE bridge under ``/run/user/$UID/gvfs`` once mounted
  (:mod:`navigator.lib.drives.gvfs`).
* **``gio trash``** (:func:`trash`): where the freedesktop Trash of
  :mod:`navigator.lib.file_ops.trash` finds no trash directory.

The command rather than GLib itself, since PyGObject is compiled and
Navigator's every dependency is pure Python -- as archives drive 7-Zip's.
``[system] use_gio`` off, or no ``gio`` on ``PATH``, and :func:`program` is
None and all of it is greyed out.  Every call but :func:`program` and
:func:`graphical` blocks: a thread runs it.
"""

from __future__ import annotations

import errno
import os
import re
import selectors
import shutil
import subprocess
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

#: How long a quick question to ``gio`` may take.
TIMEOUT = 15.0
#: How long mounting may take, a password's prompt included.
MOUNT_TIMEOUT = 60.0

#: What says there is no ``gio`` to ask.
NO_GIO = "The gio command (GLib) is not installed"

#: The URI schemes GVfs reaches that Navigator does not itself, and the
#: backend's ``*.mount`` file each needs.  Written out, since a backend's
#: ``Type=`` names its mount types (``smb-share``, ``afp-server``), not the
#: schemes it is reached by; the desktop's plumbing (``computer://``,
#: ``network://``, ``recent://``...) and the schemes Navigator speaks
#: (sftp, ftp, smb, trash) are left out.
GVFS_SCHEMES: dict[str, str] = {
    "mtp": "mtp", "gphoto2": "gphoto2", "afc": "afc", "dav": "dav", "davs": "dav",
    "afp": "afp", "nfs": "nfs", "google-drive": "google", "onedrive": "onedrive", "cdda": "cdda",
}


def program(which: Callable[[str], str | None] | None = None) -> str | None:
    """The ``gio`` to run, or None: not installed, or ``[system] use_gio`` off.

    ``shutil.which`` is looked up at the call, as :mod:`printing` does, so
    that replacing it in a test reaches here.
    """
    from navigator.settings import SETTINGS

    if not SETTINGS.system.use_gio:
        return None
    return (which or shutil.which)("gio")


def graphical() -> bool:
    """Whether there is a display for a desktop application to open on."""
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def _reason(text: str, fallback: str) -> str:
    """``gio``'s own words: its last line, less the ``gio: `` and the URI it names."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return fallback
    last = lines[-1]
    if last.startswith("gio: "):
        last = last[5:]
    # ``gio: file:///x: Error mounting...``: the URI is the caller's to say.
    match = re.match(r"^[a-z][a-z0-9+.-]*://\S*?: (.*)$", last)
    return match.group(1) if match else last


def run(*args: str, timeout: float = TIMEOUT) -> str:
    """``gio *args*``'s output; ``OSError`` with its reason when it fails."""
    gio = program()
    if gio is None:
        raise OSError(errno.ENOENT, NO_GIO)
    try:
        result = subprocess.run([gio, *args], capture_output=True, stdin=subprocess.DEVNULL, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise OSError(errno.ETIMEDOUT, f"gio {args[0]} did not answer") from None
    out = result.stdout.decode("utf-8", "replace")
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", "replace")
        raise OSError(errno.EIO, _reason(err or out, f"gio {args[0]} failed ({result.returncode})"))
    return out


def launch_detached(argv: list[str]) -> None:
    """*argv* started on its own, its output nowhere: a desktop application,
    which outlives the command that asked for it and must not paint over
    Navigator's screen."""
    subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)


# -- applications -------------------------------------------------------------------


@dataclass(frozen=True)
class App:
    """A desktop application: its ``.desktop`` file's id, name and path."""

    id: str
    name: str
    path: Path | None


def open_file(path: Path | str) -> None:
    """*path* opened in the desktop's default application for its type.

    ``gio open`` returns once the application has been asked, so it is run
    to its end -- its error is the user's to see -- and not detached.
    """
    run("open", "--", str(path), timeout=TIMEOUT)


def content_type(path: Path | str) -> str:
    """*path*'s MIME type as the desktop sees it; ``""`` when it says none."""
    out = run("info", "-a", "standard::content-type", "--", str(path))
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("standard::content-type:"):
            return line.split(":", 3)[-1].strip()
    return ""


def application_dirs() -> list[Path]:
    """Where ``.desktop`` files are, the user's first: the XDG data directories' ``applications/``."""
    home = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    others = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share"
    return [Path(each) / "applications" for each in [home, *others.split(":")] if each]


def desktop_file(app_id: str, dirs: Iterable[Path] | None = None) -> Path | None:
    """Where the ``.desktop`` file *app_id* is: ``a-b.desktop`` may be ``a/b.desktop``."""
    candidates = [app_id]
    stem = app_id.removesuffix(".desktop")
    if "-" in stem:
        candidates.append(stem.replace("-", "/") + ".desktop")
    for directory in application_dirs() if dirs is None else dirs:
        for candidate in candidates:
            path = directory / candidate
            if path.is_file():
                return path
    return None


def desktop_name(path: Path) -> str:
    """The ``Name=`` of a ``.desktop`` file's ``[Desktop Entry]``; ``""`` if none."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    in_entry = False
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("["):
            in_entry = line == "[Desktop Entry]"
        elif in_entry and line.startswith("Name="):
            return line[5:].strip()
    return ""


def parse_mime(text: str) -> list[str]:
    """The application ids ``gio mime TYPE`` names: the default, then the
    registered and the recommended, each once."""
    found: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        match = re.match(r"^Default application for .*: (\S+\.desktop)$", stripped)
        if match:
            found.append(match.group(1))
        elif line.startswith(("\t", " ")) and stripped.endswith(".desktop"):
            found.append(stripped)
    return list(dict.fromkeys(found))


def applications(mime: str, dirs: Iterable[Path] | None = None) -> list[App]:
    """The applications that open *mime*, the default first, by their names."""
    if not mime:
        return []
    dirs = list(application_dirs() if dirs is None else dirs)
    found = []
    for app_id in parse_mime(run("mime", mime)):
        path = desktop_file(app_id, dirs)
        name = desktop_name(path) if path is not None else ""
        found.append(App(app_id, name or app_id.removesuffix(".desktop"), path))
    return found


def launch(app: App, path: Path | str) -> None:
    """*path* opened in *app*: ``gio launch``, detached -- it waits for nothing."""
    gio = program()
    if gio is None:
        raise OSError(errno.ENOENT, NO_GIO)
    if app.path is None:
        raise OSError(errno.ENOENT, f"No desktop file for {app.id}")
    launch_detached([gio, "launch", str(app.path), str(path)])


# -- volumes --------------------------------------------------------------------------


@dataclass(frozen=True)
class GioVolume:
    """A volume or a mount ``gio mount -li`` knows of.

    *mounted* with *uri* where it is mounted; *device* (``/dev/sdb2``) or
    *uuid* is what :func:`mount_device` is given, *activation_root* what
    a volume with neither (a phone) is mounted through.
    """

    name: str
    device: str = ""
    uuid: str = ""
    activation_root: str = ""
    uri: str = ""
    can_mount: bool = False
    can_unmount: bool = False
    can_eject: bool = False

    @property
    def mounted(self) -> bool:
        return bool(self.uri)

    @property
    def ident(self) -> str:
        """What :func:`mount_device` mounts it by."""
        return self.device or self.uuid

    @property
    def local(self) -> str:
        """Its mount point, when *uri* is a ``file://`` one; else ``""``."""
        return file_path(self.uri)


def file_path(uri: str) -> str:
    """The local path a ``file://`` *uri* names; ``""`` for any other."""
    if not uri.startswith("file://"):
        return ""
    return unquote(urlsplit(uri).path) or "/"


_HEADER = re.compile(r"^(\s*)(Drive|Volume|Mount)\(\d+\): ?(.*)$")
_FLAG = re.compile(r"^\s*([a-z_]+)=(.*)$")
_ID = re.compile(r"^\s*([a-z-]+): '(.*)'$")


def parse_mount_list(text: str) -> list[GioVolume]:
    """Every volume and every mount without one, from ``gio mount -li``'s *text*.

    The output is a tree by indentation: drives, their volumes, their
    mounts.  A volume's mount gives it its URI and *can_unmount*; a mount
    with no volume above it (a GVfs one, a phone, a share) is listed on its
    own.  Drives are not listed: a drive is no place, its volumes are.
    """
    found: list[GioVolume] = []
    #: The open headers: ``(indent, kind, fields)``.
    stack: list[tuple[int, str, dict[str, str]]] = []

    def close(below: int) -> None:
        while stack and stack[-1][0] >= below:
            indent, kind, fields = stack.pop()
            parent = stack[-1] if stack else None
            if kind == "Mount":
                name, _, uri = fields["title"].rpartition(" -> ")
                fields["uri"] = uri
                fields["name"] = name or uri
                if parent is not None and parent[1] == "Volume":
                    parent[2]["uri"] = uri
                    parent[2]["can_unmount"] = fields.get("can_unmount", "0")
                    if fields.get("can_eject") == "1":
                        parent[2]["can_eject"] = "1"
                    continue
                found.append(_volume(fields))
            elif kind == "Volume":
                fields["name"] = fields["title"]
                found.append(_volume(fields))

    for line in text.splitlines():
        if not line.strip():
            continue
        header = _HEADER.match(line)
        if header:
            indent = len(header.group(1))
            close(indent)
            stack.append((indent, header.group(2), {"title": header.group(3).strip()}))
            continue
        if not stack:
            continue
        fields = stack[-1][2]
        ident = _ID.match(line)
        if ident:
            fields.setdefault(f"id:{ident.group(1)}", ident.group(2))
            continue
        flag = _FLAG.match(line)
        if flag:
            fields.setdefault(flag.group(1), flag.group(2).strip())
    close(0)
    return found


def _volume(fields: dict[str, str]) -> GioVolume:
    return GioVolume(
        name=fields.get("name", ""),
        device=fields.get("id:unix-device", ""),
        uuid=fields.get("id:uuid", "") or fields.get("uuid", ""),
        activation_root=fields.get("activation_root", ""),
        uri=fields.get("uri", ""),
        can_mount=fields.get("can_mount") == "1",
        can_unmount=fields.get("can_unmount") == "1",
        can_eject=fields.get("can_eject") == "1",
    )


def volumes() -> list[GioVolume]:
    """What ``gio mount -li`` lists now."""
    return parse_mount_list(run("mount", "-li"))


def mount_device(volume: GioVolume) -> None:
    """*volume* mounted: by its device or UUID, else through its activation root."""
    if volume.ident:
        run("mount", "-d", volume.ident, timeout=MOUNT_TIMEOUT)
    elif volume.activation_root:
        mount_uri(volume.activation_root)
    else:
        raise OSError(errno.EINVAL, f"{volume.name} cannot be mounted")


def unmount(where: str) -> None:
    """The mount at *where* (a URI, or a mount point) unmounted."""
    run("mount", "-u", "--", where, timeout=MOUNT_TIMEOUT)


def eject(where: str) -> None:
    """The mount at *where* unmounted and its medium ejected, or its drive made safe to remove."""
    run("mount", "-e", "--", where, timeout=MOUNT_TIMEOUT)


# -- GVfs ---------------------------------------------------------------------------


def mount_dirs() -> list[Path]:
    """Where GVfs keeps its ``*.mount`` files: one per backend it has."""
    others = os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share"
    return [Path(each) / "gvfs" / "mounts" for each in others.split(":") if each]


def gvfs_schemes(dirs: Iterable[Path] | None = None) -> tuple[str, ...]:
    """Those of :data:`GVFS_SCHEMES` whose backend is installed: its ``*.mount`` file is there."""
    dirs = list(mount_dirs() if dirs is None else dirs)
    return tuple(scheme for scheme, backend in GVFS_SCHEMES.items()
                 if any((directory / f"{backend}.mount").is_file() for directory in dirs))


def info(where: str) -> dict[str, str]:
    """``gio info``'s header lines for *where*: ``uri``, ``local path``..."""
    out = run("info", "-a", "standard::type", "--", where)
    found = {}
    for line in out.splitlines():
        if line.startswith((" ", "\t")) or ": " not in line:
            continue
        key, _, value = line.partition(": ")
        found[key.strip()] = value.strip()
    return found


def local_path(uri: str) -> Path | None:
    """Where *uri* is on the disk -- a GVfs mount's FUSE path -- or None:
    not mounted, or no FUSE bridge running."""
    try:
        found = info(uri).get("local path", "")
    except OSError:
        return None
    return Path(found) if found else None


def uri_of(path: Path | str) -> str:
    """The URI GIO gives *path*: under the FUSE bridge, the GVfs one."""
    return info(str(path)).get("uri", "")


class Prompted(Exception):
    """``gio mount`` asked something no answer was given for -- or asked for
    the password *again*, the one given being wrong.

    *what* is the prompt, less its default and colon: ``User``,
    ``Password``; *message* what it said before its first.
    """

    def __init__(self, what: str, message: str, *, again: bool = False) -> None:
        super().__init__(f"gio mount asks for {what}")
        self.what, self.message, self.again = what, message, again


_PROMPT = re.compile(r"(?:^|\n)([^\n]*?)(?: \[[^\n]*\])?: $")


def mount_uri(uri: str, answers: dict[str, str] | None = None, *, anonymous: bool = False,
              timeout: float = MOUNT_TIMEOUT) -> None:
    """*uri* mounted through GVfs, answering ``gio mount``'s prompts from
    *answers* (``{"User": ..., "Domain": ..., "Password": ...}``).

    A prompt with no answer -- or a second ``Password``, GVfs asking again
    after a wrong one -- stops it and raises :class:`Prompted`, for the
    caller to ask the user and try again; a mount there already is no
    error.  ``OSError`` with ``gio``'s reason for anything else.
    """
    gio = program()
    if gio is None:
        raise OSError(errno.ENOENT, NO_GIO)
    answers = dict(answers or {})
    argv = [gio, "mount", *(["-a"] if anonymous else []), "--", uri]
    process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               start_new_session=True)
    assert process.stdin and process.stdout and process.stderr
    out, err = b"", b""
    message = ""
    asked: dict[str, int] = {}
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "out")
    selector.register(process.stderr, selectors.EVENT_READ, "err")
    deadline = time.monotonic() + timeout
    open_streams = 2
    try:
        while open_streams:
            left = deadline - time.monotonic()
            if left <= 0:
                raise OSError(errno.ETIMEDOUT, f"Mounting {uri} did not finish")
            for key, _ in selector.select(left):
                chunk = os.read(key.fileobj.fileno(), 4096)  # type: ignore[union-attr]
                if not chunk:
                    selector.unregister(key.fileobj)
                    open_streams -= 1
                    continue
                if key.data == "err":
                    err += chunk
                    continue
                out += chunk
                text = out.decode("utf-8", "replace")
                prompt = _PROMPT.search(text)
                if prompt is None:
                    continue
                what = prompt.group(1).strip()
                # What it said before its first prompt: why it asks.
                message = message or text[:prompt.start(1)].strip()
                asked[what] = asked.get(what, 0) + 1
                answer = answers.get(what)
                # A second ``Password``: the first was wrong.  Anything else
                # is asked again with it, and answered the same.
                if answer is None or (what == "Password" and asked[what] > 1):
                    raise Prompted(what, message, again=asked[what] > 1)
                process.stdin.write(answer.encode("utf-8") + b"\n")
                process.stdin.flush()
                out = b""
        code = process.wait(max(0.1, deadline - time.monotonic()))
    except BaseException:
        process.kill()
        process.wait()
        raise
    finally:
        selector.close()
        for stream in (process.stdin, process.stdout, process.stderr):
            try:
                stream.close()
            except OSError:
                pass
    if code != 0:
        reason = _reason(err.decode("utf-8", "replace"), f"gio mount failed ({code})")
        if "already mounted" in reason.lower():
            return
        raise OSError(errno.EIO, reason)


def trash(path: Path | str) -> None:
    """*path* moved to the trash GIO finds for it: ``gio trash``."""
    run("trash", "--", str(path), timeout=MOUNT_TIMEOUT)


__all__ = [
    "App", "GVFS_SCHEMES", "GioVolume", "NO_GIO", "Prompted", "applications", "content_type", "eject", "file_path",
    "graphical", "gvfs_schemes", "launch", "local_path", "mount_device", "mount_uri", "open_file",
    "parse_mime", "parse_mount_list", "program", "run", "trash", "unmount", "uri_of", "volumes",
]
