"""Model documents: a ``.nml`` whose root is a table.

The parser's ``field``/``index``/``unique`` lines, ``navml/model.py``'s checks,
and a model built and imported from a throwaway package the way
``test_nml_build.py`` builds a widget.
"""

from __future__ import annotations

import sys

import pytest

from navml.build import build
from navml.errors import MarkupError
from navml.model import resolve_model
from navml.parser import FieldDecl, IndexDecl, parse

HEAD = "from navkit.database import Model\nfrom datetime import datetime\n\n"


def resolved(body: str):
    return resolve_model(parse(HEAD + "Note(Model):\n" + body, filename="note.nml"))


def refused(body: str) -> str:
    with pytest.raises(MarkupError) as caught:
        resolved(body)
    return caught.value.message


def test_field_and_index_lines_are_read():
    root = parse(
        HEAD + "Note(Model):\n"
        "    field title: str = \"x\"\n"
        "    field at: datetime | None\n"
        "    unique by_title: title\n",
        filename="note.nml",
    ).root
    field, nullable, index = root.declarations
    assert field == FieldDecl("title", "str", False, "'x'", 5)
    assert (nullable.type, nullable.null, nullable.default) == ("datetime", True, None)
    assert index == IndexDecl("by_title", ("title",), True, 7)


@pytest.mark.parametrize("line", [
    "    field x: list[int]",
    "    field x: str = name",
    "    index i: a, a",
])
def test_a_line_the_parser_refuses(line):
    with pytest.raises(MarkupError):
        parse(HEAD + "Note(Model):\n" + line + "\n", filename="note.nml")


def test_a_field_without_a_default_takes_its_types_empty_value():
    model = resolved("    field title: str\n    field n: int\n    field at: datetime | None\n")
    assert [f.default for f in model.fields] == ["", 0, None]
    assert model.table == "note"


@pytest.mark.parametrize("body, says", [
    ("    field at: datetime\n", "needs a default"),
    ("    field n: int = 'x'\n", "is not a int"),
    ("    field n: int = None\n", "| None"),
    ("    field d: dict\n", "a field holds one of"),
    ("    field n: int\n    index i: m\n", "not a field"),
    ("    field n: int\n    property p: 1\n", "fields and indexes"),
    ("    field n: int\n    title: 1\n", "not 'title'"),
    ("    field n: int\n    dropped: \"n\"\n", "dropped and declared"),
    ("    field id: int\n", "'id' key already"),
])
def test_what_a_model_document_cannot_say(body, says):
    assert says in refused(body)


def test_a_document_with_fields_has_to_extend_model():
    with pytest.raises(MarkupError) as caught:
        resolve_model(parse(
            "from navkit.widget import Widget\n\nNote(Widget):\n    field n: int\n",
            filename="note.nml",
        ))
    assert "not a navkit.database.Model" in caught.value.message


def test_the_fingerprint_follows_the_schema_and_nothing_else():
    one = resolved("    field n: int\n")
    documented = resolved("    #: A number.\n    field n: int\n")
    wider = resolved("    field n: int\n    field m: int\n")
    assert one.schema == documented.schema != wider.schema


@pytest.fixture
def package(tmp_path, monkeypatch):
    name = "models_" + tmp_path.name.replace("-", "_")
    directory = tmp_path / name
    directory.mkdir()
    (directory / "__init__.py").write_text("import navml\nnavml.register(__name__)\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    yield directory
    for module in [m for m in sys.modules if m.startswith(name)]:
        del sys.modules[module]


def test_a_built_model_with_a_hand_written_half_works_end_to_end(package):
    (package / "note.nml").write_text(
        HEAD + "Note(Model):\n    field title: str\n    unique by_title: title\n"
    )
    (package / "note.py").write_text(
        "from navkit.database import Model\n\n\n"
        "class Note(Model):\n"
        "    @classmethod\n"
        "    def titled(cls, title: str) -> 'Note':\n"
        "        return cls.upsert(title=title)\n"
    )
    build([package])
    assert build([package], check_only=True).ok
    stub = (package / "note.pyi").read_text()
    assert "def titled(cls, title: str) -> 'Note'" in stub
    assert "def get(cls, **conditions: _Any) -> Note | None" in stub
    module = __import__(f"{package.name}.note", fromlist=["Note"])
    assert module.Note.titled("a").id == module.Note.titled("a").id
    assert module.Note.count() == 1
