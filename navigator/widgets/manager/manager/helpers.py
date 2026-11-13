"""What the Manager's mixins share: module-level helpers of
:mod:`navigator.widgets.manager.manager.manager`.
"""

from __future__ import annotations

import stat
from pathlib import Path
from typing import Any, Iterable, Sequence

from navkit import glyphs as glyphs_module
from navkit.i18n import tr, tr_n
from navkit.stylesheet import parse_declarations

from navigator.widgets.manager.commands import Copy, Delete, Edit, View
from navigator.widgets.manager.panel.panel import SORT_MODES, DirEntry
from navigator.lib.drives import Location
from navigator.lib.drives.location import shown


#: The marked keys the bookmarks are chosen by, in order: the digits as DN's
#: box had its drive letters, then the letters *Add*, *Remove* and *Trash* leave free.
BOOKMARK_KEYS = "1234567890bcdefghijklmnopqsuvwxyz"

#: The keys that move the selected bookmark up and down in the box.
MOVE_BOOKMARK_KEYS = ("ctrl+up", "ctrl+down")

#: The key that asks for the selected bookmark's label.
LABEL_BOOKMARK_KEY = "f2"

#: The key that removes the selected bookmark.
DELETE_BOOKMARK_KEY = "delete"


def sort_captions() -> tuple[str, ...]:
    """``dlSortName`` .. ``dlSortUnsorted``, in :data:`SORT_MODES`' order --
    DN's menu order, *Group* named *Type*."""
    return (tr("~N~ame"), tr("~E~xtension"), tr("~S~ize"), tr("~T~ime"), tr("~A~ttributes"), tr("~O~wner"), tr("T~y~pe"), tr("~U~nsorted"))


def sort_radio_captions(reverse: bool, glyphs: int) -> list[str]:
    """*Sort by*'s radio captions in Alt+S and *New Manager defaults*: plain
    in each mode's own direction; with *Reverse order* ticked (*reverse*),
    each but *Unsorted*'s followed by the way it runs then."""
    from navigator.widgets.manager.panel.panel import direction_arrow

    if not reverse:
        return list(_radio_captions())
    return [f"{caption} {arrow}" if (arrow := direction_arrow(mode, True, glyphs)) else caption
            for mode, caption in zip(SORT_MODES, _radio_captions())]


def _radio_captions() -> tuple[str, ...]:
    """:func:`sort_captions` with the letters the two dialogs leave free: DN's
    *Display* box beside them had ``y``, ``o`` and ``a`` (*Directory length*,
    *Totals*, *Archives first*), and *Attributes* has no letter left.  The
    same as the markup's ``items``, which is what ``tools/i18n.py check``
    reads -- keep the two alike."""
    return (tr("~N~ame"), tr("~E~xtension"), tr("~S~ize"), tr("~T~ime"), tr("Attributes"), tr("O~w~ner"), tr("Ty~p~e"),
            tr("~U~nsorted"))


def sort_orders() -> list[tuple[str, bool]]:
    """Alt+B's entries as ``(mode, reverse)``: each of :data:`SORT_MODES` in
    its own direction and then reversed, *Unsorted* once (it has none)."""
    return [(mode, reverse) for mode in SORT_MODES
            for reverse in ((False,) if mode == "unsorted" else (False, True))]


def sort_order_captions() -> list[str]:
    """:func:`sort_captions` for :func:`sort_orders`: a reversed entry's caption
    without its hot key, so the letter chooses the mode's own direction."""
    captions = dict(zip(SORT_MODES, sort_captions()))
    return [captions[mode].replace("~", "") if reverse else captions[mode]
            for mode, reverse in sort_orders()]


def job_subject(kind: str, sources: Sequence[Any], target: str = "") -> str:
    """What a copy, a move or an erase sent to the background was started on,
    for its tooltip: *Copy photos to /mnt/backup*, *Erase 3 files*.  ``""``
    with no *sources* (Synchronize's pairs), and the title stands in."""
    if not sources:
        return ""
    target = target.rstrip("/") or target
    if len(sources) == 1:
        name = sources[0].name or str(sources[0])
        if kind == "erase":
            return tr("Erase {name}").format(name=name)
        if kind == "move":
            return tr("Move {name} to {target}").format(name=name, target=target)
        return tr("Copy {name} to {target}").format(name=name, target=target)
    n = len(sources)
    if kind == "erase":
        return tr_n("Erase {n} file", "Erase {n} files", n)
    if kind == "move":
        return tr_n("Move {n} file to {target}", "Move {n} files to {target}", n, target=target)
    return tr_n("Copy {n} file to {target}", "Copy {n} files to {target}", n, target=target)


def source_base(sources: Sequence[Any]) -> str:
    """The directory *sources* are in, which the file in hand is named from."""
    return str(sources[0].parent) if sources else ""


def relative_to(path: str, base: str) -> str:
    """*path* from *base* when it is under it, else whole."""
    if base and path.startswith(base.rstrip("/") + "/"):
        return path[len(base.rstrip("/")) + 1:]
    return path


def action_caption(action: str) -> str:
    """A worker's ``action`` -- one of the English words the erase and
    attribute jobs set on their thread -- in the current language."""
    from navigator.lib.file_ops import fileattr, fileerase
    return {
        fileerase.ERASING_FILE: tr("Erasing the file"),
        fileerase.ERASING_DIRECTORY: tr("Erasing the directory"),
        fileerase.TRASHING: tr("Moving to the Trash"),
        fileattr.CHANGING: tr("Changing attributes of"),
    }.get(action, action)


def _remembered_tooltip(row: Any) -> str:
    """What a *Remembered directories* entry keeps, in words."""
    from navkit.tooltip import lines as tooltip_lines

    lines = [row.path]
    sorts = dict(zip(SORT_MODES, (caption.replace("~", "") for caption in sort_captions())))
    mode = sorts.get(row.sort_mode, sorts["name"])
    lines.append(tr("Sorted by {mode}, reversed").format(mode=mode) if row.sort_reverse
                 else tr("Sorted by {mode}").format(mode=mode))
    views = {"simple": tr("Simple"), "detailed": tr("Detailed"), "list": tr("List")}
    lines.append(tr("View mode: {mode}").format(mode=views.get(row.view_mode, views["simple"])))
    if row.file_mask and row.file_mask != "*":
        lines.append(tr("Only files matching {mask} are shown").format(mask=row.file_mask))
    if not row.show_hidden:
        lines.append(tr("Hidden files are not shown"))
    if row.subdirs:
        lines.append(tr("The directories below are shown the same way"))
    return tooltip_lines(*lines)


def bookmark_menu(rows: list[Any], bookmarked: bool,
                  mounts: Sequence[Path] = (),
                  present: set[str] | None = None) -> tuple[Any, Any]:
    """The box's entries for *rows*, then *mounts*, and the item that adds or removes.

    An entry whose directory is not there is greyed: one not in *present*,
    or, without it, one that is not a directory now.

    The home directory is spelled ``~``, as a shell would; a file name's
    tildes are doubled so the caption shows them rather than marking a key.
    A labelled bookmark shows its label, and its path where a menu shows an
    entry's key.

    **Each entry's tooltip says what the caption leaves out** (a departure:
    DN's box had none): the whole path where a label or ``~`` stands for it,
    that a greyed one is not there now, and that a mount below the line is
    not a bookmark.
    """
    from navml.widgets.dialog.control.control import escape_caption
    from navml.widgets.menu.sub_menu import SubMenu

    menu = SubMenu()
    home = str(Path.home())
    entries = [(row.path, row.label) for row in rows]
    entries += [(str(path), "") for path in mounts]
    for index, (path, label) in enumerate(entries):
        if index == len(rows) and rows:
            menu.add_line()
        shown = path
        if shown == home or shown.startswith(home.rstrip("/") + "/"):
            shown = "~" + shown[len(home.rstrip("/")):]
        caption = escape_caption(label or shown)
        if index < len(BOOKMARK_KEYS):
            caption = f"~{BOOKMARK_KEYS[index]}~ {caption}"
        else:
            caption = f"  {caption}"
        item = menu.add_item(caption)
        if label:
            item.key = shown
        item.disabled = not (path in present if present is not None else Path(path).is_dir())
        lines = [path] if label or shown != path else []
        if index >= len(rows):
            lines.append(tr("Mounted now, not a bookmark"))
        if item.disabled:
            lines.append(tr("Not there now"))
        item.tooltip = "\n".join(lines)
    if entries:
        menu.add_line()
    toggle = menu.add_item(tr("~R~emove this folder") if bookmarked else tr("~A~dd this folder"))
    return menu, toggle


def _entry_location(here: Any, entry: Any) -> Location:
    """Where *entry* of a listing of *here* is: ``Panel.entry_location`` for a
    directory the panel may no longer show."""
    if entry.directory is not None:
        return Location.of(entry.directory) / entry.name
    return Location.of(here) / entry.name


def _rename_found(found: Any, moved: list[tuple[Any, Any]]) -> None:
    """A *Find:* listing's entries renamed where they are, as DN's record took
    the new name (``PFileRec(Own)^.Name``): each moved beside itself is
    listed by its new name.  One moved elsewhere is left to drop out on the
    re-read.  The list is replaced, so the change counts."""
    renamed = {Location.of(source): Location.of(dest) for source, dest in moved
               if Location.of(dest).parent == Location.of(source).parent}
    if not renamed:
        return
    entries = []
    for entry in found.entries:
        directory = entry.directory
        dest = renamed.get(Location.of(directory) / entry.name) if directory is not None else None
        if dest is not None:
            entry = DirEntry(dest.name, entry.is_dir, entry.size, entry.mode, entry.mtime,
                             entry.is_link, entry.link_target, entry.uid, entry.gid, directory=directory)
        entries.append(entry)
    found.entries = entries


def _at_root(panel: Any) -> bool:
    """Whether *panel* is at ``root:`` -- the disk, read as root."""
    from navigator.lib.drives.root import ROOT_SITE

    return panel.location.site == ROOT_SITE and panel.location.outer is None


def _disk_only(panel: Any) -> str:
    """Why a command that works on the disk alone is greyed on *panel*: a
    ``root:`` panel is the disk, but the command would run as the user,
    against a place only root may read (a departure's limit; the
    ``navigator-elevation`` skill) -- else it is another drive."""
    if _at_root(panel):
        return tr("Not as root: the command runs as you")
    return tr("Only on the local disk")


def _real_place(target: Location) -> Location:
    """*target* with its links resolved, on the disk and if it is there --
    blocking: on a thread."""
    if target.is_local and target.local.exists():
        return Location.of(target.local.resolve())
    return target


def _into_itself(target: Location, entries: Iterable[Any], here: Any) -> Any:
    """The first directory among *entries* of *here* that is *target* or
    above it, or None."""
    above = (target, *(Location(target.site, parent, target.outer) for parent in target.path.parents))
    return next((entry for entry in entries if entry.is_dir and _entry_location(here, entry) in above), None)


def _move_keys(glyphs: int) -> str:
    """Ctrl+Up/Ctrl+Down as the key bar says them: arrows, or words in ASCII."""
    arrows = "Up/Down" if glyphs <= glyphs_module.GLYPHS_ASCII else "\u2191\u2193"
    return f"Ctrl+{arrows}"


def link_section(menu: Any, *, before: Any = None, glyphs: int = glyphs_module.GLYPHS_UNICODE) -> dict[int, Any]:
    """The box's *Link*: DN's ``SelectDrive`` listed the other PC's drives
    under ``LINK``; here a submenu of the connection profiles, ticked where
    connected, and a *New ... link* for each protocol.  Each item's id, to its
    profile -- or, for a *New*, its scheme.  Greyed, with why, where the
    protocol cannot be had.  The
    bookmarks' own keys act on a profile in it (``choose_bookmark``)."""
    from navml.widgets.dialog.control.control import escape_caption

    from navigator.lib.drives import profiles, sessions
    from navigator.lib.drives.sessions import SESSIONS

    link = menu.add_submenu(tr("~L~ink"), before=before)
    rows = profiles.profiles()
    if rows:
        # The keys ``_profile_key`` takes there, for the key bar.
        link.hints = (("F2", tr("Edit")), ("Del", tr("Delete")), (_move_keys(glyphs), tr("Move")))
    menu.add_line(before=before)
    found: dict[int, Any] = {}
    for row in rows:
        item = link.add_item(escape_caption(row.name))
        location = profiles.location_of(row)
        item.ticked = SESSIONS.is_open(location.site)
        # The protocol before the place: what the link is over, never hidden.
        item.key = f"{sessions.protocol_sign(row.scheme)} {row.user + '@' if row.user else ''}{row.host}"
        why = sessions.available(row.scheme)
        item.disabled = why is not None
        # The whole address, the port and the directory the caption leaves out.
        lines = [str(location), tr("Connected") if item.ticked else tr("Not connected")]
        if why is not None:
            lines.append(why)
        item.tooltip = "\n".join(lines)
        found[id(item)] = row
    if rows:
        link.add_line()
    # One *New* for each protocol, named: what the link is over is never hidden.
    for caption, scheme in ((tr("~N~ew SSH link (SFTP)..."), "sftp"), (tr("New ~F~TP link..."), "ftp"),
                            (tr("New S~M~B link (Windows share)..."), "smb"), (tr("New S~3~ link (Amazon S3)..."), "s3"),
                            (tr("New ~D~ocker container link..."), "docker"),
                            (tr("New ~P~odman container link..."), "podman"),
                            (tr("New ~A~ndroid device link (adb)..."), "adb")):
        new = link.add_item(caption)
        why = sessions.available(scheme)
        if why is not None:
            new.disabled = True
            new.key = sessions.EXTRA_HINT.get(scheme, "")
            # Why it is greyed, and what to install: the key column has room
            # for the extra's name only.
            extra = sessions.EXTRA_HINT.get(scheme)
            new.tooltip = "\n".join([why] + ([tr("Install {extra}").format(extra=extra)] if extra else []))
        found[id(new)] = scheme
    # Whatever the desktop's GVfs or KIO reaches: a URI asked (``Shell.gvfs_link``).
    from navigator.lib.system import desktop

    new = link.add_item(tr("New ~G~Vfs/KIO link (MTP, WebDAV...)..."))
    if desktop.program() is None:
        new.disabled = True
        new.key = "gio/kio"
        new.tooltip = tr("Needs the desktop's gio or KDE's kioclient command")
    found[id(new)] = "gvfs"
    if rows:
        # *Saved links*, which the branch for a *New* opens for this mark.
        link.add_line()
        found[id(link.add_item(tr("~E~dit links...")))] = EDIT_LINKS
    return found


#: What ``link_section`` maps its *Edit links* item to, in place of a scheme.
EDIT_LINKS = "*edit*"


#: A double vertical line's box characters, and the single ones the held
#: divider is drawn with.
_SINGLE_VERTICAL = {
    "║": "│", "╗": "┐", "╝": "┘", "╔": "┌", "╚": "└",
    "╖": "┐", "╜": "┘", "╓": "┌", "╙": "└",
    "╢": "┤", "╣": "┤", "╟": "├", "╠": "├", "╫": "┼", "╬": "┼",
}


def _hint(widget: Any, basis: int, grow: int) -> None:
    """*widget*'s layout hint, written only if it changes."""
    current = parse_declarations(widget.inline_style)
    if current.get("basis", 0) == basis and current.get("grow", 1) == grow:
        return
    widget.merge_style({"basis": basis, "grow": grow})


def _is_archive(entry: Any) -> bool:
    """An entry Shift+F2 extracts: a file the *archive* file type takes."""
    from navigator.lib.appearance import filetypes

    return (not entry.is_dir and entry.name != ".." and stat.S_ISREG(entry.mode)
            and filetypes.group_of(entry.name) == "archive")
