"""Pygments lexers for Navigator's own two languages: ``.nss`` and ``.nml``.

Pygments knows neither, so ``highlight.ini`` used to borrow CSS for a style
sheet and YAML for markup, and both read them wrong: CSS takes every
``$variable`` for an error and a top-level ``$name: value;`` for a selector,
and YAML sees no Python at all.  These read them as navkit and navml do:

- :class:`NssLexer`, the stylesheet grammar (``navkit/stylesheet.py``,
  *The grammar* in the ``navkit-stylesheet`` skill): selectors with states,
  ``::parts`` and ``:not()``, ``$variable`` definitions and uses, and values
  that are literals only -- the sixteen colour names, ``#rrggbb``,
  ``rgb()``, palette indices, ``true``/``false``/``default``/``inherit``.
  The colour names and ``Style``'s fields come from navkit itself.
- :class:`NmlLexer`, the markup (``navml/parser.py``): imports, block heads,
  the directives, ``id``, handlers and properties, whose values are Python --
  given to Pygments' Python lexer, continued while a bracket is open, as the
  parser continues a logical line -- and ``style:`` and ``keys:`` blocks,
  whose lines are ``.nss`` declarations and key bindings.  ``#`` opens a
  comment only before a blank, an end of line or a ``:`` (``#:`` is a doc
  comment), as the parser has it.

They live in the file manager, the one layer that depends on Pygments, rather
than beside the languages in ``navkit`` and ``navml``.  :mod:`navigator.highlight`
finds them by their aliases, ``nss`` and ``nml``; installed, the
``pygments.lexers`` entry points in ``pyproject.toml`` make them Pygments' own
as well (``pygmentize -l nml``).
"""

from __future__ import annotations

import re
from typing import Iterator

from pygments.lexer import Lexer, RegexLexer, bygroups, default, words
from pygments.lexers.python import PythonLexer
from pygments.token import (
    Comment, Keyword, Name, Number, Operator, Punctuation, String, Text, Whitespace,
    _TokenType,
)

from navkit.stylesheet import COLOR_NAMES, STYLE_FIELDS

__all__ = ["NmlLexer", "NssLexer"]


class NssLexer(RegexLexer):
    """A Navigator stylesheet: CSS in shape, its values literals only."""

    name = "Navigator stylesheet"
    url = "https://github.com/yogsagot/navigator"
    aliases = ["nss"]
    filenames = ["*.nss"]
    mimetypes = ["text/x-nss"]

    _name = r"[A-Za-z_][\w-]*"

    tokens = {
        "root": [
            (r"\s+", Whitespace),
            (r"/\*", Comment.Multiline, "comment"),
            (rf"(\$[\w-]+)(\s*)(:)", bygroups(Name.Variable, Whitespace, Punctuation), "value"),
            (r"\{", Punctuation, "block"),
            (r"(:)(not)(\()", bygroups(Punctuation, Keyword, Punctuation)),
            (rf"::{_name}", Name.Decorator),
            (rf":{_name}", Name.Decorator),
            (rf"\.{_name}", Name.Class),
            (rf"#{_name}", Name.Label),
            (_name, Name.Tag),
            (r"\*", Name.Tag),
            (r"[,>]", Operator),
            (r"\)", Punctuation),
            (r".", Text),
        ],
        "comment": [
            (r"[^*]+", Comment.Multiline),
            (r"\*/", Comment.Multiline, "#pop"),
            (r"\*", Comment.Multiline),
        ],
        "block": [
            (r"\s+", Whitespace),
            (r"/\*", Comment.Multiline, "comment"),
            (r"\}", Punctuation, "#pop"),
            (r";", Punctuation),
            (words(sorted(STYLE_FIELDS), suffix=r"(?=\s*:)"), Name.Property),
            (rf"{_name}(?=\s*:)", Name.Attribute),
            (r":", Punctuation, "value"),
            (r".", Text),
        ],
        "value": [
            (r"[ \t]+", Whitespace),
            (r"/\*", Comment.Multiline, "comment"),
            (r";", Punctuation, "#pop"),
            (r"\n", Whitespace, "#pop"),
            default("#pop"),
        ],
    }
    # The literals, in their own list so the markup's style blocks can lex a
    # value alone (:meth:`value_tokens`).
    _literals = [
        (r"\$[\w-]+", Name.Variable),
        (r"#[0-9A-Fa-f]{6}\b", Number.Hex),
        (r"(rgb)(\s*)(\()", bygroups(Name.Builtin, Whitespace, Punctuation), "rgb"),
        (r"\d+\b", Number.Integer),
        (words(("true", "false", "default", "inherit"), suffix=r"\b"), Keyword.Constant),
        (words(sorted(COLOR_NAMES, key=len, reverse=True), suffix=r"\b"), Name.Builtin),
        (_name, Name.Constant),
        (r"\|", Operator),
        (r"[^\s;}]", Text),
    ]
    tokens["value"][4:4] = _literals
    tokens["rgb"] = [
        (r"\s+", Whitespace),
        (r"\d+", Number.Integer),
        (r",", Punctuation),
        (r"\)", Punctuation, "#pop"),
        default("#pop"),
    ]

    def value_tokens(self, text: str) -> Iterator[tuple[int, _TokenType, str]]:
        """*text* lexed as one declaration's value: a style block's right-hand side."""
        return self.get_tokens_unprocessed(text, stack=("root", "value"))


#: A block head: ``Name:`` or ``Name(Base):``, maybe a comment after it.
_HEAD = re.compile(r"(\w+)(\s*)(?:(\()(\s*)([\w.]+)(\s*)(\)))?(\s*)(:)(\s*)(#(?:[ \t:].*)?)?\Z")
#: ``property name: value`` and the other directives that carry a value.
_DIRECTIVE = re.compile(
    r"(property|style_property|alias|field|index|unique)(\s+)(\w+)(\s*)(:)(\s*)(.*)\Z", re.S)
#: ``event ClickEvent``.
_EVENT = re.compile(r"(event)(\s+)(\w+)(\s*)\Z")
#: ``name: value``: a property, a handler, or ``id``.
_LINE = re.compile(r"(\w+)(\s*)(:)(\s*)(.*)\Z", re.S)
#: A ``keys:`` line: a key spec, then the command.
_BINDING = re.compile(r"([^:\s][^:]*?)(\s*)(:)(\s*)(.*)\Z", re.S)
#: A ``style:`` line: an ``.nss`` declaration.
_DECLARATION = re.compile(r"([A-Za-z_][\w-]*)(\s*)(:)(\s*)(.*)\Z", re.S)

_OPEN, _CLOSE = "([{", ")]}"


class NmlLexer(Lexer):
    """navml markup: Kivy's indented blocks, Python on the right of each colon."""

    name = "navml markup"
    url = "https://github.com/yogsagot/navigator"
    aliases = ["nml", "navml"]
    filenames = ["*.nml"]
    mimetypes = ["text/x-nml"]

    def __init__(self, **options):
        super().__init__(**options)
        self._python = PythonLexer(stripnl=False, ensurenl=False)
        self._nss = NssLexer(stripnl=False, ensurenl=False)

    def get_tokens_unprocessed(self, text: str) -> Iterator[tuple[int, _TokenType, str]]:
        # Nothing is kept on the lexer: one instance serves every thread.
        #: The block whose lines are not markup -- ``("style" | "keys", its
        #: head's indent)`` -- or None.
        block: tuple[str, int] | None = None
        #: Brackets a Python value has left open: its next line goes on with it.
        depth = 0
        at = 0
        for raw in text.splitlines(keepends=True):
            line = raw.rstrip("\r\n")
            ending = raw[len(line):]
            if depth > 0:
                depth = yield from self._python_part(at, line, depth)
            else:
                block, depth = yield from self._line(at, line, block)
            if ending:
                yield at + len(line), Whitespace, ending
            at += len(raw)

    # -- one line ------------------------------------------------------------------

    def _line(self, at: int, line: str, block):
        """One logical line's first physical line: the block it leaves open, and
        the brackets."""
        body = line.lstrip(" \t")
        indent = len(line) - len(body)
        if indent:
            yield at, Whitespace, line[:indent]
        at += indent
        if not body:
            return block, 0
        if body.startswith("#:"):
            yield at, Comment.Special, body
            return block, 0
        if body.startswith("#") and (len(body) == 1 or body[1] in " \t"):
            yield at, Comment.Single, body
            return block, 0
        if block is not None and indent > block[1]:
            if block[0] == "style":
                yield from self._declaration(at, body)
                return block, 0
            depth = yield from self._binding(at, body)
            return block, depth
        if indent == 0 and (body.startswith("from ") or body.startswith("import ")):
            depth = yield from self._python_part(at, body, 0)
            return None, depth
        match = _HEAD.match(body)
        if match is not None:
            name = match.group(1)
            kind = Keyword if name in ("style", "keys") else Name.Class
            types = (kind, Whitespace, Punctuation, Whitespace, Name.Class, Whitespace, Punctuation,
                     Whitespace, Punctuation, Whitespace, Comment.Single)
            yield from _groups(at, match, types)
            return ((name, indent) if name in ("style", "keys") else None), 0
        match = _EVENT.match(body)
        if match is not None:
            yield from _groups(at, match, (Keyword.Declaration, Whitespace, Name.Class, Whitespace))
            return None, 0
        match = _DIRECTIVE.match(body)
        if match is not None:
            yield from _groups(at, match, (Keyword.Declaration, Whitespace, Name.Variable, Whitespace,
                                           Punctuation, Whitespace), last=6)
            start = at + match.start(7)
            if match.group(1) == "style_property":
                yield from _shifted(start, self._nss.value_tokens(match.group(7)))
                return None, 0
            depth = yield from self._python_part(start, match.group(7), 0)
            return None, depth
        match = _LINE.match(body)
        if match is not None:
            name = match.group(1)
            kind = Keyword if name == "id" else Name.Function if name.startswith("on_") else Name.Attribute
            yield from _groups(at, match, (kind, Whitespace, Punctuation, Whitespace), last=4)
            start = at + match.start(5)
            if name == "id":
                if match.group(5):
                    yield start, Name.Variable, match.group(5)
                return None, 0
            depth = yield from self._python_part(start, match.group(5), 0)
            return None, depth
        depth = yield from self._python_part(at, body, 0)
        return None, depth

    def _declaration(self, at: int, body: str):
        match = _DECLARATION.match(body)
        if match is None:
            yield at, Text, body
            return
        field = match.group(1)
        yield from _groups(at, match, (Name.Property if field in STYLE_FIELDS else Name.Attribute,
                                       Whitespace, Punctuation, Whitespace), last=4)
        yield from _shifted(at + match.start(5), self._nss.value_tokens(match.group(5)))

    def _binding(self, at: int, body: str):
        """A ``keys:`` line; the brackets its command leaves open."""
        match = _BINDING.match(body)
        if match is None:
            yield at, Text, body
            return 0
        yield from _groups(at, match, (String.Symbol, Whitespace, Punctuation, Whitespace), last=4)
        return (yield from self._python_part(at + match.start(5), match.group(5), 0))

    def _python_part(self, at: int, source: str, depth: int):
        """*source* as Python at *at*; the brackets it leaves open, added to *depth*."""
        for index, token, value in self._python.get_tokens_unprocessed(source):
            if token in Punctuation or token in Operator:
                depth += sum(value.count(c) for c in _OPEN) - sum(value.count(c) for c in _CLOSE)
            yield at + index, token, value
        return max(depth, 0)


def _groups(at: int, match: re.Match, types, last: int | None = None):
    """*match*'s groups as tokens, the first *last* of them; an unmatched one is skipped."""
    for number, token in enumerate(types[:last] if last else types, start=1):
        value = match.group(number)
        if value:
            yield at + match.start(number), token, value


def _shifted(at: int, tokens):
    for index, token, value in tokens:
        yield at + index, token, value
