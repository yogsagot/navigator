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

from navkit.stylesheet import Stylesheet, read


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

#: The palettes, one per colour scheme, each defining every variable the sheet
#: above reads.  They are DOS Navigator's own ``COLORS/*.PAL`` files decoded by
#: ``tools/palconv.py``, so retheming is picking one rather than writing one.
THEMES = STYLES / "themes"

#: The scheme DOS Navigator itself starts in -- ``DEFAULT.PAL``.
DEFAULT_THEME = "default"


def theme_names() -> list[str]:
    """Every theme that can be asked for by name."""
    return sorted(path.stem for path in THEMES.glob("*.nss"))


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
    property until :class:`~navigator.widgets.panel.Panel` has been imported.
    While every screen lived in one module that was a rule about where to put
    the parse; now it is a rule about what to import before it, so the import
    is here instead of being left to whoever calls.  Ordering is the price of
    catching a misspelled property at its ``.nss`` line.
    """
    import navml.widgets

    import navigator.widgets.panel  # noqa: F401 -- declares `icons'

    # And every library widget, because the sheet below styles them and a
    # `StyleProperty' is registered by its class body running.  One call
    # rather than a list of imports: a list is a thing to forget.
    navml.widgets.import_all()

    path = THEMES / f"{theme}.nss"
    if not path.is_file():
        raise LookupError(
            f"no theme {theme!r}; there is " + ", ".join(theme_names())
        )
    return read(SCHEME_PATH, path, *extra)


@cache
def default_scheme() -> Stylesheet:
    """The scheme a desktop that does not ask for a theme resolves against.

    Parsed once, because a sheet is immutable and every such desktop wants the
    same one -- but parsed on the first *call* rather than at import, which is
    what lets :func:`load_scheme` import the widgets it needs without this
    module importing them at its own import time.
    """
    return load_scheme()
