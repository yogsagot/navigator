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


def origin(app: Application) -> Widget | None:
    """The widget a command starts from: the one holding the keyboard.

    Asked the way :meth:`~navkit.widget.Widget.dispatch_key` asks it -- the
    focus path inside the modal, or inside the root -- so a command never
    starts somewhere a key could not have reached.  With nothing holding the
    keyboard it starts at the modal or the root itself.
    """
    scope = app.modal or app.root
    if scope is None:
        return None
    path = scope._focus_path()
    return path[0] if path else scope


def chain(app: Application) -> Iterable[Any]:
    """The origin, its ancestors, then the application: where a command goes."""
    widget = origin(app)
    while widget is not None:
        yield widget
        widget = widget.parent
    yield app


def target(app: Application, command: Command) -> Any:
    """Whoever would run *command* now, or None if it is disabled.

    The nearest object on :func:`chain` with a handler decides: it runs the
    command unless its ``enables`` says no, and a no from it is final.  Asking
    further out would let a distant handler answer for a command the nearer
    one has just declared impossible here.
    """
    for candidate in chain(app):
        if getattr(candidate, command.handler, None) is not None:
            return candidate if candidate.enables(command) else None
    return None


def enabled(app: Application, binding: Binding) -> bool:
    """Whether *binding*'s command would run if it were asked for now."""
    return target(app, command_of(binding)) is not None


async def run(app: Application, binding: Binding) -> bool:
    """Ask for *binding*'s command.  False if disabled or nobody claimed it.

    Emitted from :func:`origin`, so it walks the same chain :func:`target`
    looked along; a handler returning False passes it outward as with any
    event.
    """
    command = command_of(binding)
    if target(app, command) is None:
        return False
    start = origin(app)
    if start is not None:
        return await start.emit(command)
    # No tree at all: the application is the whole chain.
    from navkit.widget import _call

    return await _call(app, command, getattr(app, command.handler))


def bindings(app: Application) -> dict[str, Command]:
    """Every key that asks for a command right now, and the command it asks for.

    What a key bar shows.  The tables along :func:`chain` from the outside in,
    so the nearest binding of a key wins -- and the application's own table
    last of all, since it is consulted before any widget's and so wins every
    tie.  While a modal is up the application's table is not consulted, and
    is not shown.
    """
    tables = [key_table(type(widget)) for widget in chain(app)][:-1]
    found: dict[str, Command] = {}
    for table in reversed(tables):
        found.update({key: command_of(b) for key, b in table.items()})
    if app.modal is None:
        found.update(
            {key: command_of(b) for key, b in key_table(type(app)).items()}
        )
    return found
