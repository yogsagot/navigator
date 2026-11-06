"""The editor's *Line endings* and *Encoding* menus -- **a departure, asked for**.

DN's editor wrote every file in ``CR+LF`` and the screen's code page.  Here a
text keeps the line endings and the encoding it was read in
(:mod:`navigator.lib.editor.encodings`), the bottom frame shows both
(``FormatMarks``), and these menus change them: on Editor > File, and in a box
over the marker clicked (:func:`choose_line_ending`, :func:`choose_encoding`).
Each entry asks for a command the editor answers and ticks
(:class:`SetLineEnding`, :class:`ReopenWithEncoding`,
:class:`SaveWithEncoding`).
"""

from __future__ import annotations

from typing import Any, Callable

from navkit.i18n import tr
from navkit.reactive import bind
from navml.widgets.menu.sub_menu import SubMenu

from navigator.lib.editor import encodings
from navigator.widgets import encoding_menu
from navigator.widgets.editor.commands import ReopenWithEncoding, SaveWithEncoding, SetLineEnding

#: Each ending's key and its caption.
ENDINGS: tuple[tuple[str, Callable[[], str]], ...] = (
    ("lf", lambda: tr("~L~F (Unix)")),
    ("crlf", lambda: tr("~C~RLF (DOS, Windows)")),
    ("cr", lambda: tr("C~R~ (classic Mac)")),
)


def _caption(text: Callable[[], str]) -> object:
    return bind(lambda _o: text(), yielding=True)


def fill_line_endings(menu: SubMenu) -> None:
    """The three endings into *menu*, an empty submenu."""
    for key, caption in ENDINGS:
        item = menu.add_item("", SetLineEnding(key))
        item.text = _caption(caption)


def _fill_codecs(menu: SubMenu, command: type) -> None:
    """The Unicode encodings, then the code pages a submenu a group."""
    encoding_menu.fill(menu, [(key, caption) for key, _, caption in encodings.UNICODE], command=command)


def fill_encodings(menu: SubMenu) -> None:
    """*Reopen with encoding* and *Save with encoding* into *menu*, an empty
    submenu, each listing every encoding."""
    reopen = menu.add_submenu("")
    reopen.text = _caption(lambda: tr("~R~eopen with encoding"))
    _fill_codecs(reopen, ReopenWithEncoding)
    save = menu.add_submenu("")
    save.text = _caption(lambda: tr("~S~ave with encoding"))
    _fill_codecs(save, SaveWithEncoding)


async def _popup(window: Any, menu: SubMenu, title: str, at: tuple[int, int] | None,
                 current: int = 0) -> Any:
    """*menu* in a box with its bottom left at *at* (screen cells), else
    centred on *window*; the command chosen, or None.  Spawned, never awaited
    from a handler."""
    from navml.widgets.menu.popup_menu import PopupMenu

    app = window.application
    # The editor answers the commands, so it decides whether they are enabled.
    behind = getattr(window, "editor", window)
    width, height = PopupMenu.measure(menu, app, behind, title)
    if at is None:
        ox, oy = window.offset()
        x = ox + window.x + max(0, (window.width - width) // 2)
        y = oy + window.y + max(0, (window.height - height) // 2)
    else:
        x, y = at[0], max(0, at[1] - height)
    chosen = await PopupMenu(menu, x, y, current=current, behind=behind, title=title).execute(app)
    return None if chosen is None else chosen.command


async def choose_line_ending(window: Any, at: tuple[int, int] | None = None) -> Any:
    """The endings in a box; the :class:`SetLineEnding` chosen, or None."""
    menu = SubMenu()
    fill_line_endings(menu)
    ending = getattr(getattr(window, "editor", None), "document", None)
    keys = [key.upper() for key, _ in ENDINGS]
    current = keys.index(ending.line_ending) if ending is not None and ending.line_ending in keys else 0
    return await _popup(window, menu, tr("Line endings"), at, current)


async def choose_encoding(window: Any, at: tuple[int, int] | None = None) -> Any:
    """*Reopen with* and *Save with* in a box; the command chosen, or None."""
    menu = SubMenu()
    fill_encodings(menu)
    return await _popup(window, menu, tr("Encoding"), at)
