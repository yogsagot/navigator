---
name: navkit-terminal
description: The tty layer (navkit/terminal.py, capabilities.py, clipboard.py) -- raw mode, the alternate screen, mouse and bracketed paste, InputParser and escape timeouts, the kitty keyboard protocol and held modifiers, keypad and Ctrl+H/Backspace decoding, TerminalInfo detection and NAVKIT_* overrides, OSC 8 hyperlinks, the OSC 52 clipboard, and tools/keyprobe.py. Use when a key arrives wrong, a terminal behaves differently, or adding a terminal feature.
---

# The terminal layer

- `Terminal` owns the tty (raw mode, alternate screen, mouse tracking, bracketed paste, autowrap off, application keypad)
  and restores it in `Application`'s `finally`. `InputParser` is fed incrementally and keeps undecodable tails. **A lone
  `ESC` is ambiguous**: the parser reports `pending_escape` and the application resolves it with `ESCAPE_TIMEOUT`.
- `TerminalInfo` (`capabilities.py`) is what the terminal supports (`colors`, `alt_screen`, `mouse`, `bracketed_paste`,
  `title`, `keypad`, `hyperlinks`, `glyphs`, `palette`, `bidi` -- `NAVKIT_BIDI`, the `navkit-bidi` skill; `Terminal`
  sends `CSI 8 l` so VTE reorders nothing while Navigator owns the screen). Detection is conservative -- sixteen colours unless `COLORTERM`
  says otherwise; `NAVKIT_COLORS` (`truecolor`, `256`, `16`, `8`, `mono`, a number) overrides and outranks `NO_COLOR`.
  Colour/palette/glyph decisions are the `colours-themes-glyphs` skill.
- **Lending the terminal out.** `Terminal.suspend()`/`resume()` drop and restore the screen modes (alternate screen,
  mouse, paste, kitty flags, keypad, autowrap) but **keep raw mode**. `stop()` after a suspend restores termios only.
  `Terminal.write_bytes()` writes a relayed program's bytes unchanged.
  - `Application.release_terminal(on_input)` suspends, stops painting (`_render` returns early) and hands every raw
    byte read to `on_input`. Whatever `on_input` returns goes to the parser, as the bytes after the reclaiming key.
  - `reclaim_terminal()` resumes and forces a full repaint (`_front = None`).
  - The loop keeps running meanwhile: timers, pty output, resizes.
  - Navigator uses this for mc's Ctrl+O (`console-command-line`).

## Keys

- **The kitty keyboard protocol** is pushed without asking; `NAVKIT_KEYBOARD=legacy` turns it off. Only it reports a
  held modifier (`Application.modifiers`, which the key bar reads).
- **Super** is `KeyEvent.super_` (named `super+…` after ctrl, alt, shift; never printable), read only from a kitty-form
  key -- legacy xterm spends that modifier bit on Meta. Before it was read, Super+1 arrived as a typed `1`.
- **Ctrl+H vs Backspace**: a legacy terminal sends Ctrl+H as 0x08, which navkit reads as Ctrl+H only once the tty's
  erase character (`Terminal.erase`, termios `VERASE`, read before raw mode) says Backspace is 0x7F, and as Backspace
  otherwise (`InputParser.ctrl_h`).
- Keypad operators are named `kp_plus`/`kp_minus`/`kp_multiply`/`kp_divide` (`char` kept), from kitty codes or from
  `SS3` under application keypad mode. xfce4-terminal (VTE) and PyCharm send Gray `+` as a bare `+` even then (named
  `plus`); only Ghostty told them apart, which is why Navigator binds the plain keys too.
- **With Num Lock on, a keypad operator's Ctrl is lost or moved.** VTE (xfce4-terminal) drops it: Ctrl+Gray `*` is a
  bare `*`, byte for byte the plain key's, so nothing can bind it -- with Num Lock off it is `ESC O 5 j`
  (`ctrl+kp_multiply`). Ghostty keeps it but may send the plain character's code (`CSI 42;5u`, `ctrl+*`), so bind
  `ctrl+<char>` beside `ctrl+kp_*` (Navigator's Ctrl+Gray `*` does). VTE's checked with keyprobe; Ghostty's inferred
  from binding `ctrl+*` making it work.
- A terminal without the kitty protocol sends Ctrl+Enter as Enter; Ghostty keeps Ctrl+Enter and Ctrl+Shift+Enter
  unless unbound (`keybind = ctrl+enter=unbind`). xfce4-terminal eats Alt+E/F/V/T/B/H unless menu access keys are off.
- **Find out what a terminal sends**: `./venv/bin/python tools/keyprobe.py [--legacy] [--no-mouse]` (`q` twice or
  Ctrl+C quits) -- e.g. whether Ctrl+Shift+V arrives as a paste or a key.
- **`Application.bell()`** rings BEL now: `Terminal.bell()` queues it and the application flushes at once, since an
  unchanged frame writes (and flushes) nothing. A terminal without `bell` (a test's) is skipped; `FakeTerminal.bells`
  counts them.

## Hyperlinks (OSC 8)

`Style.link` is a per-cell URL that `render_diff` opens and closes as it switches cells, exactly as it switches SGR;
it is not in `STYLE_FIELDS`, so no sheet can declare one. `TerminalInfo.hyperlinks` gates it -- on for any interactive
terminal but `TERM=linux` (whose console prints OSC 8's tail) -- and `NAVKIT_HYPERLINKS=on|off` overrides. Ghostty opens
them with Ctrl+Shift+click.

## Clipboard

`navkit/clipboard.py`: OSC 52 plus `wl-copy`/`xclip`/`xsel`; a requested paste arrives as a `PasteEvent`. A paste
walks the focus path when `Application.on_paste` declines it. `Application.system_clipboard` false makes the clipboard
(and primary selection) private to the application: `copy_to_clipboard` keeps the text and sends nothing out,
`request_clipboard` posts it back as a `PasteEvent`. The private copy is kept either way, so switching off still has
the last copy. A paste the terminal makes on its own is the desktop's regardless.

**No tool and no OSC 52 answer falls back to the private copy.** With the system clipboard on, `_read_clipboard`
queries the terminal and waits `CLIPBOARD_ANSWER_TIMEOUT` (0.5 s); VTE and JediTerm never answer, so after it the
private copy is pasted (`PasteEvent(origin="private")`) and `Application.clipboard_unavailable()` is called once a run,
after that paste is dispatched (Navigator shows a box suggesting xclip/xsel/wl-clipboard). `PasteEvent.origin` is
`"terminal"` (bracketed paste), `"answer"` (the parser's OSC 52 reply) or `"private"`; an `"answer"` arriving with no
query pending is dropped, so a late one cannot paste a second time. Ghostty's `clipboard-read = ask` prompt is usually
slower than the timeout -- `allow` gives the real answer.

## Window title

`Terminal.set_title()` writes OSC 0, and the first one of a run pushes the terminal's own title first (`TITLE_PUSH`,
xterm's `CSI 22;0 t`); `stop()` pops it (`TITLE_POP`), so the shell's title (an ssh session's `user@host /dir`) comes
back on exit. The title cannot be read instead -- `CSI 21 t` is refused nearly everywhere. Repeating the title last sent
writes nothing. `Application.title` is a property: assigned while running, it is written and flushed at once, since a
frame flushes only when a cell changed. Navigator's title is `navigator/lib/system/title.py`'s `user@host ~/dir —
Navigator`, kept on the prompt's directory by `Shell._name_window` (an effect, beside `_follow_panel`).

## Manual checks

For what a fake terminal cannot cover (raw mode, real escapes, `SIGWINCH`), run `python -m navigator` on a pty:
`pty.fork`, `TIOCSWINSZ`, write key bytes to the master fd, read back what it paints. PyCharm's terminal (JediTerm)
repaints unevenly -- check a native terminal before blaming the loop.

## Read when

| Reference | Read when |
|---|---|
| `reference/held-modifier.md` | the kitty protocol and held modifiers |
| `reference/clipboard.md` | OSC 52 and the clipboard tools |
