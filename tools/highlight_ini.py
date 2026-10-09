#!/usr/bin/env python3
"""Write ``navigator/assets/highlight.ini``, the template of ``highlight.ini``,
from the Pygments installed: every language it lexes, with the file names it
claims.

    ./venv/bin/python tools/highlight_ini.py          # write it
    ./venv/bin/python tools/highlight_ini.py --check  # exit 1 when it is stale

What the file says is what Pygments would do anyway -- ``[*] lexer = auto``
already hands it every file nothing above names -- but written out, so a user
can see what colours a file and change one language without losing the rest.
Three parts:

- :data:`HEAD`, Navigator's own: languages Pygments does not know by name
  (navml's ``.nml`` and ``.nss``) and an example of ``none``.
- One section per lexer, its file-name patterns and its first alias, under a
  comment naming it.  A pattern that can take the same name as another
  lexer's -- ``*.h`` is C's and Objective-C's, ``*.s`` and ``*.S`` fold
  together -- goes to an ``auto`` section instead, naming the candidates, so
  Pygments goes on deciding those by the file's content.  Every pattern's own
  name therefore lexes here exactly as Pygments' guess would, which
  ``tests/test_highlight.py`` checks.
- :data:`SHEBANGS`, the ``[#!]`` section: Pygments has no table of
  interpreters (its lexers guess from the text), so this one is kept by hand.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pygments  # noqa: E402
from pygments.lexers._mapping import LEXERS  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "navigator" / "assets" / "highlight.ini"

PREAMBLE = """\
# Syntax highlighting: which Pygments lexer colours which file, in the editor
# and the viewer.  Options > Highlight file edit.  A section is a mask
# (`;'-separated patterns, case aside); the first that matches wins.  `lexer'
# is a Pygments name or alias (`python3 -m pygments -L lexers' lists them),
# `none' for no colours, or `auto' for Pygments' own choice by the file's name
# and content.  The colours are the theme's: ::token rules.
#
# Every language Pygments {version} knows by a file name is listed below, as
# Pygments itself would choose; change or delete any.  Written by
# tools/highlight_ini.py.
"""

#: Navigator's own, first so they win.
HEAD = """\
# -- Navigator's own ---------------------------------------------------------

# navml's markup is Kivy-shaped, which YAML comes closest to; its style sheets
# are CSS in shape.
[*.nml]
lexer = yaml

[*.nss]
lexer = css

# No colours at all.
[*.log]
lexer = none
"""

#: ``[#!]``: an interpreter's base name and the lexer for its scripts.
SHEBANGS: tuple[tuple[str, str], ...] = (
    ("python;pypy;pypy3", "python"),
    ("sh;bash;dash;ksh;mksh;ash;busybox", "bash"),
    ("zsh", "zsh"),
    ("fish", "fish"),
    ("csh;tcsh", "tcsh"),
    ("perl", "perl"),
    ("raku;perl6;rakudo", "raku"),
    ("ruby;jruby", "ruby"),
    ("node;nodejs;bun", "javascript"),
    ("deno;ts-node;tsx", "typescript"),
    ("php", "php"),
    ("lua;luajit", "lua"),
    ("tclsh;wish;expect", "tcl"),
    ("awk;gawk;mawk;nawk", "awk"),
    ("sed;gsed", "bash"),
    ("make;gmake", "make"),
    ("Rscript;R", "r"),
    ("julia", "julia"),
    ("groovy", "groovy"),
    ("scala", "scala"),
    ("kotlin", "kotlin"),
    ("elixir", "elixir"),
    ("escript;erl", "erlang"),
    ("guile;chicken;csi;gsi", "scheme"),
    ("racket", "racket"),
    ("sbcl;clisp;ecl", "common-lisp"),
    ("ocaml", "ocaml"),
    ("swift", "swift"),
    ("pwsh;powershell", "powershell"),
    ("octave", "octave"),
    ("crystal", "crystal"),
    ("nim", "nim"),
    ("dart", "dart"),
    ("runghc;runhaskell;stack", "haskell"),
    ("gnuplot", "gnuplot"),
    ("nix-shell", "nix"),
)

FOOTER = """\
# -- A file no mask names ----------------------------------------------------

# By its first line's #! interpreter: the command's base name, `env' and its
# options looked through; a trailing version, as in python3.12, may be left
# off.  Names are `;'-separated.
[#!]
{shebangs}

# Neither: Pygments' own guess from the file's name.  `lexer = none' here
# colours only the files named above.
[*]
lexer = auto
"""


def sample(glob: str) -> str:
    """A file name *glob* takes: ``*`` and ``?`` become ``x``, a class its first character."""
    name = re.sub(r"\[!?(.)[^\]]*\]", r"\1", glob)
    return name.replace("*", "x").replace("?", "x")


def lexers() -> list[tuple[str, str, tuple[str, ...]]]:
    """Each lexer with file names: ``(name, alias, patterns)``, by name; the
    plain-text lexer left out, its files having nothing to colour."""
    found = []
    for _, name, aliases, filenames, _ in LEXERS.values():
        if filenames and "text" not in aliases:
            found.append((name, aliases[0] if aliases else "", tuple(filenames)))
    return sorted(found, key=lambda entry: entry[0].lower())


def render() -> str:
    entries = lexers()
    claims: dict[str, set[str]] = defaultdict(set)   # pattern, folded -> lexer names
    for name, _, patterns in entries:
        for pattern in patterns:
            claims[pattern.lower()].add(name)

    def contested(name: str, pattern: str) -> bool:
        """Whether another lexer's pattern takes a name this one does, case aside."""
        if len(claims[pattern.lower()]) > 1:
            return True
        probe = sample(pattern).lower()
        return any(fnmatch.fnmatchcase(probe, other) and owners != {name}
                   for other, owners in claims.items())

    head_masks = re.findall(r"^\[([^\]]+)\]$", HEAD, re.M)
    sections, shared = [], defaultdict(list)
    for name, alias, patterns in entries:
        own = []
        for pattern in patterns:
            probe = sample(pattern).lower()
            if any(fnmatch.fnmatchcase(probe, mask.lower()) for mask in head_masks):
                raise SystemExit(f"Navigator's own section takes {name}'s {pattern}: move it")
            if alias and not contested(name, pattern):
                own.append(pattern)
            else:
                candidates = {owner for other, owners in claims.items()
                              if fnmatch.fnmatchcase(probe, other) for owner in owners}
                shared[tuple(sorted(candidates, key=str.lower))].append(pattern)
        if own:
            sections.append(f"# {name}\n[{';'.join(dict.fromkeys(own))}]\nlexer = {alias}\n")
    auto = []
    for candidates, patterns in sorted(shared.items(), key=lambda item: [c.lower() for c in item[0]]):
        auto.append(f"# {' or '.join(candidates)}, by the content\n"
                    f"[{';'.join(dict.fromkeys(patterns))}]\nlexer = auto\n")
    shebangs = "\n".join(f"{names} = {lexer}" for names, lexer in SHEBANGS)
    return "\n".join([
        PREAMBLE.format(version=pygments.__version__),
        HEAD,
        "# -- Claimed by more than one language: Pygments looks at the content -----\n",
        *auto,
        "# -- Every other language Pygments knows by name -------------------------\n",
        *sections,
        FOOTER.format(shebangs=shebangs),
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if the file is stale")
    args = parser.parse_args()
    text = render()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"{OUT.relative_to(Path.cwd()) if OUT.is_relative_to(Path.cwd()) else OUT} is out of date")
            return 1
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT} ({text.count(chr(10) + '[')} sections)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
