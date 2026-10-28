"""Zstandard, for ``.tar.zst``: Python's own :mod:`compression.zstd` where
there is one (3.14 on), else the ``zstd`` command.

:mod:`tarfile` reads a member wherever it lies, which a pipe cannot give
it, so a ``.tar.zst`` is opened by decompressing it whole into a plain tar
first (:func:`decompress`) and written as a plain tar compressed afterwards
(:func:`compress`).  Both are whole files, and block.
"""

from __future__ import annotations

import errno
import shutil
import subprocess
from pathlib import Path
from typing import Any

#: A zstd frame's first four bytes.
MAGIC = b"\x28\xb5\x2f\xfd"

#: What to install when neither is here.
MISSING = "tar.zst archives need zstd: install zstd"


def _module() -> Any:
    try:
        from compression import zstd  # type: ignore[import-not-found]
    except ImportError:
        return None
    return zstd


def _program() -> str | None:
    return shutil.which("zstd")


def available() -> bool:
    """Whether a ``.tar.zst`` can be read and written here."""
    return _module() is not None or _program() is not None


def _reason(done: subprocess.CompletedProcess[bytes]) -> str:
    return done.stderr.decode("utf-8", "replace").strip() or f"zstd exited with {done.returncode}"


def decompress(source: Path, target: Path) -> None:
    """*source*'s frames, decompressed, into *target*."""
    module = _module()
    if module is not None:
        with module.open(source, "rb") as reader, open(target, "wb") as writer:
            shutil.copyfileobj(reader, writer, 1 << 20)
        return
    program = _program()
    if program is None:
        raise OSError(errno.ENOENT, MISSING, str(source))
    done = subprocess.run([program, "-d", "-q", "-f", "-o", str(target), "--", str(source)],
                          capture_output=True, stdin=subprocess.DEVNULL)
    if done.returncode != 0:
        raise OSError(errno.EIO, _reason(done), str(source))


def compress(source: Path, target: Path, level: int = 3) -> None:
    """*source* compressed into *target* at *level* (1 to 22; above 19 is
    zstd's ``--ultra``)."""
    module = _module()
    if module is not None:
        with open(source, "rb") as reader, module.open(target, "wb", level=level) as writer:
            shutil.copyfileobj(reader, writer, 1 << 20)
        return
    program = _program()
    if program is None:
        raise OSError(errno.ENOENT, MISSING, str(target))
    switches = ["--ultra"] if level > 19 else []
    done = subprocess.run([program, *switches, f"-{level}", "-q", "-f", "-o", str(target), "--", str(source)],
                          capture_output=True, stdin=subprocess.DEVNULL)
    if done.returncode != 0:
        raise OSError(errno.EIO, _reason(done), str(target))


__all__ = ["MAGIC", "MISSING", "available", "compress", "decompress"]
