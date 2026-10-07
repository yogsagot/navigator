"""Where a colour scheme comes from.

Colour is split from structure and neither half is authored by hand:
``navigator.nss`` holds the rules and defines no variable, so it does not parse
alone, and a theme defines every variable and no rule.  One is always loaded
after the other, which is what this module is for.

Kept apart from the widgets that read it, and not only for tidiness: the
desktop resolves against a sheet and a sheet is checked against the properties
widgets declare, so a module holding both would have to be careful about the
order of its own contents.  Here the question does not arise.
"""

from __future__ import annotations

from functools import cache
from importlib.resources import files
from pathlib import Path

from navkit.stylesheet import Stylesheet, StylesheetError, load, read


#: Where sheets live.  A directory rather than a single file because a theme is
#: nothing more than another ``.nss`` loaded after the default one, so this is
#: also where one would be dropped.
#:
#: Located through the package rather than by walking out from ``__file__``,
#: so it resolves the same from a source checkout, from an installed copy, and
#: whether this module is run as ``__main__`` or imported by name.
STYLES = Path(str(files("navigator.styles")))

#: What the screens are made of: the rules, in terms of variables it does not
#: define.  It does not parse on its own; a palette always follows it.
SCHEME_PATH = STYLES / "navigator.nss"
#: Every entry's text attributes, between the rules and the theme
#: (``attributes.nss``): what Options > Colors sets beyond the colours.
ATTRIBUTES_PATH = STYLES / "attributes.nss"

#: The palettes, one per colour scheme, each defining every variable the sheet
#: above reads.  They are DOS Navigator's own ``COLORS/*.PAL`` files decoded by
#: ``tools/palconv.py``, so retheming is picking one rather than writing one.
THEMES = STYLES / "themes"

#: What a palette given as text is called in an error.
PALETTE_SOURCE = "<palette>"

#: The scheme DOS Navigator itself starts in -- ``DEFAULT.PAL``.
DEFAULT_THEME = "default"


def _theme_dirs() -> list[Path]:
    """Where a theme is looked for by name: the user's own first (Store
    palette's default directory, ``~/.config/navigator/themes``), so one
    stored under a shipped name is the one that loads, then the shipped ones."""
    from navigator.palette import user_themes

    return [user_themes(), THEMES]


def theme_names() -> list[str]:
    """Every theme that can be asked for by name, the user's among them."""
    found: set[str] = set()
    for directory in _theme_dirs():
        try:
            found.update(path.stem for path in directory.glob("*.nss"))
        except OSError:
            pass
    return sorted(found)


def theme_path(theme: str) -> Path:
    """The file *theme* names; ``LookupError`` for none."""
    for directory in _theme_dirs():
        path = directory / f"{theme}.nss"
        if path.is_file():
            return path
    raise LookupError(f"no theme {theme!r}; there is " + ", ".join(theme_names()))


def load_scheme(theme: str = DEFAULT_THEME, *extra) -> Stylesheet:
    """The rules, with *theme*'s palette merged over them.

    Merged rather than concatenated: the palette is only variable definitions,
    and those resolve across sheets before any rule is read, so a palette needs
    no rules of its own and cannot accidentally out-specify one.

    *extra* is anything :func:`~navkit.stylesheet.read` accepts, loaded last --
    a path to a sheet of one's own, or a ``(name, text)`` pair.

    **The widgets are imported first, and that import is the whole reason this
    function has a body rather than being a constant.**  A sheet is checked
    against the properties widgets declare, and a widget declares them by its
    class body running -- so ``navigator.nss``'s ``icons: auto`` is an unknown
    property until :class:`~navigator.widgets.manager.panel.Panel` has been imported.
    While every screen lived in one module that was a rule about where to put
    the parse; now it is a rule about what to import before it, so the import
    is here instead of being left to whoever calls.  Ordering is the price of
    catching a misspelled property at its ``.nss`` line.
    """
    _import_widgets()
    return read(SCHEME_PATH, ATTRIBUTES_PATH, theme_path(theme), *extra)


def _import_widgets() -> None:
    import navml.widgets

    import navigator.widgets.manager.panel  # noqa: F401 -- declares `icons'

    # And every library widget, because the sheet below styles them and a
    # `StyleProperty' is registered by its class body running.  One call
    # rather than a list of imports: a list is a thing to forget.
    navml.widgets.import_all()


def theme_sources(theme: str = DEFAULT_THEME) -> list[tuple[str, str]]:
    """The rules, the attributes and *theme*, read: what :func:`scheme_from`
    parses.  The disk half of :func:`load_scheme`, for a caller that parses
    the same three again and again -- Options > Colors, at every change --
    and reads them once, on a thread.  Raises ``OSError`` and ``LookupError``."""
    return [(str(path), path.read_text(encoding="utf-8"))
            for path in (SCHEME_PATH, ATTRIBUTES_PATH, theme_path(theme))]


def scheme_from(sources: list[tuple[str, str]], *extra: tuple[str, str]) -> Stylesheet:
    """:func:`theme_sources`' sheets parsed, with *extra* loaded last."""
    _import_widgets()
    return load([*sources, *extra])


def palette_source(text: str) -> tuple[str, str]:
    """A palette's *text*, as :func:`scheme_from` takes it."""
    return (PALETTE_SOURCE, text)


def user_scheme(theme: str = DEFAULT_THEME) -> tuple[Stylesheet, str | None]:
    """*theme* with the user's palette (Options > Colors, ``palette.nss``)
    over it, and what was wrong with the palette, or None.  A palette that
    cannot be read or parsed is left out, so a broken hand edit costs its
    colours and not the session."""
    from navigator.palette import palette_path

    path = palette_path()
    if not path.is_file():
        return load_scheme(theme), None
    try:
        return load_scheme(theme, path), None
    except StylesheetError as error:
        return load_scheme(theme), str(error)


@cache
def default_scheme() -> Stylesheet:
    """The scheme a desktop that does not ask for a theme resolves against.

    Parsed once, because a sheet is immutable and every such desktop wants the
    same one -- but parsed on the first *call* rather than at import, which is
    what lets :func:`load_scheme` import the widgets it needs without this
    module importing them at its own import time.
    """
    return load_scheme()
