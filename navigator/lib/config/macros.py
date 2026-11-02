"""Macros: DOS Navigator's two kinds.

**Key macros** (``DN.PAS``'s ``KeyMacroses``, ``TKeyMacros``): every key typed,
anywhere, recorded into one of nine slots and played back as if typed again.
DN recorded with Alt+Shift+N and played with Alt+N; here ``Ctrl+J R N`` and
``Ctrl+J N`` (a departure: the file manager's Alt+digits are its quick
directories, and terminals take them).  Recorded through
``Application.input_tap``; kept in the database (``KeyMacro``), where DN kept
them as long as its desktop.

**Editor macros** (``MACRO.PAS``'s ``TEditMacros``): ``MACRO … ENDMACRO``
blocks DN read from ``DN.HGL`` for a file's type, here from ``macros.ini``
beside ``navigator.ini`` -- ``[masks]`` sections, ``[*]`` for every file
(DN's ``DEFAULT``).  Each line is DN's:

- ``PRINT 'text', n`` -- the text typed, *n* times (``''`` a quote, ``^M``
  a control character, ``#13`` a code);
- ``GOTOXY x, y``, ``GOTOX x``, ``GOTOY y`` -- the cursor to a column and a
  line, counted from 0 as DN's ``ScrollTo`` did;
- ``MARK n``, ``GOTO n`` -- set marker *n*, or go to it (``MarkPos``);
- a command and a repeat count -- ``WordLeft, 3``: DN's names (``MakeIDs``),
  or ``keybindings.ini``'s (``word_left``).

DN played them with Ctrl+J 1..9; here those play key macros, and Ctrl+J 0 --
DN's ``cmSelectMacro``, whose body was empty -- offers the file's editor
macros in a box.
"""

from __future__ import annotations

import asyncio
import fnmatch
import json
import re
from dataclasses import dataclass, field
from typing import Any

from navkit.events import KeyEvent, PasteEvent

#: The slots: Ctrl+J R 1..9 and Ctrl+J 1..9.
SLOTS = range(1, 10)
#: How long a played key waits for what it started, at most, in seconds.
SETTLE_LIMIT = 2.0


# -- recorded keys -------------------------------------------------------------------


def encode(events: list[Any]) -> str:
    """*events* -- keys and pastes -- as the JSON a ``KeyMacro`` keeps."""
    out = []
    for event in events:
        if isinstance(event, PasteEvent):
            out.append({"paste": event.text})
        else:
            item = {"key": event.key}
            if event.char is not None:
                item["char"] = event.char
            for name in ("ctrl", "alt", "shift", "super_"):
                if getattr(event, name):
                    item[name] = True
            out.append(item)
    return json.dumps(out, ensure_ascii=False)


def decode(text: str) -> list[Any]:
    """:func:`encode` the other way; what does not read is left out."""
    try:
        items = json.loads(text or "[]")
    except ValueError:
        return []
    events: list[Any] = []
    for item in items if isinstance(items, list) else ():
        if not isinstance(item, dict):
            continue
        if "paste" in item:
            events.append(PasteEvent(str(item["paste"])))
        elif isinstance(item.get("key"), str):
            events.append(KeyEvent(item["key"], item.get("char"), ctrl=bool(item.get("ctrl")),
                                   alt=bool(item.get("alt")), shift=bool(item.get("shift")),
                                   super_=bool(item.get("super_"))))
    return events


def load(slot: int) -> list[Any]:
    """What slot *slot* holds; nothing if it was never recorded."""
    from navigator.models.key_macro import KeyMacro

    row = KeyMacro.where(slot=slot).first()
    return decode(row.keys) if row is not None else []


def store(slot: int, events: list[Any]) -> None:
    """*events* into slot *slot*, over what it held."""
    from navigator.models.key_macro import KeyMacro

    KeyMacro.upsert(slot=slot, keys=encode(events))


def keys_of(text: str) -> list[KeyEvent]:
    """*text* as the keys that type it: DN's ``TMacroString`` sent each
    character as a key press, so ``^M`` is Enter and ``^I`` Tab."""
    keys = []
    for char in text:
        if char in "\r\n":
            keys.append(KeyEvent("enter", "\n"))
        elif char == "\t":
            keys.append(KeyEvent("tab", "\t"))
        elif char == "\x08":
            keys.append(KeyEvent("backspace"))
        elif char == "\x1b":
            keys.append(KeyEvent("escape"))
        elif ord(char) < 0x20:
            keys.append(KeyEvent(chr(ord("a") + ord(char) - 1), ctrl=True))
        else:
            lower = char.lower()
            shift = char != lower and len(lower) == 1
            keys.append(KeyEvent(lower if shift else char, char, shift=shift))
    return keys


class Recorder:
    """The application's macros: the one recording, and the one playing.

    ``start`` sets ``Application.input_tap``; every key and paste is kept
    until ``stop``, which drops the keys of the chord that stopped it --
    however many it has, as rebound -- and stores the rest.  ``play`` posts a slot's keys one at a time, each when
    the application has finished with the last -- so a key that opened a
    dialog has it take the next, as DN's ``GetEvent`` feed did.
    """

    def __init__(self, app: Any) -> None:
        self.app = app
        #: The slot being recorded, or None.
        self.recording: int | None = None
        self.events: list[Any] = []
        #: Whether a macro is being played: another is refused meanwhile,
        #: as DN's ``MacroPlaying`` refused it.
        self.playing = False

    def start(self, slot: int) -> None:
        self.recording = slot
        self.events = []
        self._chord_at = 0
        self.app.input_tap = self._tap

    def _tap(self, event: Any) -> None:
        """Every key and paste, as typed.  A key that comes with no chord
        pending may begin one: where the chord that ends the recording (or
        plays a macro) began, which :meth:`stop` and :meth:`drop_chord` cut."""
        if isinstance(event, KeyEvent) and not self.app.chord:
            self._chord_at = len(self.events)
        self.events.append(event)

    def drop_chord(self) -> None:
        """The keys of the chord just completed taken out of the recording."""
        if self.recording is not None:
            del self.events[self._chord_at:]

    def stop(self) -> int | None:
        """End the recording, the chord that ended it left out, and keep it.
        The slot recorded, or None."""
        slot = self.recording
        if slot is None:
            return None
        if self.app.input_tap == self._tap:
            self.app.input_tap = None
        self.drop_chord()
        events = list(self.events)
        self.recording = None
        self.events = []
        store(slot, events)
        return slot

    async def play(self, events: list[Any]) -> bool:
        """*events* typed again; False if a macro is playing already."""
        if self.playing:
            return False
        self.playing = True
        try:
            for event in events:
                self.app.post_event(event)
                await settle(self.app)
        finally:
            self.playing = False
        return True


async def settle(app: Any) -> None:
    """Until *app* has handled what was posted and what that started has had
    its turn -- a dialog a key opened is up before the next key comes."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + SETTLE_LIMIT
    await asyncio.sleep(0)
    while app.is_running and app.busy and loop.time() < deadline:
        await asyncio.sleep(0.002)
    for _ in range(3):
        await asyncio.sleep(0)


# -- editor macros -------------------------------------------------------------------


@dataclass
class Step:
    """One line of a macro: what it does and its arguments."""

    kind: str  # "print", "goto", "mark", "jump" or "command"
    text: str = ""
    count: int = 1
    x: int | None = None
    y: int | None = None


@dataclass
class EditMacro:
    """``TEditMacros``: a name and its lines."""

    name: str
    steps: list[Step] = field(default_factory=list)


@dataclass
class MacroSection:
    """A ``[masks]`` section: the files it is for, and their macros."""

    masks: list[str]
    macros: list[EditMacro] = field(default_factory=list)

    def matches(self, name: str) -> bool:
        name = name.lower()
        return any(fnmatch.fnmatchcase(name, mask.lower()) for mask in self.masks)


def tokens(text: str) -> list[str]:
    """DN's ``Token``, every one on a line: words and quoted strings, ended by
    a comma or a blank outside quotes; ``''`` in quotes is a quote, ``^X``
    outside them a control character, ``#NN`` a character's code."""
    found: list[str] = []
    current: list[str] | None = None
    quoted = False
    index = 0
    while index < len(text):
        char = text[index]
        if quoted:
            if char == "'":
                if index + 1 < len(text) and text[index + 1] == "'":
                    current.append("'")
                    index += 1
                else:
                    quoted = False
            else:
                current.append(char)
        elif char in ", \t":
            if current is not None:
                found.append("".join(current))
                current = None
        else:
            if current is None:
                current = []
            if char == "'":
                quoted = True
            elif char == "^" and index + 1 < len(text):
                index += 1
                current.append(chr((ord(text[index].upper()) - 64) & 0x7F))
            elif char == "#" and index + 1 < len(text) and text[index + 1].isdigit():
                digits = re.match(r"\d+", text[index + 1:]).group()
                index += len(digits)
                current.append(chr(int(digits) % 0x110000))
            else:
                current.append(char)
        index += 1
    if current is not None:
        found.append("".join(current))
    return found


def _number(text: str, default: int | None = None) -> int | None:
    try:
        return int(text)
    except (TypeError, ValueError):
        return default


def parse_step(line: str) -> Step | None:
    """One macro line as a :class:`Step`, or None if it does not read."""
    words = line.split(None, 1)
    head = words[0].upper() if words else ""
    rest = tokens(words[1]) if len(words) > 1 else []
    if head == "PRINT":
        if not rest:
            return None
        return Step("print", text=rest[0], count=max(1, _number(rest[1] if len(rest) > 1 else "", 1)))
    if head in ("GOTOXY", "GOTOX", "GOTOY"):
        values = [_number(token) for token in rest]
        if not values or None in values:
            return None
        if head == "GOTOXY":
            return Step("goto", x=values[0], y=values[1] if len(values) > 1 else None) if len(values) > 1 else None
        return Step("goto", x=values[0]) if head == "GOTOX" else Step("goto", y=values[0])
    if head in ("MARK", "GOTO"):
        marker = _number(rest[0]) if rest else None
        if marker is None:
            return None
        return Step("mark" if head == "MARK" else "jump", count=max(1, min(marker, 9)))
    every = tokens(line)
    if not every:
        return None
    return Step("command", text=every[0], count=max(1, _number(every[1] if len(every) > 1 else "", 1)))


def parse(text: str) -> tuple[list[MacroSection], list[str]]:
    """``macros.ini``: its sections and their macros, and a note for every
    line that does not read -- left out, as ``keybindings.ini`` leaves one."""
    sections: list[MacroSection] = []
    problems: list[str] = []
    section: MacroSection | None = None
    macro: EditMacro | None = None
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(";") or line.startswith("#!"):
            continue
        if macro is None and line.startswith("[") and line.endswith("]"):
            section = MacroSection([mask.strip() for mask in line[1:-1].split(";") if mask.strip()])
            sections.append(section)
            continue
        upper = line.upper()
        if upper.startswith("MACRO ") or upper == "MACRO":
            if section is None:
                section = MacroSection(["*"])
                sections.append(section)
            name = line[5:].strip() or "0"
            macro = EditMacro(name)
            section.macros.append(macro)
            continue
        if upper == "ENDMACRO":
            macro = None
            continue
        if macro is None:
            problems.append(f"{number}: outside a MACRO block: {line}")
            continue
        step = parse_step(line)
        if step is None:
            problems.append(f"{number}: {line}")
        else:
            macro.steps.append(step)
    return sections, problems


def macros_for(sections: list[MacroSection], name: str) -> list[EditMacro]:
    """The macros for a file called *name*: every section whose masks match,
    in the file's order -- ``[*]`` among them."""
    found: list[EditMacro] = []
    for section in sections:
        if section.matches(name):
            found.extend(macro for macro in section.macros if macro.steps)
    return found


def read() -> list[MacroSection]:
    """``macros.ini``'s sections (``associations.MACROS``, written from its
    template at the first start).  A thread calls it."""
    from navigator.lib.config import associations

    try:
        associations.seed(associations.MACROS)
    except OSError:
        pass
    try:
        text = associations.path_of(associations.MACROS).read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = associations.TEMPLATES[associations.MACROS]
    return parse(text)[0]


# -- command names ---------------------------------------------------------------------

#: DN's ``MakeIDs`` names that are not just ``keybindings.ini``'s spelt in
#: camel case: what each is here.
DN_NAMES = {
    "scrolldn": "scroll_down",
    "delbackchar": "delete_back",
    "delchar": "delete_char",
    "delwordleft": "delete_word_left",
    "delwordright": "delete_word_right",
    "switchins": "switch_insert",
    "pgup": "page_up",
    "pgdn": "page_down",
    "blockprint": "print_block",
    "unindentblock": "unindent_block",
    "tab": "tab_key",
    "home": "line_start",
    "end": "line_end",
    "enter": "new_line",
    "insline": "insert_line",
    "deltoeoln": "delete_to_end",
    "ctrlhome": "text_start",
    "ctrlend": "text_end",
    "upblock": "upcase_block",
    "lowblock": "lowcase_block",
    "capblock": "capitalize_block",
    "contsearch": "cont_search",
}


def snake(name: str) -> str:
    """``WordLeft`` as ``word_left``; ``word_left`` as itself."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).lower()


def resolve(name: str, entries: dict[str, Any]) -> Any:
    """The binding a macro line's command names: from *entries* (the editor
    tables' ``keybindings.ini`` names), through :data:`DN_NAMES`, else an
    editor command class of that name made with no arguments.  None if none."""
    plain = name.strip()
    key = DN_NAMES.get(plain.lower().replace("_", ""), snake(plain))
    if key in entries:
        return entries[key]
    from navigator.widgets.editor import commands

    command = getattr(commands, plain, None)
    from navkit.commands import Command

    if isinstance(command, type) and issubclass(command, Command):
        try:
            return command()
        except TypeError:
            return None
    return None


def editor_entries(app: Any) -> dict[str, Any]:
    """The editor's commands by their ``keybindings.ini`` names: what a
    macro line's command is looked up among."""
    from navigator.lib.config.keybindings import TABLES, sections

    wanted = {"editor", "edit_window"}
    found: dict[str, Any] = {}
    for section in sections(type(app), skip=[name for name, _, _ in TABLES if name not in wanted]):
        if section.name in wanted:
            for entry in section.entries:
                found.setdefault(entry.name, entry.binding)
    return found


async def play_steps(editor: Any, steps: list[Step]) -> list[str]:
    """An editor macro's lines played in *editor*, in order: ``PRINT`` typed
    as keys (DN's ``TMacroString`` sent key presses), a command run as its
    key would run it, ``GOTOXY`` and the markers set straight.  The names of
    commands that are none, which are passed over."""
    from navigator.widgets.editor.commands import GotoMarker

    app = editor.application
    entries = editor_entries(app)
    unknown: list[str] = []
    for step in steps:
        if step.kind == "print":
            for _ in range(step.count):
                for key in keys_of(step.text):
                    app.post_event(key)
                    await settle(app)
        elif step.kind == "command":
            binding = resolve(step.text, entries)
            if binding is None:
                if step.text not in unknown:
                    unknown.append(step.text)
                continue
            for _ in range(step.count):
                await app.run_command(binding, editor)
                await settle(app)
        elif step.kind == "goto":
            editor._go_column(editor.line if step.y is None else step.y, editor.col if step.x is None else step.x)
        elif step.kind == "mark":
            editor.markers[step.count - 1] = (editor.line, editor.col)
        elif step.kind == "jump":
            await app.run_command(GotoMarker(step.count), editor)
            await settle(app)
    return unknown


__all__ = [
    "DN_NAMES",
    "EditMacro",
    "MacroSection",
    "Recorder",
    "Step",
    "decode",
    "encode",
    "keys_of",
    "load",
    "editor_entries",
    "macros_for",
    "play_steps",
    "parse",
    "read",
    "resolve",
    "store",
    "tokens",
]
