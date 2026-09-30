"""Commands, and the key tables that bind keys to them.

A **command** is something the user can ask for -- *make a directory*, *close
this window*, *quit* -- named apart from any key that asks for it, so that a
key, a key bar button and a menu item can all ask for the same thing, and grey
out together when it cannot be done.  Turbo Vision's ``cmXXX`` constants are
the model; what is not taken from it is the global command *set*, because
whether a command can run here is a question the widget that would run it can
answer, and a set somebody has to keep in step cannot.

**A command is an event.**  ``class MakeDirectory(Command)`` is delivered to
``on_make_directory`` by the rule every event already follows, travels by
:meth:`navkit.widget.Widget.emit`, and is held to ``async def`` by the check
every handler already gets.  It starts where the keyboard is -- the focused
widget -- and walks up to the application, which is Turbo Vision's
``evCommand`` routing: the command goes to whoever holds the state it acts on,
wherever the key that asked for it was bound.

**A key table is a class attribute**, ``keys = {"f7": MakeDirectory}``, merged
down the MRO the way ``emits`` is -- except that two tables naming one key are
two answers to one question, so the subclass's wins.  A value is a command
class, instantiated with no arguments, or an instance, which is how one command
carries a field: ``"alt+x": Quit(desktop=True)``.

**A command is enabled** if some widget on the way from the focus to the
application has its handler, and the nearest such widget does not veto it
through :meth:`~navkit.widget.Widget.enables`.  A disabled command's key is not
consumed: it carries on to the next table and to ``on_key``, the way a key
nobody bound would.  The check reads reactive state, so a key bar asking it
while it paints repaints when the answer changes.

``navkit/DESIGN.md``, *Commands and key tables*, records why each part went the
way it did.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from navkit.events import Event, _normalize

if TYPE_CHECKING:
    from navkit.application import Application
    from navkit.widget import Widget


@dataclass(frozen=True, slots=True)
class Command(Event):
    """Something the user can ask for, whatever asked.

    Subclass it once per command.  A command with no fields need not be a
    dataclass; one that carries a field -- which panel, which drive -- has to
    be, as every event with fields is.
    """

    #: What a key bar or a menu shows for this command.  Empty for a command
    #: nothing displays.
    title: ClassVar[str] = ""


#: What a key table maps a key to: a command class, or an instance of one.
Binding = type[Command] | Command


class KeyTableError(TypeError):
    """A key table that cannot mean anything, refused when its class is made."""


#: The modifiers a key spec may carry, in the order a canonical spec writes them.
MODIFIERS = ("ctrl", "alt", "shift")


def parse_key(spec: str) -> str:
    """*spec* in its canonical spelling, or :class:`ValueError` saying why not.

    ``"Ctrl+Shift+F6"`` is ``"ctrl+shift+f6"``, which is what
    :attr:`KeyEvent.name` reports, so a table keyed by this is looked up
    directly.  Refused: an empty spec, a space inside one, and a modifier
    navkit does not know -- ``"cmd+s"`` would never match a key and would
    otherwise say so only by never working -- and a modifier with no key after
    it, ``"ctrl+"``, which would otherwise be read as a key called ``ctrl``.
    """
    if not isinstance(spec, str) or not spec.strip() or any(c.isspace() for c in spec.strip()):
        raise ValueError(f"{spec!r} is not a key")
    if any(not part for part in spec.strip().split("+")):
        raise ValueError(f"{spec!r} is not a key: it has an empty part")
    normal = _normalize(spec)
    *mods, key = normal.split("+")
    unknown = [m for m in mods if m not in MODIFIERS]
    if unknown or key in MODIFIERS:
        raise ValueError(
            f"{spec!r} is not a key: modifiers are "
            f"{', '.join(MODIFIERS)}, joined to the key with '+'"
        )
    return normal


def layer_key(modifiers: Iterable[str], key: str) -> str:
    """*key* with *modifiers* held, in the canonical spelling.

    ``layer_key({"shift", "ctrl"}, "f6")`` is ``"ctrl+shift+f6"`` -- what a
    key table is keyed by, so a key bar showing the row for the modifiers held
    looks its keys up with this rather than spelling one by hand.
    """
    return parse_key("+".join([*modifiers, key]))


def command_of(binding: Binding) -> Command:
    """The command *binding* stands for, as an instance."""
    return binding() if isinstance(binding, type) else binding


def check_keys(cls: type) -> None:
    """Refuse a ``keys`` table that is not key specs mapped to commands.

    Called when the class is created, which is the earliest a typo can be
    reported and the only time it can be reported without the key being
    pressed: a table is read only when its key arrives.  A spec is also
    refused when it names a key twice under two spellings -- ``"Ctrl+R"`` and
    ``"ctrl+r"`` -- because one of the two would be lost without a word.
    """
    table = vars(cls).get("keys")
    if table is None:
        return
    if not isinstance(table, Mapping):
        raise KeyTableError(
            f"{cls.__name__}.keys must be a mapping of key to command, "
            f"not {type(table).__name__}"
        )
    seen: dict[str, str] = {}
    for spec, binding in table.items():
        try:
            normal = parse_key(spec)
        except ValueError as error:
            raise KeyTableError(f"{cls.__name__}.keys: {error}") from None
        if normal in seen:
            raise KeyTableError(
                f"{cls.__name__}.keys binds {normal!r} twice, as "
                f"{seen[normal]!r} and {spec!r}"
            )
        seen[normal] = spec
        is_class = isinstance(binding, type) and issubclass(binding, Command)
        if not is_class and not isinstance(binding, Command):
            raise KeyTableError(
                f"{cls.__name__}.keys[{spec!r}] is {binding!r}, which is not "
                f"a Command class or instance"
            )


def key_table(cls: type) -> dict[str, Binding]:
    """Every key *cls* binds, with a subclass's binding winning over its base's.

    Keyed by the canonical spelling, so a lookup by :attr:`KeyEvent.name`
    finds a key however the table spelled it.
    """
    merged: dict[str, Binding] = {}
    for klass in reversed(cls.__mro__):
        for spec, binding in vars(klass).get("keys", {}).items():
            merged[_normalize(spec)] = binding
    return merged


# -- where a command goes -------------------------------------------------------


def origin(app: Application, start: Widget | None = None) -> Widget | None:
    """The widget a command starts from: the one holding the keyboard.

    Asked the way :meth:`~navkit.widget.Widget.dispatch_key` asks it -- the
    focus path inside the modal, or inside the root -- so a command never
    starts somewhere a key could not have reached.  With nothing holding the
    keyboard it starts at the modal or the root itself.

    *start* overrides all of that with a widget of the caller's choosing.  A
    menu is the case it is for: while one is open it holds the input, so the
    question it asks -- *could Mkdir run?* -- is about the focus behind it.
    """
    if start is not None:
        return start
    scope = app.modal or app.root
    if scope is None:
        return None
    path = scope._focus_path()
    return path[0] if path else scope


def chain(app: Application, start: Widget | None = None) -> Iterable[Any]:
    """The origin, its ancestors, then the application: where a command goes."""
    widget = origin(app, start)
    while widget is not None:
        yield widget
        widget = widget.parent
    yield app


def target(app: Application, command: Command, start: Widget | None = None) -> Any:
    """Whoever would run *command* now, or None if it is disabled.

    The nearest object on :func:`chain` with a handler decides: it runs the
    command unless its ``enables`` says no, and a no from it is final.  Asking
    further out would let a distant handler answer for a command the nearer
    one has just declared impossible here.
    """
    for candidate in chain(app, start):
        if getattr(candidate, command.handler, None) is not None:
            return candidate if candidate.enables(command) else None
    return None


def enabled(
    app: Application, binding: Binding, start: Widget | None = None
) -> bool:
    """Whether *binding*'s command would run if it were asked for now."""
    return target(app, command_of(binding), start) is not None


async def run(
    app: Application, binding: Binding, start: Widget | None = None
) -> bool:
    """Ask for *binding*'s command.  False if disabled or nobody claimed it.

    Emitted from :func:`origin`, so it walks the same chain :func:`target`
    looked along; a handler returning False passes it outward as with any
    event.
    """
    command = command_of(binding)
    if target(app, command, start) is None:
        return False
    first = origin(app, start)
    if first is not None:
        return await first.emit(command)
    # No tree at all: the application is the whole chain.
    from navkit.widget import _call

    return await _call(app, command, getattr(app, command.handler))


def bindings(app: Application, start: Widget | None = None) -> dict[str, Command]:
    """Every key that asks for a command right now, and the command it asks for.

    What a key bar shows.  The tables along :func:`chain` from the outside in,
    so the nearest binding of a key wins -- and the application's own table
    last of all, since it is consulted before any widget's and so wins every
    tie.  **Ordered nearest first**, each table in its own declaration order
    and the application's after them all, which is the order a key bar shows
    a row of letters in -- the focused window's own before the desktop's.
    While a modal is up the application's table is not consulted, and
    is not shown -- unless *start* names the widget to ask from, which is a
    caller asking about the focus behind the modal rather than inside it.
    """
    tables = [key_table(type(widget)) for widget in chain(app, start)][:-1]
    found: dict[str, Command] = {}
    for table in tables:
        for key, binding in table.items():
            if key not in found:
                found[key] = command_of(binding)
    if app.modal is None or start is not None:
        found.update(
            {key: command_of(b) for key, b in key_table(type(app)).items()}
        )
    return found


#: How :func:`key_label` spells the keys whose names are not their caption.
_KEY_LABELS = {
    "pageup": "PgUp",
    "pagedown": "PgDn",
    "delete": "Del",
    "insert": "Ins",
    "backspace": "BkSp",
    "escape": "Esc",
    "enter": "Enter",
    "tab": "Tab",
    "space": "Space",
    "plus": "+",
    "kp_plus": 'Gray "+"',
    "kp_minus": 'Gray "-"',
    "kp_multiply": 'Gray "*"',
    "kp_divide": 'Gray "/"',
    "home": "Home",
    "end": "End",
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
}


def key_label(spec: str) -> str:
    """A key as a menu or a status line shows it: ``"ctrl+f5"`` is ``Ctrl-F5``.

    Turbo Vision's spelling, which DOS Navigator's menus use throughout --
    modifiers capitalised and joined with a hyphen, function keys and letters
    upper case.
    """
    *mods, key = parse_key(spec).split("+")
    name = _KEY_LABELS.get(key, key.upper() if len(key) <= 3 else key.title())
    return "-".join([*(m.title() for m in mods), name])


def key_for(
    app: Application, binding: Binding, start: Widget | None = None
) -> str | None:
    """The key that asks for *binding*'s command right now, or None.

    What a menu item shows beside its caption: read off the same tables a key
    press is, so the caption cannot claim a key that does something else.
    """
    command = command_of(binding)
    for key, bound in bindings(app, start).items():
        if bound == command:
            return key
    return None
