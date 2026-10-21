"""Panel > Multi-rename (Alt+A): many files renamed by one pattern, seen before it is done.

A departure: Total Commander's *Multi-Rename Tool*.  DOS Navigator's own
group rename was F6's ``*``/``?`` mask (:func:`navigator.lib.file_ops.filecopy.apply_mask`),
which stays; this is for what a mask cannot say -- a counter, a part of the
name, a date, a regular expression, a change of case.

**A rule** (:class:`Rule`) makes each new name in three steps:

1. *Name mask* and *Extension mask* build the stem and the extension from
   placeholders in ``[ ]``, anything else being itself:

   - ``[N]`` the old stem; ``[N3]`` its third character; ``[N2-5]`` the second
     to the fifth; ``[N2-]`` from the second on; ``[N2,4]`` four from the
     second.  A negative position counts from the end: ``[N-3-]`` the last
     three.
   - ``[E]`` the old extension, without its dot, in the same ways.
   - ``[P]`` the name of the directory the file is in, in the same ways.
   - ``[C]`` the counter -- *Start*, *Step* and *Digits* of the dialog, or of
     the placeholder itself: ``[C10+5:3]`` counts 010, 015, 020 ...; any of
     the three parts may be left out (``[C:2]``).
   - ``[Y]`` ``[M]`` ``[D]`` ``[h]`` ``[m]`` ``[s]``: the file's modification
     time, the year as four digits, the rest as two.
   - ``[[]`` and ``[]]``: a ``[`` and a ``]``.

   An empty extension leaves the name without a dot.  A directory's name is
   all stem, as is a dot-file's (``.bashrc`` has no extension).

2. *Search for* / *Replace with*, over the whole name: plain text or, with
   *Regular expression*, Python's ``re`` (``\\1`` and ``\\g<name>`` in the
   replacement); every match, or the first only; ignoring case unless *Case
   sensitive* is ticked.

3. *Case*: kept, lower, upper, every word capitalised, or the first letter
   alone upper and the rest lower.

**What is done** (:func:`plan`) is checked before anything is renamed: a
name left empty, holding a ``/``, or ``.``/``..``; two files given one
name; a name already taken by a file that is not itself being renamed away.
A file whose name comes out unchanged is left alone.  Names swapped among
the files (``a`` to ``b`` and ``b`` to ``a``) go through a temporary name
first (:func:`steps`), so a chain or a cycle renames whole.
"""

from __future__ import annotations

import re
import time
from collections.abc import Hashable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any, Callable

from navkit.i18n import tr

from navigator.lib.system.job import Job, Stopped

#: How *Case* may change a name, in the dialog's order.
CASES = ("keep", "lower", "upper", "title", "first")

#: What :func:`plan` may find wrong with a row (the dialog puts each in words).
EMPTY, SLASH, DOTS, TWICE, TAKEN = "empty", "slash", "dots", "twice", "taken"


class RuleError(ValueError):
    """A mask or a regular expression that cannot be read; ``str()`` says why."""


@dataclass(frozen=True)
class Rule:
    """How new names are made (the module docstring has the language)."""

    name_mask: str = "[N]"
    ext_mask: str = "[E]"
    search: str = ""
    replace: str = ""
    regex: bool = False
    case_sensitive: bool = False
    first_only: bool = False
    case: str = "keep"
    counter_start: int = 1
    counter_step: int = 1
    counter_width: int = 1


@dataclass(frozen=True)
class Item:
    """A file to rename: its name, what it is, and where it is.

    *place* is the directory it is in (a :class:`~navigator.lib.drives.Location`
    in Navigator; anything hashable that ``/`` joins to a name will do).
    """

    name: str
    place: Any
    is_dir: bool = False
    mtime: float = 0.0
    parent_name: str = ""


@dataclass
class Row:
    """One file's part of a plan: its new name, and what is wrong with it if anything."""

    item: Item
    new: str
    problem: str | None = None

    @property
    def changed(self) -> bool:
        return self.new != self.item.name


def split(name: str, is_dir: bool = False) -> tuple[str, str]:
    """*name* as stem and extension (no dot): a directory's, and a
    dot-file's with no other dot, are all stem."""
    if is_dir:
        return name, ""
    dot = name.rfind(".")
    if dot <= 0:
        return name, ""
    return name[:dot], name[dot + 1:]


# -- the masks ------------------------------------------------------------------------------

_RANGE = re.compile(r"^(-?\d+)?(?:(-)(-?\d+)?|,(\d+))?$")
_COUNTER = re.compile(r"^(\d+)?(?:\+(-?\d+))?(?::(\d+))?$")
_TIME = {"Y": "%Y", "M": "%m", "D": "%d", "h": "%H", "m": "%M", "s": "%S"}


def _part(text: str, spec: str, token: str) -> str:
    """*text*, or the characters of it *spec* (what follows ``N``/``E``/``P``) names."""
    if not spec:
        return text
    found = _RANGE.match(spec)
    if found is None or found.group(1) is None:
        raise RuleError(tr("[{token}] is not a placeholder").format(token=token))
    start = int(found.group(1))
    index = start - 1 if start > 0 else len(text) + start
    index = max(0, index)
    if found.group(4) is not None:
        return text[index:index + int(found.group(4))]
    if found.group(2) is None:
        return text[index:index + 1]
    if found.group(3) is None:
        return text[index:]
    end = int(found.group(3))
    stop = end if end > 0 else len(text) + end + 1
    return text[index:max(index, stop)]


def compile_mask(mask: str) -> list[str | tuple[str, str]]:
    """*mask* as literal text and ``(letter, spec)`` placeholders, in order.
    Raises :class:`RuleError` for a ``[`` never closed or a letter not known."""
    parts: list[str | tuple[str, str]] = []
    literal = ""
    index = 0
    while index < len(mask):
        char = mask[index]
        if char == "]" and not mask.startswith("]]", index):
            literal += char
            index += 1
            continue
        if char != "[":
            literal += char
            index += 1
            continue
        if mask.startswith("[[]", index):
            literal += "["
            index += 3
            continue
        if mask.startswith("[]]", index):
            literal += "]"
            index += 3
            continue
        close = mask.find("]", index + 1)
        if close < 0:
            raise RuleError(tr("A [ is never closed"))
        token = mask[index + 1:close]
        letter, spec = token[:1], token[1:]
        if letter not in "NEPC" and not (letter in _TIME and not spec):
            raise RuleError(tr("[{token}] is not a placeholder").format(token=token))
        if letter == "C" and _COUNTER.match(spec) is None:
            raise RuleError(tr("[{token}] is not a placeholder").format(token=token))
        if letter in "NEP" and spec and _RANGE.match(spec) is None:
            raise RuleError(tr("[{token}] is not a placeholder").format(token=token))
        if literal:
            parts.append(literal)
            literal = ""
        parts.append((letter, spec))
        index = close + 1
    if literal:
        parts.append(literal)
    return parts


def _fill(parts: Sequence[str | tuple[str, str]], item: Item, number: int, rule: Rule) -> str:
    stem, ext = split(item.name, item.is_dir)
    out = []
    for part in parts:
        if isinstance(part, str):
            out.append(part)
            continue
        letter, spec = part
        token = letter + spec
        if letter == "N":
            out.append(_part(stem, spec, token))
        elif letter == "E":
            out.append(_part(ext, spec, token))
        elif letter == "P":
            out.append(_part(item.parent_name, spec, token))
        elif letter == "C":
            found = _COUNTER.match(spec)
            start = int(found.group(1)) if found.group(1) is not None else rule.counter_start
            step = int(found.group(2)) if found.group(2) is not None else rule.counter_step
            width = int(found.group(3)) if found.group(3) is not None else rule.counter_width
            value = start + number * step
            out.append(("-" if value < 0 else "") + str(abs(value)).zfill(width))
        else:
            out.append(time.strftime(_TIME[letter], time.localtime(item.mtime)))
    return "".join(out)


def _searcher(rule: Rule) -> Callable[[str], str] | None:
    if not rule.search:
        return None
    flags = 0 if rule.case_sensitive else re.IGNORECASE
    count = 1 if rule.first_only else 0
    if rule.regex:
        try:
            pattern = re.compile(rule.search, flags)
        except re.error as error:
            raise RuleError(tr("Not a regular expression: {reason}").format(reason=error)) from None

        def change(name: str) -> str:
            try:
                return pattern.sub(rule.replace, name, count=count)
            except (re.error, IndexError) as error:
                raise RuleError(tr("Cannot replace with {text}: {reason}").format(
                    text=rule.replace, reason=error)) from None
        return change
    pattern = re.compile(re.escape(rule.search), flags)
    return lambda name: pattern.sub(lambda _match: rule.replace, name, count=count)


def _cased(name: str, case: str) -> str:
    if case == "lower":
        return name.lower()
    if case == "upper":
        return name.upper()
    if case == "title":
        return re.sub(r"[^\W_]+", lambda match: match.group(0)[:1].upper() + match.group(0)[1:].lower(), name)
    if case == "first":
        return name[:1].upper() + name[1:].lower()
    return name


def new_names(rule: Rule, items: Sequence[Item]) -> list[str]:
    """Each of *items*' new name under *rule*, in order (the counter's order).
    Raises :class:`RuleError` if the rule cannot be read."""
    name_parts = compile_mask(rule.name_mask)
    ext_parts = compile_mask(rule.ext_mask)
    change = _searcher(rule)
    names = []
    for number, item in enumerate(items):
        stem = _fill(name_parts, item, number, rule)
        ext = _fill(ext_parts, item, number, rule)
        name = f"{stem}.{ext}" if ext else stem
        if change is not None:
            name = change(name)
        names.append(_cased(name, rule.case))
    return names


def plan(rule: Rule, items: Sequence[Item], taken: dict[Hashable, set[str]] | None = None) -> list[Row]:
    """*items* under *rule*, each row's problem found (the module docstring
    lists them).  *taken* is the names already in each place, as far as
    they are known; a place left out is taken to hold only *items*."""
    rows = [Row(item, new) for item, new in zip(items, new_names(rule, items))]
    taken = taken or {}
    leaving: dict[Hashable, set[str]] = {}
    for row in rows:
        if row.changed:
            leaving.setdefault(row.item.place, set()).add(row.item.name)
    seen: dict[tuple[Hashable, str], Row] = {}
    for row in rows:
        if not row.changed:
            continue
        place, new = row.item.place, row.new
        if not new:
            row.problem = EMPTY
        elif "/" in new or "\0" in new:
            row.problem = SLASH
        elif new in (".", ".."):
            row.problem = DOTS
        elif (place, new) in seen:
            row.problem = TWICE
            seen[(place, new)].problem = seen[(place, new)].problem or TWICE
        elif new in taken.get(place, ()) and new not in leaving.get(place, ()):
            row.problem = TAKEN
        seen.setdefault((place, new), row)
    # A name kept by an unchanged row is taken, though it is one of *items*.
    kept = {(row.item.place, row.item.name) for row in rows if not row.changed}
    for row in rows:
        if row.changed and row.problem is None and (row.item.place, row.new) in kept:
            row.problem = TAKEN
    return rows


# -- doing it ---------------------------------------------------------------------------------


@dataclass(frozen=True)
class Step:
    """One rename, *old* to *new* in *place*; *final* is the name it is
    after, when *new* is a temporary one."""

    place: Any
    old: str
    new: str
    final: str


def steps(pairs: Iterable[tuple[Any, str, str]]) -> list[Step]:
    """*pairs* ``(place, old, new)`` as renames in an order that never lands on
    a name still to be renamed away: one whose new name is another's old one
    goes through a temporary name, out of the way, first."""
    pairs = list(pairs)
    sources = {(place, old) for place, old, _ in pairs}
    first: list[Step] = []
    middle: list[Step] = []
    last: list[Step] = []
    for number, (place, old, new) in enumerate(pairs):
        if (place, new) in sources:
            temporary = f".navrename-{number}-{old}"
            first.append(Step(place, old, temporary, new))
            last.append(Step(place, temporary, new, new))
        else:
            middle.append(Step(place, old, new, new))
    return first + middle + last


class RenameJob(Job):
    """A batch under way: how far it is, and what has been renamed (for Undo)."""

    def __init__(self, asker: Callable[[Any], Any] | None = None) -> None:
        super().__init__(asker)
        self.done: list[tuple[Any, str, str]] = []
        self.count = 0
        self.total = 0
        self.current = ""


def run(pairs: Sequence[tuple[Any, str, str]], job: RenameJob,
        drive_for: Callable[[Any], Any]) -> list[tuple[Any, str, str]]:
    """Rename *pairs* ``(place, old, new)`` on a thread, as :func:`steps`
    orders them, on the drive *drive_for* gives each place.  A name already
    taken is refused, as DOS's rename refused it.  A failure asks
    (:class:`navigator.lib.file_ops.filecopy.Failure`) whether to skip it or
    stop; a file left under its temporary name by one is put back.  Returns,
    and keeps in ``job.done``, what was renamed."""
    from navigator.lib.file_ops.filecopy import Failure

    planned = steps(pairs)
    job.total = len(pairs)
    origin = {(step.place, step.new): step.old for step in planned if step.new != step.final}
    failed: set[tuple[Any, str]] = set()
    for step in planned:
        job.wait_while_paused()
        if job.stopped:
            raise Stopped
        source_key = (step.place, step.old)
        if source_key in failed:
            continue
        drive = drive_for(step.place)
        job.current = step.old if step.new == step.final else step.final
        try:
            target = step.place / step.new
            if drive.lexists(target) and not drive.same_file(step.place / step.old, target):
                raise FileExistsError(0, tr("a file of that name is already there"))
            drive.rename(step.place / step.old, target)
        except OSError as error:
            old = origin.get(source_key, step.old)
            reason = error.strerror or str(error)
            if step.old != old:
                # Stranded under its temporary name: put back, unless another
                # file has its old name by now -- never over one.
                try:
                    if drive.lexists(step.place / old):
                        raise FileExistsError(0, "taken")
                    drive.rename(step.place / step.old, step.place / old)
                except OSError:
                    reason = tr("{reason}; it is left as {name}").format(reason=reason, name=step.old)
            failed.add((step.place, step.new))
            answer = job.ask(Failure(step.place / old, lambda: tr("Could not rename {old}\nto {new}: {reason}"),
                                     {"old": old, "new": step.final, "reason": reason}))
            if not answer:
                raise Stopped from None
            continue
        if step.new == step.final:
            old = origin.get(source_key, step.old)
            job.done.append((step.place, old, step.new))
            job.count = len(job.done)
    for place in {place for place, _, _ in pairs}:
        try:
            drive_for(place).finish()
        except OSError:
            pass
    return job.done


@dataclass
class Batch:
    """The last batch renamed, for *Undo multi-rename*: what was renamed, newest last."""

    done: list[tuple[Any, str, str]] = field(default_factory=list)

    def undo_pairs(self) -> list[tuple[Any, str, str]]:
        """What puts the batch back: each new name to its old, the last first."""
        return [(place, new, old) for place, old, new in reversed(self.done)]
