"""What Ctrl+L's *Current file* says of a Linux program: a departure, DOS
Navigator's ``TDiskInfo`` described the directory alone, and DOS had no ELF.

For an ELF file -- a program, a shared library, an object file or a core
dump -- it says which machine it is for, the libraries it needs (each one
looked for as the dynamic loader would, and flagged when it is not found)
and whether its symbols were stripped.

All of it is read here, from the file's headers, with seeks: never ``ldd``,
which on glibc may run the program it is asked about, nor ``readelf`` or
``file``, which need not be installed.  Only the libraries the file names
itself (``DT_NEEDED``) are looked for, not what they need in turn.

:func:`sniff` runs in :func:`navigator.lib.system.diskinfo.stat_file` and
gives an ELF file its MIME type, which :mod:`~navigator.lib.system.mediainfo`
reads as a program's; :func:`read` runs on the information panel's thread
after it and returns a :class:`Program` of plain fields; :func:`pairs` lays
it out on the loop, where :func:`~navkit.i18n.tr` may be read.
"""

from __future__ import annotations

import glob
import os
import re
import stat
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Callable

from navkit.i18n import tr

#: The ELF magic.
MAGIC = b"\x7fELF"

#: How much of a file :func:`sniff` reads: the header and, as a rule, its
#: program headers.
HEAD = 4096

#: The MIME types :func:`sniff` gives, as ``file --mime-type`` names them.
EXECUTABLE = "application/x-executable"
PIE = "application/x-pie-executable"
SHAREDLIB = "application/x-sharedlib"
OBJECT = "application/x-object"
CORE = "application/x-coredump"
MIMES = frozenset({EXECUTABLE, PIE, SHAREDLIB, OBJECT, CORE})

#: Every label :func:`pairs` gives, in English, for the catalogues.
LABELS = ("Program", "Interpreter", "Libraries", "Symbols")

#: ``e_machine`` names, as ``readelf`` would put them shortly.
MACHINES = {
    2: "SPARC", 3: "x86", 4: "m68k", 8: "MIPS", 15: "PA-RISC", 18: "SPARC32+", 20: "PowerPC", 21: "PowerPC64",
    22: "S/390", 40: "ARM", 42: "SuperH", 43: "SPARC V9", 50: "IA-64", 62: "x86-64", 183: "AArch64",
    243: "RISC-V", 247: "BPF", 258: "LoongArch",
}

ET_REL, ET_EXEC, ET_DYN, ET_CORE = 1, 2, 3, 4
PT_LOAD, PT_DYNAMIC, PT_INTERP = 1, 2, 3
DT_NULL, DT_NEEDED, DT_STRTAB, DT_STRSZ, DT_RPATH, DT_RUNPATH = 0, 1, 5, 10, 15, 29
DT_FLAGS_1, DF_1_PIE = 0x6FFFFFFB, 0x08000000

#: The most of the dynamic section and its strings that is read.
MOST = 1 << 20

#: A shared library's name: ``libfoo.so`` or ``libfoo.so.1.2``.
_SONAME = re.compile(r"\.so(\.\d+)*$")


@dataclass
class Program:
    """What a read of an ELF file found: plain fields, for the loop to lay
    out (:func:`pairs`)."""

    bits: int = 64
    big_endian: bool = False
    machine: int = 0
    #: ``executable``, ``pie``, ``library``, ``object`` or ``core``.
    kind: str = "executable"
    interpreter: str = ""
    #: Whether :attr:`interpreter` is there to load it.
    interpreter_found: bool = True
    #: ``(name, where it was found or None)``, in the file's order.
    needed: list[tuple[str, str | None]] = field(default_factory=list)
    #: No ``.symtab``: its symbols stripped.
    stripped: bool = False
    debug_info: bool = False
    #: Whether it has section headers at all (a core dump need not).
    sections: bool = True


@dataclass
class _Header:
    bits: int
    order: str
    type: int
    machine: int
    phoff: int
    shoff: int
    phentsize: int
    phnum: int
    shentsize: int
    shnum: int
    shstrndx: int


def _header(data: bytes) -> _Header | None:
    """The ELF header at the start of *data*; None for anything else."""
    if len(data) < 52 or not data.startswith(MAGIC) or data[4] not in (1, 2) or data[5] not in (1, 2):
        return None
    bits = 64 if data[4] == 2 else 32
    order = "<" if data[5] == 1 else ">"
    layout = "HHIQQQIHHHHHH" if bits == 64 else "HHIIIIIHHHHHH"
    size = struct.calcsize(order + layout)
    if len(data) < 16 + size:
        return None
    (type_, machine, _version, _entry, phoff, shoff, _flags, _ehsize, phentsize, phnum, shentsize, shnum,
     shstrndx) = struct.unpack(order + layout, data[16:16 + size])
    return _Header(bits, order, type_, machine, phoff, shoff, phentsize, phnum, shentsize, shnum, shstrndx)


def _phdrs(head: _Header, read: Callable[[int, int], bytes]) -> list[tuple[int, int, int, int]]:
    """The program headers as ``(type, offset, vaddr, filesz)``."""
    layout = head.order + ("IIQQQQQQ" if head.bits == 64 else "IIIIIIII")
    size = struct.calcsize(layout)
    if head.phentsize < size or not head.phoff:
        return []
    table = read(head.phoff, head.phentsize * head.phnum)
    out = []
    for index in range(head.phnum):
        chunk = table[index * head.phentsize:index * head.phentsize + size]
        if len(chunk) < size:
            break
        fields = struct.unpack(layout, chunk)
        if head.bits == 64:
            type_, _flags, offset, vaddr, _paddr, filesz = fields[:6]
        else:
            type_, offset, vaddr, _paddr, filesz = fields[:5]
        out.append((type_, offset, vaddr, filesz))
    return out


def sniff(path: Path) -> str:
    """*path*'s ELF MIME type (:data:`MIMES`), or ``""``: not a regular
    file, neither executable nor named like a library, or not ELF.  The
    link's target, for a symbolic link.  Runs on a thread."""
    try:
        info = os.stat(path)
        if not stat.S_ISREG(info.st_mode) or not (info.st_mode & 0o111 or _SONAME.search(path.name)
                                                  or path.suffix in (".o", ".ko")):
            return ""
        with open(path, "rb") as file:
            data = file.read(HEAD)
    except OSError:
        return ""
    head = _header(data)
    if head is None:
        return ""
    if head.type == ET_EXEC:
        return EXECUTABLE
    if head.type == ET_REL:
        return OBJECT
    if head.type == ET_CORE:
        return CORE
    if head.type == ET_DYN:
        interp = any(type_ == PT_INTERP for type_, *_ in _phdrs(head, lambda at, n: data[at:at + n]))
        return PIE if interp and not _SONAME.search(path.name) else SHAREDLIB
    return ""


def _string(data: bytes, at: int) -> str:
    end = data.find(b"\0", at)
    return data[at:end if end >= 0 else len(data)].decode("utf-8", "replace")


def _clean(name: str) -> str:
    """A name as a line can show it: one line, no ``~``."""
    return " ".join(name.replace("~", "").split())


def read(path: Path, wanted: Callable[[], bool] = lambda: True) -> Program | None:
    """*path*'s :class:`Program`, or None: not ELF, cut short, unreadable or
    no longer *wanted*.  Runs on a thread."""
    if not wanted():
        return None
    try:
        with open(path, "rb") as file:
            return _read(file, Path(path))
    except (OSError, struct.error, ValueError, IndexError):
        return None


def _read(file: BinaryIO, path: Path) -> Program | None:
    def read_at(at: int, count: int) -> bytes:
        file.seek(at)
        return file.read(max(0, min(count, MOST)))

    head = _header(read_at(0, 64))
    if head is None:
        return None
    program = Program(bits=head.bits, big_endian=head.order == ">", machine=head.machine)
    phdrs = _phdrs(head, read_at)
    for type_, offset, _vaddr, filesz in phdrs:
        if type_ == PT_INTERP:
            program.interpreter = _clean(_string(read_at(offset, filesz), 0))
    dynamic = _dynamic(head, phdrs, read_at)
    flags_1 = dynamic.get(DT_FLAGS_1, [None])[0]
    if head.type == ET_EXEC:
        program.kind = "executable"
    elif head.type == ET_DYN:
        pie = bool(flags_1 & DF_1_PIE) if flags_1 is not None else bool(program.interpreter)
        program.kind = "pie" if pie and not _SONAME.search(path.name) else "library"
    elif head.type == ET_REL:
        program.kind = "object"
    elif head.type == ET_CORE:
        program.kind = "core"
    else:
        program.kind = "other"
    names = _section_names(head, read_at)
    program.sections = names is not None
    names = names or set()
    program.stripped = ".symtab" not in names
    program.debug_info = ".debug_info" in names or ".zdebug_info" in names
    if program.kind in ("executable", "pie", "library"):
        program.needed = [(name, resolve(name, program, path, dynamic)) for name in dynamic.get(DT_NEEDED, [])]
        if program.interpreter:
            program.interpreter_found = _matches(program.interpreter, program)
    return program


def _dynamic(head: _Header, phdrs: list[tuple[int, int, int, int]],
             read_at: Callable[[int, int], bytes]) -> dict[int, list]:
    """The dynamic section's entries that are read, by tag: the strings of
    ``DT_NEEDED``/``DT_RPATH``/``DT_RUNPATH``, the value of ``DT_FLAGS_1``."""
    found = [(offset, filesz) for type_, offset, _vaddr, filesz in phdrs if type_ == PT_DYNAMIC]
    if not found:
        return {}
    offset, filesz = found[0]
    layout = head.order + ("qQ" if head.bits == 64 else "iI")
    size = struct.calcsize(layout)
    data = read_at(offset, filesz)
    entries: list[tuple[int, int]] = []
    for at in range(0, len(data) - size + 1, size):
        tag, value = struct.unpack(layout, data[at:at + size])
        if tag == DT_NULL:
            break
        entries.append((tag, value))
    strtab = next((value for tag, value in entries if tag == DT_STRTAB), None)
    strsz = next((value for tag, value in entries if tag == DT_STRSZ), 0)
    out: dict[int, list] = {}
    for tag, value in entries:
        if tag == DT_FLAGS_1:
            out[DT_FLAGS_1] = [value]
    if strtab is None:
        return out
    # The string table's address is a virtual one: the load segment holding
    # it says where in the file it is.
    where = next((offset + strtab - vaddr for type_, offset, vaddr, filesz in phdrs
                  if type_ == PT_LOAD and vaddr <= strtab < vaddr + filesz), None)
    if where is None:
        return out
    strings = read_at(where, strsz or MOST)
    for tag, value in entries:
        if tag in (DT_NEEDED, DT_RPATH, DT_RUNPATH) and value < len(strings):
            out.setdefault(tag, []).append(_clean(_string(strings, value)))
    return out


def _section_names(head: _Header, read_at: Callable[[int, int], bytes]) -> set[str] | None:
    """The sections' names; None for a file without section headers."""
    layout = head.order + ("IIQQQQIIQQ" if head.bits == 64 else "IIIIIIIIII")
    size = struct.calcsize(layout)
    if not head.shoff or head.shentsize < size:
        return None

    def section(index: int) -> tuple:
        chunk = read_at(head.shoff + index * head.shentsize, size)
        if len(chunk) < size:
            raise ValueError("section header cut short")
        return struct.unpack(layout, chunk)

    count, names_at = head.shnum, head.shstrndx
    if count == 0 or names_at == 0xFFFF:  # too many: the first section holds them
        first = section(0)
        count = count or first[5]
        if names_at == 0xFFFF:
            names_at = first[6]
    if not count or names_at >= count:
        return None
    _name, _type, _flags, _addr, offset, strsize, *_ = section(names_at)
    strings = read_at(offset, strsize)
    table = read_at(head.shoff, count * head.shentsize)
    names = set()
    for index in range(count):
        chunk = table[index * head.shentsize:index * head.shentsize + size]
        if len(chunk) < size:
            break
        names.add(_string(strings, struct.unpack(layout, chunk)[0]))
    return names


# -- looking for a library ---------------------------------------------------------


def _matches(candidate: str | os.PathLike, program: Program) -> bool:
    """Whether *candidate* is an ELF file the loader could use for
    *program*: there, and of its class, byte order and machine."""
    try:
        with open(candidate, "rb") as file:
            head = _header(file.read(64))
    except OSError:
        return False
    return head is not None and head.bits == program.bits and (head.order == ">") == program.big_endian \
        and head.machine == program.machine


def _expand(directory: str, origin: Path, program: Program) -> str:
    """A run path's ``$ORIGIN`` and ``$LIB`` (``${...}`` too) put in."""
    lib = "lib64" if program.bits == 64 else "lib"
    for name, value in (("ORIGIN", str(origin)), ("LIB", lib)):
        directory = directory.replace("${" + name + "}", value).replace("$" + name, value)
    return directory


#: The loader's cache, once read: ``(mtime, {name: [paths]})``.
_CACHE: dict[str, tuple[float, dict[str, list[str]]]] = {}

#: Where glibc's cache is.
LD_CACHE = Path("/etc/ld.so.cache")

#: The new format's magic, which an old-format file carries after its table.
_CACHE_MAGIC = b"glibc-ld.so.cache1.1"


def parse_cache(data: bytes) -> dict[str, list[str]]:
    """``/etc/ld.so.cache`` as ``{library name: [its paths]}`` -- the
    format glibc has written since 2.32, and the one inside the older
    compatible format."""
    start = data.find(_CACHE_MAGIC)
    if start < 0:
        return {}
    nlibs, _strings_size = struct.unpack_from("=II", data, start + 20)
    out: dict[str, list[str]] = {}
    entry = start + 48
    for index in range(nlibs):
        at = entry + 24 * index
        if at + 24 > len(data):
            break
        _flags, key, value = struct.unpack_from("=iII", data, at)
        out.setdefault(_string(data, start + key), []).append(_string(data, start + value))
    return out


def cache(path: Path = LD_CACHE) -> dict[str, list[str]]:
    """The loader's cache, read again only when the file has changed."""
    try:
        mtime = path.stat().st_mtime
        held = _CACHE.get(str(path))
        if held is not None and held[0] == mtime:
            return held[1]
        table = parse_cache(path.read_bytes())
    except (OSError, struct.error):
        return {}
    _CACHE[str(path)] = (mtime, table)
    return table


def default_dirs() -> list[str]:
    """Where the loader looks last: musl's path file, else the system's
    library directories, multiarch ones included (the candidate's machine
    sorts out which)."""
    for musl in sorted(glob.glob("/etc/ld-musl-*.path")):
        try:
            text = Path(musl).read_text()
        except OSError:
            continue
        return [part for line in text.splitlines() for part in line.replace(":", " ").split()]
    dirs = ["/lib64", "/usr/lib64", "/lib", "/usr/lib", "/lib32", "/usr/lib32", "/usr/local/lib"]
    return dirs + sorted(glob.glob("/lib/*-linux-*")) + sorted(glob.glob("/usr/lib/*-linux-*"))


def resolve(name: str, program: Program, path: Path, dynamic: dict[int, list] | None = None) -> str | None:
    """Where the loader would find library *name* for *program* at *path*,
    or None: glibc's order -- ``DT_RPATH`` when there is no ``DT_RUNPATH``,
    ``LD_LIBRARY_PATH``, ``DT_RUNPATH``, the cache, the default directories."""
    if "/" in name:
        return name if _matches(name, program) else None
    dynamic = dynamic or {}
    origin = Path(os.path.abspath(path)).parent

    def split(paths: list[str]) -> list[str]:
        return [_expand(part, origin, program) for joined in paths for part in joined.split(":") if part]

    runpath = split(dynamic.get(DT_RUNPATH, []))
    search = [] if runpath else split(dynamic.get(DT_RPATH, []))
    search += [part for part in os.environ.get("LD_LIBRARY_PATH", "").split(":") if part]
    search += runpath
    for directory in search:
        candidate = os.path.join(directory, name)
        if _matches(candidate, program):
            return candidate
    for candidate in cache().get(name, []):
        if _matches(candidate, program):
            return candidate
    for directory in default_dirs():
        candidate = os.path.join(directory, name)
        if _matches(candidate, program):
            return candidate
    return None


# -- laid out ----------------------------------------------------------------------


def _kind(program: Program) -> str:
    return {
        "executable": tr("executable"), "pie": tr("PIE executable"), "library": tr("shared library"),
        "object": tr("object file"), "core": tr("core dump"),
    }.get(program.kind, tr("unknown type"))


def pairs(program: Program | None) -> list[tuple[str, str]]:
    """*program* as ``(label, value)``, the labels English (:data:`LABELS`).
    A value already marked with ``~`` is shown as it is; an empty label
    continues the row above (the libraries, one to a row)."""
    if program is None:
        return []
    machine = MACHINES.get(program.machine) or tr("machine {n}").format(n=program.machine)
    what = tr("ELF {bits}-bit {machine}, {kind}").format(bits=program.bits, machine=machine,
                                                         kind=_kind(program))
    if program.big_endian:
        what += ", " + tr("big-endian")
    out: list[tuple[str, str]] = [("Program", what)]
    missing = " " + tr("(not found)")
    if program.interpreter:
        out.append(("Interpreter", program.interpreter if program.interpreter_found
                    else f"~{program.interpreter}~{missing}"))
    if program.kind in ("executable", "pie", "library"):
        if program.needed:
            for index, (name, found) in enumerate(program.needed):
                out.append(("" if index else "Libraries", name if found else f"~{name}~{missing}"))
        elif program.kind != "library" and not program.interpreter:
            out.append(("Libraries", tr("none, statically linked")))
        else:
            out.append(("Libraries", tr("none")))
    if program.sections:
        symbols = tr("stripped") if program.stripped else tr("not stripped")
        if program.debug_info:
            symbols += ", " + tr("with debug info")
        out.append(("Symbols", symbols))
    return out
