"""Which colour class a panel row takes: the file's type, or else its category.

Two traditions meet here, and the listing needs both.  DOS Navigator coloured a
row by *category* -- the Colors dialog's *File Panel > Highlight* group gives
Executables [173] and Archives [174] a slot each, and Custom 1 to 5 [175-181]
were coloured by masks the user typed into *Highlight groups*
(``SetHighlightGroups``, COLORS.PAS).  Midnight Commander colours a row by
*type*: a symlink, a stale one, a device, a socket or a FIFO, an executable.
A POSIX listing is full of the second kind, which DOS had none of.

So a row gets at most one class from here, and the type wins: an executable
``build.sh`` is something to run before it is source, and a link to an archive
is a link.  That is the rule :data:`navigator.icons.BY_TYPE` already follows,
so an icon and a colour never disagree about what an entry is.  A directory is
the panel's own ``.directory`` and takes no category -- a directory called
``backup.zip`` is not an archive -- but a symlink to one does take ``symlink``,
beside ``.directory``.

The classes are the file manager's vocabulary and not the kit's, which is why
this lives beside ``icons.py``; ``navigator.nss`` gives each one a colour.
"""

from __future__ import annotations

import fnmatch
from functools import lru_cache

#: A file's *type* -> class, keyed by Midnight Commander's one-character mark
#: (``DirEntry.type_mark``).  ``/`` is missing on purpose: a plain directory
#: is already ``.directory``.
BY_TYPE = {
    "*": "executable",
    "@": "symlink",
    "~": "symlink",
    "!": "stale-link",
    "-": "device",
    "+": "device",
    "=": "special",
    "|": "special",
}

#: Category -> mask, in DN's own mask syntax (``;``-separated shell patterns,
#: matched without regard to case, as *Select group* reads them).  The first
#: category that matches wins, so the order is the precedence.  ``archive`` is
#: DN's; the rest are the custom groups DN left to the user, filled in with the
#: kinds a file manager is actually pointed at.
CATEGORIES = {
    "archive": "*.zip;*.tar;*.gz;*.tgz;*.bz2;*.tbz;*.tbz2;*.xz;*.txz;*.zst;*.lz;*.lzma;*.z;"
               "*.7z;*.rar;*.arj;*.lha;*.lzh;*.cab;*.ace;*.zoo;*.cpio;*.deb;*.rpm;*.apk;"
               "*.jar;*.war;*.whl;*.iso;*.img;*.dmg",
    "image": "*.png;*.jpg;*.jpeg;*.gif;*.bmp;*.svg;*.webp;*.ico;*.tif;*.tiff;*.psd;*.xcf;"
             "*.pcx;*.tga;*.heic;*.avif;*.raw;*.cr2;*.nef",
    "media": "*.mp3;*.flac;*.ogg;*.oga;*.opus;*.wav;*.m4a;*.aac;*.wma;*.mid;*.midi;*.mod;"
             "*.mp4;*.mkv;*.avi;*.mov;*.webm;*.wmv;*.flv;*.mpg;*.mpeg;*.m4v;*.ogv",
    "document": "*.pdf;*.doc;*.docx;*.odt;*.rtf;*.xls;*.xlsx;*.ods;*.csv;*.ppt;*.pptx;*.odp;"
                "*.epub;*.djvu;*.ps;*.md;*.rst;*.txt;*.tex",
    "source": "*.py;*.pyi;*.c;*.h;*.cc;*.cpp;*.cxx;*.hpp;*.rs;*.go;*.js;*.mjs;*.ts;*.java;"
              "*.kt;*.cs;*.rb;*.pl;*.php;*.lua;*.pas;*.inc;*.asm;*.s;*.sh;*.bash;*.zsh;"
              "*.nml;*.nss",
    "temp": "*~;*.bak;*.tmp;*.temp;*.swp;*.swo;*.orig;*.rej;#*#",
}


def patterns(mask: str) -> list[str]:
    """*mask*'s patterns: ``;``-separated, blanks dropped."""
    return [pattern.strip() for pattern in mask.split(";") if pattern.strip()]


def matches(name: str, patterns: list[str]) -> bool:
    """Whether *name* matches any of *patterns*, as a POSIX shell's glob would.

    A departure from DN's ``InMask``, which folded case and let ``*.*`` match a
    name with no dot, as DOS did: here case counts and ``*.*`` needs a dot,
    since ``README`` and ``readme`` are two files.  Colouring by type still
    ignores the extension's case (:func:`category_of`), which is a matter of
    display, not of which files an operation takes.
    """
    return any(fnmatch.fnmatchcase(name, pattern) for pattern in patterns)


def _index(categories: dict[str, str]) -> tuple[dict[str, str], list[tuple[str, list[str]]]]:
    """*categories* split once for :func:`category_of`: a plain ``*.ext`` --
    nearly every pattern -- becomes an extension lookup, and the rest (``*~``,
    ``#*#``) are kept to be matched in order."""
    by_extension: dict[str, str] = {}
    others: list[tuple[str, list[str]]] = []
    for category, mask in categories.items():
        rest = []
        for pattern in patterns(mask):
            extension = pattern[2:].lower()
            if pattern.startswith("*.") and not any(c in extension for c in "*?[.;"):
                by_extension.setdefault(extension, category)
            else:
                rest.append(pattern)
        if rest:
            others.append((category, rest))
    return by_extension, others


_BY_EXTENSION, _OTHERS = _index(CATEGORIES)


#: DN's ``TType`` order, which *Group* sorts by: ``ttDirectory``, ``ttExec``,
#: ``ttArc``, then the custom groups (``ttCust1``..``ttCust5``) -- here the
#: categories after ``archive``, in their order -- and last, everything else.
GROUPS: tuple[str, ...] = ("directory", "executable", *CATEGORIES)


@lru_cache(maxsize=4096)
def group_of(name: str) -> str | None:
    """The category *name* belongs to by its name alone, or None: what
    :func:`category_of` falls back to once the entry's type has had its say."""
    stem, dot, extension = name.rpartition(".")
    if dot and stem:
        found = _BY_EXTENSION.get(extension.lower())
        if found:
            return found
    for category, rest in _OTHERS:
        if matches(name, rest):
            return category
    return None


@lru_cache(maxsize=4096)
def category_of(name: str, is_dir: bool, mark: str = " ") -> str | None:
    """The colour class for an entry called *name*, of type *mark*, or None.

    Takes the fields it needs rather than a ``DirEntry``, as
    :func:`navigator.icons.icon_for` does.  *mark* is ``DirEntry.type_mark``;
    one in :data:`BY_TYPE` beats the category.  A plain directory and ``..``
    have none.

    A pattern that is not a plain ``*.ext`` is tried after every extension,
    whichever category it belongs to -- ``*~`` does not outrank ``*.zip`` by
    being written first, since no name can end in both.
    """
    if name == "..":
        return None
    if mark in BY_TYPE:
        return BY_TYPE[mark]
    if is_dir:
        return None
    return group_of(name)
