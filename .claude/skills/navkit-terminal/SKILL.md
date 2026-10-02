---
name: navkit-terminal
description: The tty layer (navkit/terminal.py, capabilities.py, clipboard.py) -- raw mode, the alternate screen, mouse and bracketed paste, InputParser and escape timeouts, the kitty keyboard protocol and held modifiers, keypad and Ctrl+H/Backspace decoding, TerminalInfo detection and NAVKIT_* overrides, OSC 8 hyperlinks, the OSC 52 clipboard, and tools/keyprobe.py. Use when a key arrives wrong, a terminal behaves differently, or adding a terminal feature.
---

# The terminal layer

- `Terminal` owns the tty (raw mode, alternate screen, mouse tracking, bracketed paste, autowrap off, application keypad)
  and restores it in `Application`'s `finally`. `InputParser` is fed incrementally and keeps undecodable tails. **A lone
  `ESC` is ambiguous**: the parser reports `pending_escape` and the application resolves it with `ESCAPE_TIMEOUT`.
- `TerminalInfo` (`capabilities.py`) is what the terminal supports (`colors`, `alt_screen`, `mouse`, `bracketed_paste`,
  `title`, `keypad`, `hyperlinks`, `glyphs`, `palette`). Detection is conservative -- sixteen colours unless `COLORTERM`
  says otherwise; `NAVKIT_COLORS` (`truecolor`, `256`, `16`, `8`, `mono`, a number) overrides and outranks `NO_COLOR`.
  Colour/palette/glyph decisions are the `colours-themes-glyphs` skill.

## Keys

- **The kitty keyboard protocol** is pushed without asking; `NAVKIT_KEYBOARD=legacy` turns it off. Only it reports a
  held modifier (`Application.modifiers`, which the key bar reads).
- **Ctrl+H vs Backspace**: a legacy terminal sends Ctrl+H as 0x08, which navkit reads as Ctrl+H only once the tty's
  erase character (`Terminal.erase`, termios `VERASE`, read before raw mode) says Backspace is 0x7F, and as Backspace
  otherwise (`InputParser.ctrl_h`).
- Keypad operators are named `kp_plus`/`kp_minus`/`kp_multiply`/`kp_divide` (`char` kept), from kitty codes or from
  `SS3` under application keypad mode. xfce4-terminal (VTE) and PyCharm send Gray `+` as a bare `+` even then (named
  `plus`); only Ghostty told them apart, which is why Navigator binds the plain keys too.
- A terminal without the kitty protocol sends Ctrl+Enter as Enter; Ghostty keeps Ctrl+Enter and Ctrl+Shift+Enter
  unless unbound (`keybind = ctrl+enter=unbind`). xfce4-terminal eats Alt+E/F/V/T/B/H unless menu access keys are off.
- **Find out what a terminal sends**: `./venv/bin/python tools/keyprobe.py [--legacy] [--no-mouse]` (`q` twice or
  Ctrl+C quits) -- e.g. whether Ctrl+Shift+V arrives as a paste or a key.

## Hyperlinks (OSC 8)

`Style.link` is a per-cell URL that `render_diff` opens and closes as it switches cells, exactly as it switches SGR;
it is not in `STYLE_FIELDS`, so no sheet can declare one. `TerminalInfo.hyperlinks` gates it -- on for any interactive
terminal but `TERM=linux` (whose console prints OSC 8's tail) -- and `NAVKIT_HYPERLINKS=on|off` overrides. Ghostty opens
them with Ctrl+Shift+click.

## Clipboard

`navkit/clipboard.py`: OSC 52 plus `wl-copy`/`xclip`/`xsel`; a requested paste arrives as a `PasteEvent`. A paste
walks the focus path when `Application.on_paste` declines it.

## Manual checks

For what a fake terminal cannot cover (raw mode, real escapes, `SIGWINCH`), run `python -m navigator` on a pty:
`pty.fork`, `TIOCSWINSZ`, write key bytes to the master fd, read back what it paints. PyCharm's terminal (JediTerm)
repaints unevenly -- check a native terminal before blaming the loop.

## Read when

| Reference | Read when |
|---|---|
| `reference/held-modifier.md` | the kitty protocol and held modifiers |
| `reference/clipboard.md` | OSC 52 and the clipboard tools |
