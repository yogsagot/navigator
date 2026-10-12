# Copy and paste in Navigator

Copying and pasting inside a terminal program is less simple than it looks. Navigator does not own a window, so it
cannot talk to your desktop's clipboard directly the way a graphical editor can. It has two ways to reach it:

- **A small clipboard tool** installed on your computer (`xclip` or `xsel` on X11, `wl-clipboard` on Wayland).
  Navigator hands the text to the tool, and the tool puts it on the clipboard. This is the reliable way.
- **Your terminal.** Navigator can ask the terminal to put text on the clipboard, or to read it back. Some terminals
  do this, some ask you first, and some ignore the request entirely.

On top of that, terminals keep some keys for themselves, so a key that copies in one terminal may never reach
Navigator in another. This guide explains what works where, and how to set things up so that it all just works.

## Quick start

1. **Install a clipboard tool.** Find out which kind of desktop session you are running:

   ```sh
   echo $XDG_SESSION_TYPE
   ```

   Then install the tool for it:

   | Session   | Debian, Ubuntu, Mint          | Fedora                         |
   |-----------|-------------------------------|--------------------------------|
   | `x11`     | `sudo apt install xclip`      | `sudo dnf install xclip`       |
   | `wayland` | `sudo apt install wl-clipboard` | `sudo dnf install wl-clipboard` |

   `xsel` works as well as `xclip`; you only need one of them.

2. **In the editor, use Ctrl+C, Ctrl+X and Ctrl+V.** They work in every terminal tested so far.

3. **If you use Ghostty**, add these lines to `~/.config/ghostty/config` (or `config.ghostty`) and restart Ghostty:

   ```
   keybind = ctrl+insert=unbind
   keybind = shift+insert=unbind
   ```

That is all most people need. The rest of this guide is the detail behind it.

## Keys

The keys depend on where you are in Navigator.

### In the editor (F4)

| To                                         | Press                               |
|--------------------------------------------|-------------------------------------|
| Copy                                       | **Ctrl+C**, Ctrl+Ins or Ctrl+Alt+C  |
| Cut                                        | **Ctrl+X**, Shift+Del or Ctrl+Alt+X |
| Paste                                      | **Ctrl+V**, Shift+Ins or Ctrl+Alt+V |
| Delete the marked block without copying it | Ctrl+Del                            |

All four are also on the editor's **Edit** menu.

Copy and Cut work on the marked block. To mark a block, hold Shift while moving the cursor, or drag with the mouse.

There are three sets of keys because no single set works everywhere:

- **Ctrl+Ins / Shift+Del / Shift+Ins** are the original DOS Navigator keys. Some terminals keep Ctrl+Ins and Shift+Ins
  for themselves (see [Terminal notes](#terminal-notes)).
- **Ctrl+C / Ctrl+X / Ctrl+V** are the keys every other program uses.
- **Ctrl+Alt+C / Ctrl+Alt+X / Ctrl+Alt+V** are a spare set, in case your terminal or desktop takes the other two.

> **Coming from DOS Navigator?** Its editor used Ctrl+C, Ctrl+X and Ctrl+V for Page Down, cursor down and the
> insert/overwrite toggle (WordStar keys). Navigator uses them for the clipboard instead. PgDn, Down and Ins still do
> those jobs, and the other WordStar keys (Ctrl+K…, Ctrl+Q…, Ctrl+E, Ctrl+S and so on) are unchanged.

### In dialog input lines and on the command line

| To    | Press                                                                                                |
|-------|------------------------------------------------------------------------------------------------------|
| Copy  | Ctrl+Ins: copies the selection, or the whole line if nothing is selected. Ctrl+C copies a selection. |
| Cut   | Shift+Del                                                                                            |
| Paste | Shift+Ins or Ctrl+V                                                                                  |

To select text in a line, hold Shift and move the cursor, or drag with the mouse.

On the command line under the panels, **Ctrl+E and Ctrl+X go back and forward through the command history**, so
Ctrl+X does not cut there.

### In the console (Ctrl+O)

Select text by dragging with the mouse, or double-click a word. Then:

| To    | Press                                                                   |
|-------|-------------------------------------------------------------------------|
| Copy  | Ctrl+Ins, or Ctrl+C when no program is running                          |
| Paste | Your terminal's own paste key (usually Ctrl+Shift+V), or a middle click |

When a program is running in the console, Ctrl+C goes to that program (usually to stop it), as you'd expect. Text
you paste goes to the running program too.

### Other ways to copy

- **Calculator**: the *Copy* button puts the result on the clipboard.
- **Screen grabber** (Alt+Shift+Ins): move and size the area with the arrows and Shift+arrows, then press Enter to copy
  that part of the screen as text -- or drag the area out with the mouse, and it is copied when you let go. Esc or a
  right click leaves without copying.
- **Column sum** (Alt+Ins in the editor, with vertical blocks on): adds up the numbers in the marked column and puts
  the total on the clipboard.

## The mouse and the primary selection

On Linux there are really two clipboards:

- the **clipboard**, filled by Copy and read by Paste;
- the **primary selection**, filled just by selecting text and pasted with the middle mouse button.

Navigator follows the same convention. When you drag over text in the editor, the console or an input line, it
becomes the primary selection, and a **middle click** pastes the primary selection. A **double click** selects a
word.

Because Navigator uses the mouse itself, your terminal's own mouse selection is out of reach while Navigator runs.
To use it anyway (to select text the terminal's way, or to reach its right-click menu), **hold Shift** while
dragging or clicking. That works in most terminals.

## Your terminal's own paste

Your terminal has its own paste key, usually **Ctrl+Shift+V**, and a Paste item in its menu. That paste is done by
the terminal: it types the desktop's clipboard into Navigator as if you had typed it. It works whatever Navigator's
settings are and whether or not a clipboard tool is installed.

This is why pasting text copied in another program can work fine while copying *out of* Navigator does not: the
first direction is the terminal's job, the second is Navigator's.

## The "Use system clipboard" setting

**Options > Configuration > System Setup > Use system clipboard**

- **On** (the default): Copy puts text on your desktop's clipboard, so other programs can paste it, and Paste reads
  the desktop's clipboard.
- **Off**: Navigator keeps a private clipboard of its own, as DOS Navigator did. Nothing you copy leaves Navigator.
  Your terminal's own paste (Ctrl+Shift+V) still brings in whatever the desktop's clipboard holds.

Navigator always keeps its own copy of the last thing you copied, whichever way this is set.

## Terminal notes

Some terminals keep keys for themselves before Navigator ever sees them, and they differ in whether they let a
program use the clipboard.

| Terminal                                  | Takes for itself                              | Lets Navigator use the clipboard | What to do                               |
|-------------------------------------------|-----------------------------------------------|----------------------------------|------------------------------------------|
| **Ghostty**                               | Ctrl+Ins, Shift+Ins, Shift+PgUp/PgDn/Home/End | Copy: yes. Paste: asks you first | Unbind the keys (below)                  |
| **xfce4-terminal, GNOME Terminal, Tilix** | Ctrl+Ins, Shift+Ins (cannot be changed)       | No                               | Install a clipboard tool; use Ctrl+C/X/V |
| **PyCharm and other JetBrains terminals** | –                                             | No                               | Install a clipboard tool                 |

### Ghostty

By default Ghostty uses **Ctrl+Ins** to copy its own selection and **Shift+Ins** to paste the primary selection,
so those keys never reach Navigator. It also uses Shift+PgUp, Shift+PgDn, Shift+Home and Shift+End to scroll, which
the editor needs for marking text. Add this to Ghostty's config file and restart Ghostty (close every window; a new
tab is not enough):

```
keybind = ctrl+insert=unbind
keybind = shift+insert=unbind
keybind = shift+page_up=unbind
keybind = shift+page_down=unbind
keybind = shift+home=unbind
keybind = shift+end=unbind
```

You can still copy and paste in Ghostty itself with Ctrl+Shift+C and Ctrl+Shift+V.

Ghostty asks for permission before a program may *read* the clipboard. If you have no clipboard tool installed,
Navigator does not wait for your answer and pastes its own last copy instead. To let Navigator read the clipboard
without asking, add:

```
clipboard-read = allow
```

To see which keys Ghostty binds, run `ghostty +list-keybinds --default`.

### xfce4-terminal, GNOME Terminal, Tilix

These terminals are all built on the same library (VTE), which handles **Ctrl+Ins** (copy) and **Shift+Ins** (paste
the primary selection) itself. There is no setting to give these keys back, so use **Ctrl+C / Ctrl+X / Ctrl+V** (or
Ctrl+Alt+C / X / V) instead.

They also ignore a program's requests to use the clipboard, so **a clipboard tool is required** for copying out of
Navigator.

In **xfce4-terminal**, also open *Edit > Preferences > Advanced* and turn on **Disable all menu access keys** and
**Disable menu shortcut key**. Otherwise the terminal opens its own menus on Alt+E, Alt+F, Alt+V, Alt+T, Alt+B,
Alt+H and F10, which Navigator uses. This has nothing to do with the clipboard, but it is the next thing you would
run into.

### PyCharm and other JetBrains IDEs

The built-in terminal ignores a program's requests to use the clipboard, so install a clipboard tool. With *Use
system clipboard* off, copying and pasting inside Navigator works without one.

## Without a clipboard tool

Navigator still works without a clipboard tool installed:

- Copy and paste **inside Navigator** work. When the desktop's clipboard cannot be read, Navigator pastes its own
  last copy. The first time this happens, a message suggests installing a clipboard tool.
- Copying **out of Navigator** to other programs works only if your terminal accepts the request (Ghostty does;
  xfce4-terminal, GNOME Terminal and PyCharm do not).
- Pasting **into Navigator** from other programs always works with your terminal's own paste key (Ctrl+Shift+V).

The catch is that Navigator's Paste may then paste what *you last copied in Navigator*, not what you copied in
another program since.

## Over ssh and in tmux

When Navigator runs on another machine over ssh, there is no desktop there, so no clipboard tool can help. Navigator
then asks your **local** terminal to do the copying (using a terminal feature called OSC 52). Whether that works
depends on your terminal: Ghostty, kitty, WezTerm, Alacritty and foot accept copies; VTE terminals do not.

Inside **tmux**, let tmux pass the requests on by adding this to `~/.tmux.conf`:

```
set -g set-clipboard on
```

If a terminal prints garbage when you copy, you can switch the terminal route off by starting Navigator with
`NAVKIT_CLIPBOARD=off nav`.

## Troubleshooting

**Copy does nothing, or the text doesn't arrive in other programs.**
No clipboard tool is installed, and your terminal ignores Navigator's request. Install `xclip` or `wl-clipboard`
(see [Quick start](#quick-start)).

**Paste pastes old text, not what I just copied in another program.**
Navigator couldn't read the desktop's clipboard and used its own last copy. Install a clipboard tool. In Ghostty you
can also set `clipboard-read = allow`. Until then, use your terminal's paste key (Ctrl+Shift+V).

**Shift+Ins pastes something different from Ctrl+V.**
Your terminal caught Shift+Ins and pasted the *primary selection* (the last text you highlighted anywhere) instead of
the clipboard. In Ghostty, unbind it as shown above. In xfce4-terminal and GNOME Terminal, use Ctrl+V.

**A key does nothing at all.**
Your terminal or desktop probably keeps that key. From a Navigator source checkout you can see what actually
arrives:

```sh
./venv/bin/python tools/keyprobe.py
```

Press the key. If nothing is printed, the terminal kept it. Press `q` twice to quit. Use another of the keys listed
above, or bind your own (next section).

**It works in one terminal and not in another.**
That is expected. Check that terminal in [Terminal notes](#terminal-notes).

## Changing the keys

Every key is yours to change in **Options > Configuration > Key bindings**, or in
`~/.config/navigator/keybindings.ini`. A command can have several keys, separated by commas:

```ini
clipboard_cut = shift+delete, ctrl+x, ctrl+alt+x
clipboard_copy = ctrl+insert, ctrl+c, ctrl+alt+c
clipboard_paste = shift+insert, ctrl+v, ctrl+alt+v
```

A key can belong to only one command in the same place. To give Ctrl+C to something else in the editor, take it away
from `clipboard_copy` first.

Navigator writes the file with all its defaults when it first starts, and keeps what is written there. If your file
is older than a change to the defaults, it keeps your old keys. Choose the command in the Key bindings dialog and
press **Default** to take the new ones.
