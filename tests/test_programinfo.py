"""Ctrl+L's *Current file* for a Linux program (navigator/lib/system/programinfo.py)."""

from __future__ import annotations

import os
import struct
import sys
from pathlib import Path

import pytest

from navigator.lib.system import mediainfo, programinfo
from navigator.lib.system.programinfo import (CORE, EXECUTABLE, OBJECT, PIE, SHAREDLIB, Program, pairs,
                                              parse_cache, read, resolve, sniff)

X86_64, AARCH64, PPC64 = 62, 183, 21


def elf(*, bits: int = 64, big: bool = False, type_: int = 3, machine: int = X86_64, interp: str | None = None,
        needed: tuple[str, ...] = (), runpath: str | None = None, rpath: str | None = None,
        flags_1: int | None = None, sections: tuple[str, ...] | None = (".text",)) -> bytes:
    """A minimal ELF file: one load segment over the whole file (so a
    virtual address is its offset), PT_INTERP and PT_DYNAMIC as asked, and
    section headers naming *sections* (None: no section headers)."""
    o = ">" if big else "<"
    ehsize, phentsize, shentsize = (64, 56, 64) if bits == 64 else (52, 32, 40)
    dynamic = needed or runpath or rpath or flags_1 is not None
    phnum = 1 + (interp is not None) + bool(dynamic)
    at = ehsize + phnum * phentsize
    body = b""

    def place(data: bytes) -> int:
        nonlocal body
        offset = at + len(body)
        body += data
        return offset

    interp_at = place(interp.encode() + b"\0") if interp is not None else 0
    strings = b"\0"
    tags: list[tuple[int, int]] = []

    def string(text: str) -> int:
        nonlocal strings
        offset = len(strings)
        strings += text.encode() + b"\0"
        return offset

    for name in needed:
        tags.append((1, string(name)))
    if rpath is not None:
        tags.append((15, string(rpath)))
    if runpath is not None:
        tags.append((29, string(runpath)))
    if flags_1 is not None:
        tags.append((0x6FFFFFFB, flags_1))
    dynstr_at = place(strings) if dynamic else 0
    if dynamic:
        tags += [(5, dynstr_at), (10, len(strings)), (0, 0)]
    dyn_layout = o + ("qQ" if bits == 64 else "iI")
    dynamic_at = place(b"".join(struct.pack(dyn_layout, *tag) for tag in tags)) if dynamic else 0
    dynamic_size = len(tags) * struct.calcsize(dyn_layout)
    shoff = shnum = shstrndx = 0
    if sections is not None:
        names = b"\0"
        offsets = []
        for name in (*sections, ".shstrtab"):
            offsets.append(len(names))
            names += name.encode() + b"\0"
        names_at = place(names)
        shoff = at + len(body)
        layout = o + ("IIQQQQIIQQ" if bits == 64 else "IIIIIIIIII")
        table = struct.pack(layout, *[0] * 10)
        for index, name_offset in enumerate(offsets):
            last = index == len(offsets) - 1
            table += struct.pack(layout, name_offset, 3 if last else 1, 0, 0, names_at if last else 0,
                                 len(names) if last else 0, 0, 0, 1, 0)
        place(table)
        shnum, shstrndx = len(offsets) + 1, len(offsets)
    total = at + len(body)
    ph_layout = o + ("IIQQQQQQ" if bits == 64 else "IIIIIIII")

    def phdr(type_: int, offset: int, size: int) -> bytes:
        if bits == 64:
            return struct.pack(ph_layout, type_, 5, offset, offset, offset, size, size, 8)
        return struct.pack(ph_layout, type_, offset, offset, offset, size, size, 5, 8)

    phdrs = phdr(1, 0, total)
    if interp is not None:
        phdrs += phdr(3, interp_at, len(interp) + 1)
    if dynamic:
        phdrs += phdr(2, dynamic_at, dynamic_size)
    ident = b"\x7fELF" + bytes([2 if bits == 64 else 1, 2 if big else 1, 1]) + b"\0" * 9
    eh_layout = o + ("HHIQQQIHHHHHH" if bits == 64 else "HHIIIIIHHHHHH")
    header = ident + struct.pack(eh_layout, type_, machine, 1, 0, ehsize, shoff, 0, ehsize, phentsize, phnum,
                                 shentsize, shnum, shstrndx)
    return header + phdrs + body


@pytest.fixture
def nowhere(monkeypatch):
    """No cache, no default directories, no LD_LIBRARY_PATH: a library is
    found only where the file says."""
    monkeypatch.setattr(programinfo, "cache", lambda: {})
    monkeypatch.setattr(programinfo, "default_dirs", lambda: [])
    monkeypatch.delenv("LD_LIBRARY_PATH", raising=False)


def write(path: Path, data: bytes, mode: int = 0o755) -> Path:
    path.write_bytes(data)
    path.chmod(mode)
    return path


def test_sniff_names_each_kind(tmp_path):
    assert sniff(write(tmp_path / "exe", elf(type_=2))) == EXECUTABLE
    assert sniff(write(tmp_path / "pie", elf(interp="/lib/ld.so"))) == PIE
    assert sniff(write(tmp_path / "libx.so.1", elf(interp="/lib/ld.so"), 0o644)) == SHAREDLIB
    assert sniff(write(tmp_path / "a.o", elf(type_=1), 0o644)) == OBJECT
    assert sniff(write(tmp_path / "core", elf(type_=4))) == CORE
    # Not executable and not named like a library: not looked at.
    assert sniff(write(tmp_path / "data", elf(type_=2), 0o644)) == ""
    assert sniff(write(tmp_path / "script", b"#!/bin/sh\n")) == ""
    assert sniff(tmp_path) == "" and sniff(tmp_path / "missing") == ""
    os.symlink(tmp_path / "exe", tmp_path / "link")
    assert sniff(tmp_path / "link") == EXECUTABLE
    assert all(mediainfo.kind(mime) == "program" for mime in programinfo.MIMES)


def test_a_dynamic_program(tmp_path, nowhere):
    (tmp_path / "lib").mkdir()
    write(tmp_path / "lib" / "libfound.so.1", elf(), 0o644)
    write(tmp_path / "ld.so", elf())
    path = write(tmp_path / "prog", elf(interp=str(tmp_path / "ld.so"), needed=("libfound.so.1", "libgone.so.2"),
                                        runpath="$ORIGIN/lib", flags_1=0x08000000))
    program = read(path)
    assert program.kind == "pie" and program.bits == 64 and not program.big_endian
    assert program.needed == [("libfound.so.1", str(tmp_path / "lib" / "libfound.so.1")), ("libgone.so.2", None)]
    assert program.interpreter_found and program.stripped and not program.debug_info
    assert pairs(program) == [
        ("Program", "ELF 64-bit x86-64, PIE executable"), ("Interpreter", str(tmp_path / "ld.so")),
        ("Libraries", "libfound.so.1"), ("", "~libgone.so.2~ (not found)"), ("Symbols", "stripped"),
    ]
    assert mediainfo.pairs(mediainfo.read(path, PIE)) == pairs(program)


def test_a_library_of_another_class_or_machine_does_not_count(tmp_path, nowhere):
    write(tmp_path / "libx.so", elf(bits=32), 0o644)
    write(tmp_path / "liby.so", elf(machine=AARCH64), 0o644)
    write(tmp_path / "libz.so", b"not elf", 0o644)
    program = read(write(tmp_path / "prog", elf(needed=("libx.so", "liby.so", "libz.so"), rpath=str(tmp_path))))
    assert [found for _, found in program.needed] == [None, None, None]


def test_the_search_order(tmp_path, nowhere, monkeypatch):
    for place in ("rpath", "env", "runpath", "cached", "default"):
        (tmp_path / place).mkdir()
        write(tmp_path / place / "libq.so", elf(), 0o644)
    program = Program(machine=X86_64)
    path = tmp_path / "prog"
    # DT_RPATH is ignored once there is a DT_RUNPATH; LD_LIBRARY_PATH comes before DT_RUNPATH.
    monkeypatch.setenv("LD_LIBRARY_PATH", str(tmp_path / "env"))
    both = {programinfo.DT_RPATH: [str(tmp_path / "rpath")], programinfo.DT_RUNPATH: [str(tmp_path / "runpath")]}
    assert resolve("libq.so", program, path, both) == str(tmp_path / "env" / "libq.so")
    assert resolve("libq.so", program, path, {programinfo.DT_RPATH: [str(tmp_path / "rpath")]}) == \
        str(tmp_path / "rpath" / "libq.so")
    monkeypatch.delenv("LD_LIBRARY_PATH")
    assert resolve("libq.so", program, path, both) == str(tmp_path / "runpath" / "libq.so")
    monkeypatch.setattr(programinfo, "cache", lambda: {"libq.so": [str(tmp_path / "cached" / "libq.so")]})
    assert resolve("libq.so", program, path) == str(tmp_path / "cached" / "libq.so")
    monkeypatch.setattr(programinfo, "cache", lambda: {})
    monkeypatch.setattr(programinfo, "default_dirs", lambda: [str(tmp_path / "default")])
    assert resolve("libq.so", program, path) == str(tmp_path / "default" / "libq.so")
    assert resolve(str(tmp_path / "rpath" / "libq.so"), program, path) == str(tmp_path / "rpath" / "libq.so")
    assert resolve("libnone.so", program, path) is None


def test_static_stripped_and_debug_info(tmp_path, nowhere):
    static = read(write(tmp_path / "s", elf(type_=2, sections=(".text", ".symtab", ".debug_info"))))
    assert pairs(static) == [("Program", "ELF 64-bit x86-64, executable"),
                             ("Libraries", "none, statically linked"),
                             ("Symbols", "not stripped, with debug info")]
    lib = read(write(tmp_path / "libs.so", elf(sections=(".text", ".symtab")), 0o644))
    assert pairs(lib) == [("Program", "ELF 64-bit x86-64, shared library"), ("Libraries", "none"),
                          ("Symbols", "not stripped")]
    core = read(write(tmp_path / "core", elf(type_=4, sections=None)))
    assert pairs(core) == [("Program", "ELF 64-bit x86-64, core dump")]


def test_32_bit_big_endian_and_a_missing_interpreter(tmp_path, nowhere):
    program = read(write(tmp_path / "prog", elf(bits=32, big=True, machine=PPC64, type_=2,
                                                interp="/no/such/ld.so", needed=("libc.so.6",))))
    assert program.bits == 32 and program.big_endian and program.needed == [("libc.so.6", None)]
    assert pairs(program)[:3] == [("Program", "ELF 32-bit PowerPC64, executable, big-endian"),
                                  ("Interpreter", "~/no/such/ld.so~ (not found)"),
                                  ("Libraries", "~libc.so.6~ (not found)")]
    assert pairs(read(write(tmp_path / "odd", elf(machine=9999, type_=1))))[0] == \
        ("Program", "ELF 64-bit machine 9999, object file")


def test_damaged_or_unwanted_files_say_nothing(tmp_path):
    whole = elf(interp="/lib/ld.so", needed=("libc.so.6",))
    assert read(write(tmp_path / "cut", whole[:40])) is None
    assert read(write(tmp_path / "text", b"hello")) is None
    assert read(tmp_path / "missing") is None
    assert read(write(tmp_path / "prog", whole), wanted=lambda: False) is None
    assert pairs(None) == []


def test_the_loaders_cache(tmp_path):
    names = b"libq.so\0/lib/libq.so\0/lib32/libq.so\0"
    header = b"glibc-ld.so.cache1.1" + struct.pack("=II", 2, len(names)) + b"\0" * 20
    strings_at = len(header) + 2 * 24
    entries = struct.pack("=iIIIQ", 0x303, strings_at, strings_at + 8, 0, 0) + \
        struct.pack("=iIIIQ", 3, strings_at, strings_at + 21, 0, 0)
    table = header + entries + names
    assert parse_cache(table) == {"libq.so": ["/lib/libq.so", "/lib32/libq.so"]}
    # The old format carries the new after its own table.
    assert parse_cache(b"ld.so-1.7.0" + b"\0" * 13 + table) == parse_cache(table)
    assert parse_cache(b"nothing") == {}
    (tmp_path / "ld.so.cache").write_bytes(table)
    assert programinfo.cache(tmp_path / "ld.so.cache") == parse_cache(table)
    assert programinfo.cache(tmp_path / "missing") == {}


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="an ELF interpreter")
def test_this_python_reads_as_a_program():
    path = Path(os.path.realpath(sys.executable))
    program = read(path)
    assert program is not None and program.kind in ("executable", "pie")
    assert pairs(program)[0][0] == "Program" and all(found for _, found in program.needed)
