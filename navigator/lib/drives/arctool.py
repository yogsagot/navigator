"""Archives Python cannot read -- 7z and rar -- through an archiver's own
command line, as DOS Navigator ran one for every step (``TArchiver``'s
*Packer*/*UnPacker*, ``ARCHIVER.PAS``).

7-Zip (``7zz``, the official build, or p7zip's ``7z``/``7za``) reads and
writes 7z (and zip, where it is to be encrypted) and reads rar; ``unrar`` reads rar where no 7-Zip with the rar
codec is there (``7za`` has none).  Nothing is bundled: without a tool the
archive is not one Navigator can open, :class:`MissingTool` says which to
install, and Enter runs the file instead -- as a ``.docx`` is run.

:class:`ToolArchive` stands where ``zipfile.ZipFile`` does in
:class:`~navigator.lib.drives.archive.ArchiveDrive`: :meth:`~ToolArchive.infolist`,
:meth:`~ToolArchive.open` a member to read (a pipe from the tool), and
:meth:`~ToolArchive.close`.  Writing a 7z is :func:`write_7z` over a
directory laid out as the archive is to be.  Everything blocks.
"""

from __future__ import annotations

import contextlib
import errno
import io
import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

#: The kinds this module reads, by their first bytes.
SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"7z\xbc\xaf\x27\x1c", "7z"),
    (b"Rar!\x1a\x07", "rar"),
)

#: 7-Zip's programs, best first: ``7za`` reads no rar.
SEVEN_ZIP = ("7zz", "7z", "7za")


class MissingTool(Exception):
    """No program here reads this kind of archive: what to install."""


class NeedPassword(Exception):
    """The archive is encrypted and no password, or the wrong one, was given."""


def kind_of(local: Path) -> str | None:
    """``"7z"`` or ``"rar"`` by *local*'s first bytes, else None."""
    try:
        with open(local, "rb") as file:
            head = file.read(8)
    except OSError:
        return None
    for signature, kind in SIGNATURES:
        if head.startswith(signature):
            return kind
    return None


def seven_zip(*, rar: bool = False) -> str | None:
    """The 7-Zip program to run, or None; for *rar*, one with the codec."""
    for name in SEVEN_ZIP:
        if rar and name == "7za":
            continue
        found = shutil.which(name)
        if found is not None:
            return found
    return None


def tool_for(kind: str) -> tuple[str, str]:
    """``(flavour, program)`` that reads *kind*: ``"7z"`` or ``"unrar"``.  A
    zip comes here only when it is encrypted, which :mod:`zipfile` cannot read."""
    if kind in ("7z", "zip"):
        found = seven_zip()
        if found is None:
            raise MissingTool(f"{'encrypted zip' if kind == 'zip' else '7z'} archives need 7-Zip: "
                              "install 7zip (7zz) or p7zip (7z)")
        return "7z", found
    found = seven_zip(rar=True)
    if found is not None:
        return "7z", found
    found = shutil.which("unrar")
    if found is not None:
        return "unrar", found
    raise MissingTool("rar archives need unrar, or 7-Zip with its rar codec (7zz)")


@dataclass
class ToolInfo:
    """One member as the tool listed it."""

    path: str
    is_dir: bool
    size: int = 0
    #: Its packed size; None where the tool gave none (a solid block's
    #: members after the first).
    packed: int | None = None
    mtime: float = 0.0
    mode: int = 0
    is_link: bool = False
    #: Its bytes need the password (7-Zip's ``Encrypted = +``).
    encrypted: bool = False


# -- listing ---------------------------------------------------------------------------------


def _blocks(text: str) -> list[dict[str, str]]:
    """``Key = value`` (7-Zip) or ``Key: value`` (unrar) lines in blank-line blocks."""
    blocks, current = [], {}
    for line in text.splitlines():
        if not line.strip():
            if current:
                blocks.append(current)
            current = {}
            continue
        for separator in (" = ", ": "):
            key, found, value = line.partition(separator)
            if found and key.strip():
                current.setdefault(key.strip(), value)
                break
    if current:
        blocks.append(current)
    return blocks


def _time(text: str) -> float:
    """``2024-01-02 03:04:05[.fraction]`` (local time) as seconds."""
    text = text.strip().replace(",", ".")
    whole, _, _fraction = text.partition(".")
    try:
        return time.mktime(time.strptime(whole, "%Y-%m-%d %H:%M:%S"))
    except (ValueError, OverflowError):
        return 0.0


def _mode(text: str) -> tuple[int, str]:
    """The permission bits of an ``ls -l`` word in *text*, and its type letter."""
    for word in text.split():
        if len(word) == 10 and word[0] in "-dlcbps" and all(char in "-rwxsStT" for char in word[1:]):
            bits = 0
            for index, char in enumerate(word[1:]):
                if char != "-":
                    bits |= 1 << (8 - index)
            for index, (lower, upper, flag) in enumerate((("s", "S", 0o4000), ("s", "S", 0o2000),
                                                          ("t", "T", 0o1000))):
                char = word[3 + 3 * index]
                if char in (lower, upper):
                    bits |= flag
                    if char == upper:
                        bits &= ~(1 << (6 - 3 * index))
            return bits, word[0]
    return 0, ""


def _number(text: str | None) -> int | None:
    text = (text or "").strip()
    return int(text) if text.isdigit() else None


def parse_slt(text: str) -> list[ToolInfo]:
    """``7z l -slt -ba``: a block a member.  The archive's own block, if
    there (``Type = ...``), is passed over."""
    members = []
    for block in _blocks(text):
        path = block.get("Path")
        if path is None or "Type" in block or "Physical Size" in block:
            continue
        attributes = block.get("Attributes", "")
        mode, letter = _mode(attributes)
        # ``D`` among the Windows letters, ``d`` in the ``ls -l`` word, or ``Folder = +``.
        windows = attributes.split()[0] if attributes.split() else ""
        is_dir = block.get("Folder", "").strip() == "+" or letter == "d" or "D" in windows
        members.append(ToolInfo(path, is_dir, _number(block.get("Size")) or 0, _number(block.get("Packed Size")),
                                _time(block.get("Modified", "")), mode, letter == "l",
                                block.get("Encrypted", "").strip() == "+"))
    return members


def parse_unrar(text: str) -> list[ToolInfo]:
    """``unrar lta``: a block a member, ``Name:``, ``Type:`` and the rest."""
    members = []
    for block in _blocks(text):
        path = block.get("Name")
        kind = block.get("Type", "").strip().lower()
        if path is None or not kind:
            continue
        mode, letter = _mode(block.get("Attributes", ""))
        is_dir = kind == "directory" or letter == "d"
        is_link = "link" in kind or letter == "l"
        members.append(ToolInfo(path, is_dir, _number(block.get("Size")) or 0, _number(block.get("Packed size")),
                                _time(block.get("mtime", "")), mode, is_link))
    return members


# -- reading ---------------------------------------------------------------------------------


class _Piped(io.RawIOBase):
    """A member's bytes from the tool's standard output; the tool's failure,
    once they end, an ``OSError``.  Closing early stops the tool."""

    def __init__(self, process: subprocess.Popen[bytes], name: str) -> None:
        super().__init__()
        self._process, self._name = process, name

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: Any) -> int:
        stdout = self._process.stdout
        assert stdout is not None
        data = stdout.read1(len(buffer)) if hasattr(stdout, "read1") else stdout.read(len(buffer))
        if not data:
            self._finish()
        buffer[: len(data)] = data
        return len(data)

    def _finish(self) -> None:
        status = self._process.wait()
        if status != 0:
            stderr = self._process.stderr.read() if self._process.stderr is not None else b""
            raise OSError(errno.EIO, _reason(stderr.decode("utf-8", "replace")) or os.strerror(errno.EIO),
                          self._name)

    def close(self) -> None:
        if not self.closed:
            process = self._process
            if process.poll() is None:
                process.kill()
            process.wait()
            for stream in (process.stdout, process.stderr):
                if stream is not None:
                    stream.close()
        super().close()


def _reason(text: str) -> str:
    """The tool's own words for what went wrong: its ``ERROR`` lines."""
    lines = [line.strip() for line in text.splitlines() if "ERROR" in line.upper() and line.strip()]
    return "; ".join(lines) or text.strip()


def _wrong_password(text: str) -> bool:
    """Whether 7-Zip's words say the password was missing or wrong."""
    return "wrong password" in text.lower()


class ToolArchive:
    """A 7z or rar archive -- or an encrypted zip -- read through
    :func:`tool_for`'s program.

    7-Zip is given the *password* on its standard input, never as ``-p``,
    which any user's ``ps`` would show: with no ``-p`` it asks for one only
    when the archive is encrypted, and reads the answer from there once it
    has no terminal (``start_new_session``).  An encrypted archive without
    the right password raises :class:`NeedPassword`."""

    def __init__(self, local: Path, kind: str, password: str = "") -> None:
        self.local = local
        self.kind = kind
        self.password = password
        self.flavour, self.program = tool_for(kind)
        self._members = self._list()
        self.encrypted = any(member.encrypted for member in self._members)
        if self.encrypted:
            self._check_password()

    def _input(self) -> bytes:
        return (self.password + "\n").encode("utf-8")

    def _run(self, *arguments: str, cwd: Path | None = None) -> subprocess.CompletedProcess[bytes]:
        if self.flavour != "7z":
            return subprocess.run([self.program, *arguments], capture_output=True, cwd=cwd,
                                  stdin=subprocess.DEVNULL)
        return subprocess.run([self.program, *arguments], capture_output=True, cwd=cwd,
                              input=self._input(), start_new_session=True)

    def _list(self) -> list[ToolInfo]:
        if self.flavour == "7z":
            done = self._run("l", "-slt", "-ba", "--", str(self.local))
            parse = parse_slt
        else:
            done = self._run("lta", "-p-", "-c-", "--", str(self.local))
            parse = parse_unrar
        if done.returncode != 0:
            text = done.stderr.decode("utf-8", "replace") or done.stdout.decode("utf-8", "replace")
            if self.flavour == "7z" and _wrong_password(text):
                raise NeedPassword(str(self.local))  # its names are encrypted too
            raise OSError(errno.EIO, _reason(text), str(self.local))
        return parse(done.stdout.decode("utf-8", "surrogateescape"))

    def _check_password(self) -> None:
        """The password tried on the smallest encrypted file -- the listing
        needed none where only the bytes are encrypted."""
        if self.flavour != "7z":
            return
        if not self.password:
            raise NeedPassword(str(self.local))
        files = [member for member in self._members if member.encrypted and not member.is_dir]
        if not files:
            return
        smallest = min(files, key=lambda member: member.size)
        done = self._run("t", "-spd", "--", str(self.local), smallest.path)
        if done.returncode != 0:
            text = done.stderr.decode("utf-8", "replace") + done.stdout.decode("utf-8", "replace")
            if _wrong_password(text):
                raise NeedPassword(str(self.local))

    def infolist(self) -> list[ToolInfo]:
        return list(self._members)

    def open(self, info: ToolInfo) -> IO[bytes]:
        """*info*'s bytes, as the tool writes them out."""
        if self.flavour == "7z":
            # -spd: a name is a name, never a wildcard.
            command = [self.program, "x", "-so", "-spd", "--", str(self.local), info.path]
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, start_new_session=True)
            assert process.stdin is not None
            with contextlib.suppress(OSError):
                process.stdin.write(self._input())
            with contextlib.suppress(OSError):
                process.stdin.close()
        else:
            command = [self.program, "p", "-inul", "-p-", "--", str(self.local), info.path]
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
        return io.BufferedReader(_Piped(process, info.path), 1 << 16)  # type: ignore[return-value]

    def read_link(self, info: ToolInfo) -> str:
        """A symbolic link's target: what 7-Zip keeps as its contents."""
        with self.open(info) as reader:
            return reader.read().decode("utf-8", "surrogateescape")

    def extract_all(self, directory: Path) -> None:
        """Every member into *directory*, with its path, links as links."""
        if self.flavour == "7z":
            done = self._run("x", "-y", "-snl", f"-o{directory}", "--", str(self.local))
        else:
            done = self._run("x", "-y", "-inul", "-p-", "--", str(self.local), f"{directory}{os.sep}")
        if done.returncode != 0:
            raise OSError(errno.EIO, _reason(done.stderr.decode("utf-8", "replace")), str(self.local))

    def test(self) -> list[tuple[str, str]]:
        """``7z t`` / ``unrar t``: ``(member, why)`` for each that fails its check."""
        if self.flavour == "7z":
            done = self._run("t", "--", str(self.local))
        else:
            done = self._run("t", "-p-", "--", str(self.local))
        if done.returncode == 0:
            return []
        failures = []
        text = done.stdout.decode("utf-8", "replace") + "\n" + done.stderr.decode("utf-8", "replace")
        for line in text.splitlines():
            line = line.strip()
            if not line.upper().startswith("ERROR"):
                continue
            words = line.partition(":")[2].strip()
            why, _, name = words.rpartition(" : ")
            failures.append((name, why) if why else ("", words))
        return failures or [("", _reason(text) or f"{Path(self.program).name} exited with {done.returncode}")]

    def close(self) -> None:
        pass


def write_archive(target: Path, tree: Path, *, type_: str = "7z", level: int | None = None,
                  password: str = "") -> None:
    """A new 7z (or, *type_* ``"zip"``, zip) at *target* holding what is in
    *tree*, links as links: 7-Zip's ``-mx`` *level* (its default for None),
    and with a *password* encrypted -- a 7z's names too (``-mhe``), a zip's
    bytes with AES-256.  The password goes in on standard input, as
    :class:`ToolArchive`'s does: a bare ``-p`` asks for it twice."""
    program = seven_zip()
    if program is None:
        raise OSError(errno.ENOENT, f"{type_} archives need 7-Zip: install 7zip (7zz) or p7zip (7z)", str(target))
    with contextlib.suppress(FileNotFoundError):
        target.unlink()  # 7-Zip would take an empty file there for an archive
    switches = [f"-t{type_}", "-y"]
    if level is not None:
        switches.append(f"-mx{level}")
    secret = b""
    if password:
        switches += ["-p", "-mhe=on" if type_ == "7z" else "-mem=AES256"]
        secret = (password + "\n") * 4  # asked, verified -- and again on opening to delete
        secret = secret.encode("utf-8")
    names = sorted(os.listdir(tree))
    command = [program, "a", *switches, "-snl", "--", str(target), *names]
    if not names:
        # An empty archive: 7-Zip makes none from nothing, so a file it can
        # take, then taken out again.
        (tree / ".nav-empty").touch()
        command = [program, "a", *switches, "--", str(target), ".nav-empty"]
    done = subprocess.run(command, cwd=tree, capture_output=True, input=secret, start_new_session=True)
    if done.returncode == 0 and not names:
        done = subprocess.run([program, "d", *switches, "--", str(target), ".nav-empty"],
                              capture_output=True, input=secret, start_new_session=True)
    if done.returncode != 0:
        raise OSError(errno.EIO, _reason(done.stderr.decode("utf-8", "replace")), str(target))


def write_7z(target: Path, tree: Path) -> None:
    """A new 7z at *target* holding what is in *tree*, links as links."""
    write_archive(target, tree)


__all__ = ["MissingTool", "NeedPassword", "SEVEN_ZIP", "ToolArchive", "ToolInfo", "kind_of", "parse_slt",
           "parse_unrar", "seven_zip", "tool_for", "write_7z", "write_archive"]
