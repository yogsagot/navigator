## Commands and key tables

A key used to be an `if event.matches(...)` chain in whichever `on_key` it reached. That cannot answer the questions
a key bar and a menu ask, which are *what does F5 do here* and *can it be done now*. Turbo Vision answers them with
commands: `cmCopy` is what the user asked for, a status line or a menu maps a key to it, and a view that cannot copy
disables it. `navkit/commands.py` is that idea, fitted to what navkit already has. Textual's `BINDINGS` and
`check_action` answer the same questions.

### A command is an event

`class MakeDirectory(Command)` is delivered to `on_make_directory` by the rule every event follows, travels by
`Widget.emit`, and is held to `async def` by the check every handler gets. No second dispatch mechanism, no action
strings and no registry. A command that carries a field is a dataclass, as every event with fields is:
`Quit(desktop=True)`.

**It starts at the focus and walks up**, whoever bound the key. `commands.origin()` is the head of the focus path, in
the modal or the root, or the modal or root itself when nothing holds the keyboard. The key can be bound on a
container or on the application, while the state the command acts on is usually nearer the focus. Turbo Vision
routes `evCommand` the same way. `Application.run_command(binding)` is the same entry point for a key bar button or a
menu item, which is why the key bar can be clicked.

### A key table is a class attribute

`keys = {"f7": MakeDirectory, "alt+x": Quit(desktop=True)}`. A value is a command class, instantiated with no
arguments, or an instance.

- **Merged down the MRO, the subclass winning** (`commands.key_table`). This is where it parts from `emits`, which
  unions: two tables naming one key are two answers to one question, and the derived class is the one asked.
- **Checked when the class is made** (`commands.check_keys`, from `__init_subclass__` beside `check_handlers`). It
  checks that each spec is a key, that each modifier is one navkit knows, that no key appears under two spellings,
  and that each value is a command. A table is otherwise read only when its key arrives, so a typo would show up
  only as a key that never works.
- **Consulted at each step of the focus path, before that widget's `on_key`.** So a table is a declarative
  `on_key`, and a widget nearer the keyboard still has first refusal. An input line keeps Enter from its dialog's
  `Default`.
- **`Application.keys` runs where `Application.on_key` runs**, before the tree, and is stood aside from while a modal
  is up. That rule used to be written by hand at the top of every application `on_key`, and forgetting it let F10
  quit out of a dialog.

### Two keys a table could not name, until it could

**A bare Space is named `space`, and a bare `+` is named `plus`.** Their `key` is still `" "` and `"+"` and their
`char` what they type, so everything that types reads them as before; only `KeyEvent.name` changed, and
`events._KEY_NAMES` is the whole list. `space` is the spelling Ctrl+Space already had. A spec may not contain a
blank, and `+` is the separator -- `"ctrl++"` parses as nothing -- so before this no table could bind either key.
DOS Navigator's Space tags a file whenever the command line is empty, and the plain `+` stands in for Gray `+` on
terminals that cannot tell them apart (below).

**The keypad's four operators are keys of their own**: `kp_plus`, `kp_minus`, `kp_multiply`, `kp_divide`, each keeping
its `char`, so a key nobody binds still types `+`. Every other keypad key is folded into the key it duplicates, as
before. DOS Navigator's Gray `+`, `-` and `*` are the reason, and a key that only differs from the `+` above the
letters by where it sits needs the terminal's help to be told apart:

- The kitty protocol already reports the keypad by its own codes (57410--57413), which used to be folded away.
- A legacy terminal sends a plain `+` -- **unless the keypad is in application mode** (DECKPAM, `ESC =`), when xterm,
  VTE and the Linux console send `SS3 k`/`m`/`j`/`o` instead. So `Terminal` now sets it (`TerminalInfo.keypad`, off
  only for a plain terminal) and resets it (DECKPNM, `ESC >`). In that mode the digits, `.`, `,`, `=` and keypad
  Enter arrive as `SS3` too, and are decoded back to what they type -- which is what makes turning it on safe.
- A child program is sent the operator's character, never the `SS3` form: its own keypad mode is its emulated
  terminal's business, and a character is right in either.
- **Not every terminal honours the mode, and this was found by running them.** Ghostty (kitty protocol) reports the
  keypad; xfce4-terminal (VTE) and PyCharm's JediTerm sent Gray `+` as a bare `+` with DECKPAM set. So an application
  wanting the Gray keys everywhere has to bind the plain characters as well, as Navigator's `Manager` does.
  `tools/keyprobe.py` sets the keypad mode too, so it shows what a given terminal really sends.

### Enabled is decided by the nearest handler

A command is enabled when some object on the chain from the origin to the application has its handler, and **the
nearest such object** does not veto it through `enables(command)`. Its no is final: letting a handler further out
answer would run a command the nearer one has just declared impossible here. A command nobody handles is disabled,
which is what lets a key bar show DOS Navigator's ten captions before the file operations exist, greyed.

**A disabled command does not consume its key.** It carries on to the next table and to `on_key`, exactly as an
unbound key would. So while the console holds the keyboard, F1 reaches the child program: Help is bound by the
application but handled by nobody.

**`enables` reads reactive state, and so does its caller.** `Application.command_enabled()` walks the focus path,
which reads `Application.focused`, and asks `enables`, which reads what it likes. Called from a `render()` or a
`computed`, the answer is tracked, so a key bar greys and un-greys itself with no one telling it. Whether a handler
*exists* is not reactive, and does not need to be, since classes do not grow handlers at run time.

**Whether a command is *on* is asked the same way.** `checks(command)` returns True, False, or None for a command that
toggles nothing, and it is asked of the very object `enables` is (`commands.checked`,
`Application.command_checked`), so a toggle's state lives where the state does -- Navigator's Ctrl+H asks the active
panel's `show_hidden` -- and a menu ticks the entry without holding a copy that could disagree. A disabled command is
neither on nor off.

### What is not here

- **No global command set.** Turbo Vision's `disableCommands` is state somebody has to keep in step with the views.
  Asking the view that would run the command is the same answer, and it cannot go stale.
- **The modifier-held key bar is the kitty protocol's, and nobody else's.** DOS Navigator swapped the whole row while
  Alt, Ctrl or Shift was held. A legacy terminal reports no bare modifier and no release, so it has no *held* to see.
  See *The held modifier: the kitty keyboard protocol* below.
- **Keys whose meaning is computed stay in `on_key`.** Alt+letter in a dialog depends on the captions of whatever
  controls it holds, and a table is fixed when its class is made. `Modal.on_key` still walks the shortcuts.

