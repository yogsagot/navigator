## The held modifier: the kitty keyboard protocol

DOS Navigator swapped its status line while a modifier was held, which is the `-`, `+` and `:` items of a
`StatusDef`. A legacy terminal cannot report that: it sends no bare modifier press and no key release. Only the kitty
keyboard protocol does, with flag 2 (event types) and flag 8 (every key as an escape, modifiers included). kitty,
WezTerm, Ghostty, foot and Alacritty speak it. xterm, VTE, JediTerm and tmux do not, and there the key bar keeps its
plain row. **Nothing is simulated.** A "sticky" layer switched on by a modified F-key and off by the next key was
rejected, because it is a modern invention that shows a row nobody is holding.

- **Pushed without asking.** `Terminal.start` writes `CSI > 31 u` and `stop` writes `CSI < u`. The flags are 1, 2, 4,
  8 and 16: 4 and 16 are there so text keys still arrive with the character they type. Pushing onto the terminal's
  own stack means `run_on_terminal`'s stop/start hands a child a legacy terminal. A terminal that does not know the
  sequence ignores it, which is also Neovim's bet. A query would cost a round trip and an input path for its reply,
  and would learn nothing the parser does not learn from the first kitty-form key. `NAVKIT_KEYBOARD=legacy` is the
  way out, and `TerminalInfo.kitty_keyboard` is the flag.
- **Every kitty key decodes to the event its legacy form already produces.** A table-driven test pins this, so key
  tables, `encode_key` and the console's child see nothing new. The only differences are what legacy could not
  say: Ctrl+I is `ctrl+i` rather than Tab, and Escape needs no timeout.
- **The parser owns the held set, and only kitty-form input may move it.** Kitty-form means a `u` terminator or an
  explicit `:event` type. A legacy Ctrl+F5 is followed by no release, so letting it set the state would leave Ctrl
  held for good. A kitty press carries the whole held set, so each one also corrects a release that went missing.
- **Losing the focus forgets everything held.** Focus reporting (`?1004`) comes with the push. A release made
  after Alt+Tab to another window is delivered to that window, so focus-out is the only cue the application gets.
- **`ModifiersEvent` becomes `Application.modifiers` and goes no further**, the way a plain motion becomes
  `hovered`. It is reactive, so a key bar that reads it in `render()` repaints on the press and on the release.
  `commands.layer_key(held, "f6")` spells the key to look up.

**A key release is a `KeyReleaseEvent`, and it goes to the focused widget alone.** The parser used to drop every
kitty release; a button that clicks when Space is *let go*, as its mouse click does, needed one. It is a class of its
own rather than a flag on `KeyEvent`, so no key table, `on_key`, `encode_key` or child program ever meets a release it
was not written for. `Application._handle` offers it to `on_event` and then to `focused.on_key_release` (inside the
modal, as a key would be), and nowhere else: no key table and no walk up, because a release means something only to
whoever took the press. **A widget waiting for one has to know whether it will come**, and a legacy terminal never
sends it, so the press says: `KeyEvent.releases` is True for a key that arrived in kitty form. It is
`compare=False`, because it says how a key travelled rather than which key it was, and every test comparing a kitty
key with its legacy twin keeps passing. `Button` is the one reader; with no release promised it flashes instead.

The key bar's rows come from the same bindings as its plain row. When a modifier is held, a row shows every titled
binding whose modifiers are exactly the ones held: function keys first, in order, then letters in `bindings()` order.
`bindings()` is therefore **nearest table first**, and the application's table still wins every tie. Each item shows
the key alone (`F6`, `B`), because the row already says which modifier is down, exactly as `~F6~` did.
`SizeMoveWindow`, `NextWindow` and `PreviousWindow` are untitled, as both Turbo Vision's and DOS Navigator's
status lines left them. Next and Previous are on F9 and Shift+F9, DOS Navigator's `cmNext`/`cmPrev` keys, which
freed Ctrl+F6 for *Calc*. A greyed binding falls through to whatever an outer table binds the same key to, so
while the desktop held Ctrl+F6 the row would have named Calc while the key switched windows. One deviation
remains: the desktop's Ctrl+F4 *Close* shows on the file manager's Ctrl row, which DOS Navigator's file panel did
not caption, and at 80 columns it pushes *Show* off the end.

