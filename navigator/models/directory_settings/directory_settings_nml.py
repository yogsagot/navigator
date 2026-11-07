# navml: generated
"""Generated from ``directory_settings.nml``.

Do not edit: edit the markup and rerun ``python -m navml build``.
"""

from __future__ import annotations

from navkit.database import Field as _Field
from navkit.database import Index as _Index
from navkit.database import Model    # directory_settings.nml:1

__navml_component__ = "DirectorySettings"

__all__ = ["DirectorySettings"]


class DirectorySettings(Model):    # directory_settings.nml:8
    """What a directory is shown with, remembered for it: Panel > *Remember for

    this directory*, or any change made in one under File Manager Setup's
    *Remember directory settings: Every directory*
    (``navigator/lib/config/directory_settings.py``).  A departure: DN's sort,
    mask and display belonged to the panel and went wherever it went.
    """

    #: The document this class was generated from.
    __navml_source__ = "directory_settings.nml"
    __table__ = "directory_settings"
    __fields__ = (
        _Field("path", str, ''),    # directory_settings.nml:11
        _Field("subdirs", bool, False),    # directory_settings.nml:14
        _Field("view_mode", str, ''),    # directory_settings.nml:16
        _Field("sort_mode", str, ''),    # directory_settings.nml:18
        _Field("sort_reverse", bool, False),    # directory_settings.nml:19
        _Field("file_mask", str, ''),    # directory_settings.nml:20
        _Field("show_hidden", bool, True),    # directory_settings.nml:21
        _Field("columns", str, ''),    # directory_settings.nml:23
        _Field("display", str, '*'),    # directory_settings.nml:26
    )
    __indexes__ = (
        _Index("by_path", ('path',), unique=True),    # directory_settings.nml:27
    )

    #: What the table is made from, and the fingerprint _navml_schema
    #: keeps of it: a database whose row matches is never examined.
    __ddl__ = (
        'CREATE TABLE "directory_settings" ("id" INTEGER PRIMARY KEY, "path" TEXT NOT NULL DEFAULT \'\', "subdirs" INTEGER NOT NULL DEFAULT 0, "view_mode" TEXT NOT NULL DEFAULT \'\', "sort_mode" TEXT NOT NULL DEFAULT \'\', "sort_reverse" INTEGER NOT NULL DEFAULT 0, "file_mask" TEXT NOT NULL DEFAULT \'\', "show_hidden" INTEGER NOT NULL DEFAULT 1, "columns" TEXT NOT NULL DEFAULT \'\', "display" TEXT NOT NULL DEFAULT \'*\')',
        'CREATE UNIQUE INDEX "directory_settings_by_path" ON "directory_settings" ("path")',
    )
    __schema__ = "59035aed8c0fa0b9"

    id: int | None

    #: The directory, as a bookmark names it (``bookmarks.key_of``).
    path: str    # directory_settings.nml:11

    #: Whether the directories below take these too, the nearest one marked
    #: winning.
    subdirs: bool    # directory_settings.nml:14

    #: ``Panel.VIEW_MODES``' one.
    view_mode: str    # directory_settings.nml:16

    #: ``SORT_MODES``' one.
    sort_mode: str    # directory_settings.nml:18
    sort_reverse: bool    # directory_settings.nml:19
    file_mask: str    # directory_settings.nml:20
    show_hidden: bool    # directory_settings.nml:21

    #: The detailed mode's columns, comma-separated.
    columns: str    # directory_settings.nml:23

    #: The *Display* boxes, comma-separated; ``*`` while the panel followed
    #: the *New Manager defaults*.
    display: str    # directory_settings.nml:26
