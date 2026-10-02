## Clipboard: OSC 52 and the tools beside it

Navigator tracks the mouse (1000/1002/1003), so while it runs the terminal's own selection, its middle-click paste and
its right-click menu are out of reach; Shift+drag still reaches them on most terminals. A copy and a paste therefore
have to be navkit's, and a terminal application has two routes to a clipboard, neither enough alone.

- **OSC 52** (`clipboard_osc`, `clipboard_query`) asks the terminal. It works over ssh and inside tmux and needs
  nothing installed. But VTE and JediTerm ignore it, and most terminals that honour a *write* refuse a *read* or ask
  the user first. `TerminalInfo.clipboard` gates it: on everywhere interactive except `TERM=linux`, whose console
  would print it, and `NAVKIT_CLIPBOARD` overrides.
- **The desktop's tools** (`navkit/clipboard.py`: `wl-copy`/`wl-paste`, `xclip`, `xsel`) work whatever the
  terminal, but only on the machine whose display it is, and only if one is installed.

So **a copy goes both ways** (`Application.copy_to_clipboard`, the tool in an executor, never awaited), and **a paste
tries the tool first and asks the terminal only if there is none** (`Application.request_clipboard`). Either answer
becomes a `PasteEvent`. `InputParser` decodes the OSC 52 reply into one, so a paste the user asked Navigator for and
a paste the terminal made itself take one path. Only `ESC ] 52 ;` is decoded as an OSC: `ESC ]` alone is also Alt+],
and a partial head that never completes flushes back into Alt+] rather than into Escape. A clipboard reply still
arriving is never taken for a lone ESC.

**A paste now walks the focus path** (`Widget.dispatch_paste`) when `Application.on_paste` returns False, the way a
key does. That is what lets a dialog's input line take one. Before this, a paste reached the application hook and
nothing else, so under a dialog it went nowhere.

Ctrl+Shift+V was reported not to paste while Shift+Insert did. The likeliest cause is the kitty flags: flag 8 asks
for every key as an escape, and a terminal may then report Ctrl+Shift+V as a key instead of running its own paste
binding. `tools/keyprobe.py` puts a terminal in exactly Navigator's modes and prints what arrives (`--legacy`,
`--no-mouse`), and that is where the question gets answered per terminal. Meanwhile `InputLine` binds Ctrl+V and
Shift+Ins to `request_clipboard` as well, so a paste key that reaches Navigator as a key still pastes.

