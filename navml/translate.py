"""``python -m navml extract`` -- a package's text into its ``locales/<code>.toml``.

**What counts as text** is what :mod:`navkit.i18n` will be asked for:

- in markup, the caption literals of ``text``/``title``/``label_text``/
  ``items``/``prompt`` -- found by compiling each line exactly as
  ``navml build`` does, so the two can never disagree;
- in Python, the literal first argument of ``tr()``, ``tr_n()`` (keyed by the
  singular), ``tr_plain()`` and ``tr_noop()`` (a table's entry, translated
  where it is shown);
- a class's ``title = "..."``: a command's, which the key bar translates;
- whatever the package's ``locales`` module names in a ``strings()`` function
  (``(key, where)`` pairs): tables of captions kept English in the source and
  translated where they are shown, which no scan can see.

A package other than navml is not asked for a string navml already has: the
library's catalogue answers it.

**Extracting** keeps every translation it finds, adds what is missing as
``""`` with where it is used as a comment, and moves what is no longer used to
an ``[unused]`` table, which :mod:`navkit.i18n` does not read, so nothing a
translator wrote is thrown away.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import json
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from navkit.i18n import plural_form
from navml.expression import TRANSLATE, TRANSLATED, compile_expression
from navml.parser import Block, parse_file

FUNCTIONS = {"tr", "tr_plain", "tr_n", "tr_noop"}

#: The library's own package directory, whose keys no other package repeats.
LIBRARY = Path(__file__).resolve().parent


@dataclass
class Found:
    """Every key one package uses, where, and which share a hotkey scope."""

    #: ``{key: [where, ...]}`` in the order first met.
    keys: dict[str, list[str]] = field(default_factory=dict)
    #: Keys that take a list of plural forms.
    plurals: set[str] = field(default_factory=set)
    #: Captions that answer to Alt+letter together: one dialog's, one menu's.
    scopes: list[tuple[str, list[str]]] = field(default_factory=list)

    def add(self, key: str, where: str) -> None:
        self.keys.setdefault(key, []).append(where)


# -- finding the package -----------------------------------------------------


def package_directory(entry: str | Path) -> Path:
    """*entry* as a package directory: a path, or a dotted module name."""
    path = Path(entry)
    if path.is_dir():
        return path.resolve()
    spec = importlib.util.find_spec(str(entry))
    if spec is None or not spec.submodule_search_locations:
        raise ValueError(f"{entry}: not a package directory or an importable package")
    return Path(next(iter(spec.submodule_search_locations))).resolve()


def catalogue_path(package: Path, code: str) -> Path:
    return package / "locales" / f"{code}.toml"


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


def _markup(path: Path, root: Path, found: Found) -> None:
    document = parse_file(path)
    where = str(path.relative_to(root))

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


def _python(path: Path, root: Path, found: Found) -> None:
    where = str(path.relative_to(root))
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


def _declared(package: Path, found: Found) -> None:
    """What the package's ``locales.strings()`` names, if it has one."""
    if not (package / "locales" / "__init__.py").is_file():
        return
    parent = str(package.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    module = importlib.import_module(f"{package.name}.locales")
    strings = getattr(module, "strings", None)
    if strings is not None:
        for key, where in strings():
            found.add(key, where)


def scan(package: str | Path) -> Found:
    """Every key *package* uses, navml's own left out unless it is navml."""
    package = package_directory(package)
    root = package.parent
    found = Found()
    for path in sorted(package.rglob("*.nml")):
        _markup(path, root, found)
    for path in sorted(package.rglob("*.py")):
        if path.name.endswith("_nml.py") or "locales" in path.relative_to(package).parts:
            continue
        _python(path, root, found)
    _declared(package, found)
    if package != LIBRARY:
        library = scan(LIBRARY).keys
        found.keys = {k: v for k, v in found.keys.items() if k not in library}
    return found


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
    """Rewrite *path* with *found*'s keys; returns (new, unused)."""
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


def extract(package: str | Path, code: str, *, name: str | None = None) -> tuple[Path, Found, int, int]:
    """Create or update *package*'s catalogue for *code*.

    Returns the catalogue's path, what was found, and how many keys were new
    and how many translations were parked as unused.
    """
    directory = package_directory(package)
    found = scan(directory)
    path = catalogue_path(directory, code)
    existing = read(path)
    if name:
        existing.setdefault("meta", {})["name"] = name
    added, unused = write(path, code, found, existing)
    return path, found, added, unused
