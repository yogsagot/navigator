#!/usr/bin/env python3
"""Keep the translation catalogues in step with the text the program shows.

Run it from the repository root::

    ./venv/bin/python tools/i18n.py extract lv     # create or update lv.toml
    ./venv/bin/python tools/i18n.py check          # every catalogue; exit 1 on a gap
    ./venv/bin/python tools/i18n.py check lv

What counts as text, and how a catalogue is rewritten, is
:mod:`navml.translate`'s -- the same work ``python -m navml extract`` does for
any one package; this script runs it over both of this repository's layers.

**extract** keeps every translation it finds, adds what is missing as ``""``
with where it is used as a comment, and moves what is no longer used to an
``[unused]`` table, which :mod:`navkit.i18n` does not read, so nothing a
translator wrote is thrown away.  **check** writes nothing; it reports missing
and unused entries, and captions of one dialog or menu whose translated
hotkeys clash where the English ones did not, and exits 1 if there is any.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from navml.translate import Found, catalogue_path, read, scan, write  # noqa: E402

LAYERS = ("navml", "navigator")


def scan_all() -> dict[str, Found]:
    """Each layer's text, the application's without what the library has."""
    return {layer: scan(ROOT / layer) for layer in LAYERS}


# -- checking ----------------------------------------------------------------


def _hotkey(caption: str) -> str | None:
    start = caption.find("~")
    if start < 0 or start + 1 >= len(caption):
        return None
    return caption[start + 1].casefold()


def _clashes(scope: list[str], strings: dict) -> list[str]:
    def letters(captions):
        seen: dict[str, str] = {}
        clash = []
        for caption in captions:
            letter = _hotkey(caption)
            if letter is None:
                continue
            if letter in seen and seen[letter] != caption:
                clash.append(f"{seen[letter]!r} and {caption!r} share ~{letter}~")
            seen.setdefault(letter, caption)
        return clash

    if letters(scope):
        return []
    translated = [strings.get(c) if isinstance(strings.get(c), str) and strings.get(c) else c for c in scope]
    return letters(translated)


def check(code: str, layers: dict[str, Found]) -> int:
    problems = 0
    shown: dict = {}
    for layer, found in layers.items():
        path = catalogue_path(ROOT / layer, code)
        catalogue = read(path)
        strings = catalogue.get("strings", {})
        # What is shown is every layer below merged in, as navkit.i18n reads it.
        shown = {**shown, **strings}
        missing = [k for k in found.keys if strings.get(k) in (None, "", [])]
        unused = [k for k in strings if k not in found.keys]
        name = path.relative_to(ROOT)
        if missing:
            print(f"{name}: {len(missing)} of {len(found.keys)} untranslated")
        for key in unused:
            print(f"{name}: unused {key!r}")
        clashes = [
            f"{where}: {clash}"
            for where, scope in found.scopes
            for clash in _clashes(scope, shown)
        ]
        for clash in clashes:
            print(f"{name}: {clash}")
        problems += len(missing) + len(unused) + len(clashes)
    return problems


def codes() -> list[str]:
    return sorted({p.stem for layer in LAYERS for p in (ROOT / layer / "locales").glob("*.toml")})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="action", required=True)
    extract = sub.add_parser("extract", help="create or update a language's catalogues")
    extract.add_argument("code", help="the language: lv, ru, de_AT, ...")
    extract.add_argument("--name", help="the language's own name, for a new catalogue")
    checking = sub.add_parser("check", help="report gaps; exit 1 if there are any")
    checking.add_argument("code", nargs="*", help="languages to check (default: every one)")
    args = parser.parse_args()

    layers = scan_all()
    if args.action == "extract":
        for layer, found in layers.items():
            path = catalogue_path(ROOT / layer, args.code)
            existing = read(path)
            if args.name:
                existing.setdefault("meta", {})["name"] = args.name
            added, unused = write(path, args.code, found, existing)
            print(f"{path.relative_to(ROOT)}: {len(found.keys)} strings, {added} new, {unused} unused")
        return 0
    problems = sum(check(code, layers) for code in (args.code or codes()))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
