"""File > Checksums: the tagged files' digests written to a list, and checked
against one -- **a departure, asked for**: DOS Navigator had no checksums.

The lists are GNU coreutils' ``*sum`` files, so ``sha256sum -c`` checks what
Calculate wrote and Verify checks what ``sha256sum`` wrote: one line per file,
the digest in hex, two spaces (text mode) and the name -- relative to the
list's own directory -- and, for a name holding a backslash, a newline or a
carriage return, a ``\\`` before the line with those escaped in the name.
Reading also takes the ``*`` of binary mode, which on POSIX means nothing, and
BSD's ``SHA256 (name) = digest`` (``--tag``).

Which algorithm a list is in is told by its name -- ``.sha256sum``, ``.sha256``,
``SHA256SUMS`` -- and, for a name that does not tell, by its first digest's
length.  128 hex digits are SHA-512 or BLAKE2b's 512 bits alike; without a
name saying ``b2`` they are taken for SHA-512, the more common of the two.

Every read goes through the file's drive (:mod:`navigator.lib.drives`), so a
list is made or checked as well on a server or in an archive as on the disk;
nothing here may run on the loop.
"""

from __future__ import annotations

import hashlib
import stat
from dataclasses import dataclass, field
from posixpath import normpath
from typing import Any, Iterable

from navigator.lib.drives import Location, drive_of
from navigator.lib.system.job import Job, Stopped

ALGORITHMS = ("md5", "sha1", "sha256", "sha512", "blake2b")

#: What Calculate names a list in each algorithm: coreutils' own commands.
EXTENSIONS = {"md5": ".md5sum", "sha1": ".sha1sum", "sha256": ".sha256sum", "sha512": ".sha512sum",
              "blake2b": ".b2sum"}

#: Every name ending Verify takes for a list, and the algorithm it means.
SUFFIXES = {**{ext: alg for alg, ext in EXTENSIONS.items()},
            ".md5": "md5", ".sha1": "sha1", ".sha256": "sha256", ".sha512": "sha512", ".b2": "blake2b"}

#: The whole names release directories give their lists.
WHOLE_NAMES = {"md5sums": "md5", "sha1sums": "sha1", "sha256sums": "sha256", "sha512sums": "sha512",
               "b2sums": "blake2b"}

#: A digest's length in hex, for a list whose name does not tell.
DIGEST_HEX = {32: "md5", 40: "sha1", 64: "sha256", 128: "sha512"}

#: BSD's tag names (``--tag``), and coreutils' for BLAKE2b.
TAGS = {"MD5": "md5", "SHA1": "sha1", "SHA256": "sha256", "SHA512": "sha512", "BLAKE2B": "blake2b"}

CHUNK = 1 << 20

#: The reason a list with no checksum line in it gives, translated where it is shown.
NO_CHECKSUMS = "no checksums in it"


def new_hash(algorithm: str) -> Any:
    return hashlib.blake2b() if algorithm == "blake2b" else hashlib.new(algorithm)


def _suffix(name: str) -> str | None:
    lower = name.lower()
    for suffix in sorted(SUFFIXES, key=len, reverse=True):
        if lower.endswith(suffix) and len(lower) > len(suffix):
            return suffix
    return None


def algorithm_of(name: str, first_digest: str | None = None) -> str | None:
    """The algorithm a list named *name* is in: by its name, else by
    *first_digest*'s length; None when neither tells."""
    suffix = _suffix(name)
    if suffix is not None:
        return SUFFIXES[suffix]
    if name.lower() in WHOLE_NAMES:
        return WHOLE_NAMES[name.lower()]
    if first_digest is not None:
        return DIGEST_HEX.get(len(first_digest))
    return None


def is_list_name(name: str) -> bool:
    """Whether *name* says it is a checksum list."""
    return algorithm_of(name) is not None


def with_extension(name: str, algorithm: str) -> str:
    """*name* ending in *algorithm*'s extension, in place of any list
    extension it had."""
    suffix = _suffix(name)
    if suffix is not None:
        name = name[:-len(suffix)]
    return name + EXTENSIONS[algorithm]


def default_list_name(directory_name: str, algorithm: str) -> str:
    """The combined list's name for a directory: after it, as release
    directories are -- ``checksums`` at the root, which has no name."""
    return (directory_name or "checksums") + EXTENSIONS[algorithm]


def _escape(name: str) -> str:
    return name.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r")


def _unescape(text: str) -> str | None:
    out: list[str] = []
    at = 0
    while at < len(text):
        char = text[at]
        if char == "\\":
            following = text[at + 1:at + 2]
            if following not in ("\\", "n", "r"):
                return None
            out.append({"\\": "\\", "n": "\n", "r": "\r"}[following])
            at += 2
        else:
            out.append(char)
            at += 1
    return "".join(out)


def format_line(digest: str, name: str) -> str:
    """One list line, as ``sha256sum`` writes it, without its newline."""
    if any(char in name for char in "\\\n\r"):
        return f"\\{digest}  {_escape(name)}"
    return f"{digest}  {name}"


def _is_hex(text: str) -> bool:
    return bool(text) and all(char in "0123456789abcdefABCDEF" for char in text)


def parse_line(text: str) -> tuple[str, str, str | None] | None:
    """*text*'s digest (lower case), name, and the algorithm a BSD line
    names (None for coreutils' form); None for a line that is neither."""
    escaped = text.startswith("\\")
    if escaped:
        text = text[1:]
    digest, space, rest = text.partition(" ")
    if space and _is_hex(digest) and rest[:1] in (" ", "*"):
        name: str | None = rest[1:]
        algorithm = None
    else:
        # BSD's ``TAG (name) = digest``; a tag is never hex, so no line is both.
        tag, opening, rest = text.partition(" (")
        name, closing, digest = rest.rpartition(") = ")
        algorithm = TAGS.get(tag.upper().split("-")[0])
        if not opening or not closing or algorithm is None or not _is_hex(digest):
            return None
    if escaped and name is not None:
        name = _unescape(name)
    if not name:
        return None
    return digest.lower(), name, algorithm


def parse(text: str) -> tuple[list[tuple[str, str, str | None]], int]:
    """A list's lines parsed, and how many were not lines of one; empty lines
    and ``#`` comments are neither."""
    entries: list[tuple[str, str, str | None]] = []
    malformed = 0
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parsed = parse_line(line)
        if parsed is None:
            malformed += 1
        else:
            entries.append(parsed)
    return entries, malformed


class ChecksumJob(Job):
    """Files being hashed, as their box shows them: the one being read, the
    bytes read of them all, and how many are done."""

    def __init__(self) -> None:
        super().__init__()
        self.current = ""
        self.position = 0
        self.total = 0
        self.files_done = 0
        self.files_total = 0
        #: ``(name, reason)`` for every directory or file that could not be read.
        self.errors: list[tuple[str, str]] = []


def _reason(error: OSError) -> str:
    return error.strerror or str(error)


def relative_name(location: Location, base: Location) -> str:
    """*location* named from the directory *base*: the path beneath it, else
    the whole path on its drive, else the whole location."""
    if location.site != base.site or location.outer != base.outer:
        return str(location)
    path = normpath(str(location.path))
    under = normpath(str(base.path))
    if under == "/":
        return path.lstrip("/") or path
    if path.startswith(under + "/"):
        return path[len(under) + 1:]
    return path


def walk(sources: Iterable[Location], job: ChecksumJob,
         skip: Any = None) -> list[tuple[Location, int]]:
    """Every file *sources* name, each with its size: a file as itself, a
    directory walked to the bottom.  A link to a directory is not walked into
    -- one pointing back up would never end -- and a link to anything but a
    file is passed over; *skip* (a location) is left out too.  A directory
    that cannot be read goes in ``job.errors``."""
    files: list[tuple[Location, int]] = []

    def take(location: Location, st: Any, linked: bool) -> None:
        if linked:
            try:
                st = drive_of(location).stat(location)
            except OSError as error:
                job.errors.append((str(location), _reason(error)))
                return
        if stat.S_ISREG(st.st_mode) and not (skip is not None and skip(location)):
            files.append((location, st.st_size))
            job.files_total = len(files)
            job.total += st.st_size

    for source in sources:
        drive = drive_of(source)
        try:
            st = drive.lstat(source)
        except OSError as error:
            job.errors.append((str(source), _reason(error)))
            continue
        if not stat.S_ISDIR(st.st_mode):
            take(source, st, stat.S_ISLNK(st.st_mode))
            continue
        pending = [source]
        while pending:
            if job.stopped:
                raise Stopped
            directory = pending.pop()
            job.current = str(directory)
            try:
                children = sorted(drive_of(directory).children(directory), key=lambda child: child[0])
            except OSError as error:
                job.errors.append((str(directory), _reason(error)))
                continue
            below: list[Location] = []
            for name, child in children:
                if isinstance(child, OSError):
                    job.errors.append((str(directory / name), _reason(child)))
                elif stat.S_ISDIR(child.st_mode):
                    below.append(directory / name)
                else:
                    take(directory / name, child, stat.S_ISLNK(child.st_mode))
            pending.extend(reversed(below))
    return files


def hash_file(location: Location, algorithm: str, job: ChecksumJob) -> str:
    """*location*'s digest in hex, read through its drive."""
    digest = new_hash(algorithm)
    job.current = str(location)
    with drive_of(location).open_read(location) as handle:
        while True:
            if job.stopped:
                raise Stopped
            job.wait_while_paused()
            chunk = handle.read(CHUNK)
            if not chunk:
                break
            digest.update(chunk)
            job.position += len(chunk)
    return digest.hexdigest()


def calculate(files: list[tuple[Location, int]], algorithm: str,
              job: ChecksumJob) -> list[tuple[Location, str]]:
    """Each of *files* with its digest; one that cannot be read goes in
    ``job.errors`` instead."""
    done: list[tuple[Location, str]] = []
    for location, size in files:
        start = job.position
        try:
            done.append((location, hash_file(location, algorithm, job)))
        except OSError as error:
            job.errors.append((str(location), _reason(error)))
            job.position = start + size
        job.files_done += 1
    return done


def write_each(files: list[tuple[Location, int]], algorithm: str, job: ChecksumJob) -> list[Location]:
    """*Each file its own list*: ``name.<ext>`` beside each of *files*,
    written as soon as it is hashed, so what was done before a *Stop* stays
    done.  Returns the lists written."""
    written: list[Location] = []
    drives: dict[int, Any] = {}
    try:
        for location, size in files:
            start = job.position
            target = location.parent / (location.name + EXTENSIONS[algorithm])
            try:
                digest = hash_file(location, algorithm, job)
                drive = drive_of(target)
                drives[id(drive)] = drive
                with drive.open_write(target) as handle:
                    handle.write((format_line(digest, location.name) + "\n").encode("utf-8", "surrogateescape"))
                written.append(target)
            except OSError as error:
                job.errors.append((str(location), _reason(error)))
                job.position = start + size
            job.files_done += 1
    finally:
        for drive in drives.values():
            drive.finish()
    return written


def list_text(done: list[tuple[Location, str]], base: Location) -> list[str]:
    """The combined list's lines for *done*, its names from *base*."""
    return [format_line(digest, relative_name(location, base)) for location, digest in done]


@dataclass
class VerifyResult:
    """What Verify found: how many files matched, and every one that did not."""

    ok: int = 0
    failed: list[Location] = field(default_factory=list)
    missing: list[Location] = field(default_factory=list)
    unreadable: list[tuple[Location, str]] = field(default_factory=list)
    #: Lines that were not a list's, over every list.
    malformed: int = 0
    #: ``(list, reason)`` for a list that could not be read or told.
    lists_unreadable: list[tuple[Location, str]] = field(default_factory=list)

    @property
    def bad(self) -> int:
        return len(self.failed) + len(self.missing) + len(self.unreadable)


def resolve(name: str, listing: Location) -> Location:
    """The file *name* in the list *listing* means: from the list's
    directory, or from its drive's root for a whole path."""
    if name.startswith("/"):
        if listing.is_local:
            return Location.of(normpath(name))
        return Location(listing.site, type(listing.path)(normpath(name)), listing.outer)
    return Location(listing.site, type(listing.path)(normpath(str(listing.parent.path / name))), listing.outer)


def verify(lists: list[Location], job: ChecksumJob) -> VerifyResult:
    """Every file *lists* name hashed again and checked against its line."""
    result = VerifyResult()
    plans: list[tuple[Location, str, str]] = []
    for listing in lists:
        job.current = str(listing)
        try:
            with drive_of(listing).open_read(listing) as handle:
                text = handle.read().decode("utf-8", "surrogateescape")
        except OSError as error:
            result.lists_unreadable.append((listing, _reason(error)))
            continue
        entries, malformed = parse(text)
        result.malformed += malformed
        named = algorithm_of(listing.name, entries[0][0] if entries else None)
        if not entries:
            result.lists_unreadable.append((listing, NO_CHECKSUMS))
            continue
        for digest, name, tagged in entries:
            algorithm = tagged or named
            if algorithm is None or len(new_hash(algorithm).hexdigest()) != len(digest):
                result.malformed += 1
                continue
            plans.append((resolve(name, listing), digest, algorithm))
    job.files_total = len(plans)
    sizes: list[int] = []
    for location, _, _ in plans:
        if job.stopped:
            raise Stopped
        try:
            size = drive_of(location).stat(location).st_size
        except OSError:
            size = 0
        sizes.append(size)
        job.total += size
    for (location, digest, algorithm), size in zip(plans, sizes):
        start = job.position
        try:
            if hash_file(location, algorithm, job) == digest:
                result.ok += 1
            else:
                result.failed.append(location)
        except FileNotFoundError:
            result.missing.append(location)
        except OSError as error:
            result.unreadable.append((location, _reason(error)))
        job.position = start + size
        job.files_done += 1
    return result
