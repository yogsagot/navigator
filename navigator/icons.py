"""Which Nerd Font glyph stands for which kind of file.

This is the file manager's vocabulary and not the kit's, which is why it lives
here: `navkit` knows what a terminal can *draw* and nothing at all about
filenames.  Every codepoint below is in the Private Use Area and will arrive as
a replacement box on a terminal without a Nerd Font, so nothing here may be
consulted unless :attr:`navkit.capabilities.TerminalInfo.glyphs` has reached
``GLYPHS_NERD``.

A note on fidelity, since it cuts against the project's usual rule: DOS
Navigator had no icons, and could not have had them -- CP437 has no such
glyphs and the original distinguished a directory by colour and by the word
``DIR`` in the size column, which Navigator still does.  Icons are therefore a
deliberate departure rather than a recreation, taken because a terminal that
ships the font makes them free, and reversible with ``icons: none`` in a sheet
or ``--glyphs unicode`` on the command line.
"""

from __future__ import annotations

#: The generic three.  Everything that is not matched by extension lands on
#: :data:`FILE`.
FOLDER = ""       # nf-custom-folder
PARENT = ""       # nf-fa-arrow_up
FILE = ""         # nf-fa-file

#: A dot-file or dot-directory with nothing more specific to say: the outline
#: of :data:`FILE` and a folder, faint beside the solid ones as a hidden
#: entry is.  Only the plain cases -- a type mark or a known extension still
#: wins, so ``.config.json`` is JSON and a dot-link a link.  Font Awesome 4,
#: at the same codepoints in Nerd Fonts 2 and 3.
HIDDEN_FILE = ""    # nf-fa-file_o
HIDDEN_FOLDER = ""  # nf-fa-folder_o

#: A directory on the Alt+F1/Alt+F2 list.  Font Awesome 4's bookmark, at the
#: same codepoint in Nerd Fonts 2 and 3 -- Material Design's ``folder_star``
#: would say "folder" too, but it moved between the two.
BOOKMARKED_FOLDER = ""  # nf-fa-bookmark

#: Extension -> glyph.  Deliberately short: an icon set that guesses at a
#: hundred extensions is mostly wrong in ways nobody notices, and the ones
#: below are the kinds a file manager is actually pointed at.  Keys are
#: lower-cased and carry no dot.
BY_EXTENSION = {
    # code
    "py": "",
    "pyi": "",
    "c": "",
    "h": "",
    "cpp": "",
    "hpp": "",
    "rs": "",
    "go": "",
    "js": "",
    "ts": "",
    "sh": "",
    "bash": "",
    "pas": "",
    # markup and data
    "md": "",
    "rst": "",
    "txt": "",
    "html": "",
    "css": "",
    "json": "",
    "toml": "",
    "yaml": "",
    "yml": "",
    "xml": "",  # nf-fa-code
    "nss": "",
    "nml": "",  # nf-fa-code
    # archives
    "zip": "",
    "gz": "",
    "bz2": "",
    "xz": "",
    "tar": "",
    "rar": "",
    "7z": "",
    # images
    "png": "",
    "jpg": "",
    "jpeg": "",
    "gif": "",
    "bmp": "",
    "svg": "",
    "ico": "",
    # media
    "mp3": "",
    "wav": "",
    "flac": "",
    "mp4": "",
    "mkv": "",
    "avi": "",
    # documents and the rest
    "pdf": "",
    "exe": "",
    "com": "",
    "dll": "",
    "so": "",
    "o": "",
    "log": "",
    "pal": "",
}

#: A file's *type* -> glyph, keyed by Midnight Commander's one-character mark
#: (``DirEntry.type_mark``), so the Nerd tier says with a glyph what the
#: others say with ``@`` or ``*``.  The type wins over the extension: an
#: executable ``build.sh`` is shown as something to run, and a link to a
#: directory as a link.  Drawn only from Font Awesome and Octicons, which
#: Nerd Fonts 2 and 3 both carry at these codepoints.
BY_TYPE = {
    "~": "",  # nf-oct-file_symlink_directory
    "@": "",  # nf-oct-file_symlink_file
    "!": "",  # nf-fa-chain_broken
    "*": "",  # nf-oct-terminal
    "=": "",  # nf-fa-plug
    "-": "",  # nf-fa-keyboard_o
    "+": "",  # nf-fa-hdd_o
    "|": "",  # nf-fa-exchange
}


def icon_for(name: str, is_dir: bool, mark: str = " ", bookmarked: bool = False) -> str:
    """The glyph standing for an entry called *name*, of type *mark*.

    Takes the fields it needs rather than a ``DirEntry`` so that it stays
    testable on its own and imposes nothing on the entry type.  *mark* is
    ``DirEntry.type_mark``; one in :data:`BY_TYPE` beats the directory and the
    extension.  A *bookmarked* directory beats both, a link to one included:
    it is the place the user named, wherever it leads.
    """
    if name == "..":
        return PARENT
    if bookmarked and is_dir:
        return BOOKMARKED_FOLDER
    if mark in BY_TYPE:
        return BY_TYPE[mark]
    hidden = name.startswith(".")
    if is_dir:
        return HIDDEN_FOLDER if hidden else FOLDER
    plain = HIDDEN_FILE if hidden else FILE
    _, dot, extension = name.rpartition(".")
    # ``rpartition`` gives an empty separator when there is no dot at all, and
    # a leading-dot name like ``.gitignore`` has no extension either -- its
    # stem is empty, so the whole name is the "extension" and must not match.
    if not dot or not _:
        return plain
    return BY_EXTENSION.get(extension.lower(), plain)
