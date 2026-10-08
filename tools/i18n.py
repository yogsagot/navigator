#!/usr/bin/env python3
"""Keep the translation catalogues in step with the text the program shows.

Run it from the repository root::

    ./venv/bin/python tools/i18n.py extract lv     # create or update lv.toml
    ./venv/bin/python tools/i18n.py check          # every catalogue; exit 1 on a gap
    ./venv/bin/python tools/i18n.py check lv

**What counts as text** is what :mod:`navkit.i18n` will be asked for:

- in markup, the caption literals of ``text``/``title``/``label_text``/
  ``items``/``prompt`` -- found by compiling each line exactly as
  ``navml build`` does, so the two can never disagree;
- in Python, the literal first argument of ``tr()``, ``tr_n()`` (keyed by the
  singular), ``tr_plain()`` and ``tr_noop()`` (a table's entry, translated
  where it is shown);
- a class's ``title = "..."``: a command's, which the key bar translates.

Each layer has its own catalogues -- ``navml/locales`` for the library's
text, ``navigator/locales`` for the file manager's -- and a string the library
already has is not asked of the application again.

**extract** keeps every translation it finds, adds what is missing as ``""``
with where it is used as a comment, and moves what is no longer used to an
``[unused]`` table, which :mod:`navkit.i18n` does not read, so nothing a
translator wrote is thrown away.  **check** writes nothing; it reports missing
and unused entries, and captions of one dialog or menu whose translated
hotkeys clash where the English ones did not, and exits 1 if there is any.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from navkit.i18n import plural_form  # noqa: E402
from navml.expression import TRANSLATE, TRANSLATED, compile_expression  # noqa: E402
from navml.parser import Block, parse_file  # noqa: E402

LAYERS = ("navml", "navigator")
FUNCTIONS = {"tr", "tr_plain", "tr_n", "tr_noop"}


@dataclass
class Found:
    """Every key one layer uses, where, and which share a hotkey scope."""

    #: ``{key: [where, ...]}`` in the order first met.
    keys: dict[str, list[str]] = field(default_factory=dict)
    #: Keys that take a list of plural forms.
    plurals: set[str] = field(default_factory=set)
    #: Captions that answer to Alt+letter together: one dialog's, one menu's.
    scopes: list[tuple[str, list[str]]] = field(default_factory=list)

    def add(self, key: str, where: str) -> None:
        self.keys.setdefault(key, []).append(where)


# -- finding the text --------------------------------------------------------


def _captions(expression: str, line: int, filename: str) -> list[str]:
    compiled = compile_expression(expression, translate=True, line=line, filename=filename)
    if not compiled.translated:
        return []
    tree = ast.parse(compiled.expression, mode="eval")
    return [
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == TRANSLATE
    ]


def _markup(path: Path, found: Found) -> None:
    document = parse_file(path)
    where = str(path.relative_to(ROOT))

    def visit(block: Block) -> list[str]:
        mine: list[str] = []
        for prop in block.properties:
            if prop.name in TRANSLATED:
                for caption in _captions(prop.expression, prop.line, path.name):
                    found.add(caption, f"{where}:{prop.line}")
                    mine.append(caption)
        scope: list[str] = []
        for child in block.children:
            scope += visit(child)
        # An ``items`` list is a scope of its own, and the block's children
        # are another: a dialog's controls, a menu's entries.
        if len(mine) > 1:
            found.scopes.append((f"{where}:{block.line}", mine))
        if len(scope) > 1:
            found.scopes.append((f"{where}:{block.line}", scope))
        return mine

    visit(document.root)


def _python(path: Path, found: Found) -> None:
    where = str(path.relative_to(ROOT))
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=where)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = getattr(node.func, "id", getattr(node.func, "attr", None))
            args = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if name not in FUNCTIONS or not args:
                continue
            found.add(args[0], f"{where}:{node.lineno}")
            if name == "tr_n":
                found.plurals.add(args[0])
        elif isinstance(node, ast.ClassDef):
            for statement in node.body:
                if (
                    isinstance(statement, ast.Assign)
                    and [getattr(t, "id", None) for t in statement.targets] == ["title"]
                    and isinstance(statement.value, ast.Constant)
                    and isinstance(statement.value.value, str)
                    and statement.value.value
                ):
                    found.add(statement.value.value, f"{where}:{statement.lineno}")


def scan(layer: str) -> Found:
    found = Found()
    for path in sorted((ROOT / layer).rglob("*.nml")):
        _markup(path, found)
    for path in sorted((ROOT / layer).rglob("*.py")):
        if path.name.endswith("_nml.py") or "locales" in path.parts:
            continue
        _python(path, found)
    return found


def _tables(found: Found) -> None:
    """Tables of captions kept English and passed to ``tr()`` where shown.

    Read rather than marked: the palette's is regenerated by ``palconv.py
    --names``, and the key tables' titles head ``keybindings.ini`` sections.
    """
    from navigator import keybindings, palette

    where = "navigator/palette.py"
    for _, _, group, item in palette.ENTRIES:
        found.add(group, where)
        found.add(item, where)
    found.add(palette.NAVIGATOR_GROUP, where)
    for item in palette.DERIVED_ITEMS.values():
        found.add(item, where)
    for _, title, _ in keybindings.TABLES:
        found.add(title, "navigator/keybindings.py")


def scan_all() -> dict[str, Found]:
    """Each layer's text, the application's without what the library has."""
    layers = {layer: scan(layer) for layer in LAYERS}
    _tables(layers["navigator"])
    library = layers["navml"].keys
    application = layers["navigator"]
    application.keys = {k: v for k, v in application.keys.items() if k not in library}
    return layers


# -- the catalogue -----------------------------------------------------------


def _forms(code: str) -> int:
    return max(plural_form(code, n) for n in range(1000)) + 1


def _string(text: str) -> str:
    # A JSON string is a TOML basic string, escapes and all.
    return json.dumps(text, ensure_ascii=False)


def _value(value: str | list[str]) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(_string(v) for v in value) + "]"
    return _string(value)


def read(path: Path) -> dict:
    if not path.is_file():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def write(path: Path, code: str, found: Found, existing: dict) -> tuple[int, int]:
    strings = {**existing.get("unused", {}), **existing.get("strings", {})}
    meta = existing.get("meta", {"name": code})
    lines = ["[meta]"]
    lines += [f"{key} = {_value(value)}" for key, value in meta.items()]
    lines += ["", "[strings]"]
    added = 0
    for key, places in found.keys.items():
        value = strings.get(key)
        if value is None or value == "" or value == []:
            added += value is None
            value = [""] * _forms(code) if key in found.plurals else ""
        lines.append(f"# {', '.join(places[:3])}{' ...' if len(places) > 3 else ''}")
        lines.append(f"{_string(key)} = {_value(value)}")
    unused = {k: v for k, v in strings.items() if k not in found.keys and v not in ("", [])}
    if unused:
        lines += ["", "# No longer shown anywhere; kept so nothing written is lost.", "[unused]"]
        lines += [f"{_string(k)} = {_value(v)}" for k, v in unused.items()]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return added, len(unused)


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
        path = ROOT / layer / "locales" / f"{code}.toml"
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
            path = ROOT / layer / "locales" / f"{args.code}.toml"
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
