# Why the database is built this way

## Our own layer, not an ORM

SQLAlchemy takes 150–300 ms to import and peewee about 30 ms, and each is a run-time dependency in a project whose only
one is `pyte`. Navigator's tables are small and flat (histories, bookmarks, positions), so what an ORM adds is mostly
unused: relationships, sessions, identity maps, a migration framework. `sqlite3` is stdlib and imports in about 1 ms.
Opening the file and running the first query took 0.4 ms when measured.

The other reason is the generator. navml already turns markup into a class with a source map and a stub. A model
document reuses all of that (the import block, the two halves, `--check`), and its output is a plain class carrying
data rather than an ORM declaration that would need the ORM to interpret it.

## Per-model fingerprints, not `PRAGMA user_version`

`user_version` is one integer for the whole file. Models are imported lazily, so whether "the schema changed" is a
question for each table, not for the file. One row per table in `_navml_schema`, read whole at open, answers it with a
dictionary lookup. A model that is never imported is never checked, and nothing has to know every model up front.

The fingerprint is computed at build time and stored in the generated module, so a field edited in markup and not
rebuilt shows up as a stale `__schema__` in `navml build --check`.

## Diff against the live table, not the old fingerprint

A fingerprint says *that* something changed, not *what*. A migration that reasoned from "the previous version" would
need every previous version. Reading `PRAGMA table_info` instead (only on a mismatch, so rarely) makes a migration
correct whatever wrote the file: a newer Navigator, an older one, or one interrupted half way.

## The downgrade rule: defaults everywhere, columns never inferred away

Two versions of Navigator can share a file, in two terminals or after a downgrade. If a column vanished whenever a
model stopped mentioning it, an older version would destroy a newer one's data on open. If a field could be
`NOT NULL` without a default, an older version's inserts would fail. So removing a column is always explicit
(`dropped:`), and every field has a default the build insists on. An older model writing to a newer table then
produces valid rows. A rebuild carries columns it does not know over as they were.

## Not done yet

- Renaming a column. A `field new: str, was old` form was considered and left out until something needs it. For now a
  rename is an added field plus `dropped:`, and the data is not carried across.
- Foreign keys between models. `PRAGMA foreign_keys = ON` is set, but the grammar has no reference type yet.
- Change notification. A widget showing a table's rows re-reads it when it opens; nothing pushes changes to it.
