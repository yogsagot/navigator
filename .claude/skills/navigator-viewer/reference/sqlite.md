# SQLite in the dBase window

DN's *As DataBase* (`cmViewDBF`, DBVIEW.PAS) read dBase files. SQLite is the single-file database of today, so
the same window shows it. This is a departure, and asked for.

## One window, two sources

`TDBViewer` drew `TDBFile`'s fields and records. The grid asks its source a few questions:
- `fields`, `count`, `record(n)`;
- `shown`, `raw`, `memo`;
- `flag` (dBase's delete byte);
- `memo_kinds` (which fields F3 opens);
- `editable` (whether F4 may write).

`dbf.DBFile` and `sqlite.SQLTable` both answer them, so neither the grid nor the window branches on the
format, except for F2's schema and the SQLite-only F5/F6.

## Why read-only

A SQLite file is often in use by the program that owns it: a browser profile, a mail client, an
application's state. Writing to it from outside can corrupt what that program assumes. So the file is
opened `mode=ro` with `PRAGMA query_only`. Where even `mode=ro` fails, for example a WAL database in a
directory that cannot take a `-shm`, it is opened `immutable=1`, which reads the main file alone. F4 is
greyed with the reason.

## Why the rowid paging

A table of millions of rows must open at once, as the dBase viewer opens any `.dbf`. `LIMIT/OFFSET` costs
the offset in rows skipped, so a row deep in the table would stall the loop. Instead, listing the rowids on
a thread is one pass of the table's b-tree. After that, any screenful is one indexed seek
(`WHERE rowid >= ?`), as cheap on the loop as the dBase viewer's `pread`. A view, a `WITHOUT ROWID` table
and a query's result have no such key, so they are read whole on the thread, up to `ROW_LIMIT`, and the
count says `+` when cut.

## Why an authorizer for queries

`query_only` already refuses writes to the database. A typed statement could still `ATTACH` another file,
or turn `query_only` off with a `PRAGMA`. While a typed query runs, an authorizer allows SELECT, READ,
FUNCTION and RECURSIVE and nothing else. The window's own `PRAGMA`s run outside it.
