"""No function reads a global its module never binds.

Python reports such a name only when the line runs -- a ``NameError`` from the
one key or menu item that reaches it -- so the rest of the suite catches it
only where a test happens to press that key.  It is the mistake splitting a
class into mixins makes easiest: a method moved to its own module still names
a class defined after the one it left (Shell's ``UserScreenPeek``), or a
helper the new module never imported.  pyflakes calls it *undefined name*;
there is no lint tooling here, so this asks :mod:`symtable` the same question
of every module in the three packages: each name a function or class body
reads as a global is bound at module level, or is a builtin.
"""

from __future__ import annotations

import builtins
import pathlib
import symtable

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGES = ("navkit", "navml", "navigator")

#: What every module has without binding it.
MODULE_NAMES = frozenset(dir(builtins)) | {
    "__file__", "__name__", "__doc__", "__spec__", "__loader__", "__package__", "__path__",
    "__builtins__", "__annotations__", "__dict__", "__debug__",
}


def _modules() -> list[pathlib.Path]:
    return sorted(
        path for package in PACKAGES for path in (ROOT / package).rglob("*.py")
        if "__pycache__" not in path.parts
    )


def _scopes(table: symtable.SymbolTable):
    for child in table.get_children():
        yield child
        yield from _scopes(child)


def undefined_names(source: str, filename: str) -> list[tuple[str, str]]:
    """Every ``(scope, name)`` in *source* read as a global that nothing binds."""
    top = symtable.symtable(source, filename, "exec")
    bound = {
        symbol.get_name() for symbol in top.get_symbols()
        if symbol.is_assigned() or symbol.is_imported() or symbol.is_namespace()
    }
    if any(symbol.get_name() == "*" for symbol in top.get_symbols()):
        return []  # ``from x import *`` binds what it cannot say
    scopes = list(_scopes(top))
    # A ``global`` statement assigned in a function binds the name too.
    for scope in scopes:
        bound.update(
            symbol.get_name() for symbol in scope.get_symbols()
            if symbol.is_declared_global() and symbol.is_assigned()
        )
    found = []
    for scope in scopes:
        for symbol in scope.get_symbols():
            name = symbol.get_name()
            # A parameter is never undefined, though symtable can report one
            # global too (``Mkdir.top``'s ``self`` under a dataclass).
            if (symbol.is_referenced() and symbol.is_global()
                    and not symbol.is_parameter() and not symbol.is_local()
                    and name not in bound and name not in MODULE_NAMES):
                found.append((scope.get_name(), name))
    return found


@pytest.mark.parametrize("path", _modules(), ids=lambda path: str(path.relative_to(ROOT)))
def test_every_global_a_module_reads_is_bound(path):
    source = path.read_text(encoding="utf-8")
    assert undefined_names(source, str(path)) == []


def test_the_check_finds_a_name_defined_nowhere():
    source = (
        "import os\n"
        "def moved(self):\n"
        "    return UserScreenPeek(os.getcwd())\n"
    )
    assert undefined_names(source, "<mixin>") == [("moved", "UserScreenPeek")]


@pytest.mark.parametrize("source", [
    "def f():\n    return later()\ndef later():\n    return 1\n",        # defined after: fine at call time
    "def f():\n    global seen\n    seen = 1\ndef g():\n    return seen\n",  # bound by a global statement
    "class A:\n    x = 1\n    y = x + 1\n",                               # the class body's own name
    "def f():\n    return len(__file__)\n",                                # builtins and module dunders
    "try:\n    import tomllib\nexcept ImportError:\n    tomllib = None\n"
    "def f():\n    return tomllib\n",
])
def test_the_check_leaves_what_is_bound_alone(source):
    assert undefined_names(source, "<module>") == []
