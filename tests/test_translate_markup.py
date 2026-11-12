"""``tr()`` in markup is extracted, and ``verbatim()`` keeps a symbol as it is.

A caption literal of ``text``/``title``/... was always extracted; a ``tr()``
call inside a markup line was not, so a sentence with a placeholder had to
live in a method of the hand-written half.  Now any line's ``tr()`` family
call with a literal first argument is a key, as in Python.
"""

from __future__ import annotations

from pathlib import Path

from navml.checks import check
from navml.generator import generate
from navml.parser import parse
from navml.resolve import resolve
from navml.translate import Found, _markup


DOCUMENT = (
    "from navkit.i18n import tr, tr_n, verbatim\n"
    "from navml.widgets.dialog.label import Label\n"
    "from navml.widgets.dialog.button import Button\n"
    "from navml.widgets.layout.horizontal_layout import HorizontalLayout\n\n"
    "Widget_(HorizontalLayout):\n"
    "    property count: 0\n"
    "    Label:\n"
    "        id: line\n"
    "        text: tr(\"Example: {stamp}\").format(stamp=root.name)\n"
    "    Label:\n"
    "        id: total\n"
    "        text: tr_n(\"{n} file\", \"{n} files\", root.count) if root.count else tr(\"No files\")\n"
    "    Button:\n"
    "        id: clear\n"
    "        text: verbatim(\"X\")\n"
    "        on_click: root.set_title(tr(\"Cleared\"))\n"
)


def found(tmp_path: Path) -> Found:
    path = tmp_path / "widget.nml"
    path.write_text(DOCUMENT, encoding="utf-8")
    result = Found()
    _markup(path, tmp_path, result)
    return result


def test_a_tr_call_in_any_line_is_a_key(tmp_path):
    keys = found(tmp_path).keys
    assert "Example: {stamp}" in keys
    assert "No files" in keys
    assert "Cleared" in keys
    assert keys["Example: {stamp}"] == ["widget.nml:10"]


def test_tr_n_is_keyed_by_its_singular_and_counted_plural(tmp_path):
    result = found(tmp_path)
    assert "{n} file" in result.keys
    assert "{n} file" in result.plurals


def test_verbatim_is_neither_a_key_nor_translated(tmp_path):
    assert "X" not in found(tmp_path).keys
    resolved = resolve(parse(DOCUMENT, filename="widget.nml"))
    check(resolved)
    code = generate(resolved)
    assert "verbatim('X')" in code
    assert "_tr('X')" not in code


def test_a_line_calling_tr_follows_the_language():
    resolved = resolve(parse(DOCUMENT, filename="widget.nml"))
    code = generate(resolved)
    lines = code.splitlines()
    at = next(i for i, l in enumerate(lines) if "Example: {stamp}" in l)
    # A long binding is wrapped at its bracket: ``_bind(`` may open the line before.
    assert "_bind(" in lines[at] or "_bind(" in lines[at - 1]
