"""The database: models, queries, and a schema examined only when it changed.

``navkit/database.py``.  Models here are built by hand with :func:`model`, the
way the generator would write them, so the run time is tested apart from the
markup; ``test_nml_model.py`` tests the markup.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from navkit.database import (
    DATABASE,
    Database,
    DatabaseError,
    Field,
    Index,
    Model,
    ddl_for,
    fingerprint,
)


def model(fields, indexes=(), dropped=(), table="note", name="Note"):
    ddl = ddl_for(table, fields, indexes)
    return type(name, (Model,), {
        "__table__": table,
        "__fields__": tuple(fields),
        "__indexes__": tuple(indexes),
        "__dropped__": tuple(dropped),
        "__ddl__": ddl,
        "__schema__": fingerprint(ddl, dropped),
    })


BASE = [Field("title", str, ""), Field("done", bool, False)]
UNIQUE = [Index("title", ("title",), unique=True)]
Note = model(BASE, UNIQUE)


def traced(database=DATABASE) -> list[str]:
    statements: list[str] = []
    database.connection.set_trace_callback(statements.append)
    return statements


# -- rows and queries -------------------------------------------------------------


def test_create_get_save_and_delete_a_row():
    note = Note.create(title="milk")
    assert note.id is not None and note.done is False
    note.done = True
    note.save()
    assert Note.get(title="milk") == note
    note.delete()
    assert Note.get(title="milk") is None and Note.count() == 0


def test_a_query_filters_orders_limits_and_is_immutable():
    for title in ("b", "a", "c", "d"):
        Note.create(title=title, done=title in "ab")
    everything = Note.query()
    assert [n.title for n in everything.order("title").limit(2).offset(1)] == ["b", "c"]
    assert everything.count() == 4
    assert Note.where(done=True).order("-title").values("title") == ["b", "a"]
    assert Note.where(title__in=["a", "z"]).count() == 1
    assert Note.where(title__gt="b").count() == 2
    assert Note.where(title__like="%").count() == 4


def test_a_query_deletes_and_updates_what_it_selects():
    for title in "abcd":
        Note.create(title=title)
    assert Note.query().order("title").offset(2).delete() == 2
    assert Note.where(title="a").update(done=True) == 1
    assert [(n.title, n.done) for n in Note.query().order("title")] == [
        ("a", True), ("b", False)]


def test_upsert_updates_only_the_fields_it_is_given():
    Note.create(title="milk", done=True)
    found = Note.upsert(title="milk")
    assert found.done is True and Note.count() == 1
    assert Note.upsert(title="bread", done=False).id != found.id


def test_upsert_needs_a_unique_index_its_values_cover():
    with pytest.raises(DatabaseError):
        model(BASE).upsert(title="x")


def test_an_unknown_field_or_operator_is_refused_before_any_sql():
    with pytest.raises(DatabaseError):
        Note.where(nope=1)
    with pytest.raises(DatabaseError):
        Note.where(title__near="x")
    with pytest.raises(TypeError):
        Note(nope=1)


def test_codecs_round_trip_and_none_compares_with_is():
    Stamp = model([
        Field("at", datetime, None, null=True),
        Field("where", Path, None, null=True),
        Field("blob", bytes, b""),
        Field("ratio", float, 0.0),
    ], table="stamp", name="Stamp")
    at = datetime(2026, 10, 2, 12, 30)
    Stamp.create(at=at, where=Path("/tmp"), blob=b"\x00", ratio=0.5)
    Stamp.create()
    row = Stamp.where(at__ne=None).first()
    assert (row.at, row.where, row.blob, row.ratio) == (at, Path("/tmp"), b"\x00", 0.5)
    assert Stamp.where(at=None).count() == 1


def test_a_transaction_commits_together_or_not_at_all():
    with pytest.raises(RuntimeError):
        with DATABASE.transaction():
            Note.create(title="a")
            with DATABASE.transaction():
                Note.create(title="b")
            raise RuntimeError
    assert Note.count() == 0


# -- the schema, examined only when it changed --------------------------------------


def test_a_fresh_file_creates_the_table_and_records_its_fingerprint(tmp_path):
    DATABASE.open(tmp_path / "x.db")
    Note.create(title="a")
    assert DATABASE.schema_of("note") == Note.__schema__
    other = sqlite3.connect(tmp_path / "x.db")
    assert other.execute("SELECT schema FROM _navml_schema").fetchall() == [
        (Note.__schema__,)]


def test_reopening_an_unchanged_file_examines_nothing(tmp_path):
    DATABASE.open(tmp_path / "x.db")
    Note.create(title="a")
    DATABASE.open(tmp_path / "x.db")
    statements = traced()
    assert Note.count() == 1
    assert statements == ['SELECT COUNT(*) FROM "note"']


def test_a_model_is_checked_once_per_process(tmp_path):
    DATABASE.open(tmp_path / "x.db")
    statements = traced()
    Note.count()
    Note.count()
    assert sum("PRAGMA table_info" in s for s in statements) == 1


def test_a_new_field_is_added_and_the_rows_are_kept(tmp_path):
    DATABASE.open(tmp_path / "x.db")
    Note.create(title="a", done=True)
    Wider = model(BASE + [Field("rank", int, 7)], UNIQUE)
    DATABASE.open(tmp_path / "x.db")
    statements = traced()
    row = Wider.get(title="a")
    assert (row.done, row.rank) == (True, 7)
    assert any("ADD COLUMN" in s for s in statements)
    assert not any("DROP TABLE" in s for s in statements)


def test_a_dropped_or_retyped_field_rebuilds_the_table_keeping_the_rest(tmp_path):
    DATABASE.open(tmp_path / "x.db")
    Note.create(title="a", done=True)
    Retyped = model([Field("title", str, ""), Field("rank", float, 0.0)],
                    UNIQUE, dropped=["done"])
    DATABASE.open(tmp_path / "x.db")
    statements = traced()
    assert [(r.title, r.rank) for r in Retyped.all()] == [("a", 0.0)]
    assert any("DROP TABLE" in s for s in statements)
    columns = [r[1] for r in DATABASE.execute('PRAGMA table_info("note")')]
    assert columns == ["id", "title", "rank"]
    assert Retyped.upsert(title="a", rank=2.0).rank == 2.0  # the index came back


def test_an_older_model_still_writes_to_a_newer_table(tmp_path):
    Wider = model(BASE + [Field("rank", int, 7)], UNIQUE)
    DATABASE.open(tmp_path / "x.db")
    Wider.create(title="new")
    DATABASE.open(tmp_path / "x.db")
    Note.create(title="old")
    DATABASE.open(tmp_path / "x.db")
    assert [(r.title, r.rank) for r in Wider.query().order("title")] == [
        ("new", 7), ("old", 7)]


def test_two_processes_migrate_once(tmp_path):
    path = tmp_path / "x.db"
    first, second = Database(), Database()
    first.open(path)
    second.open(path)  # read the fingerprints before either migrated
    first.ensure(Note)
    statements = traced(second)
    second.ensure(Note)
    assert not any("PRAGMA table_info" in s for s in statements)
    first.close()
    second.close()


def test_a_model_first_used_inside_a_transaction_is_cached_once_committed(tmp_path):
    DATABASE.open(tmp_path / "x.db")
    with DATABASE.transaction():
        Note.create(title="a")
    statements = traced()
    for _ in range(3):
        with DATABASE.transaction():
            Note.count()
    assert not any("_navml_schema" in s for s in statements)
