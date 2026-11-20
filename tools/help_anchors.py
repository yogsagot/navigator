"""Point a translated help page's links at its own headings.

A translated page under ``docs/CODE/`` keeps English's headings one for one
(the ``navigator-help`` skill), so a heading's GitHub slug differs from
English's but stands in the same place.  A translator writes a link as
English does, ``file-operations.md#copy``; this rewrites each such anchor to
the slug of the heading standing there in that language's target page
(``navigator.lib.help.pages.aliases``), so the link works on GitHub as in
Help.  An anchor the target already has is left alone.

    ./venv/bin/python tools/help_anchors.py [--check] [CODE ...]

``--check`` writes nothing and exits 1 when a page would change, or when a
link names a heading neither English nor the translation has.
"""

from __future__ import annotations

import argparse
import re
import sys
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from navigator.lib.help import pages  # noqa: E402
from navigator.lib.viewer import markdown  # noqa: E402

DOCS = ROOT / "docs"
ENGLISH = DOCS / pages.ENGLISH
#: An inline link's target with an anchor: ``](page.md#slug)`` or ``](#slug)``.
_LINK = re.compile(r"\]\((?P<target>[^()\s#]*)#(?P<anchor>[^()\s]+)\)")


@cache
def anchors(page: Path) -> tuple[str, ...]:
    """*page*'s heading anchors in order, as Help finds them."""
    return tuple(markdown.render(page.read_bytes(), 80).anchors)


def fix(page: Path, language: Path) -> tuple[str, list[str]]:
    """*page*'s text with its anchors rewritten, and what could not be."""
    text = page.read_text(encoding="utf-8")
    problems: list[str] = []

    def rewrite(match: re.Match[str]) -> str:
        target, anchor = match["target"], match["anchor"]
        other = (page.parent / target).resolve() if target else page
        if not other.is_file():
            return match[0]  # the docs test says so
        own = anchors(other)
        if anchor in own:
            return match[0]
        english = ENGLISH / other.relative_to(language)
        mapped = pages.aliases(list(anchors(english)), list(own)).get(anchor) if english.is_file() else None
        if mapped is None:
            problems.append(f"{page.relative_to(DOCS)}: no heading for {target}#{anchor}")
            return match[0]
        return f"]({target}#{mapped})"

    return _LINK.sub(rewrite, text), problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("languages", nargs="*", metavar="CODE")
    parser.add_argument("--check", action="store_true", help="write nothing; exit 1 when a page would change")
    options = parser.parse_args(argv)
    codes = options.languages or sorted(p.name for p in DOCS.iterdir() if p.is_dir() and p != ENGLISH)
    stale = False
    for code in codes:
        language = DOCS / code
        for page in sorted(language.rglob("*.md")):
            text, problems = fix(page, language)
            for problem in problems:
                print(problem, file=sys.stderr)
            stale = stale or bool(problems)
            if text != page.read_text(encoding="utf-8"):
                stale = True
                if options.check:
                    print(f"{page.relative_to(DOCS)}: anchors to rewrite", file=sys.stderr)
                else:
                    page.write_text(text, encoding="utf-8")
                    anchors.cache_clear()
    return 1 if stale and options.check else 0


if __name__ == "__main__":
    sys.exit(main())
