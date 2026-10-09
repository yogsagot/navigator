"""DOS Navigator's palette, as its Colors dialog names it: the table the themes
are generated from (``tools/palconv.py``) and Options > Colors edits.

Kept here rather than in the tool because the application reads it too: the
dialog's groups and items are these rows, and each row's *variable stem* is
what the themes and ``navigator.nss`` call it -- ``$panel-fg``,
``$panel-bg``, and now ``$panel-bold`` and the other attributes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

#: DOS attribute nibble to colour name, in DOS order.  navkit names all sixteen
#: and its own integer constants are in ANSI order, where 1 is red and 4 is
#: blue -- the reverse of this.  Emitting the *name* is what makes that a
#: non-issue: ``blue`` means blue at both ends.
DOS_COLORS = (
    "black", "blue", "green", "cyan",
    "red", "magenta", "brown", "light_gray",
    "dark_gray", "light_blue", "light_green", "light_cyan",
    "light_red", "light_magenta", "yellow", "white",
)

#: Every entry DOS Navigator's Colors dialog exposes, in the dialog's own
#: order, as ``(variable stem, palette index, group, item)``.  Transcribed
#: from ``RESOURCE/ENGLISH/DN.DNR``; regenerate with ``--names``.
ENTRIES = (
    # -- Timer -------------------------------------------------------------
    ("desktop", 1, "Timer", "Color"),
    # -- Menus -------------------------------------------------------------
    ("bar", 2, "Menus", "Normal"),
    ("bar-disabled", 3, "Menus", "Disabled"),
    ("bar-key", 4, "Menus", "Shortcut"),
    ("bar-selected", 5, "Menus", "Selected"),
    ("bar-selected-disabled", 6, "Menus", "Selected disabled"),
    ("bar-selected-key", 7, "Menus", "Shortcut selected"),
    # -- Dialogs -----------------------------------------------------------
    ("dialog-frame-background", 33, "Dialogs", "Frame/background"),
    ("dialog-frame-icons", 34, "Dialogs", "Frame icons"),
    ("dialog-scroll-bar-page", 35, "Dialogs", "Scroll bar page"),
    ("dialog-scroll-bar-icons", 36, "Dialogs", "Scroll bar icons"),
    ("dialog-static-text", 37, "Dialogs", "Static text"),
    ("dialog-label-normal", 38, "Dialogs", "Label normal"),
    ("dialog-label-selected", 39, "Dialogs", "Label selected"),
    ("dialog-label-shortcut", 40, "Dialogs", "Label shortcut"),
    ("dialog-button-normal", 41, "Dialogs", "Button normal"),
    ("dialog-button-default", 42, "Dialogs", "Button default"),
    ("dialog-button-selected", 43, "Dialogs", "Button selected"),
    ("dialog-button-disabled", 44, "Dialogs", "Button disabled"),
    ("dialog-button-shortcut", 45, "Dialogs", "Button shortcut"),
    ("dialog-shortcut-selected", 178, "Dialogs", "Shortcut selected"),
    ("dialog-shortcut-default", 179, "Dialogs", "Shortcut default"),
    ("dialog-button-shadow", 46, "Dialogs", "Button shadow"),
    ("dialog-cluster-normal", 47, "Dialogs", "Cluster normal"),
    ("dialog-cluster-selected", 48, "Dialogs", "Cluster selected"),
    ("dialog-cluster-shortcut", 49, "Dialogs", "Cluster shortcut"),
    ("dialog-input-normal", 50, "Dialogs", "Input normal"),
    ("dialog-input-selected", 51, "Dialogs", "Input selected"),
    ("dialog-input-arrow", 52, "Dialogs", "Input arrow"),
    ("dialog-history-button", 53, "Dialogs", "History button"),
    ("dialog-history-sides", 54, "Dialogs", "History sides"),
    ("dialog-history-bar-page", 55, "Dialogs", "History bar page"),
    ("dialog-history-bar-icons", 56, "Dialogs", "History bar icons"),
    ("dialog-list-normal", 57, "Dialogs", "List normal"),
    ("dialog-list-focused", 58, "Dialogs", "List focused"),
    ("dialog-list-selected", 59, "Dialogs", "List selected"),
    ("dialog-list-divider", 60, "Dialogs", "List divider"),
    ("dialog-information-pane", 61, "Dialogs", "Information pane"),
    # -- Tree --------------------------------------------------------------
    ("dialog-tree-normal-tree", 104, "Tree", "Normal tree"),
    ("dialog-tree-normal-nodes", 105, "Tree", "Normal nodes"),
    ("dialog-tree-selected-node", 106, "Tree", "Selected node"),
    ("dialog-tree-default-node", 107, "Tree", "Default node"),
    ("dialog-tree-selected-default", 108, "Tree", "Selected default"),
    ("dialog-tree-selected-passive", 109, "Tree", "Selected passive"),
    ("dialog-tree-selected-def-passive", 110, "Tree", "Selected def. passive"),
    # -- File Manager ------------------------------------------------------
    ("frame", 80, "File Manager", "Frame passive"),
    ("active-frame", 81, "File Manager", "Frame active"),
    ("frame-icon", 82, "File Manager", "Frame icons"),
    ("scrollbar-page", 83, "File Manager", "Scroll bar page"),
    ("scrollbar-arrow", 84, "File Manager", "Scroll bar icons"),
    # -- File Panel --------------------------------------------------------
    ("panel", 85, "File Panel", "Normal text"),
    ("marked", 87, "File Panel", "Selected text"),
    ("cursor", 88, "File Panel", "Normal cursor"),
    ("marked-cursor", 89, "File Panel", "Selected cursor"),
    ("divider", 86, "File Panel", "List divider"),
    ("active-title", 90, "File Panel", "Directory active"),
    ("title", 91, "File Panel", "Directory passive"),
    ("column-title", 165, "File Panel", "Column title"),
    # -- Highlight ---------------------------------------------------------
    ("directory", 172, "Highlight", "Directories"),
    ("executable", 173, "Highlight", "Executables"),
    ("archive", 174, "Highlight", "Archives"),
    ("highlight-custom-1", 175, "Highlight", "Custom 1"),
    ("highlight-custom-2", 176, "Highlight", "Custom 2"),
    ("highlight-custom-3", 177, "Highlight", "Custom 3"),
    ("highlight-custom-4", 180, "Highlight", "Custom 4"),
    ("highlight-custom-5", 181, "Highlight", "Custom 5"),
    # -- Drive Line --------------------------------------------------------
    ("drive-line-drive-letters", 186, "Drive Line", "Drive letters"),
    ("drive-line-drive-selected", 188, "Drive Line", "Drive selected"),
    ("drive-line-frame", 187, "Drive Line", "Frame"),
    # -- Info --------------------------------------------------------------
    ("info-current-file", 119, "Info", "Current file"),
    ("info-selected-text", 120, "Info", "Selected text"),
    ("info-selected-numbers", 121, "Info", "Selected numbers"),
    ("info-totals-text", 122, "Info", "Totals text"),
    ("info-totals-numbers", 123, "Info", "Totals numbers"),
    ("info-free-space-text", 124, "Info", "Free space text"),
    ("info-free-space-numbers", 125, "Info", "Free space numbers"),
    # -- Tree --------------------------------------------------------------
    ("tree-normal-tree", 94, "Tree", "Normal tree"),
    ("tree-normal-nodes", 95, "Tree", "Normal nodes"),
    ("tree-selected-node", 96, "Tree", "Selected node"),
    ("tree-default-node", 97, "Tree", "Default node"),
    ("tree-selected-default", 98, "Tree", "Selected default"),
    ("tree-selected-passive", 99, "Tree", "Selected passive"),
    ("tree-selected-def-passive", 100, "Tree", "Selected def. passive"),
    ("tree-info-box", 101, "Tree", "Info box"),
    # -- Quick View --------------------------------------------------------
    ("quick-view-normal-text", 92, "Quick View", "Normal text"),
    ("quick-view-selected-text", 93, "Quick View", "Selected text"),
    # -- Disk Info ---------------------------------------------------------
    ("disk-info-normal-text", 103, "Disk Info", "Normal text"),
    ("disk-info-highlighted-text", 102, "Disk Info", "Highlighted text"),
    # -- File Viewer -------------------------------------------------------
    ("viewer-frame-passive", 112, "File Viewer", "Frame passive"),
    ("viewer-frame-active", 113, "File Viewer", "Frame active"),
    ("viewer-frame-icons", 114, "File Viewer", "Frame icons"),
    ("viewer-scroll-bar-page", 115, "File Viewer", "Scroll bar page"),
    ("viewer-scroll-bar-icons", 116, "File Viewer", "Scroll bar icons"),
    ("viewer-normal-text", 117, "File Viewer", "Normal text"),
    ("viewer-selected-text", 118, "File Viewer", "Selected text"),
    # -- Editor/Spreadsheet ------------------------------------------------
    ("editor-frame-passive", 70, "Editor/Spreadsheet", "Frame passive"),
    ("editor-frame-active", 71, "Editor/Spreadsheet", "Frame active"),
    ("editor-frame-icons", 73, "Editor/Spreadsheet", "Frame icons"),
    ("editor-frame-title", 72, "Editor/Spreadsheet", "Frame title"),
    ("editor-scroll-bar-page", 74, "Editor/Spreadsheet", "Scroll bar page"),
    ("editor-scroll-bar-icons", 75, "Editor/Spreadsheet", "Scroll bar icons"),
    ("editor-normal-text", 76, "Editor/Spreadsheet", "Normal text"),
    ("editor-selected-text", 77, "Editor/Spreadsheet", "Selected text"),
    # -- Highlight ---------------------------------------------------------
    ("editor-highlight-comments", 164, "Highlight", "Comments"),
    ("editor-highlight-symbols", 189, "Highlight", "Symbols"),
    ("editor-highlight-strings", 190, "Highlight", "Strings"),
    ("editor-highlight-numbers", 191, "Highlight", "Numbers"),
    ("editor-highlight-current-line", 182, "Highlight", "Current line"),
    ("editor-highlight-cur-line-comments", 184, "Highlight", "Cur. line comments"),
    ("editor-highlight-current-line-selected", 183, "Highlight", "Current line selected"),
    ("editor-highlight-current-column", 185, "Highlight", "Current column"),
    # -- Menu --------------------------------------------------------------
    ("editor-menu-normal", 64, "Menu", "Normal"),
    ("editor-menu-disabled", 65, "Menu", "Disabled"),
    ("editor-menu-shortcut", 66, "Menu", "Shortcut"),
    ("editor-menu-selected", 67, "Menu", "Selected"),
    ("editor-menu-selected-disabled", 68, "Menu", "Selected disabled"),
    ("editor-menu-shortcut-selected", 69, "Menu", "Shortcut selected"),
    # -- Disk Fixer --------------------------------------------------------
    ("fixer-frame-passive", 153, "Disk Fixer", "Frame passive"),
    ("fixer-frame-active", 154, "Disk Fixer", "Frame active"),
    ("fixer-frame-icons", 156, "Disk Fixer", "Frame icons"),
    ("fixer-frame-title", 155, "Disk Fixer", "Frame title"),
    ("fixer-scroll-bar-page", 157, "Disk Fixer", "Scroll bar page"),
    ("fixer-scroll-bar-icons", 158, "Disk Fixer", "Scroll bar icons"),
    ("fixer-normal-text", 159, "Disk Fixer", "Normal text"),
    ("fixer-selected-text", 160, "Disk Fixer", "Selected text"),
    ("fixer-sector-title", 161, "Disk Fixer", "Sector title"),
    ("fixer-edit-line", 162, "Disk Fixer", "Edit line"),
    # -- Menu --------------------------------------------------------------
    ("fixer-menu-normal", 147, "Menu", "Normal"),
    ("fixer-menu-disabled", 148, "Menu", "Disabled"),
    ("fixer-menu-shortcut", 149, "Menu", "Shortcut"),
    ("fixer-menu-selected", 150, "Menu", "Selected"),
    ("fixer-menu-selected-disabled", 151, "Menu", "Selected disabled"),
    ("fixer-menu-shortcut-selected", 152, "Menu", "Shortcut selected"),
    # -- Terminal ----------------------------------------------------------
    ("terminal-frame-passive", 8, "Terminal", "Frame passive"),
    ("terminal-frame-active", 9, "Terminal", "Frame active"),
    ("terminal-frame-icons", 10, "Terminal", "Frame icons"),
    ("terminal-scroll-bar-page", 11, "Terminal", "Scroll bar page"),
    ("terminal-scroll-bar-icons", 12, "Terminal", "Scroll bar icons"),
    # -- dBase viewer ------------------------------------------------------
    ("dbase-frame-passive", 166, "dBase viewer", "Frame passive"),
    ("dbase-frame-active", 167, "dBase viewer", "Frame active"),
    ("dbase-frame-icons", 168, "dBase viewer", "Frame icons"),
    ("dbase-fields-titles", 169, "dBase viewer", "Fields titles"),
    ("dbase-normal-text", 170, "dBase viewer", "Normal text"),
    ("dbase-cursor", 171, "dBase viewer", "Cursor"),
)


#: Variables Navigator needs and DOS Navigator had no slot for: name ->
#: ``(slot, why)``.  Each is written into every theme as an *alias* of the
#: slot's own variables -- ``$image-fg: $highlight-custom-1-fg;`` -- so every
#: palette gives it a colour it already draws, and changing the slot changes
#: it.  A theme that wants something else says so in
#: :data:`DERIVED_DEPARTURES`.
#:
#: They are the file-type classes of ``navigator/filetypes.py``.  DN coloured
#: rows by category and left Custom 1-5 [175-181] to masks the user typed
#: (*Highlight groups*), so the categories Navigator fills in take those five;
#: Midnight Commander's type classes, which DOS had no files for, share them.
#:
#: Where no slot fits, the entry carries a DOS colour pair ``(fg, bg)`` instead
#: of a slot, written as colours rather than as an alias.  ``root-title`` is
#: one: the titles of a session running as root, white on dark red, which no
#: DN palette draws anywhere because DOS had no root to warn about.
DERIVED: dict[str, tuple[int | tuple[int, int], str]] = {
    "image": (175, "images -- DN's Custom 1"),
    "media": (176, "audio and video -- DN's Custom 2"),
    "document": (177, "documents -- DN's Custom 3"),
    "stale-link": (180, "a symlink pointing nowhere -- DN's Custom 4"),
    "source": (181, "source code -- DN's Custom 5"),
    "symlink": (175, "a symlink -- Midnight Commander's class, on Custom 1"),
    "device": (177, "a character or block device -- MC's class, on Custom 3"),
    "special": (177, "a socket or a FIFO -- MC's class, on Custom 3"),
    "temp": (85, "backups and temporaries -- MC's class, on Normal text"),
    "root-title": ((15, 4), "a title while running as root -- no slot"),
    "keyword": (76, "the editor's keywords -- DN loaded KEYWORDS1 and never painted them; on Normal text"),
}


# -- the user's palette ----------------------------------------------------------------
#
# Options > Colors, Store palette and Load palette.  DN kept the edited palette
# in DN.CFG and stored or loaded a whole one as a .PAL file; here both are
# .nss sheets of variable definitions, which is all a theme is.  The edited
# palette is ``palette.nss`` in the configuration directory, read after the
# theme at every start, holding only what differs from the theme -- so a
# theme changed underneath it keeps the rest of its colours.

#: The text attributes a terminal draws beyond DN's two colours, as the
#: ``Style`` fields they set.  ``inherit`` (the default for most entries) says
#: nothing, so the attribute comes from what the widget sits on.
ATTRIBUTES = ("bold", "dim", "italic", "underline", "reverse")

#: Every variable an entry has, as the suffix after its stem.
KEYS = ("fg", "bg") + ATTRIBUTES

#: What the Colors dialog calls the group of Navigator's own entries.
NAVIGATOR_GROUP = "Navigator"

#: The dialog's names for :data:`DERIVED`'s entries.
DERIVED_ITEMS = {
    "image": "Images",
    "media": "Audio and video",
    "document": "Documents",
    "stale-link": "Broken link",
    "source": "Source code",
    "symlink": "Symbolic link",
    "device": "Device",
    "special": "Socket or FIFO",
    "temp": "Temporary file",
    "root-title": "Title as root",
    "keyword": "Keywords",
}

#: The palette the Colors dialog writes, in the configuration directory.
PALETTE_NAME = "palette.nss"

#: Where Store palette puts a palette by default, and a theme is also looked
#: for by name -- DN's ``COLORS`` directory.
THEMES_NAME = "themes"


def groups() -> list[tuple[str, list[tuple[str, str]]]]:
    """The dialog's groups, each ``(name, [(stem, item), ...])``, in DN's
    order: a run of :data:`ENTRIES` with one group name is one group, as
    DN's ``ColorGroup`` list was (so *Tree* and *Menu* each come twice, as
    they did), and Navigator's own entries last."""
    found: list[tuple[str, list[tuple[str, str]]]] = []
    for stem, _, group, item in ENTRIES:
        if not found or found[-1][0] != group:
            found.append((group, []))
        found[-1][1].append((stem, item))
    found.append((NAVIGATOR_GROUP, [(stem, DERIVED_ITEMS.get(stem, stem)) for stem in DERIVED]))
    return found


def stems() -> list[str]:
    """Every entry's stem, in the dialog's order."""
    return [stem for _, items in groups() for stem, _ in items]


def palette_path() -> Path:
    from navigator.settings import config_dir

    return config_dir() / PALETTE_NAME


def user_themes() -> Path:
    from navigator.settings import config_dir

    return config_dir() / THEMES_NAME


def read_palette(path: Path) -> dict[str, str]:
    """*path*'s definitions, as written.  Raises ``OSError``."""
    from navkit.stylesheet import variables_in

    return variables_in(path.read_text(encoding="utf-8"))


def entry_values(variables: Mapping[str, str]) -> dict[str, str]:
    """What a sheet's *variables* give every entry's :data:`KEYS`, by name."""
    return {f"{stem}-{key}": variables[f"{stem}-{key}"]
            for stem in stems() for key in KEYS if f"{stem}-{key}" in variables}


def differences(base: Mapping[str, str], values: Mapping[str, str]) -> dict[str, str]:
    """What *values* say that *base* does not: a user palette's content."""
    return {name: value for name, value in values.items() if base.get(name) != value}


def render_palette(values: Mapping[str, str], title: str) -> str:
    """*values* as a sheet of definitions, in the dialog's groups and order,
    under a comment naming it *title*.  An entry none of whose variables is
    in *values* is left out."""
    lines = ["/*", f" * {title}", " *",
             " * Written by Navigator's Options > Colors (Store palette); it defines",
             " * variables and no rules, and loads after navigator.nss as a theme does.",
             " */", ""]
    for group, items in groups():
        body = []
        for stem, item in items:
            named = [f"${stem}-{key}: {values[f'{stem}-{key}']};" for key in KEYS
                     if f"{stem}-{key}" in values]
            if named:
                body.append(f"/* {item} */ " + " ".join(named))
        if body:
            lines.append(f"/* -- {group} {'-' * max(0, 66 - len(group))} */")
            lines += body
            lines.append("")
    return "\n".join(lines)


def write_sheet(path: Path, text: str) -> None:
    """*text* to *path*, its directory made, written beside it and renamed
    over it so a reader never sees half.  Raises ``OSError``.  On a thread."""
    import os
    import tempfile

    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            file.write(text)
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def save_palette(values: Mapping[str, str]) -> None:
    """The Colors dialog's *values* (what differs from the theme) as
    ``palette.nss``; none, and the file goes.  Raises ``OSError``.  On a
    thread."""
    path = palette_path()
    if values:
        write_sheet(path, render_palette(values, "Navigator's palette -- Options > Colors"))
    else:
        path.unlink(missing_ok=True)
