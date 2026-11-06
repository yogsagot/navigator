"""The encodings a text is read and written in -- **a departure, asked for**.

DOS Navigator's editor knew one code page, the screen's; a file in another was
translated through an ``*.XLT`` table on the way in and out.  Here the editor
holds Unicode and each text remembers the encoding its bytes are in: UTF-8
(with or without a byte order mark), UTF-16 with a mark, or one of the
one-byte code pages the viewer's Shift+F6 knows
(:data:`navigator.lib.viewer.ENCODINGS`).

**What is read is written back byte for byte.**  A byte order mark is taken
off on reading and put back on writing; the ASCII-compatible encodings decode
with ``surrogateescape``, so a byte the encoding has no character for is kept
as a lone surrogate and written back as itself.  UTF-16 decodes strictly: a
file that claims it with its mark but does not decode is read as UTF-8.

The bottom frame of F4 shows :func:`label` of the text's encoding, and the
File > Encoding > Convert text command speaks the same keys.
"""

from __future__ import annotations

import codecs
import re
from typing import Iterable

from navigator.lib.viewer import ENCODINGS as _ONE_BYTE

#: The default: UTF-8 without a mark.
UTF8 = "utf-8"
UTF8_BOM = "utf-8-bom"
UTF16_LE = "utf-16-le"
UTF16_BE = "utf-16-be"

#: Every encoding a text may be in: its key, the short label the frame shows,
#: and the caption a menu gives it.  The one-byte code pages are the viewer's.
CODECS: tuple[tuple[str, str, str], ...] = (
    (UTF8, "UTF-8", "UTF-8"),
    (UTF8_BOM, "UTF-8 BOM", "UTF-8 with BOM"),
    (UTF16_LE, "UTF-16LE", "UTF-16 LE with BOM"),
    (UTF16_BE, "UTF-16BE", "UTF-16 BE with BOM"),
    *((key, caption.split()[0], caption) for key, caption in _ONE_BYTE if key != UTF8),
)

#: The one-byte code pages alone: what a file that is not UTF-8 may be read as.
ONE_BYTE: tuple[str, ...] = tuple(key for key, _ in _ONE_BYTE if key != UTF8)

_BY_KEY = {key: (short, caption) for key, short, caption in CODECS}

#: Each mark and the encoding it says, longest first.
_BOMS = (
    (codecs.BOM_UTF8, UTF8_BOM),
    (codecs.BOM_UTF16_LE, UTF16_LE),
    (codecs.BOM_UTF16_BE, UTF16_BE),
)
_BOM_OF = {key: bom for bom, key in _BOMS}

#: The Python codec each key decodes and encodes with, the mark aside.
_PYTHON = {UTF8: "utf-8", UTF8_BOM: "utf-8", UTF16_LE: "utf-16-le", UTF16_BE: "utf-16-be"}


def known(key: str) -> bool:
    return key in _BY_KEY


def label(key: str) -> str:
    """What the frame shows for *key*: ``UTF-8``, ``UTF-16LE``, ``CP1251``..."""
    return _BY_KEY.get(key, (key.upper(), ""))[0]


def caption(key: str) -> str:
    """What a menu shows for *key*."""
    return _BY_KEY.get(key, ("", key.upper()))[1]


def python_codec(key: str) -> str:
    """The codec Python decodes *key* with, the mark aside."""
    return _PYTHON.get(key, key)


def bom(key: str) -> bytes:
    """The mark a text in *key* starts with, or ``b""``."""
    return _BOM_OF.get(key, b"")


def ascii_compatible(key: str) -> bool:
    """Whether a CR and an LF are those bytes alone in *key* -- every encoding
    but UTF-16, which the chunked reader must decode before it splits."""
    return key not in (UTF16_LE, UTF16_BE)


def errors(key: str) -> str:
    """The error handler for *key*: ``surrogateescape`` keeps every byte of an
    ASCII-compatible text; UTF-16 has nothing to keep a stray byte as."""
    return "surrogateescape" if ascii_compatible(key) else "strict"


def sniff(head: bytes) -> tuple[str, int]:
    """The encoding a file's first bytes say by their mark, and the mark's
    length -- or UTF-8 and 0 when there is none."""
    for mark, key in _BOMS:
        if head.startswith(mark):
            return key, len(mark)
    return UTF8, 0


def decode(data: bytes, key: str) -> str:
    """*data*, mark already taken off, as text.  Raises ``UnicodeDecodeError``
    for UTF-16 that does not decode."""
    return data.decode(python_codec(key), errors(key))


def encode(text: str, key: str) -> bytes:
    """*text* in *key*, no mark.  Raises ``UnicodeEncodeError`` for a character
    *key* has not -- or, in UTF-16, for a byte kept from a file that was not."""
    return text.encode(python_codec(key), errors(key))


_ESCAPED = re.compile("[\udc80-\udcff]")


def has_escaped(text: str) -> bool:
    """Whether *text* holds a byte that did not decode (a lone surrogate)."""
    return not text.isascii() and _ESCAPED.search(text) is not None


def first_unencodable(lines: Iterable[str], key: str) -> tuple[int, int] | None:
    """The ``(line, index)`` of the first character *key* cannot write, or None."""
    codec, handler = python_codec(key), errors(key)
    for number, line in enumerate(lines):
        if line.isascii():
            continue
        try:
            line.encode(codec, handler)
        except UnicodeEncodeError as error:
            return number, error.start
    return None
