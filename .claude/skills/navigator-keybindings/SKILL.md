---
name: navigator-keybindings
description: User key bindings -- navigator/keybindings.py (TABLES, Section, Entry, ini names, render/read/load/seed/apply/write), keybindings.ini beside navigator.ini, navkit's run-time overrides (override_keys, restore_keys, default_keys, own_keys, check_table in navkit/commands.py), Options > Configuration > Key bindings (KeyBindingsSetup, Shell.key_bindings, KeyBindingsDialog with BindingList, KeyCaptureDialog with KeyCatcher). Use when adding a key table, renaming a command a table binds, or changing how keys are rebound.
---

# Key bindings and keybindings.ini

The user can rebind every key that sits in a key table. Keys handled in an `on_key` (list, viewer and panel cursor
movement, typing) are not covered: move one into a table to make it rebindable.

**This is a departure.** DOS Navigator 1.51 had no key editor. It was added by request, and the departure is recorded in
`KeyBindingsSetup`'s docstring and in the module docstring.

## navkit: run-time overrides (`navkit/commands.py`)

- **`override_keys(cls, table, base)`** sets `cls`'s keys to `key_table(base) | table` in place of what the classes
  from `base` (exclusive) to `cls` bind. It replaces, so a key can be taken away as well as added, and both halves of a
  component (the markup half and the hand-written half) count as one table.
  - A subclass with no override of its own still adds its keys on top.
  - A base's override shows through. This is how `CopyDialog` sees a rebound `Dialog`.
- **The other functions:**
  - `restore_keys(cls)` drops one override; `restore_keys()` drops them all.
  - `default_keys(cls, base)` is what the code binds.
  - `own_keys(cls, base)` is what is bound now.
  - `check_table(owner, table)` is `check_keys`' validation with the table passed in, so it works for a table that is
    not a class attribute.
- **No cache.** `key_table()` is read at every key press, menu caption and key-bar paint, so an override is live at
  once.
- `tests/conftest.py`'s autouse `_default_keys` calls `restore_keys()` around every test.

## The model (`navigator/keybindings.py`)

**Sections.** `TABLES` lists `(name, title, "module:Class")` in the dialog's order.
- `global` has None for its class. The caller passes the application class (`Navigator`), because importing
  `navigator.__main__` by name would make a second class.
- `Section.base` is the first class in the MRO whose name differs from the section's class. That skips the
  generated half: `Manager` sits over `Window`, and `CopyDialog` over `Dialog`.

**Adding a key table means adding a row to `TABLES`.** `test_every_section_names_each_command_once` then checks it.

**Entries.** `entries(table)` makes one `Entry` per distinct command, compared by equality. Commands are frozen
dataclasses, so all the keys that ask for one command are gathered under it:
- `store_quick_dir_1 = alt+shift+1, alt+!`
- the WordStar pair, `block_start = ctrl+k b, ctrl+k ctrl+b`

**Names.** A name is the class name in snake case.
- When a table binds a class more than one way, each variant gets suffixes from the fields that differ between them:
  - a True bool adds the field's name;
  - a number or word adds the value, with `-` written `minus_`;
  - False or None adds nothing;
  - fields that are equal in every variant (`by_key=True`) add nothing.
- Examples: `move_left_extend`, `quick_change_3`, `scroll_names_minus_1`.
- **Names are the file's keys.** Renaming a command class, or giving one a new variant, renames its line, and the old
  line becomes an "unknown command" warning.

**Titles.** A title is the name, humanised. A command's `title` is not used, because that is a short key-bar caption
("Dupe").

## The file

- **Location and creation.** It lives at `config_dir()/keybindings.ini`, beside `navigator.ini`. `main()` calls
  `load_keybindings()` after `seed_associations()`. That function:
  1. calls `seed(Navigator)`, which writes every default with `open("x")` and so never overwrites;
  2. calls `load(Navigator)`;
  3. prints warnings as `nav: ...` before the screen is taken.
- **Format.** There is one `[section]` per table, with its title as a comment.
  - A line is `name = key, key`, in canonical spelling. A chord's keys are separated by a blank.
  - An empty value means the command has no key.
  - A line that differs from its default ends with `# default: ...`.
  - A key starting with `#` or `;` is joined with a bare `,` (`format_keys`), because ` #` would start an inline
    comment.
- **Reading** (`read`). Problems are warnings, never errors:
  - a missing line keeps its default;
  - an unknown section or name is a warning;
  - a key that will not parse is a warning, and that line keeps its default;
  - a section that fails `Section.table` (one key on two commands, or a chord whose first key is also bound alone) is a
    warning, and the whole section keeps its defaults;
  - a file that is not ini at all is one warning, and every section uses its defaults.
- **Applying** (`apply` / `Section.apply`). A section equal to its defaults calls `restore_keys`; any other calls
  `override_keys`.
- **Writing** (`write`). The whole file is written through `settings.write_atomically`. It touches the disk only, so
  the caller binds first with `apply` on the loop, then writes on a thread. Comments written by hand are not kept.

## The dialog

- **Opening it.** `KeyBindingsSetup` is under Options > Configuration > *Key bindings...*. Its handler
  `Shell.key_bindings` does three things:
  1. runs `KeyBindingsDialog(sections)`;
  2. on OK, calls `keybindings.apply`;
  3. calls `asyncio.to_thread(keybindings.write, ...)`, showing an *Error* box on `OSError`. The keys stay bound for
     the session.
- **`KeyBindingsDialog`** (`navigator/widgets/setup/key_bindings_dialog/`).
  - **Lists.** *Category* on the left is a ListViewer of section titles. *Commands* is a `BindingList`: title, a `│`
    divider, then keys as `key_label` writes them. A `*` marks a command that is not at its default. The `detail` line
    under the lists shows the full keys and the default.
  - **Pending edits.** Edits live in `assignments` (`{section: {name: keys}}`). Nothing is bound until OK, and Cancel
    drops them.
  - **Buttons.**
    - *Rebind* (the default button) and *Add* open `KeyCaptureDialog`.
    - *Clear* sets `()`.
    - *Default* restores the command's defaults.
    - *Reset* restores every section, after asking.
  - **`bind_key` checks.**
    - Another command in the same section has the key: it asks *"F5 is bound to Copy. Reassign it?"*, and Yes takes the
      key from that command.
    - In any section but `global`, a key the global table binds: it asks, because the application's table is looked at
      first.
    - Last, `_put` validates through `Section.table` and shows *Cannot bind that:* with the reason.
- **`KeyCaptureDialog`** is a small Dialog over a `KeyCatcher` (a `Control`). The catcher has the focus, so its `on_key`
  sees every key before the dialog's own table: Tab, Alt+letter and F10 are captured.
  - Enter accepts and Esc cancels, so those two can be bound only in the file.
  - Two keys make a chord, and a third key starts again.
  - A bare modifier never arrives: it is a `ModifiersEvent`.
  - It answers the canonical spec.

## Tests

- `tests/test_key_overrides.py` covers the navkit layer.
- `tests/test_keybindings.py` covers names, the file and the dialog, driven with `Until` titles: *Key Bindings* for the
  dialog, *Press a key* for the capture box, *Key bindings* for its questions.
  - The refusal box opens in the same batch the capture box closes, so don't wait for *Key Bindings* in between.
