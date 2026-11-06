"""Encodings in a menu, the legacy code pages grouped by script and region --
one shape for the editor's *Reopen with* / *Save with* and the viewer's
Shift+F6, so each box fits a 24-row screen.

The entries at the top (the Unicode encodings, or the viewer's *UTF-8*) come
first, then a line, then a submenu per group of
:data:`navigator.lib.codepages.GROUPS`.  The group captions are bound as the
generator binds a markup caption, so they follow a change of language; the
code pages' own captions are names and stay as they are.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from navkit.reactive import bind
from navml.widgets.menu.menu_item import MenuItem
from navml.widgets.menu.sub_menu import SubMenu

from navigator.lib.codepages import CODEPAGES, GROUPS, CodePage, grouped


def marked(captions: Iterable[str], taken: set[str] | None = None) -> list[str]:
    """*captions* with a hotkey each: the first letter or digit neither a
    caption before it nor *taken* has, else none."""
    taken = set() if taken is None else set(taken)
    out = []
    for caption in captions:
        for at, char in enumerate(caption):
            if char.isalnum() and char.casefold() not in taken:
                taken.add(char.casefold())
                out.append(f"{caption[:at]}~{char}~{caption[at + 1:]}")
                break
        else:
            out.append(caption)
    return out


def _hotkey(caption: str) -> str:
    start = caption.find("~")
    return caption[start + 1].casefold() if 0 <= start < len(caption) - 1 else ""


@dataclass
class Filled:
    """What :func:`fill` put in: each item's key, and where each key is --
    ``(index of its entry in the menu, index in its submenu or -1)``."""

    keys: dict[int, str] = field(default_factory=dict)
    places: dict[str, tuple[int, int]] = field(default_factory=dict)

    def key_of(self, item: MenuItem | None) -> str | None:
        return None if item is None else self.keys.get(id(item))


def fill(menu: SubMenu, top: Iterable[tuple[str, str]], pages: tuple[CodePage, ...] = CODEPAGES,
         command: Callable[[str], Any] | None = None) -> Filled:
    """*top* (``(key, caption)``) into *menu*, a line, then *pages* a submenu
    a group.  Each item asks for ``command(key)`` when *command* is given."""
    filled = Filled()
    groups = grouped(pages)
    group_keys = {_hotkey(GROUPS[group]()) for group, _ in groups}
    top = list(top)
    for (key, _), caption in zip(top, marked([caption for _, caption in top], group_keys)):
        _add(menu, key, caption, command, filled, len(menu.entries()), -1)
    if groups:
        menu.add_line()
    for group, members in groups:
        index = len(menu.entries())
        sub = menu.add_submenu("")
        sub.text = bind(lambda _o, text=GROUPS[group]: text(), yielding=True)
        for at, (page, caption) in enumerate(zip(members, marked([page.caption for page in members]))):
            _add(sub, page.key, caption, command, filled, index, at)
    return filled


def _add(menu: SubMenu, key: str, caption: str, command: Callable[[str], Any] | None,
         filled: Filled, index: int, at: int) -> None:
    item = menu.add_item(caption, command(key) if command is not None else None)
    filled.keys[id(item)] = key
    filled.places[key] = (index, at)
