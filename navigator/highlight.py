"""Syntax highlighting: DOS Navigator's ``DN.HGL`` and ``DoHighlite``, by Pygments.

DN's editor coloured a text when ``DN.HGL`` had a ``FILES`` mask for it
(``InitEditorHighLight`` in ``MACRO.PAS``), and ``DoHighlite``
(``MICROED.PAS``) found comments, quoted strings, symbols and numbers in each
line on its own.  Here **Pygments lexes, in token mode**, and the widgets
paint each token through the stylesheet part ``::token``, whose classes are
the pieces of the token's type (:func:`classes_of`): ``Comment.Single`` is
``::token.comment.single``.  ``navigator.nss`` gives comments, strings,
numbers and symbols DN's four slots, [164], [190], [191] and [189];
everything else stays normal text, keywords included, as DN left them.

Departures: Pygments' lexers stand for ``DN.HGL``'s comment and keyword
lists, so a construct running over several lines -- a C comment, a Python
triple-quoted string -- is coloured whole, where DN saw one line at a time;
and ``highlight.ini`` (:data:`navigator.associations.HIGHLIGHT`) stands for
``DN.HGL`` itself, a mask per section naming a Pygments lexer, plus the
``[#!]`` section for files known by their first line.  The editor options
``DN.HGL`` carried too (``AUTOINDENT``, the margins) stay in
``navigator.ini``.

Nothing here touches anything reactive: the lexing runs on a thread, and
:func:`read_rules` reads the file.  Pygments itself is imported only when a
file is first lexed.
"""

from __future__ import annotations

import configparser
import fnmatch
import os
import re
import threading
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Sequence

from navigator.associations import HIGHLIGHT, TEMPLATES, path_of
from navigator.filetypes import patterns

#: A coloured stretch of text: start, end (exclusive) and the token's classes.
#: String indices in a line for the editor, byte offsets in the file for the
#: viewer.
Span = tuple[int, int, tuple[str, ...]]

#: What ``lexer`` may say besides a Pygments name: no colours at all, or
#: Pygments' own guess from the file's name.
NONE, AUTO = "none", "auto"


@dataclass(frozen=True)
class Rules:
    """``highlight.ini`` as read: what lexes which file."""

    #: Each mask section's patterns and the lexer it names, in file order.
    masks: tuple[tuple[tuple[str, ...], str], ...] = ()
    #: ``[#!]``: an interpreter's name and its lexer.
    shebangs: tuple[tuple[str, str], ...] = ()
    #: ``[*]``'s lexer, for a file nothing above names: :data:`AUTO` or :data:`NONE`.
    fallback: str = AUTO

    def by_mask(self, file_name: str) -> str | None:
        name = file_name.lower()
        for masks, lexer in self.masks:
            if any(fnmatch.fnmatchcase(name, mask.lower()) for mask in masks):
                return lexer
        return None

    def by_shebang(self, first_line: str) -> str | None:
        interpreter = shebang_interpreter(first_line)
        if interpreter is None:
            return None
        table = dict(self.shebangs)
        bare = re.sub(r"[\d.]+$", "", interpreter)
        return table.get(interpreter) or table.get(bare)


def parse_rules(text: str, source: str = "<string>") -> Rules:
    """*text* as :class:`Rules`, or ``ValueError`` saying where it is not an ``.ini``.

    A section is a mask with a ``lexer`` line, ``[#!]`` whose keys are
    interpreters (``;``-separated, as masks are), or ``[*]``.
    """
    parser = configparser.ConfigParser(
        interpolation=None, delimiters=("=",), comment_prefixes=("#", ";"),
        inline_comment_prefixes=None, empty_lines_in_values=False, default_section="\0",
    )
    parser.optionxform = str.lower  # type: ignore[assignment,method-assign]
    try:
        parser.read_string(text, source)
    except configparser.Error as error:
        raise ValueError(str(error)) from None
    masks, shebangs, fallback = [], [], AUTO
    for section in parser.sections():
        if section.strip() == "#!":
            for names, lexer in parser.items(section):
                shebangs.extend((name, lexer.strip().lower()) for name in patterns(names))
            continue
        lexer = parser.get(section, "lexer", fallback="").strip().lower()
        if not lexer:
            continue
        if section.strip() == "*":
            fallback = NONE if lexer == NONE else AUTO
            continue
        masks.append((tuple(patterns(section)), lexer))
    return Rules(tuple(masks), tuple(shebangs), fallback)


#: The template's own rules: what a missing ``highlight.ini`` means, so a
#: file removed after the first start still colours as it did.
DEFAULT_RULES = parse_rules(TEMPLATES[HIGHLIGHT], HIGHLIGHT)

_rules_lock = threading.Lock()
_rules_cache: dict[str, tuple[tuple[int, int], Rules]] = {}


def read_rules() -> Rules:
    """``highlight.ini`` beside ``navigator.ini``, read again only once it has
    changed; the template's rules when it is missing or will not parse (a
    broken file is not worth failing to open the text over).  Touches the
    file system: run it on a thread."""
    path = path_of(HIGHLIGHT)
    try:
        info = os.stat(path)
    except OSError:
        return DEFAULT_RULES
    stamp = (info.st_mtime_ns, info.st_size)
    with _rules_lock:
        cached = _rules_cache.get(str(path))
        if cached is not None and cached[0] == stamp:
            return cached[1]
    try:
        rules = parse_rules(path.read_text(encoding="utf-8", errors="replace"), str(path))
    except (OSError, ValueError):
        rules = DEFAULT_RULES
    with _rules_lock:
        _rules_cache[str(path)] = (stamp, rules)
    return rules


def shebang_interpreter(first_line: str) -> str | None:
    """The interpreter a ``#!`` line runs, by its base name, or None.

    ``env`` is looked through, its options and ``NAME=value`` assignments
    skipped: ``#!/usr/bin/env -S python3.12 -u`` is ``python3.12``.
    """
    if not first_line.startswith("#!"):
        return None
    words = first_line[2:].split()
    if not words:
        return None
    name = os.path.basename(words[0])
    if name == "env":
        rest = [word for word in words[1:] if not word.startswith("-") and "=" not in word]
        if not rest:
            return None
        name = os.path.basename(rest[0])
    return name.lower() or None


@lru_cache(maxsize=None)
def _lexer_named(name: str) -> Any:
    """A lexer for the Pygments name or alias *name*, or None if there is none.

    Shared between threads: a lexer holds only its options, and every
    ``get_tokens_unprocessed`` call has its own generator.
    """
    from pygments.lexers import get_lexer_by_name
    from pygments.util import ClassNotFound

    try:
        return _usable(get_lexer_by_name(name, stripnl=False, ensurenl=False))
    except ClassNotFound:
        return None


@lru_cache(maxsize=256)
def _lexer_guessed(file_name: str, head: str) -> Any:
    from pygments.lexers import find_lexer_class_for_filename

    try:
        cls = find_lexer_class_for_filename(file_name, head)
    except Exception:  # a lexer's analyse_text may choke on odd text
        return None
    return _usable(cls(stripnl=False, ensurenl=False)) if cls is not None else None


def _usable(lexer: Any) -> Any:
    """None for plain text, which has nothing to colour."""
    from pygments.lexers.special import TextLexer

    return None if isinstance(lexer, TextLexer) else lexer


def lexer_for(file_name: str, first_line: str, rules: Rules | None = None) -> Any:
    """The lexer for the file called *file_name* whose first line is
    *first_line*, or None when it is not to be coloured.

    The first ``highlight.ini`` mask that takes the name decides; then
    ``[#!]`` by the interpreter on the first line; then, unless ``[*]`` says
    ``none``, Pygments' own guess from the name.  A lexer name Pygments does
    not know counts as no answer at that step.  *rules* default to
    :func:`read_rules`' -- on a thread, then.
    """
    if rules is None:
        rules = read_rules()
    name = os.path.basename(file_name)
    for chosen in (rules.by_mask(name), rules.by_shebang(first_line)):
        if chosen == NONE:
            return None
        if chosen is not None and chosen != AUTO:
            lexer = _lexer_named(chosen)
            if lexer is not None:
                return lexer
    if rules.fallback == NONE:
        return None
    return _lexer_guessed(name, first_line)


@lru_cache(maxsize=None)
def classes_of(token_type: Sequence[str]) -> tuple[str, ...]:
    """The part classes a token of *token_type* is painted with: its type's
    pieces lower-cased, ``Literal.String.Double`` giving ``literal``, ``string``
    and ``double``.  Text, whitespace, errors and the bare root give none --
    plain text, no span."""
    pieces = tuple(piece.lower() for piece in token_type)
    if not pieces or pieces[0] in ("text", "whitespace", "error", "other"):
        return ()
    return pieces


def lex_lines(lexer: Any, lines: Sequence[str], until_line: int,
              stop: threading.Event | None = None) -> list[list[Span]] | None:
    """The spans of each of *lines*, from the first through *until_line* (or
    the last, if fewer), lexed as one text joined with line breaks.

    Spans are string indices within their line; a token running over a break
    is cut at it.  Lines past *until_line* are not lexed at all, which is
    what keeps typing near the top of a long file cheap.  None if *stop* was
    set meanwhile.
    """
    last = min(until_line, len(lines) - 1)
    spans: list[list[Span]] = [[] for _ in range(last + 1)]
    if last < 0:
        return spans
    text = "\n".join(lines)
    number, start = 0, 0
    end_of_line = len(lines[0])
    for index, token_type, value in lexer.get_tokens_unprocessed(text):
        if stop is not None and stop.is_set():
            return None
        classes = classes_of(token_type)
        position, finish = index, index + len(value)
        while position < finish:
            while position > end_of_line:
                number += 1
                if number > last:
                    return spans
                start = end_of_line + 1
                end_of_line = start + len(lines[number])
            if position == end_of_line:
                # The break itself belongs to no line.
                position += 1
                continue
            cut = min(finish, end_of_line)
            if classes:
                spans[number].append((position - start, cut - start, classes))
            position = cut
    return spans


def lex_bytes(lexer: Any, data: bytes, base: int, codec: str = "utf-8",
              stop: threading.Event | None = None) -> list[Span] | None:
    """The coloured spans of *data*, which starts at byte *base* of the file,
    in byte offsets; only those with classes, in order.  None if *stop* was
    set meanwhile.

    *codec* is the viewer's encoding: UTF-8 with undecodable bytes kept as
    themselves, or a one-byte code page, where a character is a byte.
    """
    one_byte = codec != "utf-8" or data.isascii()
    if codec == "utf-8":
        text = data.decode("utf-8", errors="surrogateescape")
    else:
        text = data.decode(codec, errors="replace")
    spans: list[Span] = []
    at = base
    for _, token_type, value in lexer.get_tokens_unprocessed(text):
        if stop is not None and stop.is_set():
            return None
        size = len(value) if one_byte else len(value.encode("utf-8", errors="surrogateescape"))
        classes = classes_of(token_type)
        if classes and size:
            spans.append((at, at + size, classes))
        at += size
    return spans


def shift_spans(spans: list[list[Span]], kind: str, start: Any, end: Any) -> None:
    """Move per-line *spans* in place with an edit, so colours stay on their
    text until it is lexed again.

    *kind*, *start* and *end* are ``EditBuffer``'s report: ``insert`` put text
    from *start* to *end*, ``delete`` took out what lay between them.  Text
    typed inside a span widens it, so typing in a comment stays a comment.
    """
    line, index = start.line, start.index
    if line >= len(spans):
        return
    if kind == "insert":
        width = end.index - index
        before, after = [], []
        for first, last, classes in spans[line]:
            if last <= index:
                before.append((first, last, classes))
            elif first >= index:
                after.append((first, last, classes))
            elif end.line == line:
                before.append((first, last + width, classes))
            else:
                before.append((first, index, classes))
                after.append((index, last, classes))
        moved = [(first - index + end.index, last - index + end.index, classes)
                 for first, last, classes in after]
        if end.line == line:
            spans[line] = before + moved
            return
        spans[line] = before
        spans[line + 1:line + 1] = [[] for _ in range(end.line - line - 1)] + [moved]
        return
    if end.line == line:
        width = end.index - index

        def place(at: int) -> int:
            return at if at <= index else index if at <= end.index else at - width

        spans[line] = [(place(first), place(last), classes) for first, last, classes in spans[line]
                       if place(last) > place(first)]
        return
    kept = [(first, min(last, index), classes) for first, last, classes in spans[line]
            if first < index]
    if end.line < len(spans):
        tail = [(max(first, end.index) - end.index + index, last - end.index + index, classes)
                for first, last, classes in spans[end.line] if last > end.index]
    else:
        tail = []
    spans[line] = kept + tail
    del spans[line + 1:end.line + 1]
