# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

Early. `navkit` has its event loop, terminal layer, screen buffer, reactive attributes, widget base, and a console layer
that runs child programs on a pty it owns; `navigator/__main__.py` is a working shell (menu bar, two live directory
panels, key bar, Ctrl+O console) that exercises them and is already written in the declarative style — its panels bind
their geometry to the desktop and derive their listing from a path rather than being placed and refreshed by hand.
**`navml/` is now a working toolchain end to end.** `navml/_merge.py` joins a component's markup half to its
hand-written half; `navml/parser.py` reads a document into a node graph and `navml/errors.py` carries `MarkupError`,
the one exception both halves raise; and **the code generator is written**, so `navml/widgets/*_nml.py` and `*.pyi`
are generated artefacts rather than stand-ins — `python -m navml build` regenerates them and `--check` reports markup
that no longer matches. The README sketches the rest. `navkit` itself is complete for what it does, the stylesheet and its lookup engine
included, and **the interaction layer a widget library needs is now complete**: focus, signals, the mount/unmount
lifecycle, modal/overlay support and a real cursor. That was the whole of *What the widget library needs first* in
`navkit/DESIGN.md`; its **`Still open` list is a separate one**. Two of its five entries were navkit's own work and
are now answered (`Application.background`, and where the console's key routing belongs); the other three wait for the
widget library by their own argument: which parts and properties the library widgets declare, which glyphs beyond a
box frame they need, and what a full-screen child does.

**The toolchain is proved end to end: `navigator/widgets/manager/manager.nml` is the desktop.** The conversion `navml`
existed to make possible is done, and it is a byte-for-byte proof rather than a plausible one — the commit before it
and the commit after paint the same 3725 bytes on a pty at 80x24, `cmp`-identical. `manager.py` keeps the handlers and
the three seeded values; the tree, the geometry and the `visible` flags are markup.

**The screen is now a desktop of overlapping windows.** The root is `navigator/widgets/shell/` — menu bar, `Console`,
navml's `Desktop` over it, key bar — and `Manager` is a frameless `Window` on that desktop, opened zoomed, which the
user can drag, resize from its corner, zoom with `[↕]`/`[↑]`, close with `[■]`, and bring forward by clicking it.
**The console is the background and is always showing**; Ctrl+O hides the desktop, which is one `visible` binding.
The old framed `Window` is `Modal` — fixed, centred, bound geometry, `modal = True` — and `Dialog` derives from it.
Four rules from building it: **a window's rectangle is state, never bound** (drag, resize and zoom assign it);
**raising is `Widget.raise_child`, a reorder** — `add()` would unmount; **a shadow is `Widget.shadow`**, painted
by `render_tree` into the parent's surface before the widget, after a modal's dim (on for `Window`, `Modal`, `MenuBox`,
`HistoryList`); and **the application's own `on_key` /
`on_mouse_click` must step aside while `app.modal` is set**, because they run before navkit's modal routing (the
application's *key table* does this by itself). navkit
grew `raise_child`/`lower_child`, `Application.capture_mouse` and `Widget.render_after` for it; *Windows: raising,
capturing, painting over* in `navkit/DESIGN.md` and *Windows, the desktop and the modal* in `navml/DESIGN.md` have
the rest.

**The widget library's first tier is written**, and none of it was designed: DOS Navigator's Colors dialog names the
widgets and their states, `tools/palconv.py` had already transcribed all 144 slots into every theme, and the
*Dialogs* group is the specification. Thirteen components — `Control`, `Cluster`, `StaticText`, `Label`, `Button`,
`InputLine`, `CheckBoxes`, `RadioButtons`, `ScrollBar`, `ListViewer`, `Modal`, `Dialog`, `Field` — plus `Spacer`, and
since then `Window` and `Desktop`, which are Turbo Vision's rather than the Colors dialog's, and `Timer`, which paints
nothing and emits `TimerEvent` every `interval` ms — Navigator's `Clock` (`navigator/widgets/clock/`, top-right of the
menu bar, `HH:MM` with a blinking colon, coloured by the Colors dialog's *Timer* slot `[1]`) is built on it.
`navigator/styles/navigator.nss` binds them to the `$dialog-*` variables the eleven themes had been carrying inert,
and **F7 Mkdir is the first dialog wired into the application**, proved on a pty. *The widget library* in
`navml/DESIGN.md` records what each decision cost. **Menus are written** (`navml/widgets/menu/`, slots `[2-7]`):
`MenuBar`, `MenuBox`, and `SubMenu`/`MenuItem`/`MenuLine` blocks that are invisible data widgets. Navigator's menu
is DOS Navigator 1.51's own `dlgMainMenu`, transcribed into `navigator/widgets/main_menu/main_menu.nml`, with every
entry whose feature does not exist greyed. **Every submenu has an id** (`app.shell.menu.file`, `menu.file_view`),
and `MenuBar`/`SubMenu` share `MenuContainer`'s Python API for plugins: `add_item`/`add_submenu`/`add_line` with
`before=`/`after=` anchors (an entry, a caption, or a command), `remove_entry`, `move_entry`, `entry`,
`item_for(command)`, plus reactive `hidden`/`disabled` on every entry. *Menus* in `navml/DESIGN.md` has the geometry and the rules. **History is
written** (`[53-56]`): `navml/history.py`'s `HistoryStore`/`HISTORY` (DOS Navigator's `HistList`: per-id lists,
newest first, 20 each, pinned entries kept) and the `History` button with its `HistoryList` drop-down, which
`Field(history_id=...)` places after its line; Make directory has `"mkdir"`. *History* in `navml/DESIGN.md` has the
rest. **Trees are written** (`[94-101]`, `[104-110]`): the
library's `TreeView` (a `ListViewer` of flattened, lazily loaded `TreeNode`s drawn as `TTreeView.Draw` draws them)
and Navigator's `DirectoryTree`, which Ctrl+T puts in the passive panel's place (`DBLWND.PAS`'s `SwitchView`):
the tree follows the active panel, and Enter or a resting cursor sends the panel where the tree points. *Trees* in
`navml/DESIGN.md` has the rest. **Alt+T is DOS Navigator's *Choose Directory*** (`TTreeDialog`,
`navigator/widgets/change_dir_dialog/`): the tree frameless in a dialog (`ListViewer.framed = False`), the path under
it, and OK / Drive (disabled: one root) / Re-read / MkDir / Cancel down the right; OK sends the active panel there.
**Manager > New (Ctrl+F3) is `cmCreatePanel`**: another `Manager` window, zoomed to the desktop, both panels on
the active panel's directory (DOS Navigator asked for a drive first; one root has none to ask for). Ctrl+F3 is on the
application's key table so it works with no file manager open. With several open, **`Shell.active_manager`** -- the
file manager nearest the top of the desktop -- is what "the file manager" means; `shell.manager` / `app.manager`
stay the first one. **Disk > Directory tree opens `TTreeWindow`** (`navigator/widgets/tree_window/`): a *Directory Tree*
window on the desktop in the dialog palette, Esc closes it, and Enter sends the file manager's active panel there
(the tree's `ChosenEvent` bubbles to `Shell`). DOS Navigator 1.51 defined that window but never opened it; its menu
entry opened a second file manager instead -- taking the window was a choice, recorded in *Trees*.
**Window > List (Alt+0) is DOS Navigator's *Windows Manager*** (`cmWindowManager`, `dlgWindowManager`;
`navml/widgets/window_manager/` and `window_list/`): the desktop's windows top first, named by
`Window.list_name()` (`cmGetName`; a file manager is its active panel's directory), OK switches and Close closes
while the dialog stays up. **Window > Tile, Cascade and Close all** are DOS Navigator's `TDesktop.Tile`/`Cascade` and
`cmClearDesktop`, ported from `DNAPP.PAS`; every window is arranged unless it says `tileable: False` -- on by default,
where DN's `ofTileable` was opt-in and skipped the tree window. *Windows, the desktop and the modal* in `navml/DESIGN.md` has the rest.
**F3 is DOS Navigator's internal viewer** (`FVIEWER.PAS`): `navigator/viewer.py` is the model (`ViewSource`: `pread`
into cached chunks, never `mmap`, so a truncated log cannot `SIGBUS` Navigator), and `FileViewer` inside `FileWindow` is
`TFileViewer` inside `TFileWindow`. It opens zoomed on the desktop, with the scroll bar on the frame and `TViewInfo`
over the bottom edge. Positions are byte offsets and nothing counts lines, so a gigabyte opens at once. Text is UTF-8,
and an undecodable byte or a control is its CP437 glyph. F4 cycles text/hex/dump, F2 wraps, F6 filters,
F7/Shift+F7/Ctrl+F7 search (a bytes regex, on a thread), and F5 goes to a hex address. Esc closes it, and so does F3,
uncaptioned (Midnight Commander's key, a departure). File > View > As Text / As Hex open it in either mode. It is
read-only for now. A search still running after two ticks shows DN's *Search Progress* box (`TWhileView`: gauge,
percentage, Stop), fed through a `SearchJob` the thread writes and the loop reads. **Ctrl+Q is DN's quick view**
(`QuickViewer`, a framed `FileViewer`). It stands in the passive panel's place through `Manager.switch_view`, the
`SwitchView` that Ctrl+T now shares (`replaced`/`replacement`; `tree_replaces` is a computed over them). It follows the
active panel's cursor, and Tab moves the keyboard in and out. *The file viewer* in `navml/DESIGN.md` has the rest and
what is deferred.
**F4 is DOS Navigator's internal editor** (`MICROED.PAS`), being built in phases toward everything DN's editor had:
`navigator/editor/` is the model (`Document`, `columns`, `EditBuffer` with undo, `save`), `FileEditor` is `TFileEditor`
and `EditWindow` is `TEditWindow`, zoomed on the desktop with `TInfoLine` over the bottom frame. **A file round-trips
byte for byte** -- tabs, each line's own terminator, bytes that are not UTF-8 (`surrogateescape`) -- which departs from
DN's rewriting. Every key is a command named after DN's `cm*` in `FileEditor.keys`; `Widget.edits_text` makes the
command line's Enter/Home/End/Tab and pastes step aside. **Closing asks** through `Window.must_ask`/`ask_to_close`
(`Valid(cmClose)`), which `request_close`, Close all and Alt+X all go through; `Dialog.buttons` has `yes-no-cancel`.
Saving renames a new file over the old one. *The editor* in `navml/DESIGN.md` has the rest and the phases left.
**≡ > About is DOS Navigator's `MessageBoxAbout`** (`navigator/widgets/about_dialog/`): `Dialog` with `buttons: "ok"`
and its `message` centred. Its facts are never written twice: `navigator/about.py`'s `project_info()` reads
`pyproject.toml`'s `[project]` table in a checkout and the installed distribution's `METADATA` otherwise (the toml
does not reach a wheel). The README screenshot shows it open, so a version bump makes `screenshot.py --check` stale.
The home page is an **OSC 8 hyperlink**: `Style.link` is a per-cell URL that `render_diff` opens and closes as it
switches cells, exactly as it switches SGR; it is not in `STYLE_FIELDS`, so no sheet can declare one.
`TerminalInfo.hyperlinks` gates it -- on for any interactive terminal but `TERM=linux`, whose console prints OSC 8's
tail as text -- and `NAVKIT_HYPERLINKS=on|off` overrides. `StaticText.links` marks the `http(s)://` runs it paints.
**The command line is DOS Navigator's `TCommandLine`** (`navigator/widgets/command_line/`, a Python-only
`InputLine`): one row above the key bar, docked after `KeyBar` in `shell.nml`, in the hard-coded `$0F`/`$07` the
original drew it in (the one literal-colour rule in `navigator.nss`). **Its prompt is the user's own shell prompt**,
colours and all -- a deliberate departure, since `CMDLINE.PAS`'s `SetDirShape` ignored `PROMPT` and drew `<dir>>`,
which survives as the fallback (`Shell.command_prompt`) for `sh` and for the moment before the shell has printed a
prompt in the active panel's directory (`Shell.command_prompt_cells` compares `Console.prompt_cwd`). The hook
*brackets* whatever `PS1` the rc or a prompt command left rather than replacing it, the shell expands it, and
`console.py`'s `prompt_cells()` decodes the held-back bytes on a one-row `ConsoleScreen`, so a multi-line prompt shows
its last line. `Subshell.sync` sends the silent `cd` whenever the active panel moves while the shell is idle, and
`Navigator.on_start` starts the shell at once on a real tty (headless, the first command still does). It **never holds the
keyboard**: a key the focused widget declines walks up to `Shell.on_key`, which types it there -- DN's
`ofPostProcess` -- and navkit's `_cursor` now asks the whole focus path, nearest first, so `Shell.cursor_position`
puts the caret on the line. Enter, Home and End are `ExecuteCommandLine`/`CommandLineHome`/`CommandLineEnd` on the
application's key table, **disabled while the line is empty** so the key falls through to the panel. Esc clears,
Ctrl+E/Ctrl+X walk `HISTORY["command"]`, a paste lands on it. **Tab completes by the same rule**
(`CompleteCommandLine`): with text on the line the shell is asked silently -- ` __nav_complete <base64> <point>`,
answered by a `C` mark -- bash through `compgen` and the command's own `complete` spec (bash-completion's functions
included), zsh through its command tables and globbing only, since compsys cannot be asked from outside ZLE; `sh`
cannot, and Tab stays the panel key. One candidate ends the word (`/` for a directory, a space otherwise, shell
specials backslashed), several that agree extend it, and the rest drop a `CompletionList` (a `HistoryList`) over
the line. **Typing with the list open goes on into the line**: the list narrows at once and is refilled by a fresh
query (so `/` descends), a blank or Backspace past the word closes it, and it dims nothing
(`Widget.dims_behind = False`). Queries are answered in order -- `Subshell._completions` is a queue, because two keys
in one read send two queries before the first answer. **With the console up and idle it stands for the terminal**
(`Shell._console_is_the_terminal`): Up/Down walk the *shell's* history (` __nav_history`, an `H` mark, `fc -lnr`),
and where the user's rc binds Up or Ctrl+R to atuin (detected once at startup by `__nav_keys`, a `U` mark) those keys
run `atuin search -i` on the console exactly as atuin's own binding does -- descriptors swapped, the choice back in an
`R` mark, `__atuin_accept__:` running it at once. Such a line is sent in the queue's **`"reveal"` mode**: hidden until
its `O` mark, shown after, holding the keys (`busy`) while it runs, and finishing no command. With the panels up, Up
is the panel's and Ctrl+R re-reads, as in DOS Navigator. **Enter on an executable runs it** (`Panel.choose` emits
`ExecuteFile`, `Shell.on_execute_file` runs `./name` as if typed; a plain file is left alone), and **Ctrl+Enter puts
the entry's name on the command line** (`InsertName`, DN's `_CtrlEnter`/`cmInsertName`: a space after, one before if
the caret follows a word, `..` giving the directory itself; Ctrl+Shift+Enter the whole path, Ctrl+double-click the
same). Alt+Enter is bound beside it -- mc's key -- because a terminal without the kitty protocol sends Ctrl+Enter as
Enter, and Ghostty, which has the protocol, keeps Ctrl+Enter (fullscreen) and Ctrl+Shift+Enter for itself unless
unbound (`keybind = ctrl+enter=unbind`) -- both found with `keyprobe`; for the same reason `ListViewer` claims only a *bare* Enter. **A re-read keeps the cursor on its entry**, as
DN's `RereadDir` did (`Panel.reload`), and only a change of directory starts at the top. **The clipboard** is navkit's (`navkit/clipboard.py`, *Clipboard* in `navkit/DESIGN.md`): OSC 52 plus
`wl-copy`/`xclip`/`xsel`, a requested paste arriving as a `PasteEvent`. Every `InputLine` selects with a drag or a
double click (a finished one is the primary selection), and takes Ctrl+Ins (copy, the whole line with no selection,
as DN's did), Shift+Del, Shift+Ins, Ctrl+C (only with a selection) and Ctrl+V; a middle click pastes the primary
selection. The console selects its output with a drag or a double click unless a program tracks the mouse, reversed
on screen and cleared by new output or a scroll, and Ctrl+Ins copies it -- `Shell.on_key` asks the console before
the command line. A paste now walks the focus path when `Application.on_paste` declines it, so a dialog's line takes
one. **Commands run in one persistent `$SHELL`**
(`navigator/subshell.py`'s `Subshell`, owned by the `Console`): bash and zsh load the user's rc and then a hook,
anything else runs bash or `sh`. The hook prints private OSC marks (`ESC ] 6973;<nonce>;A|B|D`) that say where the
prompt is, when a command finished and the shell's `$PWD`. **The shell's own prompt is held back** and painted only
when a command is sent, so the console log reads `prompt$ cmd`, the shape DN's `/dir>cmd` echo had. The panel's directory reaches the shell
by a **silent `cd`** (leading space, output swallowed) sent only when the two differ, and a `cd` typed on the line
moves the active panel when the command finishes (`CommandFinished`, posted from the pty reader to
`Navigator.on_command_finished`). While a command runs the console is up and holds the keys; afterwards the windows
come back and both panels re-read, unless Ctrl+O had put the console up, in which case it stays. **An idle console
takes no keys**: Ctrl+O shows output, and typing still goes to the command line. **While a program runs it gets every key,
Ctrl+O included** (`Shell.program_has_keys`, which `Shell.enables` and `Navigator.enables` both consult, disables every
command, so F10 reaches `htop`/`mc` and Ctrl+O is `mc`'s and `nano`'s), arrows follow
its DECCKM (`encode_key(..., application_cursor=)`, `SS3` vs `CSI`, with xterm's modifier parameter on special keys),
and its mouse reports go back down the pty (`encode_mouse`, modes 9/1000/1002/1003 and SGR 1006). `navkit/console.py`'s
`_Screen` adds what pyte lacks: the **alternate screen** (47/1047/1049, so a full-screen program's last frame does not
bury the log), **answers to queries** (`ConsoleScreen.respond`, cursor position and device attributes), dropping a
private CSI pyte would crash on (`mc` sends `CSI ? Pm r`) or misread (`CSI > 4;2 m` was bold+underline), and a parser
rebuilt rather than dead if pyte raises anyway -- its parser is a generator, which one exception closes for good.

Four rules from building it, each of which was found by running something rather than by reasoning:

- **A handler starts a dialog; it does not wait for one.** `await dialog.execute(app)` inside `on_key` mounts the
  dialog, takes the modal focus and *never paints it*: `_main_loop` awaits `_handle` before rendering and is the
  event queue's only consumer, so the key that would dismiss the dialog is never dispatched. Use
  `self.spawn(self._work())` and let the handler return. `Dialog.execute` raises rather than hanging.
- **A dialog's geometry must be bound, not assigned.** `Widget.add()` lays a child out into its parent and
  `Component.layout` steps around a side only when it carries a binding — so a dialog sized with a literal becomes
  full-screen the moment `overlay()` adds it. Route the size through a declared property the base binds from, which
  is also the only way a derived document can change it.
- **A derived component's own children land *after* its base's**, because `super().__init__()` is the generated
  constructor's first line. `Dialog.focusable()` moves its buttons to the end; without it every derived dialog opens
  with the focus on OK.
- **Effects belong in `mounted()`, not `__init__`**, for any widget that can be removed and put back — which is
  every widget in a dialog. `remove()` disposes a subtree's effects.

**Layouts are written**, and they replaced the arithmetic every container used to place its children with:
`HorizontalLayout`, `VerticalLayout`, `GridLayout`, `DockLayout` and `StackLayout`, all on a Python-only `Layout`
that paints nothing. A child asks for room with **style hints the layout reads off the child** — `basis`, `grow`
(default 1, so siblings that say nothing share evenly) and `dock` — so a `style:` block or a sheet rule says it. A
layout re-arranges from an effect on its own size, its children's `visible` and their hints, which makes a child's
geometry *navigated*: its markup says nothing about it. `Field` is `Field(HorizontalLayout)`, `Shell` is
`Shell(DockLayout)`, and `Dialog`'s buttons and `Manager`'s panels sit in an id'd `HorizontalLayout`. **Components are grouped**: the layouts are one component directory each under `navml/widgets/layout/`, and the
thirteen *Dialogs* components (`Control` through `Field`, `Modal` and `Dialog` included) under `navml/widgets/dialog/`
(`from navml.widgets.layout.horizontal_layout import HorizontalLayout`,
`from navml.widgets.dialog.dialog import Dialog`). `Window`, `Desktop`, `Timer` and `Spacer` stay at the top. A
group's `__init__.py` is a docstring and never re-exports, `_COMPONENTS` maps a name to its dotted path
(`"dialog.button"`), and `from navml.widgets import Button` is unchanged. *Components come in groups* in
`navml/DESIGN.md` has the rest. All four
conversions paint `cmp`-identically on a pty. *Layouts* in `navml/DESIGN.md` has the rules.

**The generator is seven modules with one concern each**, in a one-way chain: `expression.py` compiles a property
expression or a handler body by rewriting free names on the syntax tree; `sibling.py` reads the hand-written `.py`
**without importing it**; `resolve.py` is the only module that imports what a document names; `checks.py` refuses
everything a live class can reveal; `generator.py` and `stubs.py` emit the two artefacts; `build.py` orders a
directory by its import graph and writes. `navml/_alias.py` sits beside `navml/component.py` as run-time support the
generated code names. **Anything emitting code goes through `navml/coder.py`'s `Coder`** — a line buffer with logical
indents and trailing comments — and not through string assembly or a whole-module `ast.unparse`, because `ast` carries
no comments and navml's source map *is* comments.

**A component that paints has two halves by construction.** Markup declares and places; Python paints. `Label` had to
gain a `label.py` for exactly this, and `navml/widgets/dialog/field/field.nml` is the markup-only example in its place. The
converse bit too: `CheckBoxes` and `RadioButtons` *lost* their markup halves by being finished, because everything
they declare is `Cluster`'s and everything they show is painted — a document holding nothing but a head says only
what its `class` statement already says.

**And a property a widget *navigates* cannot be bound** — the one rule converting the desktop turned up. A markup
property line compiles to a binding, a bound attribute is read-only until something unbinds it, and `Panel.enter()`
assigns `path` on every descent, so `path: root.left_path` compiles, paints correctly, and then raises the first time
somebody presses Enter. A starting value is not something markup can say, so `manager.py` seeds `left.path`,
`right.path` and `console.cwd` after `super().__init__()` and the document says nothing about them. *A property a
widget navigates cannot be bound* in `navml/DESIGN.md` has the three alternatives that were rejected.

**The parser imports nothing the document names**, and that is the line between it and the generator: every check
a document can fail on its own — structure, identifiers, reserved words, collisions with itself — is
`navml/parser.py`'s, and every check needing a live class is the generator's. `parse(text)` / `parse_file(path)`
return a `Document`; `imports_of(path)` reads only the import block, which is what orders a cold build by its
import graph without executing anything. Three lexical rules it settled: **blocks are made of spaces** and a tab is
an error; **a logical line continues only while a bracket is open**, Python's own implicit continuation and nothing
else; and **`#` opens a comment only when a space, an end of line or a `:` follows it**, because `#rrggbb` is a
colour inside a `style:` block. A `#:` run above a declaration is captured for the generator to re-emit. The root
block takes no `id` — it is `root` in every expression already.

**Everything that blocked the generator is now settled**, and the answers converged on one mechanism.
`navml.component.Component` is the base every generated class names (`class Label(_Component)`, or
`class FramedButton(Button, _Component)` — always, so a component derived from a *Python-only* widget still stops
`Widget.layout` cascading into children the markup placed). It holds the `layout()` override, `__navml_source__`, and
the constructor that makes the rest work. **A component's parameters are the properties it declares, arriving as
keywords** — `Component.__init__` takes the names `type(self)` declares out of `**kwargs` and sets them *before*
`Widget.__init__` joins the widget to its parent, because that constructor is keyword-only and closed and would refuse
them. A keyword naming no declaration is left in `kwargs` and still raises. **And a widget markup constructs must take
no required constructor argument**, because a child block compiles to `Type(parent=self)` and nothing else — which is
why `Panel.path` now has a default. Beware: `navkit.stylesheet._is_a` matches a type selector by class *name*, so
**`Component { }` is a live `.nss` selector** matching every markup-built widget and no hand-written one; it reads
*built from markup*, never *is a component* (`spacer.py` is a component and does not match).
`Widget._stylesheet` is now the public `Widget.stylesheet`, matching `Application.stylesheet`, and the computed that
walks up to the nearest sheet is `effective_stylesheet`: **`stylesheet` is what an object brings and is assigned,
`effective_stylesheet` is what a widget resolves against and is derived.** So markup assigns a component's own sheet
like any other property. `equal=` is deliberately not
expressible in markup: a comparator is a function and a document has nowhere to put one, so a property needing one is
declared in the hand-written half. navkit grew the three things navml asked of it: a public `Declaration`,
`Binding.owned_by(owner)`, and `stylesheet.check_declarations(text, *, line, filename)`, which checks a declaration
set's names and grammar while leaving `$variables` for run time.
**Every `on_*` handler is `async def`, and navkit refuses a synchronous one** — at class creation for a handler a
class body defines, and at the call for one assigned onto an instance, which is what markup compiles to. The rule's
boundary: **a hook that cannot be awaited where it is called does not get an `on_*` name.** `Widget.mounted()` and
`unmounting()` run from `add()`, which runs from `__init__`, so they are plain synchronous callbacks taking no event;
`Application.on_start`/`on_stop` keep their names because `run_async` can await them. A handler that awaits lets the
loop run mid-batch but **cannot cause a repaint** — `_render` is only ever awaited from `_main_loop` — so one frame
per batch still holds.
`Widget.emit(event)` walks an event from the widget that raised it up through its ancestors to the application,
stopping at the first handler that returns True, and an event class names its own handler (`Event.handler`, derived
from the class name — `ClickEvent` reaches `on_click`). A widget declares what it raises with `emits = (ClickEvent,)`,
read through `navkit.events.emitted(cls)`, which **unions down the MRO** rather than shadowing as `declarations()`
does. `navkit/events.py` carries only the events navkit itself raises — terminal input and the loop's wake — and
everything a *widget* means belongs to the library. `Application.focused` holds the widget keys go to,
`Widget.can_focus` (False by default) says who may hold it, `Widget.focus()` takes it and `Application.focus_next()`
moves it; `dispatch_key` now walks the focus path rather than touring every descendant, so **with nothing focused a key
reaches no widget at all**. `Widget.focused` is a computed, which makes `:focused` a stylesheet state for free.
`Widget.is_mounted` says whether a widget is in a tree an application owns — spelled that way so `mounted()` can be
the callback — and `mounted()`/`unmounting()` are called by the walks that `Application.root`, `add()` and `remove()`
drive. **`remove()` disposes the subtree's effects** (`navkit.reactive.dispose_effects`), so **a widget that can be
removed and put back declares its effects in `mounted()`, not `__init__`**. `Widget.modal` makes a widget take all
input while it is mounted — the mount walks
maintain `Application.modal`, so every way out of the tree gives the input back — and `Application.overlay(widget)`
puts one on top of everything, closed again with `app.root.remove(widget)`. `Widget.cursor_position()` returns where
the terminal's own cursor belongs in a widget's coordinates, and the application places it at the end of each frame for
whichever widget the keys are going to — so a caret is never shown on a widget that cannot receive what is typed; the
`caret` widget property sets its DECSCUSR shape from a sheet and defaults to leaving the user's own alone.
`navkit/DESIGN.md`'s *The cursor: shown where the keys go*, *Modal and overlay: the input, not the painting*,
*Mounting: joining a live tree, and leaving one*, *Focus: one pointer, and eligibility decided at delivery* and
*Emitting: a widget event walks up* record why each part went the way it did.
Decisions taken ahead of the code live in two design notes, and are where the next one belongs: `navml/DESIGN.md` for
the markup language, `navkit/DESIGN.md` for the core, whose *Still open* section names what is left.

There is no lint tooling configured yet. When adding one, record the command here. Packaging is setuptools via
`pyproject.toml`: `./venv/bin/python -m build` (needs `pip install build`, and setuptools 77+ for the PEP 639
`license = "MIT"` expression the metadata uses).

The **distribution** name is `navigator-fm`; the **import** names stay `navigator`, `navkit`, `navml` and the command
stays `nav`. Plain `navigator` and `nav` were taken on PyPI before this project existed. Installation folds only runs of
`-`, `_` and `.` into one separator, but *registration* is stricter -- PyPI refuses a new name that collides with an
existing one once those characters are deleted outright, so `navigator-fm` reserves `navigatorfm` against everybody,
this project included; see below. Versions are placeholders in the 0.0.x series until the first real release, which
keeps 0.1.0; PyPI never lets a version number be re-used, so a botched upload costs a version rather than being
replaceable.

**The version is written in exactly one place**, `navigator/__init__.py`'s `__version__`. `pyproject.toml` declares
`dynamic = ["version"]` and reads it through `[tool.setuptools.dynamic]`, which setuptools resolves by parsing the
syntax tree rather than importing the package -- so it must stay a plain string literal, and the build needs none of
the run-time dependencies to find it. `packaging/navfm/pyproject.toml` deliberately does *not* track it: the alias
depends on `navigator-fm` unpinned, so it is re-uploaded approximately never.

Verify a build with
`./venv/bin/python -m twine check dist/*` and by installing the wheel into a throwaway venv and running `nav
--list-themes` from *outside* the checkout -- that is what proves the `importlib.resources` asset lookup survives
installation, which a run from the repository root cannot.

`nav --version` prints the version, the directory the running copy was imported from, and the interpreter, in
`pip --version`'s format. The path is the point: Navigator can be installed as a system package, a pipx copy and a
checkout at once, and `~/.local/bin` precedes `/usr/bin` on most PATHs, so the copy that runs is often not the one
that was just installed. `version_banner()` prefers `importlib.metadata` over `__version__` because the two diverge
exactly when a checkout has been edited since it was installed.

`packaging/navfm/` holds the one near-miss name worth holding, as its own project with its own `pyproject.toml`,
`README.md` and a copy of the root `LICENSE` (setuptools will not follow `license-files` out of a project directory).
It is an **alias, not a build of this code**: `packages = []` makes it a metadata-only distribution whose sole
dependency is `navigator-fm`, unpinned, so `pip install navfm` resolves to the current real release and never has to be
re-uploaded alongside it. Adding a module to it would defeat the point.

```
./venv/bin/python -m build -o dist .
./venv/bin/python -m build -o dist packaging/navfm
./venv/bin/python -m twine check dist/*
```

`navigator-fm` has to reach PyPI before the alias is installable, so upload it first. The alias chain is verified by
`pip install --find-links dist navfm` into a throwaway venv: it must pull `navigator-fm` and `pyte` in behind it and
leave a working `nav`.

`packaging/linux/` builds the `.deb` and the `.rpm`, both from one `nfpm.yaml`:
`NFPM=/path/to/nfpm PYTHON=./venv/bin/python ./packaging/linux/build.sh` after a `python -m build`. Output lands in
`build/pkg/` (gitignored). Three things about it are load-bearing:

- **The tree is staged by `pip install --target`, not by copying directories**, so the files that reach the package
  are exactly the ones the wheel declares -- `navigator/styles/*.nss` included. `build.sh` then asserts the stylesheet
  and all eleven themes are present, because losing them yields an application that starts and *then* fails to theme.
- **One `arch: all` / `noarch` package serves every interpreter from 3.12 up**, because every dependency is pure
  Python. A venv could not: it bakes its minor version into `lib/python3.N/site-packages` and into `pyvenv.cfg`, so it
  would need one build per distro. `build.sh` fails the build if a `.so` ever appears in the staged tree, since that
  is the moment the claim stops being true.
- **`/usr/bin/nav` runs `python3 -sP`, and the `-P` is not hygiene.** A file manager is launched inside arbitrary
  directories, and without it a directory that merely *contains* an `icons.py` or a `pyte.py` shadows the real module,
  so Navigator dies on startup in that one directory and nowhere else. This is verified, not assumed: dropping a
  decoy `pyte.py` into the working directory crashes `-s` and leaves `-sP` untouched.

`packaging/linux/repo/` publishes the two repositories, and `.github/workflows/release.yml` drives the whole release
from a `v*` tag: tests, then PyPI, then the packages, then the site. Four things there are not obvious:

- **The repository scripts add to a published site, they do not build one.** apt indexes by scanning the pool and
  `createrepo_c` by scanning the directory, so the previously released files have to be *present* or the new index
  silently forgets them and every pinned or older install breaks. The workflow checks out `gh-pages` first for that
  reason, and passes `EXPECT_AT_LEAST` -- the count read off the live site -- so the scripts refuse to publish an index
  smaller than reality. Comparing before with after inside one run cannot catch this: a run that started from an empty
  directory has nothing to lose, which is exactly the failing case.
- **`GPG_KEY_ID` must be the *signing subkey's* 16-hex-digit long key id**, and each half of that sentence was paid
  for. nfpm parses it as a 64-bit integer, so a 40-character fingerprint is `value out of range` -- and so is a
  17-character one, which is what `make-signing-key.sh` printed until it stopped slicing the id off the end of the
  fingerprint. Given the *primary's* id nfpm fails differently and far less helpfully, with `no valid signing keys`:
  CI holds an `--export-secret-subkeys` export, so the primary is a stub with no private key, and it is certify-only
  besides. `ghaction-import-gpg` has the same blind spot from the other side -- without its `fingerprint` input it
  presets the passphrase against the stub primary's keygrip and dies on gpg-agent error 67108891 (source 4,
  code 27, `NOT_FOUND`) before nfpm is ever reached. gpg itself is the relaxed one: `--local-user` takes a subkey id
  without complaint, which is why the repository scripts never noticed the question. `release.yml`'s
  published-key check therefore matches `GPG_KEY_ID` against **both** the `pub` and `sub` records of the committed
  keyring; matching `pub` alone rejected precisely the value that works.
- **The two ecosystems verify different things.** apt verifies the *index* (`InRelease`/`Release.gpg`) and takes
  per-package integrity from the SHA256 in `Packages` -- it does not check per-package signatures at all. dnf is the
  reverse: `gpgcheck=1` verifies a signature inside each `.rpm`, which nfpm has to write at *build* time, and
  `repo_gpgcheck=1` verifies `repomd.xml.asc`. Signing only one half of either leaves a repository that warns or
  refuses.
- **CI signs with a subkey, and that subkey is exported *without* a passphrase.** `make-signing-key.sh` exports
  `--export-secret-subkeys`, so the certifying primary never leaves the maintainer's machine and a leaked CI secret
  can be revoked without users having to trust a new key. The missing passphrase is not an oversight: **nfpm cannot
  decrypt a subkey whose primary is the `gnu-dummy` stub such an export leaves behind**, and fails with
  `signing key is encrypted` no matter what passphrase it is given -- measured against nfpm 2.47.0, which is the
  latest, with a key whose passphrase was known. The same file with no passphrase signs. The alternatives were
  handing CI the full secret key, which puts the certifying primary on a build runner and gives up the property
  above, or taking the `.rpm` signature away from nfpm and doing it with `rpmsign`. Dropping the passphrase costs
  least, because it never protected anything: it would have lived in the same GitHub secret store as the key it
  protects. `make-signing-key.sh` asserts the export is unprotected rather than trusting it, since the failure
  otherwise surfaces only in CI. There is consequently **no `GPG_PASSPHRASE` secret** -- do not reintroduce one.

The apt half is verified end to end without Docker: point the real `apt-get` at a private `Dir::State`/`Dir::Cache` and
a `file://` source, and it accepts the signed repository, lists both published versions and refuses the same repository
under a different key (exit 100, `NO_PUBKEY`). The rpm half has no such local check -- `createrepo_c` and `rpm` are not
installed here -- and is exercised only in CI.

`native_version.py` imports **`packaging`, the PyPI distribution** -- not `packaging/`, this repository's directory of
the same name -- so `build.sh` needs it installed and names it if it is missing. Every development venv carries it via
`build` and `pytest` and a bare CI runner does not, which is why the release workflow installs it explicitly and why
its absence first surfaced as a `ModuleNotFoundError` several jobs into a release.

`native_version.py` maps a PEP 440 version onto the Debian and RPM spelling, and `tests/test_packaging.py` checks the
result against `dpkg --compare-versions` rather than against a table -- what matters is the ordering, not the string.
A pre-release takes `~` so it sorts *below* its release; `.devN` takes **two**, because past a single tilde `a` < `d`
would put `~dev5` after `~a1` and invert PEP 440. That inversion is asserted in the tests so the reason cannot be
optimised away.

**Do not add a `packaging/navigatorfm/` back.** It was tried and PyPI answered `400 Bad Request`. PyPI "ultranormalises"
a proposed new name -- separators deleted rather than folded, and confusable characters such as `l`/`1`/`i` and `0`/`o`
run together -- and refuses it if the result matches an existing project. `navigator-fm` ultranormalises to
`navigatorfm`, so that spelling is already reserved against everyone and is unregisterable by us for the same reason.
The 400 carries no explanation (warehouse#17375), which is what makes this worth writing down. The same rule is why
`navfm` is a separate name and does have to be held deliberately.

The application lives in the `navigator/` package: `navigator/__main__.py` is the entry point, `navigator/widgets/`
the screens, `navigator/scheme.py` the stylesheet loader, and `navigator/styles/` the assets it reads. Assets are found through `importlib.resources` rather than relative to `__file__`, and
`navigator/styles/*.nss` is declared as package data — a new asset directory needs a matching
`[tool.setuptools.package-data]` entry or it will work from a checkout and vanish on install. `navigator/styles/themes/`
is the second such directory and carries its own `__init__.py` and package-data entry for that reason.

Colour is split from structure and neither half is authored by hand. `navigator/styles/navigator.nss` holds the rules
and defines no variable, so it does not parse alone; `navigator/styles/themes/*.nss` define every variable and no rule,
and one is always loaded after it (`load_scheme("norton")`, `python -m navigator --theme norton`). The themes are
generated: each is a DOS Navigator `COLORS/*.PAL` palette decoded by `tools/palconv.py`, which documents the file format
in full and — the part that took the work — which of the 228 attribute bytes means what. Re-derive rather than hand-edit
a theme. **A deliberate departure from a palette goes in `palconv.py`'s `DEPARTURES`** (theme -> slot -> colours and
why), which applies it on generation and marks it in the theme's comment. There is one: `default` [117], the viewer's
*Normal text*, is #D8D8D8 rather than DEFAULT.PAL's light grey on dark grey (2.6:1 contrast), at the user's request.

The slot table comes from `RESOURCE/ENGLISH/DN.DNR` in the DOS Navigator source — the script the resource compiler turns
into the `dlgColors` resource — which names all 144 entries the Colors dialog exposes, in 20 nested groups, as
`COLORITEM <name>, <index>` lines. Every theme carries all 144, so a `.nss` is a full transcription of its `.PAL`;
`navigator.nss` reads eight of them today and the rest are marked `>`-less and inert.
`palconv.py --names path/to/DN.DNR` regenerates the table. Twenty-three entries also carry the Turbo Vision
palette-string chain that independently arrives at the same index; the two routes were worked out separately and agree
everywhere, which is what makes the other 121 trustworthy. Group names repeat across the tree (two `Tree`s, two
`Highlight`s, two `Menu`s), so variables are stemmed by group *path*, and a published variable name is API —
`HAND_NAMED` pins the ones `navigator.nss` uses.

The 84 entries `DN.DNR` does not name are ones DOS Navigator never let the user set, and are not carried.

## Environment and commands

- Python 3.12, virtualenv at `venv/` (not tracked): `source venv/bin/activate`
- One run-time dependency, `pyte`, and it is load-bearing: it is the VT emulator behind `navkit/console.py`, which is
  what makes Ctrl+O possible at all — install it with `./venv/bin/pip install -r requirements.txt`. Everything else is
  stdlib. Test tooling lives in `requirements-dev.txt`: `./venv/bin/pip install -r requirements-dev.txt`
- Run the file manager: `./venv/bin/python -m navigator [LEFT_DIR] [RIGHT_DIR]` (Tab switches panels,
  arrows/PgUp/PgDn/Home/End move, Enter descends, typing goes to the command line and Enter runs it there, Ctrl+E/Ctrl+X
  recall commands, Ctrl+R rescans, Ctrl+O shows the console and Shift+PgUp/PgDn scrolls
  it back, F10 opens DOS Navigator's menu, Alt+X quits). `--theme NAME` picks a colour scheme, `--list-themes` names them, `--palette terminal`
  gives the terminal's own scheme back the sixteen colour names, `--glyphs {auto,ascii,unicode,nerd}` overrides what the
  terminal's font is assumed to draw, `--no-dim-modal` stops what is behind a dialog being painted faint
- Regenerate the colour schemes from a DOS Navigator distribution:
  `./venv/bin/python tools/palconv.py path/to/DN/COLORS --out navigator/styles/themes`; `--dump ONE.PAL` prints one
  palette's decoded slots instead
- See what a terminal sends while it is in Navigator's modes (raw, mouse, bracketed paste, kitty flags):
  `./venv/bin/python tools/keyprobe.py [--legacy] [--no-mouse]`, `q` twice or Ctrl+C quits -- the way to find out whether a key
  the terminal binds for itself (Ctrl+Shift+V) arrives as a paste or as a key
- Regenerate the README screenshot: `./venv/bin/python tools/screenshot.py` paints the desktop headless (pinned
  directory, clock and console) and writes `docs/screenshot.svg` plus the text copy between the README's
  `<!-- screenshot:begin/end -->` markers; `--check` exits 1 when either is stale, `--theme`/`--size` pick the scene.
  The README links the SVG by absolute `raw.githubusercontent.com` URL because PyPI renders the same README
- Regenerate a component's Python from its markup: **`./venv/bin/python -m navml build navml navigator`** — both
  component packages, and naming them is necessary because the no-argument form builds the installed `navml` package
  alone, which is the edit-in-site-packages workflow rather than this repository's. `--check` reports markup that no
  longer matches its generated half and exits 1, which is what to run after editing any `.nml`; a generated file is
  only ever overwritten if its first line is `# navml: generated`
- Run the tests: `./venv/bin/python -m pytest`; one file with `... -m pytest tests/test_screen.py`; one test with
  `... -m pytest tests/test_screen.py::test_only_changed_cells_are_emitted` or `-k <substring>`
- pytest config lives in `pyproject.toml`; `pythonpath = ["."]` is what lets tests import `navkit` and `navigator` from
  the repo root

## Testing

`tests/conftest.py` carries the three things every application test needs:

- `FakeTerminal` — stands in for the tty (`is_tty` false, so no reader or raw mode is installed) and records one
  `frames` entry per flush. `len(frames)` is therefore the number of repaints that produced actual output, while a
  widget's own render counter is the number of render passes; an unchanged frame renders but writes nothing, so assert
  on whichever of the two you actually mean.
- `run_app(app, actions)` — runs the app to completion on `asyncio.run`, applying each action (an event to post, or a
  callable taking the app) once the loop is live, and exiting afterwards if the app has not already stopped. Everything
  is wrapped in a timeout so a stuck loop fails instead of hanging the suite.
- `settle()` — runs the queued reactive effects, which is what the event loop does between dispatching a batch and
  painting. A test that drives a widget's model directly (`panel.enter()`, `panel.reload()`, `panel.cursor = 99`) has no
  loop draining the scheduler, so it must call this between acting and asserting. Tests going through `run_app` never
  need it. An autouse fixture clears the shared scheduler around every test so one test's queued work cannot leak into
  the next.

Tests drive the loop through `Application.post_event()` and read `Application.is_running`; both exist so tests never
have to reach into the private queue. Actions posted in a single callback land in one batch, which is how the "one frame
per batch" behaviour is asserted.

For the parts a fake terminal cannot cover — raw mode, real escape output, `SIGWINCH` — run `python -m navigator` on a
pty (`pty.fork`, set the window size with `TIOCSWINSZ`, write key bytes to the master fd, read back what it paints).
This is a manual check, not part of the suite.

## Intended architecture

Navigator is a faithful recreation of the DOS Navigator two-panel file manager for modern POSIX terminals. It is layered
in three parts, each depending only on the one below it:

### `navkit/` — application core (lowest layer, no widget library knowledge)

Written, and the pieces fit together like this:

- `application.py` — `Application` owns the only asyncio loop. Terminal input arrives through a `loop.add_reader`
  callback that feeds `InputParser` and queues the resulting events. The order in one turn is fixed: **dispatch the
  whole batch, flush the reactive effects it queued, then paint one frame** — so a paste or a mouse drag costs a single
  repaint, and nothing reactive runs during the paint. `SIGWINCH` becomes a `ResizeEvent`; events reach the
  `Application.on_*` hooks first and the widget tree second. It also holds `ClickTracker`, which turns two presses and
  a clock into a `DoubleClickEvent` — see below.
- `terminal.py` — `Terminal` owns the tty (raw mode, alternate screen, mouse tracking, bracketed paste, autowrap off)
  and restores it in `Application`'s `finally`. `InputParser` is fed incrementally and keeps undecodable tails, so
  sequences split across reads still decode. A lone `ESC` is inherently ambiguous: the parser reports `pending_escape`
  and the application resolves it with an `ESCAPE_TIMEOUT` timer.
- `screen.py` — `Surface` is what widgets paint into. `ScreenBuffer` is the one that owns cells;
  `surface.view(x, y, w, h)` returns a shifted, clipped window onto another surface that owns nothing and forwards.
  `render_tree` hands each widget a view of its own area, so **widgets paint from `0, 0` in their own size and cannot
  draw outside themselves** — no `self.x +` arithmetic, no manual bounds checks, and a wide character at a widget's
  right edge degrades to a blank instead of spilling onto its neighbour. Drawing still clips silently, and double-width
  characters occupy a cell plus an empty continuation cell. `render_diff()` emits only the escapes needed to turn the
  last flushed buffer into the new one, comparing each row whole before walking its cells, and repaints fully when the
  size changed.
- `glyphs.py` — the character sets a frame is drawn from (`single`, `double`, `round`, `ascii`) and the tiers that
  govern them. Imports nothing, which is what lets `screen.py` keep having no runtime import of `capabilities.py`:
  `draw_box` takes the six characters themselves, never a name for them, so the buffer never learns that a tier exists.
  A widget resolves the two halves with `Widget.box_charset()` — the sheet says which set is *wanted*, the tier says
  which can be *shown*, and either vetoes.
- `style.py` — `Style` is an immutable cell appearance that knows its own SGR sequence. Nothing else writes colour
  codes.
- `capabilities.py` — `TerminalInfo` is what the terminal supports (`colors`, `alt_screen`, `mouse`, `bracketed_paste`,
  `title`), what a palette index *means* (`palette`), and the decisions that follow. `Terminal` detects one at
  construction and gates its escapes on it; `render_diff(previous, current, info)` is where a colour the terminal cannot
  name is quantised to one it can. **That is the only place the question is asked** — a widget asks for the colour it
  wants and a sheet records the colour the original asked for, so nothing upstream degrades anything. A palette *index*
  is passed through untouched **unless a palette is pinned**: with `TerminalInfo.palette` unset — navkit's default —
  `blue` stays whatever the user's terminal theme paints, and with `VGA_PALETTE` set it means the register value the DOS
  original asked for. `navigator` pins by default, because a theme that names a colour is transcribing a `.PAL` that
  left the VGA registers alone; `--palette terminal` hands the question back. **A child program's cells are never pinned**: the
  console marks them `Style.terminal_palette` (per cell, like `link`, and not a sheet field), and `adapt_style`
  leaves their indices alone, so `ls --color` in the console matches the plain terminal whatever the theme. Pinning is a no-op below 256 colours — an
  index resolved through the palette quantises straight back to itself — so only a terminal that can do better sees a
  difference, and `--reprogram-palette` (OSC 4, reset with OSC 104) is the opt-in that reaches the ones that cannot.
  Detection is conservative — sixteen colours unless `COLORTERM` says otherwise — and `NAVKIT_COLORS` (`truecolor`,
  `256`, `16`, `8`, `mono`, or a number) overrides it, outranking `NO_COLOR`; `NAVKIT_PALETTE` (`dos`/`vga`, `terminal`/
  `none`/`off`) does the same for the palette, and `--palette` outranks it.
  `TerminalInfo.glyphs` is the same question asked about *characters* — `GLYPHS_ASCII` < `GLYPHS_UNICODE` <
  `GLYPHS_NERD`, `NAVKIT_GLYPHS` overriding and `--glyphs` outranking that. **A font cannot be detected**: no escape
  sequence reports one, and the cursor-position probe measures the terminal's width table rather than the font's
  coverage. So the Nerd tier is granted only to emulators that *bundle* a Nerd Font fallback (kitty, WezTerm, Ghostty)
  or to a session that says so itself; a multiplexer hides all of it and needs the override. Guessing too high costs a
  replacement box on every line, so a non-UTF-8 locale gets ASCII rather than the benefit of the doubt.
- `reactive.py` — observable attributes and the bindings between them; the mechanism `navml` markup relies on.
  `reactive()` declares a source, `computed()` a derived value, and assigning `obj.attr = bind(expression)` attaches an
  expression to *one instance* — which is what markup compiles to. `bind()` only wraps the expression in a `Binding`;
  the descriptor recognises one on assignment and installs it instead of storing a value, so the target is named by a
  real attribute reference rather than by a string. The three calls that have to name an attribute without assigning to
  it — `unbind(obj, Widget.width)`, `is_bound()`, `peek()` — take the class attribute itself, which is the declaration
  object. Dependencies are discovered by running the expression and noting what it read, so a conditional subscribes
  only to the branch it took. Propagation is push-pull: a write eagerly marks dependents stale, values are recomputed
  lazily on read and memoised. That makes it glitch-free (a diamond recomputes once, from inputs that are all final) and
  mirrors the frame loop one layer up. `effect()` is the only eager node, for reactions that must happen whether or not
  anybody reads a value.
- `widget.py` — `Widget` has children, `render(surface)`, `layout(width, height)` (called on the root at every
  resize) and `dispatch_key`/`dispatch_mouse`, which offer events to the topmost child first — `dispatch_mouse` under
  `event.handler` rather than to `on_mouse_click` by name, which is what makes a refinement of a mouse action reach
  its own handler. Its geometry, `visible`, `style` and `parent` are reactive, so assigning one asks for a repaint on
  its own; `layout()` steps around any size that carries a binding. **All coordinates are relative to the parent** —
  `x`/`y`, `contains()`, and the position a `MouseClickEvent` carries, which `dispatch_mouse` shifts as it descends.
  Only the root sits in screen coordinates, and it sits at the origin.

**A double-click is navkit's, and it is a fact rather than a meaning.** The terminal reports no such thing — SGR gives
`press`, `release` and `move` — so `ClickTracker` synthesises one from two presses and a clock, the way a lone `ESC`
becomes an escape key. It belongs here and `ClickEvent` does not because the membership test is *does navkit raise it*,
and because `Application._loop.time()` is the only clock event handling can reach; a widget library doing this would
have to reach into the private loop of the object that owns it. Four things to know: **the press is still delivered**
(the double-click is *additional*, so a widget acting on both acts twice — which is what lets
`Panel.on_double_click` be three lines that only `enter()`, the press having already moved the cursor); it is
dispatched **inline** right after that press and re-enters `_handle`, so `on_event` sees it; the run keys on the
**exact cell and button** with no tolerance, counts upward so a triple click raises one double-click and not two, and
is forgotten on a wheel, a resize or a modal push/pop; and `DOUBLE_CLICK_TIMEOUT` is 0.4 but `Application(double_click=
…)` overrides it — unlike `ESCAPE_TIMEOUT`, because this window is a property of the user's hand rather than of the
terminal. `ClickTracker` is **clockless by construction** — told `now` rather than reading one — which is what makes
the whole rule testable without a fake clock.

- `console.py` — the screen a *child program* paints on, and the mirror image of `terminal.py`: there, bytes from the
  user become events; here, bytes from a program Navigator started become cells. The emulation is `pyte`; what lives
  here is the translation. **A terminal will not give its cells back** — no escape sequence returns screen contents, and
  `navkit/DESIGN.md` records every route that was surveyed and rejected — so the only way to show a program's output
  behind the panels, as the DOS original did by reading video memory, is to have been the one who received it.
  `ConsoleScreen` keeps a `ScreenBuffer` mirror in step with pyte's sparse grid, converting only the rows pyte marks
  dirty; `seed_from_host` makes a best-effort grab of whatever was on screen *before* Navigator started, from tmux,
  kitty or `/dev/vcsa`, and usually fails, which is expected.
- **The one clock is `Application.call_every(seconds, async_callback)`**, returning a cancellable `Repeat`. It may be
  called before the loop runs (a tree is mounted from the constructor) and every tick is *posted* and awaited inside a
  dispatch, so it is painted with its batch and a failure stops the app like a handler's. *Timers: through the queue*
  in `navkit/DESIGN.md`.
- `process.py` — `PtyProcess` runs a child on a pty this application owns, reading it through `loop.add_reader` and
  sizing it with `TIOCSWINSZ` on the master (the kernel raises `SIGWINCH` on the child itself, so nothing signals it by
  hand). `run_on_terminal` is the escape hatch for a program that needs the real terminal, and its output is *not*
  captured — which is the trade the whole module exists to avoid.

Things to know before touching this layer:

- **A write is checked against the annotation beside the declaration.** `width: int = reactive(0)` refuses a `str` with
  `ReactiveTypeError`, which is a `TypeError` too. Only *writes* — a value a binding or a `computed` produced is not
  checked, because it came from values that were. An attribute annotated `Any`, or not annotated, or annotated with a
  name that only exists under `TYPE_CHECKING`, is unchecked; that is the opt-out, and there is no flag. The erasure is
  shallow, so `frozenset[str]` checks the `frozenset` and not the strings.
- **Assigning a *value* over a live binding raises**, deliberately: call `unbind()` to take an attribute back by hand.
  Assigning another `bind()` expression is fine and replaces the old one. This is why `Widget.layout()` checks
  `is_bound()` — without it the first `SIGWINCH` would take down every declaratively-sized widget in the tree.
- **A `bind()` expression assigned to a non-reactive attribute is silently stored**, because there is no descriptor to
  notice it. A `computed` target raises, and an unknown `Widget()` keyword raises, so what is left is a typo on a plain
  attribute; the `Binding` repr (`<unassigned binding ...>`) is what gives it away.
- **A computed may not write.** The write path refuses if any frame on the tracking stack is a computed, which is what
  makes it safe to pull a stale value in the middle of composing a frame. Use an `effect` for anything impure.
- **A collection has to be replaced to count as changed.** `entries.append(x)` followed by `self.entries = entries`
  propagates nothing, because the equality guard sees the same object. Build a new list.
- An object carrying reactive attributes needs a `__dict__`, so slotted value types (`Style`, `DirEntry`) cannot host
  them.
- **A console screen is not reactive and cannot be.** It is a great deal of mutable state that changes together, so
  `Console.revision` is one counter standing in for all of it: `render()` reads it for the dependency and the output
  callback bumps it. Anything mutating the screen behind the widget's back — scrollback, a reset — has to bump it too.

- `stylesheet.py` — the `.nss` language and its lookup engine. CSS in shape (selectors, brace-delimited declarations, a
  cascade ordered by specificity) and not in scope: every declaration either names a `Style` field or names a property
  the widget interprets. `parse()` reads one sheet, `load()` merges several in order so a theme can redefine another's
  variables. Selectors are `Panel` (by class *name*, subclasses included), `.tag`, `:state` (any truthy attribute, including
  navkit's own `focused`, `focus_within`, `hovered` and `inert`), `:not(compound)`,
  `#name` and `Panel::part`, with descendant and child combinators. Specificity is CSS's
  `(names, classes + states, types)`, ties break on source order, and there is no `!important`.

Things to know before touching the style layer:

- **A widget's `style` is a `computed`, not a value you assign.** It cascades in four levels: the parent's resolved
  style (so appearance inherits), then matching `.nss` rules, then `inline_style`, then whatever `render()` passes
  straight to a drawing primitive. Assigning `widget.style` raises; author through `inline_style` or `merge_style()`.
- **`inline_style` is partial.** `"bg: red"` overlays one property and leaves the rest inheriting; it is not a whole
  `Style`. A `Style` is accepted and becomes the seven declarations it makes.
- **`classes` is a `frozenset` and `inline_style` is replaced, never mutated** — the reactive layer only counts a change
  when a collection is replaced. Use `add_class` / `remove_class` / `merge_style`.
- **Only a *reactive* attribute restyles.** `:state` matches any truthy attribute, but a plain one is read outside the
  dependency graph: it matches the first time and never invalidates afterwards.
- **Widget properties do not inherit**, only `Style` fields do. `border: double` on a panel does not give its children a
  frame. A non-`Style` declaration is declared on the widget that reads it — `icons = StyleProperty("auto",
  values=("auto", "none"))` — which names it, defaults it, and says what a sheet may set it to; the parser rejects both
  an unregistered name and a value outside the declared vocabulary, each with its `.nss` line. The type is the
  default's own, so `StyleProperty(0)` takes a number. `stylesheet.register_property()` is the bare form underneath,
  for a key no attribute is held for.
- **A sheet cannot be parsed before the widgets it styles are imported**, which is the price of that check. This is why
  `navigator/__main__.py` parses its default sheet in `default_scheme()` on first use rather than at import: the sheet
  names `icons` and `Panel` is defined further down the file.
- `navkit/DESIGN.md` records why each of these went the way it did, including the parts that were measured rather than
  argued. Add to it rather than re-deciding.

- A widget may carry its own sheet in `stylesheet`, governing the subtree under it; the nearest one wins and the search
  ends at the application's. `Manager` uses this, so the desktop is styled with or without an application around it.

### `navml/` — markup language + widget library

- `*.nml` markup language: QML for the architecture (a declarative tree, `id`s, properties that are re-evaluated
  expressions), Kivy for the syntax (blocks made by indentation, no braces, no semicolons, one property per line)
- Parser translating `.nml` into a node graph — **written**, `navml/parser.py`
- Code generator traversing that node graph to emit a Python class — **written**, and reached through
  `python -m navml build [PATH ...] [--check]`
- Rich widget library (windows, buttons, menus, labels, standard event handlers) modelled on Borland's TurboVision
- `navml/_merge.py` — **written**, and the rest of this section is about it.

**Both halves of a component are optional, and a component is up to four files.** `button.nml` is the markup;
`button_nml.py` is what the generator emits from it, tracked and shipped; `button.py` is the hand-written handlers;
`button.pyi` is the generated stub. Markup alone, Python alone and both are three peer shapes, and
`from navml.widgets.dialog.button import Button` is the same line for all three — a component can move between them without
that line changing and, going from Python to both, without its `.py` changing either. `navml/widgets/` carries one
example of each and they are all real widgets now: `spacer` and `control` are Python alone, `field` is markup alone,
`button` and `label` are both, and `dialog` is both *and* derived from `modal`, which is itself both.
`dialog` is also the one whose *children* raise the events its hand-written half handles, and it pins the
`on_<id>_<event>` convention below — which a dialog with an OK and a Cancel in it does by being one.

**And a component is a directory.** Those four files live in `navml/widgets/dialog/button/` beside an `__init__.py` that
re-exports the class (and any event it declares — `button` publishes `ClickEvent` too), so the import line is
unchanged and the files that make one component sit together. **The files repeat the directory's name**, because
everything navml prints is a bare filename and `packaging/linux/build.sh` finds a component's siblings by stripping
`_nml.py`. **Every component gets a directory, Python-only ones included**, so gaining a markup half adds files rather
than moving them. **The library registers, not the component**: `navml.register("navml.widgets")` is still the one
call and `navml/_merge.py`'s `_registered()` walks up the dotted name, so a component directory's `__init__.py` is a
docstring, an import and an `__all__` with no line to forget. **The flat shape stays legal** — nothing in the loader
requires a directory, and `tests/test_nml_build.py`'s `package` fixture is deliberately flat so it keeps being
exercised. Two things underneath had to learn the rule and both failed *silently* before they did: `build.order()`
keys its graph on the name a document is imported by (the directory) as well as the module's own, or every dependency
edge vanishes and a cold build compiles in alphabetical order; and `build._forget()` evicts the component's package
along with its module, or a second build in one process resolves later documents against the class from before it.
*A component is a directory* in `navml/DESIGN.md` has the whole of it.

Things to know before touching this layer:

- **The merge is one line**, `handwritten.__bases__ = (generated,)`, and the generated class is always the base —
  forced by the contract that a hand-written `__init__` calls `super().__init__()` and then finds every id live.
- **The hand-written half never names the generated class.** `class Button(Widget)` is what a Python-only component
  says too, and that is exactly why: it is what lets a component gain or lose its markup half without being edited.
  The base it names is the one the markup names, and the loader refuses the pair if the two disagree — CPython does
  not, it drops the declared base from the MRO in silence.
- **A class based only on `object` cannot be spliced at all**, so `class Button:` is not an option: the assignment
  fails with `deallocator differs from 'object'`.
- **The finder keys on `button_nml.py`, never on `button.nml`.** Both halves are then ordinary `.py` files that reach a
  wheel automatically, so the import path cannot be broken by a missing `package-data` entry. The markup ships anyway,
  as source to read and rebuild from — which is one `"*" = ["*.nml", "*.pyi"]` entry in
  `[tool.setuptools.package-data]`, setuptools' every-package key, merged with the exact keys beside it. It is spelled
  that way rather than per package because a component is a directory: markup and stubs live one package deeper than
  the library and these keys do not inherit, so naming them would be one line per component and a silent hole the
  first time one was forgotten. **A component is a module, never a package**, and the finder now refuses to claim one
  — a stale flat `button_nml.py` left beside a `button/` directory would otherwise make it splice a re-exported class
  onto a generated base from before the move.
- **A component module must never be a test module, a `conftest.py` or a pytest plugin.** pytest's assertion rewriter
  consults `PathFinder` directly and bypasses `sys.meta_path`, so the splice would not happen and the component would
  come up as a plain `Widget` subclass.
- **A component package registers itself** with `navml.register(__name__)` in its `__init__.py`. Importing anything
  inside a package runs that file first, so there is no ordering hole; a `.pth` file would not do, because the `.deb`
  and `.rpm` mount their tree on `PYTHONPATH` rather than as a site directory.
- **The generated class constructs its children inline in `__init__`, not in a `_build()` method.** A shared method
  name would be overridden by a derived component's, so the base's children would never be built and the derived one's
  would be built twice.
- **A document says where its types come from in Python's own words** — `from navml.widgets.dialog.label import Label` at the
  top of the `.nml`, copied into the generated module verbatim. `import *` and `__future__` imports are refused.
  Components are the case it exists for, but any import is legal, and it is worth taking: a declared type is only
  checked at run time if the generated module can resolve it (`_resolve_annotation` silently answers *unchecked* and
  caches that), and a `style:` block can only be validated against a property whose widget has been imported.
- **Markup writes a bare `Button:` to extend `Widget`, never `Button(Widget):`.** The parenthesised form names a type,
  and a type a document names is one it imports — so `Button(Widget):` means whatever the document imported under that
  name. The hand-written half still has to spell it, `class Button(Widget)`, because a Python class with no bases is
  `object` and cannot be spliced.
- **An event a component raises is declared beside it, and the widget says so.** `navml/widgets/dialog/button/button.py` declares
  `class ClickEvent(Event)` next to `class Button` and sets `emits = (ClickEvent,)`; a mouse press and a Space press
  both go through one `press()` that emits it, so a listener never learns which route fired. Markup may declare one
  instead with `event ClickEvent` (root block only, no fields), and **which half declares it follows which half emits
  it** — a markup `event` line puts the class in the generated module, which the hand-written half may never name. A
  component may not do both. `navml/DESIGN.md`'s *Declaring an event* has the whole of it, including why this settles
  the widget-alias question as no.
- **A handler in markup is one line, and it takes one argument called `event`.** Anything longer — a branch, a loop, a
  `try`, two statements in sequence — is a method in the hand-written half that the markup line calls
  (`on_click: self.confirm_quit()`); one line keeps a handler body going through the same expression compiler and the
  same name-resolution table a property expression does, and keeps a failing body one emitted statement with one
  `# button.nml:12` on it. The argument is fixed at one and named by the language because markup has no parameter list
  and should not grow one — a hand-written handler may name it anything, and navkit's own hooks already all say
  `event`. Two things follow: **`event` is reserved** alongside `self`, `root` and `parent`, and **a handler compiles
  to a one-statement `def` in the generated `__init__`, closing over its widget** — not a lambda, because
  `on_key: self.title = event.key` is an assignment and a lambda cannot hold one; not a method, because a derived
  component's generated class would shadow its base's by the same naming rule. **A markup handler always consumes** —
  the generated function ends `return True`, because the alternative leaves a markup-only component unable to bind a
  key without growing a Python half, whereas this one only sends the rarer watch-without-consuming case there. The
  body, its argument and its return value are settled.
- **A child's event reaches the hand-written half under `on_<id>_<event>`, and the generator writes both ends.** For
  every id'd child and every event its class declares in `emits`, the generated class declares a **no-op handler
  returning False** and assigns it (`self.cancel.on_click = self.on_cancel_click`); the hand-written half overrides it
  as an ordinary derived class. `Event` carries no sender and `ClickEvent` is fieldless, so this is the only thing that
  can say *which* child spoke — and the stub is what makes it free. Three consequences worth knowing: the generated
  file never reads the sibling `.py` to decide what to emit, so there is **no `--check` drift**; a stub nobody
  overrides **declines**, so the component's own `on_click` still catches every child the `.py` did not name; and
  `check_handlers` enforces `async def` on both halves for free. An explicit `on_click:` line on that child
  **suppresses** the convention, and the method such a line routes to is **never** named `on_*` — the prefix means
  navkit found it under `event.handler`, and `self.info.on_click = self.on_click` would be called twice by one walk.
  Renaming an `id` would silently orphan the method, so the generator refuses an `on_<X>_<event>` in the `.py` whose
  `X` names no id.
- **Everything the generator emits for itself is underscored** — `_bind`, `_reactive`, `_is_bound`, `_Any`, `_Widget`.
  The generator consequently reserves no word: a document may import any name at all and gets exactly what it asked
  for. The language reserves exactly one, `event` above, and the parser rejects an import of that name rather than
  letting it be shadowed inside handler bodies alone.
- **A component package's `__init__.py` must not re-export eagerly.** The code generator reads `declarations(cls)` off
  the classes a document names, so generating a component really imports the ones it uses; eager re-export would mean
  importing any one component imported every one, and a cold build could generate nothing. `navml/widgets/__init__.py`
  re-exports through a PEP 562 module `__getattr__` with a `TYPE_CHECKING` block beside it for the real types.

`navml/DESIGN.md` records why each of these went the way it did, *The two halves of a component* for this layer, and
records the decisions taken ahead of the parser and the generator — how a property expression
(`width: parent.width // 2`) is compiled into the one-argument lambda `bind()` expects, by rewriting the expression's
free names on the syntax tree rather than by formatting strings; and what markup still cannot say, which is four things
and each of which blocks converting `Manager`. Read it before starting the parser or the generator, and add to it rather
than re-deciding.

### `navigator` / `nav` — the file manager application

The application is three parts. **`navigator/widgets/` holds the screens**, one directory each — `shell/` (the root:
the bars, the console and the desktop), `manager/` (the file manager window), `panel/` (whose `panel.py` carries
`DirEntry` beside `Panel`, and whose `__init__.py` re-exports both), `menubar/`, `keybar/` and `console/` — and it is
a registered navml component package with lazy re-exports.
**`navigator/scheme.py` holds the sheet**: `load_scheme`, `default_scheme`, `theme_names` and where the `.nss` files
are. **`navigator/__main__.py` holds the command line**, the terminal it hands to navkit, and the `Navigator`
application subclass.

**Why the widgets are not in `__main__.py` any more**: that module is what the command runs, so it is already in
`sys.modules` as `__main__`, and `from navigator.__main__ import Panel` imports a *second* copy of it — a second
`Panel` class and two of everything the two copies then disagree about. A widget a document names has to be importable
by its own name.

**`load_scheme()` imports `navigator.widgets.panel` before it parses**, and that import is the whole reason it has a
body. A sheet is checked against the properties widgets declare and a widget declares them by its class body running,
so `navigator.nss`'s `icons: auto` is an unknown property until `Panel` has been imported. While every screen lived in
one module this was a rule about where to put the parse; now it is a rule about what to import before it, so the import
is inside the function rather than left to whoever calls.

**`manager.py` is the worked example of a converted screen**: the document holds the tree and the geometry, and the
Python holds the keys, `active_panel` and the two paths markup may not bind. `shell.py` holds `toggle_console` and the
console's seeded `cwd`. The other screens are still hand-written and move next. `Panel` is the one to read before
converting another — it assigns `path` and lets the listing, cursor and scroll follow, which is the model markup wants, and it is
also the widget that showed why a navigated property is seeded rather than bound.

- `Manager` window with two file-listing panels on a `Desktop`, and the `Console` behind the desktop covering the
  band between the bars. Ctrl+O hides the desktop, which is one reactive flag and one `visible` binding; the menu bar
  and key bar are simply left alone, which is why they stay painted over the output and why this is DOS Navigator's
  Ctrl+O rather than Midnight Commander's. `toggle_console` hands the console the keyboard **in the same call that
  flips the flag, never from an effect** — an effect runs after the whole batch is dispatched, so a Ctrl+O and the
  keystroke behind it would be routed by a focus that had not moved yet — and hiding the console again re-activates
  the top window, which hands the keyboard back to exactly the widget that had it. The console holds the keys only
  while a command the command line sent is running (`Console.busy`); idle, it declines them and they reach the
  command line under it. Closing the last window
  (`Desktop` raises `EmptiedEvent`) leaves the console showing and focused, and opening any window (`OpenedEvent`)
  hides the console again so the window is seen -- no command that opens one checks `console_visible` itself. `Console.can_focus` is set in `__init__`, never in the class body, where it would shadow the
  reactive descriptor with a plain attribute. The console reports the child's cursor through `cursor_position()`, so
  the caret is the terminal's own
- **Keys are commands, bound in key tables** (`navkit/commands.py`; *Commands and key tables* in `navkit/DESIGN.md`).
  A command is an `Event` subclass (`class MakeDirectory(Command)`, handled by `on_make_directory`), emitted from
  the focused widget up to the application. A key table is a class attribute, `keys = {"f7": MakeDirectory}`, or a
  markup `keys:` block (root block only). It is consulted at each step of the focus path before that widget's
  `on_key`, and the application's table before the tree, never under a modal. **The nearest widget with the
  handler decides whether the command is enabled**, through `enables(command)`, and a command nobody handles is
  disabled. A disabled command's key falls through as if unbound. `Navigator.keys` holds Ctrl+O, F1, F10 (the
  menu), Alt+X, and Enter/Home/End for the command line; `manager.nml` holds Tab, Alt+R/Ctrl+R and F2–F8; `Desktop.keys` holds the window keys;
  `dialog.nml` holds Esc, Enter and Tab. Navigator's commands are in `navigator/commands.py`, the library's in
  `navml/commands.py`. Alt+X is on the application because a way out cannot live on a window the user can close, and
  it is `Quit(desktop=True)`, which `Navigator.enables` vetoes while a running command's console is over the
  windows, so the child gets Meta+X. **The key bar reads its captions off the bindings** (`app.bindings()`) and greys a disabled command in
  DOS Navigator's `$bar-disabled` slot; a click on a caption runs its command. **While Alt, Ctrl or Shift is held the
  bar is that modifier's row** (`StatusDef hcFilePanel`'s `-`/`+`/`:` items, bound in `manager.nml`), read off
  the reactive `Application.modifiers`. Only a terminal speaking the kitty keyboard protocol reports a held
  modifier; `Terminal` pushes it without asking, `NAVKIT_KEYBOARD=legacy` turns that off, and *The held modifier* in
  `navkit/DESIGN.md` has the rules. `Console.on_key` still keeps the
  scrollback and sends the rest to the child. There is no `console_visible` check in any of the widgets — the
  console holds the focus while it is showing, and the focus path decides. `Navigator.on_mouse_click` returns False
  while `app.modal` is set
- **And so do mouse gestures, by the same rule.** `Panel.on_double_click` enters the clicked row — a directory, or
  `..` — because it needs nothing but the panel it lands on, and routing by position is what picks which panel. It
  needs no `console_visible` check either: the desktop's `visible` is bound to that flag and `dispatch_mouse` skips an
  invisible child. What stays on `Navigator.on_mouse_click` is what genuinely needs the desktop — activating the other
  panel on a press, the wheel, and the console's scrollback
- View and Edit file windows
- File operations over the selected files
- Pluggable filesystem handlers so operations work over ssh, smb, inside zip archives, etc.
- Plugin system for third-party extensions
- Look and feel carefully recreated from Ritlabs' classic DOS Navigator (including its TETRIS easter egg)

## Working conventions

- Keep `navkit` free of any dependency on `navml` or the application; keep `navml` free of any dependency on the file
  manager. The dependency direction is strictly one-way.
- Prefer recreating original DOS Navigator behaviour over inventing modern alternatives when the two conflict — fidelity
  is the point of the project. The **one standing exception** is the Nerd Font icon gutter in `Panel`, which the
  original had no glyphs for; it was taken deliberately, is on only where the font is known to exist, and is reversible
  with `icons: none` or `--glyphs unicode`. `navkit/DESIGN.md` records the argument — don't re-litigate it, and don't
  read it as licence for the next modern flourish.

P.S. NEVER suggest to commit code, unless you are explicitly asked to do so.