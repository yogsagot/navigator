---
name: console-command-line
description: The console and the command line -- navkit/console.py (pyte, ConsoleScreen, alternate screen, query answers), navkit/process.py (PtyProcess), navigator/subshell.py (persistent $SHELL, OSC 6973 marks, silent cd, held-back prompt, completion, history, atuin), the Console widget and Ctrl+O, the CommandLine (TCommandLine), Tab completion and CompletionList, running a program with every key, executing a file, Ctrl+Enter insert name, console selection. Use when touching anything that runs a command or shows its output.
---

# The console and the command line

## Owning the screen

**A terminal will not give its cells back** -- no escape returns screen contents -- so the only way to show a program's
output behind the panels, as DOS did from video memory, is to have received it. `navkit/console.py`: `ConsoleScreen`
keeps a `ScreenBuffer` mirror in step with pyte's sparse grid, converting only dirty rows; `seed_from_host` grabs the
pre-start screen from tmux, kitty or `/dev/vcsa` and usually fails, which is expected. `pyte` is the one run-time
dependency and it is load-bearing.

- `_Screen` adds what pyte lacks: the **alternate screen** (47/1047/1049), **answers to queries**
  (`ConsoleScreen.respond`: cursor position, device attributes), dropping a private CSI pyte would crash on (`mc`'s
  `CSI ? Pm r`) or misread (`CSI > 4;2 m`), and a parser rebuilt if pyte raises anyway (its parser is a generator one
  exception closes for good).
- `navkit/process.py`'s `PtyProcess` runs a child on a pty via `loop.add_reader`, sized with `TIOCSWINSZ` on the master
  (the kernel signals the child). `run_on_terminal` is the escape hatch whose output is *not* captured.
- **A console screen is not reactive**: `Console.revision` stands in; anything mutating it behind the widget must bump it.

## The Console widget and Ctrl+O

The `Console` covers the band between the bars behind the desktop. Ctrl+O hides the desktop (one reactive flag, one
`visible` binding); menu and key bars stay painted -- DN's Ctrl+O, not mc's. `toggle_console` hands the console the
keyboard **in the same call that flips the flag, never from an effect** (an effect runs after the batch, so Ctrl+O and
the next key would be routed by a stale focus); hiding it re-activates the top window. `Console.can_focus` is set in
`__init__`. The console reports the child's cursor through `cursor_position()`. Shift+PgUp/PgDn scroll back.
`Console.on_key` keeps the scrollback and sends the rest to the child.

- **An idle console takes no keys** (it holds them only while a command the line sent runs, `Console.busy`); typing
  reaches the command line.
- **While a program runs it gets every key, Ctrl+O included** (`Shell.program_has_keys`, consulted by `Shell.enables`
  and `Navigator.enables`, disables every command, so F10 reaches `htop`/`mc` and Ctrl+O is `mc`'s and `nano`'s). Arrows follow its DECCKM
  (`encode_key(..., application_cursor=)`, `SS3` vs `CSI`, xterm modifier parameter); its mouse reports go back down
  (`encode_mouse`, modes 9/1000/1002/1003, SGR 1006). Alt+X is `Quit(desktop=True)`, vetoed by `Navigator.enables`
  while a running command's console is over the windows.
- The console selects output with a drag or double click unless a program tracks the mouse (reversed, cleared by new
  output or a scroll); Ctrl+Ins copies it -- `Shell.on_key` asks the console before the command line.

### Without the internal terminal (mc's Ctrl+O)

System Setup's *Use internal terminal* (`SETTINGS.system.internal_terminal`, a departure from DN) is on by default.
With it off, Ctrl+O and *ESC for user screen* call `Shell.relay_terminal()` instead of showing the console:

- **What relaying does.** `Application.release_terminal` takes Navigator out of full-screen mode, and
  `Subshell.start_relay(terminal.write_bytes)` sends everything the console would show to the real terminal. That
  includes the prompt, shown once (`_relayed`: `prompt`/`typed`/`other`). The screen stops answering queries,
  because the real terminal does.
- **Keys and the pty.** Keys go raw through `Shell._relayed_input` to `Subshell.relay_input`. `Console.relayed` sizes
  the pty to the whole screen.
- **Ctrl+O takes the terminal back** (`0x0f`, or kitty's `CSI 111;5u`), unless a command the line sent is running:
  that command gets every key. `end_relay()` then clears an abandoned typed line with Ctrl+E Ctrl+U, and the panel
  follows a `cd`.
- **A line entered at the relayed shell** clears `_ready` until its next prompt, so nothing is typed into a program
  the user started there.
- **A command from the line runs relayed** and comes back when it finishes (`_relayed_for_command`).
- **The shell exiting ends the relay** (`Subshell.on_exit`).
- **No real tty** (headless, tests): it falls back to the console.

## The subshell

**Commands run in one persistent `$SHELL`** (`Subshell`, owned by the `Console`): bash and zsh load the user's rc then a
hook; anything else runs bash or `sh`. The hook prints private OSC marks (`ESC ] 6973;<nonce>;A|B|D` ...) for prompt
position, command finished, and `$PWD`; other marks: `C` (completion), `H` (history), `U` (atuin keys), `R` (atuin
choice), `O` (reveal output).

- **The shell's own prompt is held back** and painted only when a command is sent, so the log reads `prompt$ cmd`, the shape DN's `/dir>cmd` echo had.
- The panel's directory reaches the shell by a **silent `cd`** (leading space, output swallowed) only when they differ;
  `Subshell.sync` sends it whenever the active panel moves while idle. A `cd` typed on the line moves the active panel
  when the command finishes (`CommandFinished`, posted from the pty reader to `Navigator.on_command_finished`).
- While a command runs the console is up and holds the keys; afterwards the windows return and both panels re-read --
  unless Ctrl+O had put the console up.
- `Navigator.on_start` starts the shell at once on a real tty (headless, the first command does).
- **Every child carries `NAVIGATOR=1`** (`navkit.process.MARKER`, set by `PtyProcess.environment()`), and `main()`
  refuses to start under it -- so `nav` typed inside Navigator says so and exits 1, while another terminal is
  unaffected (no lock file). `--help`, `--version` and `--list-themes` still work; `NAVIGATOR= nav` forces a nested copy.
- Queries are answered in order -- `Subshell._completions` is a queue (two keys in one read send two queries).

## The command line

DN's `TCommandLine` (`navigator/widgets/shell/command_line/`, a Python-only `InputLine`), one row above the key bar,
docked after `KeyBar` in `shell.nml`, in the hard-coded `$0F`/`$07`.

- **Its prompt is the user's own shell prompt**, colours and all -- a departure (`SetDirShape` drew `<dir>>`, which
  survives as the fallback `Shell.command_prompt` for `sh` and before the shell has printed a prompt in the active
  panel's directory; `Shell.command_prompt_cells` compares `Console.prompt_cwd`). The hook *brackets* whatever `PS1` the
  rc left; `prompt_cells()` decodes the held-back bytes on a one-row `ConsoleScreen`, so a multi-line prompt shows its
  last line.
- **It never holds the keyboard**: a key the focused widget declines walks up to `Shell.on_key`, which types it there
  (DN's `ofPostProcess`); `Shell.cursor_position` puts the caret on the line.
- Enter, Home, End are `ExecuteCommandLine`/`CommandLineHome`/`CommandLineEnd` on the application's table, **disabled
  while the line is empty** so the key falls through to the panel. A widget whose `edits_text` is True (quick search,
  the editor) makes Enter/Home/End/Tab and pastes step aside. Esc clears, Ctrl+E/Ctrl+X walk `HISTORY["command"]`, a
  paste lands on it.
- **Tab completes** (`CompleteCommandLine`) with text on the line: ` __nav_complete <base64> <point>`, answered by a `C`
  mark -- bash through `compgen` and the command's `complete` spec, zsh through its tables and globbing only (compsys
  cannot be asked outside ZLE); `sh` cannot, and Tab stays the panel's. One candidate ends the word (`/` or a space,
  specials backslashed), several that agree extend it, the rest drop a `CompletionList` (a `HistoryList`,
  `dims_behind = False`). Typing with it open goes on into the line; the list narrows and is refilled (so `/`
  descends); a blank or Backspace past the word closes it.
- **With the console up and idle it stands for the terminal** (`Shell._console_is_the_terminal`): Up/Down walk the
  shell's history (` __nav_history`, `H` mark, `fc -lnr`); where the rc binds Up or Ctrl+R to atuin (detected once by
  `__nav_keys`, `U` mark) those keys run `atuin search -i` on the console as atuin's binding does (descriptors swapped,
  choice back in an `R` mark, `__atuin_accept__:` runs it). Such a line is sent in the queue's **`"reveal"` mode**:
  hidden until its `O` mark, holding keys (`busy`), finishing no command. With panels up, Up is the panel's and Ctrl+R
  re-reads.
- **Enter on an executable runs it** (`Panel.choose` emits `ExecuteFile`; `Shell.on_execute_file` runs `./name`); a plain
  file is left alone.
- **Ctrl+Enter puts the entry's name on the line** (`InsertName`, DN's `cmInsertName`: a space after, one before if the
  caret follows a word, `..` giving the directory); Ctrl+Shift+Enter the whole path, Ctrl+double-click the same (DN's `_CtrlEnter`); Alt+Enter
  bound beside it (mc's key) for terminals that send Ctrl+Enter as Enter.
- **Space tags while the line is empty** (`ToggleMarkBySpace`, bound in `manager.nml`, handled and gated by `Shell`).

## The character table (Ctrl+B)

Utilities > *Character table* (DN's *ASCII Table*, `cmASCIITable`, `kbCtrlB` in `Navigator.keys`): `Shell.ascii_table`
opens `AsciiChart` (`shell/ascii_chart`) and puts the character picked -- its CP437 glyph, `│` for 179 -- on the
command line with `CommandLine.insert`, where DN put it back as a key press the line took; code 0 is nothing.
Disabled with *Hide command line*. Inside an editor Ctrl+B is the start of its ^B^V chord, so the editor keeps it
(its own Ctrl+P opens the same chart for the text). Under tmux, Ctrl+B is tmux's prefix and never arrives.

## User screen (Alt+F5) and Refresh display

- **≡ > User screen, Alt+F5** (`ShowUserScreen`, DN's `cmShowUserScreen`; Ctrl+O is its `cmShowOutput`):
  `Shell.on_show_user_screen` shows the console and overlays `UserScreenPeek`, a modal layer that paints nothing,
  does not dim, and ends on the next key or click -- which goes nowhere else -- and the windows come back. Already
  showing, it stays; with *Use internal terminal* off it is Ctrl+O's hand-over.
- **≡ > Refresh display** (`Refresh`, DN's `cmRefresh`): `Navigator.on_refresh` -> navkit's `Application.redraw()`,
  which forgets the front buffer so the next frame sends every cell -- for a screen another program wrote over.

## Screen grabber (Shift+Alt+Ins)

`ScreenGrab` (global key; ≡ > Screen grabber), DN's `cmExecGrabber` -> `ScreenGrabber`: `Shell.screen_grab` says
DN's `dlGrabWelcome` once a session, then overlays `shell/grabber.ScreenGrabber` -- modal, undimming, painting the
cells already under its rectangle with `reverse` flipped and keeping their text (`surface.get`, continuation cells
skipped). `TGrabber.HandleEvent`'s keys: arrows move (Ctrl: 8 across, 4 down), Shift+arrows size from the bottom
right, PgUp/PgDn/Home/End to the edges, clamped on screen and at least a cell. Enter copies the rows joined by
newlines through `app.copy_to_clipboard`; Esc nothing. The rectangle is remembered (`grabber._last`, DN's
`Top`/`Bot`). A departure: the screen under it is live, not a frozen copy.

## The calculator (Ctrl+F6)

`Calculator` (bound in `manager.nml`; Utilities > Calculator from anywhere) is `Shell.on_calculator`: DN's `InsertCalc`,
**one** `CalculatorWindow` (`shell/calculator_window`) on the desktop -- a dialog in a `Window`, DN's
`InsertWindow`, 49x15 at (10, 5), dialog colours from `navigator.nss`. A window has no dialog keys of its own, so it
binds Esc/Enter/Tab/Shift+Tab to navml's `Cancel`/`Default`/`SelectNext`/`SelectPrevious` and answers them itself
(Tab cycles its own `focusable()`), and walks Alt+letter over its controls. The indicator's five rows (decimal, hex,
binary, octal, exponent; *Error*; *Overflow*) follow the line through an effect. Enter evaluates: the line becomes
the value, selected, and `CalcLine` lets a digit replace it and anything else carry on from it. *Copy* puts *Copy
As*'s form through `app.copy_to_clipboard`. Esc/*Close* record the line in history `calc`. The sums are
`navigator/calculator.py` (`PAR.PAS`'s numbers, operators and functions; **arithmetic precedence, a departure** --
DN's put `^` below `*`; integer forms 64-bit where DN's were 32). Button ids must not shadow methods (`evaluate`).

## Read when

| Reference | Read when |
|---|---|
| `reference/console.md` | why the screen is owned, why pyte, the mirror, what owning the pty costs |
