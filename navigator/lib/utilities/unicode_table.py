"""What the character table lists: every Unicode character, by block, by
general category and by name, and a Nerd Font's icons by set.

Not DOS Navigator's, which charted the 256 characters of code page 437
(``ASCIITAB.PAS``, recreated as ``AsciiChart``); that chart is still what a
terminal in the ASCII glyph tier gets.  This is the model of the one every
other tier gets instead -- a departure, by request, because a UTF-8 terminal
can show a hundred and forty thousand characters and the editor and the
command line can take any of them.

**Three ways to group**, which the dialog switches between:

- *Blocks*, the Unicode Character Database's ``Blocks.txt`` (shipped in
  ``navigator/assets/unicode/``, written by ``tools/unicode_tables.py`` for the
  newest Unicode any supported Python has, so a block this Python's
  :mod:`unicodedata` has nothing in yet is left out).  Read at once: a block
  is a range, and listing one asks :mod:`unicodedata` only about its own codes.
- *Categories*, the general categories (``Lu``, ``Sm``, ``So``...), which
  are not ranges, so each is a scan of the whole code space.
- *Nerd Fonts*, in the Nerd glyph tier only: the sets of nerd-fonts'
  ``glyphnames.json`` (``nerdfont.txt`` beside ``Blocks.txt``), which also
  give the icons the names :mod:`unicodedata` cannot -- they are in the
  Private Use Area, which has no names by definition.

The scan and the name list are an :class:`Index`, built once per process by
:func:`build_index` -- half a second, so on a thread
(:class:`navml.background.Background`), the dialog showing blocks meanwhile.

**What is never listed**: unassigned codes, surrogates (no string can hold
one alone) and the Private Use Area outside the Nerd sets, which no font
agrees about.
"""

from __future__ import annotations

import bisect
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from importlib.resources import files

#: The last code point there is.
LAST = 0x10FFFF

#: How many characters *Recent* keeps.
RECENT_LIMIT = 64

#: The general categories, their two-letter codes in the order the Unicode
#: Standard lists them (its Table 4-4), with the names it gives them.
GENERAL = {
    "Lu": "Letter, uppercase",
    "Ll": "Letter, lowercase",
    "Lt": "Letter, titlecase",
    "Lm": "Letter, modifier",
    "Lo": "Letter, other",
    "Mn": "Mark, nonspacing",
    "Mc": "Mark, spacing combining",
    "Me": "Mark, enclosing",
    "Nd": "Number, decimal digit",
    "Nl": "Number, letter",
    "No": "Number, other",
    "Pc": "Punctuation, connector",
    "Pd": "Punctuation, dash",
    "Ps": "Punctuation, open",
    "Pe": "Punctuation, close",
    "Pi": "Punctuation, initial quote",
    "Pf": "Punctuation, final quote",
    "Po": "Punctuation, other",
    "Sm": "Symbol, math",
    "Sc": "Symbol, currency",
    "Sk": "Symbol, modifier",
    "So": "Symbol, other",
    "Zs": "Separator, space",
    "Zl": "Separator, line",
    "Zp": "Separator, paragraph",
    "Cc": "Other, control",
    "Cf": "Other, format",
}

#: What a Nerd Font icon's category is called, which is not one of
#: :data:`GENERAL`'s lists: the icons are the Nerd sets.
PRIVATE_USE = "Other, private use"

#: The Nerd Font sets, by the prefix ``glyphnames.json`` gives their names,
#: in the order of nerd-fonts' own cheat sheet.  ``indent`` and
#: ``indentation`` are two strays of Seti-UI's range.
NERD_SETS = {
    "md": "Material Design",
    "fa": "Font Awesome",
    "fae": "Font Awesome Extension",
    "dev": "Devicons",
    "oct": "Octicons",
    "cod": "Codicons",
    "seti": "Seti-UI",
    "custom": "Custom",
    "linux": "Font Logos",
    "weather": "Weather Icons",
    "pl": "Powerline",
    "ple": "Powerline Extra",
    "pom": "Pomicons",
    "iec": "IEC Power Symbols",
    "extra": "Extra",
}
NERD_STRAYS = {"indent": "seti", "indentation": "seti"}

#: Shown where a character has nothing to draw of its own.
DOTTED_CIRCLE = "◌"
DOTTED_SQUARE = "⬚"


@dataclass(frozen=True)
class Category:
    """One entry of the list on the left: what the grid shows when it is chosen.

    *kind* is ``recent``, ``found`` (what the search found), ``block``,
    ``general`` or ``nerd``; *key* says which, and is what the dialog
    remembers to reopen on it.  A block carries its range.
    """

    kind: str
    key: str
    name: str
    first: int = 0
    last: int = -1

    @property
    def ident(self) -> str:
        return f"{self.kind}:{self.key}"


@dataclass(frozen=True)
class Block:
    first: int
    last: int
    name: str


def _asset(name: str) -> str:
    return (files("navigator.assets") / "unicode" / name).read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def blocks() -> tuple[Block, ...]:
    """``Blocks.txt``: every block, in code order."""
    found = []
    for line in _asset("Blocks.txt").splitlines():
        match = re.match(r"([0-9A-F]+)\.\.([0-9A-F]+);\s*(.+)", line)
        if match:
            found.append(Block(int(match.group(1), 16), int(match.group(2), 16), match.group(3).strip()))
    return tuple(found)


@lru_cache(maxsize=None)
def _assigned(block: Block) -> bool:
    """Whether this Python's :mod:`unicodedata` has anything in *block*."""
    return any(unicodedata.category(chr(code)) != "Cn" for code in range(block.first, block.last + 1))


@lru_cache(maxsize=1)
def _block_starts() -> list[int]:
    return [block.first for block in blocks()]


def block_of(code: int) -> str:
    """The name of the block *code* is in, or ``""`` for none."""
    index = bisect.bisect_right(_block_starts(), code) - 1
    if index >= 0 and code <= blocks()[index].last:
        return blocks()[index].name
    return ""


def is_listed(code: int, nerd: dict[int, tuple[str, ...]] | None = None) -> bool:
    """Whether *code* is a character the table shows.  A private-use code is
    one only when *nerd* names it."""
    category = unicodedata.category(chr(code))
    if category == "Co":
        return nerd is not None and code in nerd
    return category not in ("Cn", "Cs")


def name_of(code: int, nerd: dict[int, tuple[str, ...]] | None = None) -> str:
    """The character's name: :mod:`unicodedata`'s, the Nerd Font's
    ``nf-`` names for an icon, ``<control-0009>`` as the UCD writes a
    control, which has none."""
    name = unicodedata.name(chr(code), "")
    if name:
        return name
    if nerd is not None and code in nerd:
        return ", ".join("nf-" + n for n in nerd[code])
    if unicodedata.category(chr(code)) == "Cc":
        return f"<control-{code:04X}>"
    return ""


def display(code: int) -> str:
    """What the grid paints for *code*: the character itself, where it draws.

    A control is drawn as its *control picture* (``␉`` for a tab) or a
    middle dot past the C0 set; a mark on a dotted circle, as the code charts
    draw one, so it has a base to sit on; a format character, which has no
    shape at all, as a dotted square.  The string is one cell's.
    """
    char = chr(code)
    category = unicodedata.category(char)
    if category == "Cc":
        if code < 0x20:
            return chr(0x2400 + code)
        return "␡" if code == 0x7F else "·"
    if category.startswith("M"):
        return DOTTED_CIRCLE + char
    if category in ("Cf", "Zl", "Zp"):
        return DOTTED_SQUARE
    return char


def describe(code: int, nerd: dict[int, tuple[str, ...]] | None = None) -> tuple[str, str]:
    """The info line's two rows: ``U+2502  │  BOX DRAWINGS LIGHT VERTICAL``,
    then its category, its decimal code, its UTF-8 bytes and its block --
    last, the longest, so a narrow line cuts that and not the bytes."""
    char = chr(code)
    category = unicodedata.category(char)
    first = f"U+{code:04X}  {display(code)}  {name_of(code, nerd)}"
    utf8 = " ".join(f"{byte:02X}" for byte in char.encode("utf-8", "surrogatepass"))
    where = block_of(code)
    if nerd is not None and code in nerd:
        sets = [NERD_SETS.get(NERD_STRAYS.get(n.split("-")[0], n.split("-")[0]), "") for n in nerd[code]]
        where = ", ".join(dict.fromkeys(s for s in sets if s)) or where
    parts = [f"{category} {GENERAL.get(category, PRIVATE_USE if category == 'Co' else '')}".strip(),
             f"Dec {code}", f"UTF-8 {utf8}", where]
    return first, "  ·  ".join(part for part in parts if part)


def block_categories() -> list[Category]:
    """Every block with something listed in it.  The Private Use Area's
    three and the surrogates' are left out, there being nothing in them
    any font agrees about, and so is a block newer than this Python's
    :mod:`unicodedata`, which has nothing assigned in it."""
    found = []
    for block in blocks():
        if "Private Use" in block.name or "Surrogate" in block.name or not _assigned(block):
            continue
        found.append(Category("block", block.name, block.name, block.first, block.last))
    return found


def general_categories() -> list[Category]:
    return [Category("general", code, f"{code} {name}") for code, name in GENERAL.items()]


def nerd_categories() -> list[Category]:
    return [Category("nerd", prefix, name) for prefix, name in NERD_SETS.items()]


@dataclass
class Index:
    """The scan behind *Categories*, the Nerd sets and the search."""

    #: Every listed code with what a search looks through: its name, lower-cased.
    names: list[tuple[int, str]] = field(default_factory=list)
    #: General category -> its codes, in order.
    general: dict[str, list[int]] = field(default_factory=dict)
    #: Nerd set prefix -> its codes, in order.
    sets: dict[str, list[int]] = field(default_factory=dict)
    #: Code -> its Nerd Font names, ``fa-folder`` (``nf-`` left off); empty
    #: outside the Nerd tier.
    nerd: dict[int, tuple[str, ...]] = field(default_factory=dict)


def read_nerd() -> dict[int, tuple[str, ...]]:
    """``nerdfont.txt``: code -> its names."""
    names = {}
    for line in _asset("nerdfont.txt").splitlines():
        if line and not line.startswith("#"):
            code, _, rest = line.partition("\t")
            names[int(code, 16)] = tuple(rest.split())
    return names


def build_index(nerd: bool) -> Index:
    """The whole code space read once: run on a thread.  *nerd* is whether
    the Nerd sets are wanted -- the Nerd glyph tier."""
    index = Index(general={code: [] for code in GENERAL})
    if nerd:
        index.nerd = read_nerd()
        for code, names in index.nerd.items():
            for name in names:
                prefix = name.split("-")[0]
                prefix = NERD_STRAYS.get(prefix, prefix)
                found = index.sets.setdefault(prefix, [])
                if not found or found[-1] != code:
                    found.append(code)
    table = index.nerd if nerd else None
    for code in range(LAST + 1):
        char = chr(code)
        category = unicodedata.category(char)
        if category in ("Cn", "Cs"):
            continue
        if category == "Co" and code not in index.nerd:
            continue
        if category in index.general:
            index.general[category].append(code)
        name = unicodedata.name(char, "")
        if code in index.nerd:
            nerd_names = " ".join("nf-" + n for n in index.nerd[code])
            name = f"{name} {nerd_names}" if name else nerd_names
        index.names.append((code, (name or name_of(code, table)).lower()))
    return index


def characters(category: Category, index: Index | None) -> list[int] | None:
    """What *category* lists, or None while it waits for *index*.  Not for
    *Recent* or a search's results, which the dialog holds itself."""
    if category.kind == "block":
        table = index.nerd if index is not None else None
        return [code for code in range(category.first, category.last + 1) if is_listed(code, table)]
    if index is None:
        return None
    if category.kind == "general":
        return list(index.general.get(category.key, ()))
    if category.kind == "nerd":
        return list(index.sets.get(category.key, ()))
    return []


_CODE = re.compile(r"(?:u\+|0x|\\u|\\x)?([0-9a-f]{2,6})", re.IGNORECASE)


def search(query: str, index: Index) -> list[int]:
    """What *query* finds: the characters whose names have every word of it.

    A name holding the words as typed, in order, comes first; then names
    matching more of the words whole (``arrow`` finds
    ``LEFTWARDS ARROW`` before ``ARROWHEAD``), the shorter of two names --
    the plainer character -- before the longer, then in code order.  A query that is a
    code -- ``U+2502``, ``0x2502``, ``2502`` -- or one character typed puts
    that character first.
    """
    text = query.strip()
    if not text:
        return []
    first: list[int] = []
    if len(text) == 1 and not text.isascii():
        first.append(ord(text))
    match = _CODE.fullmatch(text)
    if match:
        code = int(match.group(1), 16)
        if code <= LAST and is_listed(code, index.nerd or None):
            first.append(code)
    words = text.lower().split()
    if len(text) == 1 and not text.isalnum():
        return first
    whole = [re.compile(r"(?<![\w-])" + re.escape(word) + r"(?![\w])") for word in words]
    phrase = " ".join(words)
    ranked: list[tuple[bool, int, int, int]] = []
    for code, name in index.names:
        if all(word in name for word in words):
            ranked.append((phrase not in name, -sum(1 for pattern in whole if pattern.search(name)), len(name), code))
    ranked.sort()
    found = dict.fromkeys(first)
    found.update(dict.fromkeys(code for *_, code in ranked))
    return list(found)


# -- Recent --------------------------------------------------------------------------


def recent() -> list[int]:
    """The characters last taken, newest first."""
    from navigator.models.recent_char import RecentChar

    return [row.code for row in RecentChar.query().order("-seq").limit(RECENT_LIMIT).all()]


def remember(code: int) -> None:
    """*code* to the front of *Recent*, and the oldest past the limit out."""
    from navkit.database import DATABASE

    from navigator.models.recent_char import RecentChar

    with DATABASE.transaction():
        newest = RecentChar.query().order("-seq").first()
        RecentChar.upsert(code=code, seq=1 if newest is None else newest.seq + 1)
        for row in RecentChar.query().order("-seq").offset(RECENT_LIMIT).all():
            row.delete()
