"""What the command palette answers: the command chosen, or None.

**What is listed** (:func:`gather`) is asked from *behind*, the widget that
had the keyboard before the box opened, exactly as a menu box asks: every
item of the main menu that has a command -- the active window's own menus
among them, since ``MenuBar.entries`` splices those in, and none hidden --
then every titled command a key is bound to there whose class no item
holds, so a window's keys with no menu (the editor's chords, the macro
slots) are found too.  Each keeps
its key (the menu's own caption, live), whether it would run and why not.
The palette's own command is left out.

**Typing narrows**, wherever the keyboard is in the box: a printable key or
Backspace goes to the line across the top, Up/Down/PgUp/PgDn to the list.
The titles are scored by :func:`navml.fuzzy.score`, each title's menu path
counting a little less, the best first and the menus' order between equals.
Esc empties a line holding something, and the next one closes.

**Enter** on a command that would run closes with it; on a greyed one it
stays, the line under the list already saying why.  The caller runs the
answer from *behind* (``Shell.command_palette``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from navkit import commands
from navkit.commands import Command, command_of
from navkit.events import KeyEvent
from navkit.i18n import tr
from navkit.reactive import effect
from navkit.widget import Widget
from navml import fuzzy
from navml.widgets.dialog.commands import Cancel, Default
from navml.widgets.dialog.control import parse_shortcut
from navml.widgets.dialog.dialog import Dialog
from navml.widgets.menu.menu_box.menu_box import key_caption
from navml.widgets.menu.menu_item import MenuItem
from navml.widgets.menu.sub_menu import SubMenu

#: How much a match in the menu path counts against one in the title.
PATH_DISCOUNT = 3

#: The keys that move the list rather than the line.
_LIST_KEYS = ("up", "down", "pageup", "pagedown")


@dataclass(frozen=True, slots=True)
class Entry:
    """One command the palette offers."""

    command: Command
    #: Its caption, translated, the hotkey marks taken out.
    title: str
    #: Where it is in the menus, ``File > Make directory``; ``""`` if nowhere.
    path: str
    #: Its key as a menu shows it, ``""`` for none.
    key: str
    enabled: bool
    #: Why it would not run, where whoever refuses it says.
    reason: str


@dataclass(frozen=True, slots=True)
class Found:
    """An entry that matched what is typed, and where its letters fell in the title."""

    entry: Entry
    places: tuple[int, ...] = ()


def _caption(node: Any) -> str:
    return parse_shortcut(node.text)[0].rstrip(".…").rstrip()


def _items(container: Any, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], MenuItem]]:
    found: list[tuple[tuple[str, ...], MenuItem]] = []
    for node in container.entries():
        if isinstance(node, SubMenu):
            found.extend(_items(node, (*path, _caption(node))))
        elif isinstance(node, MenuItem) and node.command is not None:
            found.append((path, node))
    return found


def gather(app: Any, behind: Widget | None, menu: Any = None) -> list[Entry]:
    """Every command the palette offers, asked from *behind*: *menu*'s
    items (the main menu, by default) in its order, then the titled
    commands bound to keys there that no item holds."""
    from navigator.widgets.shell.commands import OpenCommandPalette

    if menu is None:
        menu = getattr(getattr(app, "shell", None), "menu", None)
    entries: list[Entry] = []
    seen: list[Command] = []

    def offered(command: Command) -> bool:
        return isinstance(command, OpenCommandPalette) or command in seen

    for path, item in _items(menu) if menu is not None else []:
        command = command_of(item.command)
        if offered(command):
            continue
        seen.append(command)
        enabled = not item.disabled and app.command_enabled(command, behind)
        entries.append(Entry(
            command=command,
            title=parse_shortcut(item.text)[0],
            path=" > ".join(path),
            key=key_caption(item, app, behind),
            enabled=enabled,
            reason="" if enabled else app.command_disabled_reason(command, behind),
        ))
    # A key's variant of a command a menu item offers -- Alt+F6's *Ren*
    # beside File > Rename/Move -- is that item's, under the key bar's short
    # title; the item says it better.
    in_menus = {type(command) for command in seen}
    for key, command in app.bindings(behind).items():
        if not type(command).title or offered(command) or type(command) in in_menus:
            continue
        seen.append(command)
        enabled = app.command_enabled(command, behind)
        entries.append(Entry(
            command=command,
            title=tr(type(command).title),
            path="",
            key=commands.key_label(key),
            enabled=enabled,
            reason="" if enabled else app.command_disabled_reason(command, behind),
        ))
    return entries


def narrow(entries: list[Entry], query: str) -> list[Found]:
    """*entries* that *query* matches, best first, the given order between equals."""
    query = query.strip()
    if not query:
        return [Found(entry) for entry in entries]
    scored: list[tuple[int, int, Found]] = []
    for order, entry in enumerate(entries):
        best = fuzzy.score(query, entry.title)
        places: tuple[int, ...] = ()
        if best is not None:
            places = tuple(fuzzy.spans(query, entry.title))
        if entry.path:
            through = fuzzy.score(query, f"{entry.path} > {entry.title}")
            if through is not None:
                through //= PATH_DISCOUNT
                if best is None or through > best:
                    best = through
        if best is not None:
            scored.append((-best, order, Found(entry, places)))
    scored.sort(key=lambda row: row[:2])
    return [found for _, _, found in scored]


class CommandPalette(Dialog):
    """*Commands*: one of them, chosen by name."""

    def __init__(self, behind: Widget | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        #: Where the keyboard was: what every question is asked from.
        self.behind = behind
        self.entries: list[Entry] = []

    @property
    def buttons_row(self) -> tuple[Any, ...]:
        return ()

    def mounted(self) -> None:
        super().mounted()
        app = self.application
        if app is not None and not self.entries:
            self.entries = gather(app, self.behind)
        effect(self, CommandPalette._follow_filter)
        effect(self, CommandPalette._describe)
        self.filter.focus()

    def _follow_filter(self) -> None:
        found = narrow(self.entries, self.filter.value)
        self.results.items = found
        first = next((at for at, row in enumerate(found) if row.entry.enabled), 0)
        self.results.cursor = first
        self.results.scroll = 0
        self.results.error = None if found else tr("No command matches")

    def _describe(self) -> None:
        """The line under the list: why the command under the cursor cannot
        run, else where it is in the menus."""
        found = self.results.selected
        if found is None:
            self.hint.text = ""
            return
        entry = found.entry
        if not entry.enabled:
            self.hint.text = entry.reason or tr("Not available here")
        else:
            self.hint.text = entry.path

    def take(self) -> bool:
        """Close with the command under the cursor, if it would run."""
        found = self.results.selected
        if found is None or not found.entry.enabled:
            return False
        self.close(found.entry.command)
        return True

    def accept(self) -> Command | None:
        found = self.results.selected
        return found.entry.command if found is not None and found.entry.enabled else None

    def enables(self, command: Command) -> bool:
        """Enter needs no button here: it takes the row under the cursor."""
        if isinstance(command, Default):
            return True
        return super().enables(command)

    async def on_default(self, event: Default) -> bool:
        self.take()
        return True

    async def on_cancel(self, event: Cancel) -> bool:
        """Esc with something typed empties the line, and the next one closes."""
        if self.filter.value:
            self.filter.value = ""
            self.filter.cursor = 0
            self.filter.focus()
            return True
        return await super().on_cancel(event)

    async def on_key(self, event: KeyEvent) -> bool:
        if any(event.matches(name) for name in _LIST_KEYS) and not self.results.focused:
            return await self.results.on_key(event)
        typed = event.is_printable and event.char and not event.ctrl and not event.alt
        if (typed or event.matches("backspace")) and not self.filter.focused:
            self.filter.focus()
            self.filter.anchor = None
            self.filter.cursor = len(self.filter.value)
            return await self.filter.on_key(event)
        return await super().on_key(event)
