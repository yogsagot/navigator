"""The keys, as the user has them: ``keybindings.ini`` beside ``navigator.ini``.

Every key Navigator binds is in a key table, a class's ``keys`` (navkit's
:mod:`navkit.commands`).  This module lists those tables as *sections* --
the application's own, the desktop's, the file manager's, the editor's and
so on -- and reads ``keybindings.ini`` over them through
:func:`navkit.commands.override_keys`, so a key the user moves is moved
wherever it is looked up: the key itself, the key bar and the menus.

**A departure.** DOS Navigator 1.51 had no way to change a key short of
rebuilding it; this is the file and the Options > Configuration > *Key
bindings* dialog that edits it, by request.

**The file.** A section per table, ``[manager]``; a line per command the
table binds, ``copy = f5``, its keys after the ``=`` separated by commas, a
chord's keys by a blank (``block_start = ctrl+k b, ctrl+k ctrl+b``), and
nothing after it for a command with no key.  The command's name is its
class's, in snake case, with what tells its variants apart when a table
binds more than one of a class (``move_left_extend``, ``quick_change_3``):
:func:`entries`.  Only commands a table binds by default have a line, since
a key table is where a command's place is decided -- the editor's commands
mean nothing on a panel.

**Reading.** A line that is missing keeps its default (so a command a newer
Navigator adds arrives bound), and a line that will not do -- an unknown
name, a key that is not one, two commands on one key -- is a warning, as
``navigator.ini``'s are: the line, or for a clash the whole section, keeps
its default.  Written whole on the first start (:func:`seed`) and by the
dialog's OK (:func:`save`); comments written by hand are not kept.

The application's own class is passed in rather than imported, since
``navigator.__main__`` is ``__main__`` when Navigator runs and importing it
by name would make a second ``Navigator``.
"""

from __future__ import annotations

import configparser
import dataclasses
import importlib
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from navkit.commands import (
    Binding,
    KeyTableError,
    check_table,
    command_of,
    default_keys,
    override_keys,
    own_keys,
    parse_key,
    restore_keys,
)
from navml.coder import Coder
from navigator.settings import (
    COMMENT_COLUMN,
    INLINE_COMMENT_PREFIXES,
    config_dir,
    write_atomically,
)

#: The file's name, in :func:`navigator.settings.config_dir`.
FILE_NAME = "keybindings.ini"

#: Each table there is a section for, in the order the dialog lists them:
#: the section's name, its title, and its class as ``module:Class`` -- None
#: for the application's own, which the caller passes.
TABLES: tuple[tuple[str, str, str | None], ...] = (
    ("global", "Global", None),
    ("desktop", "Windows", "navml.widgets.desktop:Desktop"),
    ("manager", "File panels", "navigator.widgets.manager.manager:Manager"),
    ("tree_window", "Tree window", "navigator.widgets.tree.tree_window:TreeWindow"),
    ("tree_view", "Trees", "navml.widgets.dialog.tree_view:TreeView"),
    ("editor", "Editor", "navigator.widgets.editor.file_editor:FileEditor"),
    ("edit_window", "Editor window", "navigator.widgets.editor.edit_window:EditWindow"),
    ("viewer", "Viewer", "navigator.widgets.viewer.file_window:FileWindow"),
    ("db_viewer", "Database viewer", "navigator.widgets.viewer.db_window:DBWindow"),
    ("dialog", "Dialogs", "navml.widgets.dialog.dialog:Dialog"),
    ("copy_dialog", "Copy dialog", "navigator.widgets.file_ops.copy_dialog:CopyDialog"),
    ("link_dialog", "Link dialog", "navigator.widgets.file_ops.link_dialog:LinkDialog"),
    (
        "uu_encode_dialog",
        "UU encode dialog",
        "navigator.widgets.file_ops.uu_encode_dialog:UUEncodeDialog",
    ),
    (
        "uu_decode_dialog",
        "UU decode dialog",
        "navigator.widgets.file_ops.uu_decode_dialog:UUDecodeDialog",
    ),
    ("calculator", "Calculator", "navigator.widgets.shell.calculator_window:CalculatorWindow"),
    ("game", "Game", "navigator.widgets.game.game_window:GameWindow"),
)

#: What a section's keys are, by command name: ``{"copy": ("f5",)}``.
Assignment = dict[str, tuple[str, ...]]


@dataclass(frozen=True)
class Entry:
    """One command a table binds: its name in the file, its title in the
    dialog, the binding a key runs, and the keys it has by default."""

    name: str
    title: str
    binding: Binding
    defaults: tuple[str, ...]


@dataclass(frozen=True)
class Section:
    """One key table: its name in the file, its title, its class, and the
    class whose keys it is laid over -- the first one in the MRO that is not
    a half of this one (a component's markup and hand-written halves share a
    name), so the section is everything the component itself binds."""

    name: str
    title: str
    cls: type

    @cached_property
    def base(self) -> type:
        return next(k for k in self.cls.__mro__[1:] if k.__name__ != self.cls.__name__)

    @cached_property
    def entries(self) -> tuple[Entry, ...]:
        return entries(default_keys(self.cls, self.base))

    def entry(self, name: str) -> Entry | None:
        return next((entry for entry in self.entries if entry.name == name), None)

    def defaults(self) -> Assignment:
        """Each command's keys as the code binds them."""
        return {entry.name: entry.defaults for entry in self.entries}

    def current(self) -> Assignment:
        """Each command's keys as they are bound now."""
        keys: dict[str, list[str]] = {entry.name: [] for entry in self.entries}
        names = {command_of(entry.binding): entry.name for entry in self.entries}
        for key, binding in own_keys(self.cls, self.base).items():
            name = names.get(command_of(binding))
            if name is not None:
                keys[name].append(key)
        return {name: tuple(found) for name, found in keys.items()}

    def table(self, assignment: Mapping[str, Iterable[str]]) -> dict[str, Binding]:
        """The key table *assignment* makes, checked as a class's is
        (``KeyTableError`` for a key bound twice or a chord's start bound
        alone)."""
        table: dict[str, Binding] = {}
        for entry in self.entries:
            for key in assignment.get(entry.name, entry.defaults):
                if key in table:
                    other = next(e for e in self.entries if e.binding is table[key])
                    raise KeyTableError(
                        f"{key!r} is bound to both {other.name} and {entry.name}"
                    )
                table[key] = entry.binding
        try:
            return check_table(self.name, table)
        except KeyTableError as error:
            text = str(error).removeprefix(f"{self.name}.keys ")
            raise KeyTableError(text[:1].upper() + text[1:]) from None

    def apply(self, assignment: Mapping[str, Iterable[str]]) -> None:
        """Bind *assignment*'s keys; the defaults again restore the code's table."""
        table = self.table(assignment)
        if table == self.table(self.defaults()):
            restore_keys(self.cls)
        else:
            override_keys(self.cls, table, self.base)


def sections(app_class: type) -> list[Section]:
    """Every section, the application's own as *app_class*'s table."""
    found = []
    for name, title, where in TABLES:
        if where is None:
            cls = app_class
        else:
            module, _, attribute = where.partition(":")
            cls = getattr(importlib.import_module(module), attribute)
        found.append(Section(name, title, cls))
    return found


# -- names -----------------------------------------------------------------------


def _snake(name: str) -> str:
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", "_", name).lower()


def _suffix(value: object, field: str) -> str:
    """What a field's value adds to a variant's name: a set flag its field's
    name, a number or a word itself, and nothing for an unset one."""
    if value is True:
        return f"_{field}"
    if value is False or value is None:
        return ""
    text = str(value).replace("-", "minus_")
    return "_" + re.sub(r"\W+", "_", text).strip("_").lower()


def entries(table: Mapping[str, Binding]) -> tuple[Entry, ...]:
    """*table*'s commands, one entry each, in the order the table first
    names them, every key that asks for one gathered under it.

    Two bindings are one command when they make equal commands, so
    ``StoreQuickDir(slot=1)`` under two keys is one entry.  A command's name
    is its class's in snake case; when the table binds the class more than
    one way, each variant is told apart by the fields that differ between
    them (``MoveLeft(extend=True)`` is ``move_left_extend``).
    """
    keys: dict[object, list[str]] = {}
    bindings: dict[object, Binding] = {}
    for key, binding in table.items():
        command = command_of(binding)
        keys.setdefault(command, []).append(key)
        bindings.setdefault(command, binding)
    variants: dict[type, list[object]] = {}
    for command in keys:
        variants.setdefault(type(command), []).append(command)
    found = []
    for command, bound in keys.items():
        cls = type(command)
        name = _snake(cls.__name__)
        same = variants[cls]
        if len(same) > 1 and dataclasses.is_dataclass(command):
            for field in dataclasses.fields(command):
                if len({repr(getattr(other, field.name)) for other in same}) > 1:
                    name += _suffix(getattr(command, field.name), field.name)
        title = name.replace("_", " ").capitalize()
        found.append(Entry(name, title, bindings[command], tuple(bound)))
    return tuple(found)


# -- the file ----------------------------------------------------------------------


def path() -> Path:
    """Where the file lives: beside ``navigator.ini``."""
    return config_dir() / FILE_NAME


def format_keys(keys: Iterable[str]) -> str:
    """*keys* as a line of the file writes them.  A key that would start
    with a comment character after a blank is joined without one."""
    text = ""
    for key in keys:
        if text:
            text += "," if key[0] in INLINE_COMMENT_PREFIXES else ", "
        text += key
    return text


def parse_keys(text: str) -> tuple[str, ...]:
    """A line's keys, each in its canonical spelling; ``ValueError`` for one
    that is not a key."""
    return tuple(parse_key(part) for part in text.split(",") if part.strip())


def render(found: Iterable[Section], assignments: Mapping[str, Assignment]) -> str:
    """The whole file: every section, every command, *assignments*' keys or
    the defaults -- a line that is not its default saying what that is."""
    coder = Coder("ini")
    coder.comment(0, "Navigator key bindings.")
    coder.comment(0, "One line per command: its keys after the '=', separated by commas, a chord's")
    coder.comment(0, "keys by a blank (ctrl+k b); nothing after the '=' leaves it without a key.")
    coder.comment(0, "Modifiers are ctrl, alt and shift. Rewritten by Options > Configuration >")
    coder.comment(0, "Key bindings, which keeps the values but not comments written here.")
    for section in found:
        assignment = assignments.get(section.name, {})
        coder.new_line()
        coder.add(0, f"[{section.name}]")
        coder.comment(0, section.title)
        for entry in section.entries:
            keys = assignment.get(entry.name, entry.defaults)
            option = f"{entry.name} = {format_keys(keys)}".rstrip()
            if tuple(keys) == entry.defaults:
                coder.add(0, option)
                continue
            padding = max(COMMENT_COLUMN - len(option), 2)
            default = format_keys(entry.defaults) or "no key"
            coder.add(0, f"{option}{' ' * padding}# default: {default}")
    return coder.render()


def read(file: Path, found: Iterable[Section]) -> tuple[dict[str, Assignment], list[str]]:
    """What *file* binds, section by section, and a warning per line that
    will not do.  ``OSError`` or ``configparser.Error`` for a file that
    cannot be read at all."""
    parser = configparser.ConfigParser(
        interpolation=None, inline_comment_prefixes=INLINE_COMMENT_PREFIXES
    )
    with open(file, encoding="utf-8") as stream:
        parser.read_file(stream)
    by_name = {section.name: section for section in found}
    assignments: dict[str, Assignment] = {}
    warnings: list[str] = []
    for name in parser.sections():
        section = by_name.get(name)
        if section is None:
            warnings.append(f"{file}: [{name}]: no such section")
            continue
        assignment: Assignment = {}
        for option, text in parser.items(name):
            entry = section.entry(option)
            if entry is None:
                warnings.append(f"{file}: [{name}] {option}: no such command")
                continue
            try:
                assignment[option] = parse_keys(text)
            except ValueError as error:
                warnings.append(f"{file}: [{name}] {option}: {error}; using the default")
        try:
            section.table(assignment)
        except KeyTableError as error:
            warnings.append(f"{file}: [{name}]: {error}; using the defaults")
            continue
        assignments[name] = assignment
    return assignments, warnings


def apply(found: Iterable[Section], assignments: Mapping[str, Assignment]) -> None:
    """Bind every section as *assignments* say, the rest by default."""
    for section in found:
        section.apply(assignments.get(section.name, {}))


def load(app_class: type, file: Path | None = None) -> list[str]:
    """Read the file and bind its keys; the warnings, one per line that
    will not do.  A missing file binds the defaults, and one that cannot be
    read at all is a warning and the defaults too."""
    file = file or path()
    found = sections(app_class)
    try:
        assignments, warnings = read(file, found)
    except FileNotFoundError:
        assignments, warnings = {}, []
    except (OSError, configparser.Error) as error:
        assignments, warnings = {}, [f"{file}: {error}"]
    apply(found, assignments)
    return warnings


def seed(app_class: type, file: Path | None = None) -> bool:
    """Write the file with every default if it is not there.

    True when it was written, False when it was there already; ``OSError``
    when it could not be.  Never overwrites: the file is created exclusively.
    """
    file = file or path()
    file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with file.open("x", encoding="utf-8") as stream:
            stream.write(render(sections(app_class), {}))
    except FileExistsError:
        return False
    return True


def write(found: Iterable[Section], assignments: Mapping[str, Assignment],
          file: Path | None = None) -> Path:
    """The whole file written with *assignments*; ``OSError`` if it cannot be.

    Touches the disk alone, so a caller on the loop runs it on a thread after
    binding the keys with :func:`apply` -- a file that cannot be written
    then still leaves the session with what was asked for.
    """
    file = file or path()
    write_atomically(file, render(found, assignments))
    return file
