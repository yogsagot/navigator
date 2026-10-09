"""The *File type* submenu the editor's and the viewer's menus share.

Built from :data:`navigator.highlight.FILE_TYPES` rather than written out in
both windows' markup: *Automatic* (``highlight.ini``'s choice), a submenu per
group, and *None*, each asking for :class:`SetFileType` -- in a window's
menu, or on its own in a box by Ctrl+Shift+H (:func:`choose_file_type`).  The captions are
bound as the generator binds a markup caption, so they follow a change of
language; the languages' own names are names and stay as they are.
"""

from __future__ import annotations

from typing import Any, Callable

from navkit.i18n import tr
from navkit.reactive import bind
from navml.widgets.menu.sub_menu import SubMenu

from navigator.highlight import FILE_TYPES, NONE
from navigator.widgets.editor.commands import SetFileType

#: Each group's caption, by its name in ``FILE_TYPES``.
GROUPS: dict[str, Callable[[], str]] = {
    "programming": lambda: tr("~P~rogramming languages"),
    "scripting": lambda: tr("~S~cripting languages"),
    "markup": lambda: tr("~M~arkup languages"),
    "misc": lambda: tr("M~i~scellaneous"),
}


def _marked(captions: list[str]) -> list[str]:
    """*captions* with a hotkey each: the first character no caption
    before it has taken, else none."""
    taken: set[str] = set()
    marked = []
    for caption in captions:
        for at, char in enumerate(caption):
            if not char.isspace() and char.casefold() not in taken:
                taken.add(char.casefold())
                marked.append(f"{caption[:at]}~{char}~{caption[at + 1:]}")
                break
        else:
            marked.append(caption)
    return marked


def _caption(text: Callable[[], str]) -> object:
    return bind(lambda _o: text(), yielding=True)


def fill_file_types(menu: SubMenu) -> None:
    """Put the file types into *menu*, an empty submenu."""
    automatic = menu.add_item("", SetFileType(""))
    automatic.text = _caption(lambda: tr("~A~utomatic"))
    menu.add_line()
    for group, languages in FILE_TYPES:
        sub = menu.add_submenu("")
        sub.text = _caption(GROUPS[group])
        for caption, (_, lexer) in zip(_marked([name for name, _ in languages]), languages):
            sub.add_item(caption, SetFileType(lexer))
    menu.add_line()
    none = menu.add_item("", SetFileType(NONE))
    none.text = _caption(lambda: tr("~N~one"))


async def choose_file_type(window: Any) -> str | None:
    """Ctrl+Shift+H: the file types in a box centred on *window*, ticked from
    its ``checks``; the file type chosen, or None for Esc.  Spawned, never
    awaited from a handler."""
    from navml.widgets.menu.popup_menu import PopupMenu

    menu = SubMenu()
    fill_file_types(menu)
    app = window.application
    width, height = PopupMenu.measure(menu, app, window)
    ox, oy = window.offset()
    x = ox + window.x + max(0, (window.width - width) // 2)
    y = oy + window.y + max(0, (window.height - height) // 2)
    chosen = await PopupMenu(menu, x, y, current=0, behind=window).execute(app)
    if chosen is None or not isinstance(chosen.command, SetFileType):
        return None
    return chosen.command.file_type
