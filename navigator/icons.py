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
    "xml": "",
    "nss": "",
    "nml": "",
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


def icon_for(name: str, is_dir: bool) -> str:
    """The glyph standing for an entry called *name*.

    Takes the two fields it needs rather than a ``DirEntry`` so that it stays
    testable on its own and imposes nothing on the entry type -- which is
    slotted, and gains no field for this.
    """
    if name == "..":
        return PARENT
    if is_dir:
        return FOLDER
    _, dot, extension = name.rpartition(".")
    # ``rpartition`` gives an empty separator when there is no dot at all, and
    # a leading-dot name like ``.gitignore`` has no extension either -- its
    # stem is empty, so the whole name is the "extension" and must not match.
    if not dot or not _:
        return FILE
    return BY_EXTENSION.get(extension.lower(), FILE)
